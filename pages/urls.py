# pages/urls.py
from django.urls import path
# Assurez-vous d'avoir bien importé les classes dans pages/views.py
from .views import AboutView, ContactView


app_name = 'pages'


urlpatterns = [
    # Utilisation des Class-Based Views (méthode as_view())
    path('a-propos/', AboutView.as_view(), name='a_propos'),
    # Note : Pour Contact, il faudra peut-être remplacer par une FormView plus tard
    path('contact/', ContactView.as_view(), name='contact'),
]
