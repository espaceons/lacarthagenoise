import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .forms import ContactForm
from .models import MessageContact

logger = logging.getLogger(__name__)


def _a_champ_utilisateur():
    return any(field.name == 'utilisateur' for field in MessageContact._meta.get_fields())


def _est_admin(user):
    return bool(user.is_authenticated and (user.is_staff or user.is_superuser))


def _est_proprietaire_message(user, msg):
    if not user.is_authenticated:
        return False
    if _a_champ_utilisateur() and getattr(msg, 'utilisateur_id', None) == user.pk:
        return True
    email_user = (user.email or '').strip()
    return bool(email_user and (msg.email or '').strip().lower() == email_user.lower())


def _queryset_messages_pour_utilisateur(user):
    """Retourne tous les messages pour l'admin, ou uniquement ceux de l'utilisateur."""
    if _est_admin(user):
        return MessageContact.objects.all()

    email_user = (user.email or '').strip()
    filtre = Q(email__iexact=email_user) if email_user else Q(pk__in=[])

    if _a_champ_utilisateur():
        filtre = Q(utilisateur=user) | filtre

    return MessageContact.objects.filter(filtre)

def AboutView(request):
    """Affiche la page À propos de La Carthagenoise."""
    return render(request, 'pages/a_propos.html')

def ContactView(request):
    """Affiche et traite le formulaire de contact de La Carthagenoise."""
    initial_data = {}
    if request.user.is_authenticated:
        full_name = request.user.get_full_name().strip() or request.user.username
        initial_data = {
            'nom': full_name,
            'email': request.user.email,
        }

    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            nom = form.cleaned_data['nom']
            email_visiteur = form.cleaned_data['email']
            telephone = form.cleaned_data['telephone'] or ''
            sujet = form.cleaned_data['sujet']
            message = form.cleaned_data['message']

            create_kwargs = {
                'nom': nom,
                'email': email_visiteur,
                'telephone': telephone,
                'sujet': sujet,
                'message': message,
            }
            if request.user.is_authenticated and _a_champ_utilisateur():
                create_kwargs['utilisateur'] = request.user

            # Enregistrement en base pour la boîte de messagerie
            MessageContact.objects.create(**create_kwargs)

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

        messages.error(
            request,
            "Veuillez corriger les erreurs indiquées dans le formulaire.",
        )
    else:
        form = ContactForm(initial=initial_data)

    return render(request, 'pages/contact.html', {'form': form})


@login_required(login_url='utilisateur:login')
def liste_messages_contact(request):
    """Boîte de messagerie : tous les messages pour l'admin, ses propres messages pour l'utilisateur."""
    est_admin = _est_admin(request.user)
    etat_filtre = request.GET.get('etat', '').strip()
    recherche = request.GET.get('q', '').strip()

    base_qs = _queryset_messages_pour_utilisateur(request.user)

    if est_admin:
        non_lus_qs = base_qs.filter(lu=False)
        lus_qs = base_qs.filter(lu=True)
    else:
        non_lus_qs = base_qs.filter(lu=False, repondu=True)
        lus_qs = base_qs.exclude(pk__in=non_lus_qs.values('pk'))

    qs = base_qs
    if etat_filtre == 'non_lu':
        qs = non_lus_qs
    elif etat_filtre == 'lu':
        qs = lus_qs

    if recherche:
        qs = qs.filter(
            Q(nom__icontains=recherche)
            | Q(email__icontains=recherche)
            | Q(sujet__icontains=recherche)
            | Q(message__icontains=recherche)
        )

    stats = {
        'total': base_qs.count(),
        'non_lus': non_lus_qs.count(),
        'lus': lus_qs.count(),
    }

    context = {
        'messages_contact': qs,
        'stats': stats,
        'etat_filtre': etat_filtre,
        'recherche': recherche,
        'est_admin': est_admin,
    }
    return render(request, 'pages/messages_contact.html', context)


