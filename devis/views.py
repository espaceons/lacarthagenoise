# devis/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages

from catalogue.models import Produit
from .models import DevisRequest
# from .forms import DevisForm  # (À décommenter plus tard pour le formulaire de soumission)

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
        # Si le produit est déjà là, incrémenter la quantité
        devis_panier[produit_key]['quantite'] += 1
        messages.info(request, f"Quantité de '{produit.nom}' mise à jour.")
    else:
        # Ajouter le nouveau produit
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

    # Rediriger vers la page précédente (catalogue ou détail produit)
    return redirect(request.META.get('HTTP_REFERER', reverse('catalogue:liste_produits')))


def remove_from_devis(request, produit_id):
    """Retire complètement ou réduit la quantité d'un produit."""
    devis_panier = request.session.get(DEVIS_SESSION_KEY, {})
    produit_key = str(produit_id)

    if produit_key in devis_panier:
        if devis_panier[produit_key]['quantite'] > 1:
            # Réduire la quantité
            devis_panier[produit_key]['quantite'] -= 1
            messages.warning(
                request, f"Quantité de '{devis_panier[produit_key]['nom']}' réduite.")
        else:
            # Retirer complètement
            del devis_panier[produit_key]
            messages.error(request, "Article retiré de la liste de devis.")

        request.session[DEVIS_SESSION_KEY] = devis_panier
        request.session.modified = True  # Assurer que Django sauvegarde la session

    # ✅ CORRECTION : Utilisation du namespace 'devis:'
    return redirect('devis:view_devis')


def clear_devis(request):
    """Vide toute la liste de devis."""
    if DEVIS_SESSION_KEY in request.session:
        del request.session[DEVIS_SESSION_KEY]
        messages.success(request, "Votre liste de devis a été vidée.")

    # ✅ CORRECTION : Utilisation du namespace 'devis:'
    return redirect('devis:view_devis')


# -------------------------------------------
# 2. VIEW DEVIS (Affichage)
# -------------------------------------------

def view_devis(request):
    """Affiche le contenu du panier et rend le template view_devis.html."""

    # 1. Récupérer les données brutes de la session
    devis_panier_session = request.session.get(DEVIS_SESSION_KEY, {})

    # 2. Préparer une liste sécurisée d'articles complets
    devis_items = []

    # Parcourir chaque ID de produit dans la session
    for produit_id, item_data in devis_panier_session.items():
        try:
            # Tenter de récupérer l'objet Produit complet
            produit = Produit.objects.get(pk=produit_id)

            # Ajouter l'objet produit et la quantité à la liste des articles
            devis_items.append({
                'produit': produit,  # L'objet Produit complet
                'quantite': item_data.get('quantite', 1),
            })

        except Produit.DoesNotExist:
            # Si le produit n'existe plus en BD, on l'ignore
            print(
                f"ATTENTION: Produit ID {produit_id} dans la session n'existe plus en BD.")
            continue

    context = {
        'devis_items': devis_items,
        'devis_panier_session': devis_panier_session
    }
    return render(request, 'devis/view_devis.html', context)


# -------------------------------------------
# 3. SUBMIT LOGIC (Formulaire et Envoi)
# -------------------------------------------

def submit_devis(request):
    """Gère l'envoi du formulaire de demande de devis."""
    devis_panier = request.session.get(DEVIS_SESSION_KEY)

    if not devis_panier:
        messages.error(
            request, "Impossible de soumettre : votre liste de devis est vide.")
        return redirect('devis:view_devis')

    # Si l'utilisateur a soumis le formulaire (méthode POST)
    if request.method == 'POST':
        # TODO: Ici, vous pourrez récupérer les données du formulaire (nom, email, etc.)
        # et éventuellement les sauvegarder en base de données avec DevisRequest.

        # 🚨 SUPPRESSION DE LA LISTE DE DEVIS APRÈS SOUMISSION 🚨
        if DEVIS_SESSION_KEY in request.session:
            del request.session[DEVIS_SESSION_KEY]
            request.session.modified = True

        messages.success(
            request, "Votre demande de devis a été envoyée avec succès ! Nous vous recontacterons bientôt.")

        # Rediriger vers l'accueil ou une page de confirmation
        return redirect('catalogue:liste_produits')

    # Si c'est un affichage simple (GET), on affiche le formulaire de soumission
    context = {}
    return render(request, 'devis/submit_devis.html', context)
