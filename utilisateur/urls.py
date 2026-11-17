# utilisateurs/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'utilisateur'

urlpatterns = [
    # Inscription
    path('inscription/', views.inscription, name='inscription'),

    # Connexion (utilise le template par défaut ou un template personnalisé)
    path('connexion/', auth_views.LoginView.as_view(
        template_name='utilisateur/connexion.html'), name='login'),

    # Déconnexion
    path('deconnexion/', auth_views.LogoutView.as_view(
        next_page='catalogue:liste_produits'), name='logout'),

    # Profil utilisateur
    path('profil/', views.profil, name='profil'),
]
