# devis/models.py
from django.db import models
from catalogue.models import Produit

from django.contrib.auth.models import User

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


class Devis(models.Model):
    STATUT_CHOICES = [
        ('attente', 'En attente de validation'),
        ('valide', 'Validé'),
        ('Livraison', 'En Cour de Livraison'),
        ('termine', 'Prêt / Livré'),
        ('annule', 'Annulé'),
    ]

    utilisateur = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    nom_client = models.CharField(max_length=100, blank=True, null=True)
    email_client = models.EmailField(blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='attente'
    )

    def __str__(self):
        return f"Devis #{self.id} - {self.get_statut_display()}"

    def save(self, *args, **kwargs):
        ancien_statut = None
        if self.pk:
            ancien_devis = Devis.objects.filter(pk=self.pk).first()
            if ancien_devis:
                ancien_statut = ancien_devis.statut

        super().save(*args, **kwargs)

        # Mise à jour automatique de quantite_vendue (et quantite_annulee)
        if ancien_statut != self.statut:
            for ligne in self.lignedevis_set.select_related('produit').all():
                produit = ligne.produit
                modifie = False

                # Passage vers 'termine' -> incrémenter quantite_vendue
                if self.statut == 'termine' and ancien_statut != 'termine':
                    produit.quantite_vendue += ligne.quantite
                    if ancien_statut == 'annule':
                        produit.quantite_annulee = max(
                            produit.quantite_annulee - ligne.quantite, 0)
                    modifie = True

                # Sortie de 'termine' vers un autre statut -> décrémenter quantite_vendue
                elif ancien_statut == 'termine' and self.statut != 'termine':
                    produit.quantite_vendue = max(
                        produit.quantite_vendue - ligne.quantite, 0)
                    modifie = True

                # Passage vers 'annule' -> incrémenter quantite_annulee
                if self.statut == 'annule' and ancien_statut != 'annule':
                    produit.quantite_annulee += ligne.quantite
                    modifie = True

                if modifie:
                    produit.save()


class LigneDevis(models.Model):
    devis = models.ForeignKey(
        Devis, on_delete=models.CASCADE, verbose_name="Devis associé"
    )
    produit = models.ForeignKey(
        Produit, on_delete=models.CASCADE, verbose_name="Produit"
    )
    quantite = models.PositiveIntegerField(default=1, verbose_name="Quantité")
    prix_unitaire = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Prix unitaire"
    )

    def __str__(self):
        return f"{self.quantite}x {self.produit.nom} (Devis #{self.devis.id})"

    def sous_total(self):
        """Calcule le sous-total pour cette ligne si le prix existe."""
        if self.prix_unitaire:
            return self.quantite * self.prix_unitaire
        return 0
