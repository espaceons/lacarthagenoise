"""
URL configuration for carthagenoise_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.conf import settings  # Importez settings
from django.conf.urls.static import static  # Importez static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Intégration des routes de l'application utilisateurs avec un namespace
    path('utilisateur/', include(('utilisateur.urls',
         'utilisateur'), namespace='utilisateur')),
    # Le catalogue devient l'index du site
    # 🚨 1. LES URLS FIXES DOIVENT ÊTRE EN PREMIER (avant le catalogue)
    path('devis/', include(('devis.urls', 'devis'), namespace='devis')),
    path('pages/', include(('pages.urls', 'pages'), namespace='pages')),

    # 2. LE CATALOGUE (AVEC SON SLUG DYNAMIQUE) DOIT ÊTRE EN DERNIER
    path('', include(('catalogue.urls', 'catalogue'), namespace='catalogue')),
]


# CE BLOC DOIT ÊTRE UTILISÉ UNIQUEMENT EN DÉVELOPPEMENT (DEBUG=True)
if settings.DEBUG:
    # Pour les fichiers MÉDIAS (images des produits)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    # Pour les fichiers STATIQUES (CSS, JS)
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
