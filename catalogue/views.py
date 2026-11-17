# catalogue/views.py
from django.views.generic import ListView, DetailView
from .models import Produit, Categorie
from django.shortcuts import get_object_or_404


class ProduitListView(ListView):
    model = Produit
    template_name = 'catalogue/liste_produits.html'
    context_object_name = 'produits'

    def get_queryset(self):
        # Filtrer par catégorie si un slug est fourni dans l'URL
        queryset = super().get_queryset().filter(disponible=True)
        slug = self.kwargs.get('slug')

        if slug:
            # CORRECTION : Utilisation de get_object_or_404
            # Si le slug ne correspond à aucune catégorie, Django renverra une erreur 404
            # au lieu de l'erreur interne DoesNotExist, qui est plus propre.
            categorie = get_object_or_404(Categorie, slug=slug)

            # Si le slug est trouvé, filtrer par cette catégorie
            queryset = queryset.filter(categorie=categorie)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ceci est seulement pour les vues de catalogue. Pour la navbar, utilisez un Context Processor.
        context['categories'] = Categorie.objects.all()
        return context


class ProduitDetailView(DetailView):
    model = Produit
    template_name = 'catalogue/detail_produit.html'
    context_object_name = 'produit'
    pk_url_kwarg = 'pk'  # Utiliser l'ID/clé primaire dans l'URL
