# utilisateurs/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import InscriptionForm


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
    """Affiche le profil de l'utilisateur connecté."""
    context = {
        'user': request.user
    }
    return render(request, 'utilisateur/profil.html', context)
