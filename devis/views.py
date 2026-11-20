# devis/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction

from catalogue.models import Produit
from .models import Devis, LigneDevis

# Clé de session utilisée pour stocker le panier de devis
DEVIS_SESSION_KEY = 'devis_panier'


def _get_quantite_demander(item_data):
    """Récupère la quantité demandée dans la session (avec repli sur 'quantite' si nécessaire)."""
    return int(item_data.get('quantite_demander', item_data.get('quantite', 1)))


# -------------------------------------------
# 1. ADD / REMOVE / CLEAR LOGIC (Session Management)
# -------------------------------------------

def add_to_devis(request, produit_id):
    """Ajoute un produit avec la quantité demandée à la liste de devis stockée dans la session."""
    produit = get_object_or_404(Produit, pk=produit_id)

    quantite_raw = request.POST.get(
        'quantite_demander', request.GET.get('quantite_demander', 1)
    )
    try:
        quantite_demander = int(quantite_raw)
    except (ValueError, TypeError):
        quantite_demander = 1

    if quantite_demander < 1:
        messages.error(
            request, "La quantité demandée doit être supérieure ou égale à 1."
        )
        return redirect(
            request.META.get('HTTP_REFERER', reverse(
                'catalogue:liste_produits'))
        )

    stock_dispo = getattr(produit, 'quantite_restante', None)
    if stock_dispo is not None and stock_dispo > 0 and quantite_demander > stock_dispo:
        messages.warning(
            request,
            f"Quantité ajustée au stock disponible ({stock_dispo}) pour '{produit.nom}'.",
        )
        quantite_demander = stock_dispo

    devis_panier = request.session.get(DEVIS_SESSION_KEY, {})
    produit_key = str(produit_id)

    if produit_key in devis_panier:
        ancienne_qte = _get_quantite_demander(devis_panier[produit_key])
        nouvelle_qte = ancienne_qte + quantite_demander
        if stock_dispo is not None and stock_dispo > 0 and nouvelle_qte > stock_dispo:
            nouvelle_qte = stock_dispo
        devis_panier[produit_key]['quantite_demander'] = nouvelle_qte
        devis_panier[produit_key].pop('quantite', None)
        messages.info(
            request,
            f"Quantité demandée pour '{produit.nom}' mise à jour (total : {nouvelle_qte}).",
        )
    else:
        devis_panier[produit_key] = {
            'nom': produit.nom,
            'reference': produit.reference,
            'quantite_demander': quantite_demander,
            'image_url': produit.image.url if produit.image else None,
        }
        messages.success(
            request,
            f"{quantite_demander} x '{produit.nom}' ajouté(s) à votre liste de devis.",
        )

    request.session[DEVIS_SESSION_KEY] = devis_panier
    request.session.modified = True

    return redirect(
        request.META.get('HTTP_REFERER', reverse('catalogue:liste_produits'))
    )


def remove_from_devis(request, produit_id):
    """Retire complètement ou réduit la quantité demandée d'un produit."""
    devis_panier = request.session.get(DEVIS_SESSION_KEY, {})
    produit_key = str(produit_id)

    if produit_key in devis_panier:
        qte_actuelle = _get_quantite_demander(devis_panier[produit_key])
        if qte_actuelle > 1:
            devis_panier[produit_key]['quantite_demander'] = qte_actuelle - 1
            devis_panier[produit_key].pop('quantite', None)
            messages.warning(
                request,
                f"Quantité de '{devis_panier[produit_key]['nom']}' réduite.",
            )
        else:
            del devis_panier[produit_key]
            messages.error(request, "Article retiré de la liste de devis.")

        request.session[DEVIS_SESSION_KEY] = devis_panier
        request.session.modified = True

    return redirect('devis:view_devis')


def clear_devis(request):
    """Vide toute la liste de devis."""
    if DEVIS_SESSION_KEY in request.session:
        del request.session[DEVIS_SESSION_KEY]
        request.session.modified = True
        messages.success(request, "Votre liste de devis a été vidée.")

    return redirect('devis:view_devis')


# -------------------------------------------
# 2. VIEW DEVIS (Affichage)
# -------------------------------------------

def view_devis(request):
    """Affiche le contenu du panier et rend le template view_devis.html."""
    devis_panier_session = request.session.get(DEVIS_SESSION_KEY, {})
    devis_items = []

    for produit_id, item_data in devis_panier_session.items():
        try:
            produit = Produit.objects.get(pk=produit_id)
            quantite_demander = _get_quantite_demander(item_data)
            devis_items.append({
                'produit': produit,
                'quantite': quantite_demander,
                'quantite_demander': quantite_demander,
            })
        except Produit.DoesNotExist:
            continue

    context = {
        'devis_items': devis_items,
        'devis_panier_session': devis_panier_session,
    }
    return render(request, 'devis/view_devis.html', context)


