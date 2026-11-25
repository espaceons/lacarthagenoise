import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import EmailMessage
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import ContactForm
from .models import MessageContact

logger = logging.getLogger(__name__)


def AboutView(request):
    """Affiche la page À propos de La Carthagenoise."""
    return render(request, 'pages/a_propos.html')


def ContactView(request):
    """Affiche et traite le formulaire de contact de La Carthagenoise."""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            nom = form.cleaned_data['nom']
            email_visiteur = form.cleaned_data['email']
            telephone = form.cleaned_data['telephone'] or ''
            sujet = form.cleaned_data['sujet']
            message = form.cleaned_data['message']

            # Enregistrement en base pour l'interface de réception administrateur
            MessageContact.objects.create(
                nom=nom,
                email=email_visiteur,
                telephone=telephone,
                sujet=sujet,
                message=message,
            )

            destinataire = getattr(
                settings, 'CONTACT_EMAIL', 'contact@lacarthagenoise.com'
            )
            expediteur_smtp = getattr(
                settings, 'DEFAULT_FROM_EMAIL', destinataire
            )

            contenu = (
                "Nouveau message reçu depuis le site La Carthagenoise :\n\n"
                f"Nom : {nom}\n"
                f"Email : {email_visiteur}\n"
                f"Téléphone : {telephone or 'Non renseigné'}\n"
                f"Sujet : {sujet}\n\n"
                f"Message :\n{message}"
            )

            email_msg = EmailMessage(
                subject=f"[Contact La Carthagenoise] {sujet}",
                body=contenu,
                from_email=f"{nom} <{expediteur_smtp}>",
                to=[destinataire],
                reply_to=[email_visiteur],
            )

            try:
                email_msg.send(fail_silently=False)
            except Exception as exc:
                logger.exception(
                    "Erreur lors de l'envoi de l'email de contact : %s", exc
                )
                messages.warning(
                    request,
                    "Votre message a bien été enregistré, mais l'envoi de notification email a rencontré un souci technique.",
                )
            else:
                messages.success(
                    request,
                    "Votre message a bien été envoyé. Nous vous répondrons dans les plus brefs délais.",
                )
            return redirect('pages:contact')
        else:
            messages.error(
                request,
                "Veuillez corriger les erreurs indiquées dans le formulaire.",
            )
    else:
        form = ContactForm()

    return render(request, 'pages/contact.html', {'form': form})


@staff_member_required(login_url='utilisateur:login')
def liste_messages_contact(request):
    """Interface administrateur de réception des messages de contact."""
    etat_filtre = request.GET.get('etat', '').strip()
    recherche = request.GET.get('q', '').strip()

    qs = MessageContact.objects.all()

    if etat_filtre == 'non_lu':
        qs = qs.filter(lu=False)
    elif etat_filtre == 'lu':
        qs = qs.filter(lu=True)

    if recherche:
        qs = qs.filter(
            Q(nom__icontains=recherche)
            | Q(email__icontains=recherche)
            | Q(sujet__icontains=recherche)
            | Q(message__icontains=recherche)
        )

    stats = {
        'total': MessageContact.objects.count(),
        'non_lus': MessageContact.objects.filter(lu=False).count(),
        'lus': MessageContact.objects.filter(lu=True).count(),
    }

    context = {
        'messages_contact': qs,
        'stats': stats,
        'etat_filtre': etat_filtre,
        'recherche': recherche,
    }
    return render(request, 'pages/messages_contact.html', context)


@staff_member_required(login_url='utilisateur:login')
def repondre_message_contact(request, message_id):
    """Envoie une réponse par email au visiteur depuis l'interface d'administration."""
    if request.method == 'POST':
        msg = get_object_or_404(MessageContact, pk=message_id)
        sujet_reponse = (
            request.POST.get('sujet_reponse', '').strip() or f"Re: {msg.sujet}"
        )
        contenu_reponse = request.POST.get('contenu_reponse', '').strip()

        if not contenu_reponse:
            messages.error(
                request, "Veuillez saisir le texte de votre réponse.")
            return redirect('pages:liste_messages_contact')

        expediteur_smtp = getattr(
            settings, 'DEFAULT_FROM_EMAIL', 'contact@lacarthagenoise.com'
        )

        corps_email = (
            f"Bonjour {msg.nom},\n\n"
            f"{contenu_reponse}\n\n"
            "Cordialement,\n"
            "L'équipe La Carthagenoise\n"
            "----------------------------------------\n"
            f"Votre message initial ({msg.date_envoi.strftime('%d/%m/%Y %H:%M')}) :\n"
            f"{msg.message}"
        )

        email_msg = EmailMessage(
            subject=sujet_reponse,
            body=corps_email,
            from_email=f"La Carthagenoise <{expediteur_smtp}>",
            to=[msg.email],
            reply_to=[expediteur_smtp],
        )

        try:
            email_msg.send(fail_silently=False)
        except Exception as exc:
            logger.exception(
                "Erreur lors de l'envoi de la réponse au message #%s : %s",
                msg.id,
                exc,
            )
            messages.error(
                request,
                "Échec de l'envoi de l'email de réponse. Vérifiez la configuration SMTP.",
            )
        else:
            msg.lu = True
            msg.repondu = True
            msg.reponse = contenu_reponse
            msg.date_reponse = timezone.now()
            msg.save(update_fields=['lu', 'repondu',
                     'reponse', 'date_reponse'])
            messages.success(
                request,
                f"Votre réponse a bien été envoyée à {msg.nom} ({msg.email}).",
            )

    return redirect('pages:liste_messages_contact')


@staff_member_required(login_url='utilisateur:login')
def marquer_message_contact(request, message_id):
    """Bascule ou force l'état lu/non lu d'un message de contact."""
    if request.method == 'POST':
        msg = get_object_or_404(MessageContact, pk=message_id)
        action = request.POST.get('action', 'toggle')
        if action == 'lu':
            msg.lu = True
        elif action == 'non_lu':
            msg.lu = False
        else:
            msg.lu = not msg.lu
        msg.save(update_fields=['lu'])
        messages.success(request, "Statut du message mis à jour.")
    return redirect('pages:liste_messages_contact')


@staff_member_required(login_url='utilisateur:login')
def supprimer_message_contact(request, message_id):
    """Supprime définitivement un message de contact."""
    if request.method == 'POST':
        msg = get_object_or_404(MessageContact, pk=message_id)
        msg.delete()
        messages.success(request, "Message supprimé.")
    return redirect('pages:liste_messages_contact')
