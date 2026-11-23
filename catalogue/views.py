# catalogue/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Q, Count
from django.views.generic import ListView, DetailView
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils.http import url_has_allowed_host_and_scheme

from .models import Produit, Categorie
from .forms import ProduitForm, CategorieForm


class ProduitListView(ListView):
    model = Produit
    template_name = 'catalogue/liste_produits.html'
    context_object_name = 'produits'

    def get_queryset(self):
        # Filtrer par catégorie si un slug est fourni dans l'URL
        queryset = super().get_queryset().filter(disponible=True)
        slug = self.kwargs.get('slug')

        if slug:
            # Si le slug ne correspond à aucune catégorie, Django renvoie une erreur 404 propre
            categorie = get_object_or_404(Categorie, slug=slug)
            queryset = queryset.filter(categorie=categorie)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Categorie.objects.all()
        return context


class ProduitDetailView(DetailView):
    model = Produit
    template_name = 'catalogue/detail_produit.html'
    context_object_name = 'produit'
    pk_url_kwarg = 'pk'  # Utiliser l'ID/clé primaire dans l'URL


# ==========================================
# GESTION DU CATALOGUE PAR LE STAFF / ADMIN
# ==========================================


@staff_member_required(login_url='utilisateur:login')
def liste_produits_admin(request):
    if request.method == 'POST':
        form = ProduitForm(request.POST, request.FILES)
        if form.is_valid():
            produit = form.save()
            messages.success(
                request, f"Le produit '{produit.nom}' a été ajouté avec succès."
            )
            return redirect('catalogue:admin_produits')
    else:
        form = ProduitForm()

    produits = (
        Produit.objects.select_related('categorie')
        .annotate(
            qte_attente=Sum(
                'lignedevis__quantite',
                filter=Q(lignedevis__devis__statut='attente'),
                default=0,
            ),
            qte_valide=Sum(
                'lignedevis__quantite',
                filter=Q(lignedevis__devis__statut='valide'),
                default=0,
            ),
            qte_livraison=Sum(
                'lignedevis__quantite',
                filter=Q(lignedevis__devis__statut='Livraison'),
                default=0,
            ),
            qte_termine=Sum(
                'lignedevis__quantite',
                filter=Q(lignedevis__devis__statut='termine'),
                default=0,
            ),
            qte_annule=Sum(
                'lignedevis__quantite',
                filter=Q(lignedevis__devis__statut='annule'),
                default=0,
            ),
        )
        .order_by('-id')
    )

    return render(
        request,
        'catalogue/admin_produits.html',
        {
            'produits': produits,
            'form': form,
        },
    )


@staff_member_required(login_url='utilisateur:login')
@require_POST
def toggle_disponibilite_produit(request, produit_id):
    """Bascule ou définit l'état 'disponible' d'un produit depuis admin_produits.html."""
    produit = get_object_or_404(Produit, pk=produit_id)

    if 'disponible' in request.POST:
        produit.disponible = request.POST.get(
            'disponible') in ('1', 'true', 'True', 'on')
    else:
        produit.disponible = not produit.disponible

    # Empêche de marquer disponible si le stock restant est épuisé
    if produit.quantite_totale > 0 and produit.quantite_restante == 0:
        produit.disponible = False
        messages.warning(
            request,
            f"Stock restant épuisé pour '{produit.nom}' : le produit reste Indisponible."
        )
    else:
        etat_label = "Disponible" if produit.disponible else "Indisponible"
        messages.success(
            request, f"Disponibilité de '{produit.nom}' mise à jour : {etat_label}."
        )

    produit.save()

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect('catalogue:admin_produits')


@staff_member_required(login_url='utilisateur:login')
def ajouter_produit(request):
    """Permet au staff d'ajouter un nouveau produit."""
    if request.method == 'POST':
        form = ProduitForm(request.POST, request.FILES)
        if form.is_valid():
            produit = form.save()
            messages.success(
                request, f"Le produit '{produit.nom}' a été ajouté avec succès.")
            return redirect('catalogue:admin_produits')
    else:
        form = ProduitForm()

    context = {
        'form': form,
        'titre': 'Ajouter un produit',
        'bouton_texte': 'Enregistrer le produit',
    }
    return render(request, 'catalogue/form_produit.html', context)


