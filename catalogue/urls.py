# catalogue/urls.py
from django.urls import path
from . import views

app_name = 'catalogue'

urlpatterns = [
    # --- Vues Publiques du Catalogue ---
    path('', views.ProduitListView.as_view(), name='liste_produits'),
    path('categorie/<slug:slug>/',        views.ProduitListView.as_view(),
         name='liste_par_categorie',),
    path('produit/<int:pk>/',        views.ProduitDetailView.as_view(),
         name='detail_produit',),

    # --- CRUD Produits (Staff / Administrateur) ---
    path('gestion/produits/',        views.liste_produits_admin,
         name='admin_produits',),
    path('gestion/produits/ajouter/',
         views.ajouter_produit,        name='ajouter_produit',),
    path('gestion/produits/<int:produit_id>/modifier/',
         views.modifier_produit,        name='modifier_produit',),
    path('gestion/produits/<int:produit_id>/supprimer/',
         views.supprimer_produit,        name='supprimer_produit',),
    path('gestion/produits/<int:produit_id>/toggle-disponibilite/',
         views.toggle_disponibilite_produit, name='toggle_disponibilite_produit',),

    # --- CRUD Catégories (Staff / Administrateur) ---
    path( 'gestion/categories/',        views.liste_categories_admin,        name='liste_categories_admin',    ),
    path( 'gestion/categories/ajouter/',        views.ajouter_categorie,        name='ajouter_categorie',    ),
    path( 'gestion/categories/<int:categorie_id>/modifier/',        views.modifier_categorie,        name='modifier_categorie',    ),
    path( 'gestion/categories/<int:categorie_id>/supprimer/',        views.supprimer_categorie,        name='supprimer_categorie',    ),
]
