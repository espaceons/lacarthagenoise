# devis/urls.py
from django.urls import path
from . import views  # Importe toutes les vues de devis/views.py


app_name = 'devis'


urlpatterns = [
    # 1. Ajouter un produit à la liste de devis (nécessite l'ID du produit)
    # Exemple : /devis/add/12/
    path('add/<int:produit_id>/', views.add_to_devis, name='add_to_devis'),

    # 2. Retirer un produit de la liste de devis (nécessite l'ID du produit)
    # Exemple : /devis/remove/12/
    path('remove/<int:produit_id>/',
         views.remove_from_devis, name='remove_from_devis'),

    # 3. Afficher la liste complète des articles sélectionnés
    # Exemple : /devis/
    path('', views.view_devis, name='view_devis'),

    # 4. Soumettre la demande de devis (formulaire de contact)
    # Exemple : /devis/submit/
    path('submit/', views.submit_devis, name='submit_devis'),

    # 5. Optionnel : Vider toute la liste de devis en une fois
    # Exemple : /devis/clear/
    path('clear/', views.clear_devis, name='clear_devis'),
    
    # Espace Administrateur personnalisé
    path('administration/commandes/', views.gestion_commandes, name='gestion_commandes'),
    path('administration/commandes/<int:devis_id>/statut/', views.changer_statut_commande, name='changer_statut_commande'),
]
