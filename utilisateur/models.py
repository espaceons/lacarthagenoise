# utilisateurs/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class ProfilUtilisateur(models.Model):
    # Choix du type de client
    TYPE_CLIENT_CHOICES = [
        ('particulier', 'Particulier'),
        ('revendeur', 'Revendeur'),
        ('artisan', 'Artisan / Partenaire'),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profil'
    )
    type_client = models.CharField(
        max_length=20,
        choices=TYPE_CLIENT_CHOICES,
        default='particulier',
        verbose_name="Type de client"
    )
    telephone = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Téléphone"
    )
    adresse = models.TextField(blank=True, null=True, verbose_name="Adresse")

    # Champs optionnels pour les professionnels (Revendeur / Artisan)
    nom_entreprise = models.CharField(
        max_length=150, blank=True, null=True, verbose_name="Nom de l'entreprise / Boutique"
    )
    matricule_fiscal = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="Matricule Fiscal / N° TVA"
    )

    def __str__(self):
        return f"Profil de {self.user.username} ({self.get_type_client_display()})"


# Signal unique et sécurisé pour créer ou sauvegarder le profil automatiquement
@receiver(post_save, sender=User)
def gerer_profil_utilisateur(sender, instance, created, **kwargs):
    profil, _ = ProfilUtilisateur.objects.get_or_create(user=instance)
    if not profil:
        profil.save()
