# catalogue/urls.py
from django.urls import path
from .views import ProduitListView, ProduitDetailView


app_name = 'catalogue'

urlpatterns = [
    # Page d'accueil du catalogue (tous les produits)
    path('', ProduitListView.as_view(), name='liste_produits'),
    # Filtrer par catégorie
    path('<slug:slug>/', ProduitListView.as_view(), name='liste_par_categorie'),
    # Détail d'un produit (pk est la clé primaire)
    path('produit/<int:pk>/', ProduitDetailView.as_view(), name='detail_produit'),
]
