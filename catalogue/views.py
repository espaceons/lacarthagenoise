# catalogue/views.py
from django.views.generic import ListView, DetailView
from .models import Produit, Categorie


class ProduitListView(ListView):
    model = Produit
    template_name = 'catalogue/liste_produits.html'
    context_object_name = 'produits'

    def get_queryset(self):
        # Filtrer par catégorie si un slug est fourni dans l'URL
        queryset = super().get_queryset().filter(disponible=True)
        slug = self.kwargs.get('slug')
        if slug:
            categorie = Categorie.objects.get(slug=slug)
            queryset = queryset.filter(categorie=categorie)
        return queryset


class ProduitDetailView(DetailView):
    model = Produit
    template_name = 'catalogue/detail_produit.html'
    context_object_name = 'produit'
    pk_url_kwarg = 'pk'  # Utiliser l'ID/clé primaire dans l'URL
