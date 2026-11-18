# devis/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required

from catalogue.models import Produit
# Assurez-vous d'importer vos modèles de devis
from .models import Devis, LigneDevis

# Clé de session utilisée pour stocker le panier de devis
DEVIS_SESSION_KEY = 'devis_panier'

# -------------------------------------------
# 1. ADD / REMOVE / CLEAR LOGIC (Session Management)
# -------------------------------------------

def add_to_devis(request, produit_id):
    """Ajoute un produit à la liste de devis stockée dans la session."""
    produit = get_object_or_404(Produit, pk=produit_id)
    devis_panier = request.session.get(DEVIS_SESSION_KEY, {})

    produit_key = str(produit_id)

    if produit_key in devis_panier:
        devis_panier[produit_key]['quantite'] += 1
        messages.info(request, f"Quantité de '{produit.nom}' mise à jour.")
    else:
        devis_panier[produit_key] = {
            'nom': produit.nom,
            'reference': produit.reference,
            'quantite': 1,
            'image_url': produit.image.url if produit.image else None,
        }
        messages.success(
            request, f"'{produit.nom}' ajouté à votre liste de devis.")

    request.session[DEVIS_SESSION_KEY] = devis_panier
    request.session.modified = True

    return redirect(request.META.get('HTTP_REFERER', reverse('catalogue:liste_produits')))


def remove_from_devis(request, produit_id):
    """Retire complètement ou réduit la quantité d'un produit."""
    devis_panier = request.session.get(DEVIS_SESSION_KEY, {})
    produit_key = str(produit_id)

    if produit_key in devis_panier:
        if devis_panier[produit_key]['quantite'] > 1:
            devis_panier[produit_key]['quantite'] -= 1
            messages.warning(
                request, f"Quantité de '{devis_panier[produit_key]['nom']}' réduite.")
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
            devis_items.append({
                'produit': produit,
                'quantite': item_data.get('quantite', 1),
            })
        except Produit.DoesNotExist:
            continue

    context = {
        'devis_items': devis_items,
        'devis_panier_session': devis_panier_session
    }
    return render(request, 'devis/view_devis.html', context)


# -------------------------------------------
# 3. SUBMIT LOGIC (Formulaire et Envoi en BD)
# -------------------------------------------

def submit_devis(request):
    """Gère l'envoi de la demande de devis et l'enregistre en base de données."""
    devis_panier = request.session.get(DEVIS_SESSION_KEY)

    if not devis_panier:
        messages.error(
            request, "Impossible de soumettre : votre liste de devis est vide.")
        return redirect('devis:view_devis')

    if request.method == 'POST':
        # 1. Créer l'objet Devis principal en base de données
        devis = Devis.objects.create(
            # Associe l'utilisateur s'il est connecté, sinon None (invité)
            utilisateur=request.user if request.user.is_authenticated else None,
            statut='attente'
        )

        # 2. Parcourir les articles du panier de session pour créer les lignes de devis
        for produit_id, item_data in devis_panier.items():
            try:
                produit = Produit.objects.get(pk=produit_id)
                quantite = item_data.get('quantite', 1)

                # Création de la ligne liée au devis
                LigneDevis.objects.create(
                    devis=devis,
                    produit=produit,
                    quantite=quantite,
                    prix_unitaire=produit.prix if produit.prix else 0
                )
            except Produit.DoesNotExist:
                continue

        # 3. Vider la session après la soumission réussie
        if DEVIS_SESSION_KEY in request.session:
            del request.session[DEVIS_SESSION_KEY]
            request.session.modified = True

        messages.success(
            request, f"Votre demande de devis (#{devis.id}) a été envoyée avec succès ! Vous pouvez suivre son avancement dans votre profil.")

        # Rediriger vers le profil si connecté, sinon vers le catalogue
        if request.user.is_authenticated:
            return redirect('utilisateur:profil')
        return redirect('catalogue:liste_produits')

    context = {}
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
def changer_statut_commande(request, devis_id):
    """Met à jour le statut d'un devis/commande depuis le tableau de bord."""
    if request.method == 'POST':
        devis = get_object_or_404(Devis, id=devis_id)
        nouveau_statut = request.POST.get('statut')
        
        if nouveau_statut in dict(Devis.STATUT_CHOICES):
            devis.statut = nouveau_statut
            devis.save()
            messages.success(request, f"Le statut du devis #{devis.id} a été mis à jour.")
            
    return redirect('devis:gestion_commandes')