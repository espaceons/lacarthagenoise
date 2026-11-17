# catalogue/urls.py
from django.urls import path
from .views import ProduitListView, ProduitDetailView


app_name = 'catalogue'

urlpatterns = [
    # 1. Chemin Racine (le plus spécifique)
    path('', ProduitListView.as_view(), name='liste_produits'),

    # 2. Chemin Détail Produit (spécifique avec PK)
    path('produit/<int:pk>/', ProduitDetailView.as_view(), name='detail_produit'),

    # 3. Chemin Catégorie (le plus générique)
    # Laissez ce chemin à la fin.
    path('<slug:slug>/', ProduitListView.as_view(), name='liste_par_categorie'),
]
