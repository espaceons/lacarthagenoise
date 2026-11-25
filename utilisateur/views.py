# utilisateurs/views.py
from .forms import AdminProfilForm
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import InscriptionForm
from devis.models import Devis

def inscription(request):
    """Gère l'inscription d'un nouvel utilisateur."""
    if request.user.is_authenticated:
        return redirect('catalogue:liste_produits')

    if request.method == 'POST':
        form = InscriptionForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(
                request, f"Compte créé avec succès pour {username} ! Vous pouvez maintenant vous connecter.")
            return redirect('utilisateur:login')
    else:
        form = InscriptionForm()

    context = {'form': form}
    return render(request, 'utilisateur/inscription.html', context)




@login_required
def profil(request):
    """Affiche le profil de l'utilisateur connecté et ses demandes de devis."""
    mes_devis = (
        Devis.objects.filter(utilisateur=request.user)
        .prefetch_related('lignedevis_set__produit')
        .order_by('-date_creation')
    )

    context = {
        'user': request.user,
        'mes_devis': mes_devis,
    }
    return render(request, 'utilisateur/profil.html', context)


# utilisateur/views.py (Ajouts pour l'administration)


@staff_member_required(login_url='utilisateur:login')
def liste_utilisateurs_admin(request):
    """Affiche la liste de tous les utilisateurs inscrits pour le staff."""
    type_filtre = request.GET.get('type', '')

    utilisateurs = User.objects.all().order_by('-date_joined')
    if type_filtre:
        utilisateurs = utilisateurs.filter(profil__type_client=type_filtre)

    context = {
        'utilisateurs': utilisateurs,
        'type_filtre': type_filtre,
    }
    return render(request, 'utilisateur/admin_utilisateurs.html', context)


@staff_member_required(login_url='utilisateur:login')
def modifier_utilisateur_admin(request, user_id):
    """Permet au staff de modifier le type de client ou le statut d'un utilisateur."""
    user_cible = get_object_or_404(User, id=user_id)
    profil = user_cible.profil

    if request.method == 'POST':
        form = AdminProfilForm(request.POST, instance=profil)
        if form.is_valid():
            form.save()
            # Mettre à jour des infos de base de User si besoin (ex: is_active)
            user_cible.is_active = 'is_active' in request.POST
            user_cible.save()

            messages.success(
                request, f"Le profil de {user_cible.username} a été mis à jour.")
            return redirect('utilisateur:admin_utilisateurs')
    else:
        form = AdminProfilForm(instance=profil)

    context = {
        'form': form,
        'user_cible': user_cible,
    }
    return render(request, 'utilisateur/form_utilisateur_admin.html', context)