@staff_member_required(login_url='utilisateur:login')
def modifier_produit(request, produit_id):
    """Permet au staff de modifier un produit existant."""
    produit = get_object_or_404(Produit, id=produit_id)
    if request.method == 'POST':
        form = ProduitForm(request.POST, request.FILES, instance=produit)
        if form.is_valid():
            produit = form.save()
            messages.success(
                request, f"Le produit '{produit.nom}' a été mis à jour.")
            return redirect('catalogue:admin_produits')
    else:
        form = ProduitForm(instance=produit)

    context = {
        'form': form,
        'produit': produit,
        'titre': f'Modifier : {produit.nom}',
        'bouton_texte': 'Mettre à jour',
    }
    return render(request, 'catalogue/form_produit.html', context)


@staff_member_required(login_url='utilisateur:login')
def supprimer_produit(request, produit_id):
    """Permet au staff de supprimer un produit."""
    produit = get_object_or_404(Produit, id=produit_id)
    if request.method == 'POST':
        nom = produit.nom
        produit.delete()
        messages.success(request, f"Le produit '{nom}' a été supprimé.")
        return redirect('catalogue:admin_produits')

    context = {
        'produit': produit,
        'objet': produit,
        'titre_objet': f'le produit "{produit.nom}"',
        'url_annulation': 'catalogue:admin_produits',
    }
    return render(request, 'catalogue/confirmer_suppression.html', context)


# ==========================================
# GESTION DES CATÉGORIES PAR LE STAFF / ADMIN
# ==========================================

@staff_member_required(login_url='utilisateur:login')
def liste_categories_admin(request):
    """Liste les catégories du catalogue."""
    categories = Categorie.objects.annotate(nb_produits=Count('produits')).order_by('nom')
    form = CategorieForm()

    if request.method == 'POST':
        form = CategorieForm(request.POST)
        if form.is_valid():
            categorie = form.save()
            messages.success(request, f"La catégorie '{categorie.nom}' a été ajoutée.")
            return redirect('catalogue:liste_categories_admin')

    return render(request, 'catalogue/admin_categories.html', {
        'categories': categories,
        'form': form,
    })


@staff_member_required(login_url='utilisateur:login')
def ajouter_categorie(request):
    """Permet au staff d'ajouter une nouvelle catégorie sur une page dédiée."""
    if request.method == 'POST':
        form = CategorieForm(request.POST)
        if form.is_valid():
            categorie = form.save()
            messages.success(request, f"La catégorie '{categorie.nom}' a été ajoutée avec succès.")
            return redirect('catalogue:liste_categories_admin')
    else:
        form = CategorieForm()

    return render(request, 'catalogue/form_categorie.html', {
        'form': form,
        'titre': 'Nouvelle catégorie',
        'bouton_texte': 'Ajouter la catégorie',
    })


@staff_member_required(login_url='utilisateur:login')
def modifier_categorie(request, categorie_id):
    """Modifie une catégorie existante."""
    categorie = get_object_or_404(Categorie, pk=categorie_id)
    if request.method == 'POST':
        form = CategorieForm(request.POST, instance=categorie)
        if form.is_valid():
            form.save()
            messages.success(request, f"La catégorie '{categorie.nom}' a été mise à jour.")
            return redirect('catalogue:liste_categories_admin')
    else:
        form = CategorieForm(instance=categorie)

    return render(request, 'catalogue/form_categorie.html', {
        'form': form,
        'categorie': categorie,
        'titre': f'Modifier la catégorie : {categorie.nom}',
        'bouton_texte': 'Enregistrer',
    })


@staff_member_required(login_url='utilisateur:login')
def supprimer_categorie(request, categorie_id):
    """Supprime une catégorie."""
    categorie = get_object_or_404(Categorie, pk=categorie_id)
    if request.method == 'POST':
        nom = categorie.nom
        categorie.delete()
        messages.success(request, f"La catégorie '{nom}' a été supprimée.")
        return redirect('catalogue:liste_categories_admin')

    return render(request, 'catalogue/confirmer_suppression.html', {
        'objet': categorie,
        'titre_objet': f'la catégorie "{categorie.nom}"',
        'url_annulation': 'catalogue:liste_categories_admin',
    })