@login_required(login_url='utilisateur:login')
@require_POST
def repondre_message_contact(request, message_id):
    """Envoie une réponse par email (admin -> client ou client -> atelier) et met à jour le fil."""
    msg = get_object_or_404(MessageContact, pk=message_id)
    est_admin = _est_admin(request.user)
    email_utilisateur = (request.user.email or '').strip()

    if not est_admin and not _est_proprietaire_message(request.user, msg):
        messages.error(
            request, "Vous n'êtes pas autorisé à répondre à ce message."
        )
        return redirect('pages:liste_messages_contact')

    sujet_reponse = (
        request.POST.get('sujet_reponse', '').strip() or f"Re: {msg.sujet}"
    )
    contenu_reponse = request.POST.get('contenu_reponse', '').strip()

    if not contenu_reponse:
        messages.error(request, "Veuillez saisir le texte de votre réponse.")
        return redirect('pages:liste_messages_contact')

    expediteur_smtp = getattr(
        settings, 'DEFAULT_FROM_EMAIL', 'contact@lacarthagenoise.com'
    )
    email_atelier = getattr(settings, 'CONTACT_EMAIL', expediteur_smtp)
    horodatage = timezone.now().strftime('%d/%m/%Y %H:%M')
    date_envoi_str = msg.date_envoi.strftime(
        '%d/%m/%Y %H:%M') if msg.date_envoi else ''

    if est_admin:
        corps_email = (
            f"Bonjour {msg.nom},\n\n"
            f"{contenu_reponse}\n\n"
            "Cordialement,\n"
            "L'équipe La Carthagenoise\n"
            "----------------------------------------\n"
            f"Votre message initial ({date_envoi_str}) :\n"
            f"{msg.message}"
        )
        email_msg = EmailMessage(
            subject=sujet_reponse,
            body=corps_email,
            from_email=f"La Carthagenoise <{expediteur_smtp}>",
            to=[msg.email],
            reply_to=[expediteur_smtp],
        )
        auteur_fil = "Atelier La Carthagenoise"
    else:
        reply_to_addr = email_utilisateur or msg.email
        corps_email = (
            f"Nouvelle réponse de {msg.nom} ({reply_to_addr}) concernant : {msg.sujet}\n\n"
            f"{contenu_reponse}\n\n"
            "----------------------------------------\n"
            f"Message initial ({date_envoi_str}) :\n"
            f"{msg.message}"
        )
        email_msg = EmailMessage(
            subject=sujet_reponse,
            body=corps_email,
            from_email=f"La Carthagenoise <{expediteur_smtp}>",
            to=[email_atelier],
            reply_to=[reply_to_addr],
        )
        auteur_fil = f"{msg.nom} (Client)"

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
        nouvelle_entree = f"[{auteur_fil} - {horodatage}]\n{contenu_reponse}"
        if msg.reponse:
            msg.reponse = f"{msg.reponse}\n\n----------------------------------------\n{nouvelle_entree}"
        else:
            msg.reponse = nouvelle_entree

        if est_admin:
            # Reste "Non lu" pour l'admin tant qu'il ne le marque pas lu, avec badge "Répondu"
            msg.lu = False
            msg.repondu = True
            msg.date_reponse = timezone.now()
            msg.save(update_fields=['lu', 'repondu',
                     'reponse', 'date_reponse'])
            messages.success(
                request,
                f"Votre réponse a bien été envoyée à {msg.nom} ({msg.email}).",
            )
        else:
            # Réponse du client : notifie l'atelier (lu=False, repondu=False)
            msg.lu = False
            msg.repondu = False
            msg.save(update_fields=['lu', 'repondu', 'reponse'])
            messages.success(
                request,
                "Votre réponse a bien été envoyée à l'atelier La Carthagenoise.",
            )

    return redirect('pages:liste_messages_contact')


@login_required(login_url='utilisateur:login')
@require_POST
def marquer_message_contact(request, message_id):
    """Bascule ou force l'état lu/non lu d'un message de contact (admin ou propriétaire)."""
    msg = get_object_or_404(MessageContact, pk=message_id)
    est_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if not _est_admin(request.user) and not _est_proprietaire_message(request.user, msg):
        if est_ajax:
            return JsonResponse(
                {'ok': False, 'error': "Vous n'êtes pas autorisé à modifier ce message."},
                status=403,
            )
        messages.error(
            request, "Vous n'êtes pas autorisé à modifier ce message.")
        return redirect('pages:liste_messages_contact')

    action = request.POST.get('action', 'toggle')
    if action == 'lu':
        msg.lu = True
    elif action == 'non_lu':
        msg.lu = False
    else:
        msg.lu = not msg.lu

    msg.save(update_fields=['lu'])

    if est_ajax:
        return JsonResponse({'ok': True, 'id': msg.id, 'lu': msg.lu})

    if action != 'lu':
        messages.success(request, "Statut du message mis à jour.")

    return redirect('pages:liste_messages_contact')


@staff_member_required(login_url='utilisateur:login')
@require_POST
def supprimer_message_contact(request, message_id):
    """Supprime définitivement un message de contact."""
    msg = get_object_or_404(MessageContact, pk=message_id)
    msg.delete()
    messages.success(request, "Message supprimé.")
    return redirect('pages:liste_messages_contact')