# -------------------------------------------
# 3. SUBMIT LOGIC (Formulaire et Envoi en BD)
# -------------------------------------------

@transaction.atomic
def submit_devis(request):
    """Gère l'envoi de la demande de devis et l'enregistre en base de données."""
    devis_panier = request.session.get(DEVIS_SESSION_KEY)

    if not devis_panier:
        messages.error(
            request, "Impossible de soumettre : votre liste de devis est vide."
        )
        return redirect('devis:view_devis')

    if request.method == 'POST':
        nom_client = request.POST.get('nom_client', '').strip()
        email_client = request.POST.get('email_client', '').strip()
        telephone = request.POST.get('telephone', '').strip()

        if request.user.is_authenticated:
            if not nom_client:
                nom_client = request.user.get_full_name() or request.user.username
            if not email_client:
                email_client = request.user.email
            if not telephone and hasattr(request.user, 'profil'):
                telephone = request.user.profil.telephone or ''

        devis = Devis.objects.create(
            utilisateur=request.user if request.user.is_authenticated else None,
            nom_client=nom_client or None,
            email_client=email_client or None,
            telephone=telephone or None,
            statut='attente',
        )

        lignes_creees = 0
        for produit_id, item_data in devis_panier.items():
            try:
                produit = Produit.objects.get(pk=produit_id)
                quantite_demander = _get_quantite_demander(item_data)

                LigneDevis.objects.create(
                    devis=devis,
                    produit=produit,
                    quantite=quantite_demander,
                    prix_unitaire=produit.prix if produit.prix else 0,
                )
                lignes_creees += 1
            except Produit.DoesNotExist:
                continue

        if lignes_creees == 0:
            devis.delete()
            messages.error(
                request, "Aucun produit valide trouvé pour enregistrer votre demande."
            )
            return redirect('devis:view_devis')

        if DEVIS_SESSION_KEY in request.session:
            del request.session[DEVIS_SESSION_KEY]
            request.session.modified = True

        messages.success(
            request,
            f"Votre demande de devis (#{devis.id}) a été envoyée avec succès ! Vous pouvez suivre son avancement dans votre profil.",
        )

        if request.user.is_authenticated:
            return redirect('utilisateur:profil')
        return redirect('catalogue:liste_produits')

    initial_data = {}
    if request.user.is_authenticated:
        initial_data['nom_client'] = request.user.get_full_name(
        ) or request.user.username
        initial_data['email_client'] = request.user.email
        if hasattr(request.user, 'profil'):
            initial_data['telephone'] = request.user.profil.telephone or ''

    context = {
        'initial_data': initial_data,
    }
    return render(request, 'devis/submit_devis.html', context)


# -------------------------------------------
# 4. GESTION DES COMMANDES (Admin / Staff)
# -------------------------------------------

@staff_member_required(login_url='utilisateur:login')
def gestion_commandes(request):
    """Tableau de bord administrateur pour gérer toutes les demandes de devis."""
    statut_filtre = request.GET.get('statut', '')

    commandes = Devis.objects.all().order_by('-date_creation')
    if statut_filtre:
        commandes = commandes.filter(statut=statut_filtre)

    stats = {
        'total': Devis.objects.count(),
        'attente': Devis.objects.filter(statut='attente').count(),
        'valide': Devis.objects.filter(statut='valide').count(),
        'termine': Devis.objects.filter(statut='termine').count(),
        'annule': Devis.objects.filter(statut='annule').count(),
    }

    context = {
        'commandes': commandes,
        'stats': stats,
        'statut_filtre': statut_filtre,
        'statut_choices': Devis.STATUT_CHOICES,
    }
    return render(request, 'devis/gestion_commandes.html', context)


@staff_member_required(login_url='utilisateur:login')
@transaction.atomic
def changer_statut_commande(request, devis_id):
    """Met à jour le statut d'un devis/commande (le stock est mis à jour dans Devis.save())."""
    if request.method == 'POST':
        devis = get_object_or_404(Devis, id=devis_id)
        nouveau_statut = request.POST.get('statut')

        if nouveau_statut in dict(Devis.STATUT_CHOICES) and nouveau_statut != devis.statut:
            devis.statut = nouveau_statut
            devis.save()
            messages.success(
                request, f"Le statut du devis #{devis.id} a été mis à jour."
            )

    return redirect('devis:gestion_commandes')