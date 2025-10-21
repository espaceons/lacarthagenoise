# devis/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
# Pour les messages de succès/erreur (optionnel mais recommandé)
from django.contrib import messages

from catalogue.models import Produit
from .models import DevisRequest
# from .forms import DevisForm  # (À créer pour la fonction submit_devis)

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
            messages.error(request, f"Article retiré de la liste de devis.")

        request.session[DEVIS_SESSION_KEY] = devis_panier
        request.session.modified = True  # Assurer que Django sauvegarde la session

    return redirect('view_devis')


def clear_devis(request):
    """Vide toute la liste de devis."""
    if DEVIS_SESSION_KEY in request.session:
        del request.session[DEVIS_SESSION_KEY]
        messages.success(request, "Votre liste de devis a été vidée.")

    return redirect('view_devis')

# -------------------------------------------
# 2. VIEW DEVIS (Affichage)
# -------------------------------------------


def view_devis(request):
    """Affiche le contenu du panier et rend le template view_devis.html."""
    devis_panier = request.session.get(DEVIS_SESSION_KEY, {})

    context = {
        'devis_panier': devis_panier,
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
        return redirect('view_devis')

    # LOGIQUE FORMULAIRE (à compléter avec un Formulaire Django)
    # 1. Créer le formulaire de contact (nom, email, téléphone, message) dans devis/forms.py
    # 2. Gérer la soumission du formulaire (POST) :
    # if request.method == 'POST':
    #     form = DevisForm(request.POST)
    #     if form.is_valid():
    #         # 3. Formatter le contenu de la demande (résumé du panier)
    #         contenu_text = "\n".join([
    #             f"- {item['nom']} (Réf: {item['
