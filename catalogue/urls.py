# catalogue/urls.py
from django.urls import path
from . import views

app_name = 'catalogue'

urlpatterns = [
    # --- Vues Publiques du Catalogue ---
    path('', views.ProduitListView.as_view(), name='liste_produits'),
    path('categorie/<slug:slug>/', views.ProduitListView.as_view(),
         name='liste_par_categorie'),
    path('produit/<int:pk>/', views.ProduitDetailView.as_view(),
         name='detail_produit'),

    # --- Vues de Gestion pour le Staff / Administrateur ---
    path('gestion/produits/', views.liste_produits_admin, name='admin_produits'),
    path('gestion/produits/ajouter/',
         views.ajouter_produit, name='ajouter_produit'),
    path('gestion/produits/<int:produit_id>/modifier/',
         views.modifier_produit, name='modifier_produit'),
    path('gestion/produits/<int:produit_id>/supprimer/',
         views.supprimer_produit, name='supprimer_produit'),
]
