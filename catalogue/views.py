# catalogue/views.py
from .models import Produit
from django.shortcuts import render
from django.db.models import Sum, Q
from django.views.generic import ListView, DetailView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from .models import Produit, Categorie
from .forms import ProduitForm


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

    return render(request, 'catalogue/admin_produits.html', {'produits': produits})


@staff_member_required(login_url='utilisateur:login')
def ajouter_produit(request):
    """Permet au staff d'ajouter un nouveau produit."""
    if request.method == 'POST':
        form = ProduitForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Le produit a été ajouté avec succès.")
            return redirect('catalogue:admin_produits')
    else:
        form = ProduitForm()

    context = {'form': form, 'titre': 'Ajouter un produit'}
    return render(request, 'catalogue/form_produit.html', context)


@staff_member_required(login_url='utilisateur:login')
def modifier_produit(request, produit_id):
    """Permet au staff de modifier un produit existant."""
    produit = get_object_or_404(Produit, id=produit_id)
    if request.method == 'POST':
        form = ProduitForm(request.POST, request.FILES, instance=produit)
        if form.is_valid():
            form.save()
            messages.success(
                request, f"Le produit '{produit.nom}' a été mis à jour.")
            return redirect('catalogue:admin_produits')
    else:
        form = ProduitForm(instance=produit)

    context = {'form': form, 'titre': f'Modifier : {produit.nom}'}
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

    context = {'produit': produit}
    return render(request, 'catalogue/confirmer_suppression.html', context)
