# devis/models.py
from django.db import models
from catalogue.models import Produit


class DevisRequest(models.Model):
    # Informations du client
    nom_complet = models.CharField(max_length=255)
    email = models.EmailField()
    telephone = models.CharField(max_length=20, blank=True)
    message = models.TextField(
        blank=True, help_text="Informations supplémentaires ou questions.")

    # Informations de la demande
    date_soumission = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=50, default='Nouveau')

    # Le contenu du devis sera stocké dans un champ TEXT ou JSON (plus avancé)
    # Pour simplifier, nous stockerons ici un résumé du panier
    contenu_devis = models.TextField()

    def __str__(self):
        return f"Devis de {self.nom_complet} ({self.date_soumission.strftime('%Y-%m-%d')})"
