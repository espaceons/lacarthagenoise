# pages/views.py
from django.views.generic import TemplateView


class AboutView(TemplateView):
    template_name = "pages/a_propos.html"


class ContactView(TemplateView):
    template_name = "pages/contact.html"

# Pour la page Contact, vous voudrez probablement une vue basée sur un Formulaire
# pour gérer la soumission et l'envoi d'email :
# from django.views.generic.edit import FormView
# ...
