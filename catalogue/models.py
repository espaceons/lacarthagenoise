# catalogue/models.py
from django.db import models
from django.utils.text import slugify


class Categorie(models.Model):
    nom = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, max_length=100, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nom


class Produit(models.Model):
    categorie = models.ForeignKey(
        Categorie, on_delete=models.CASCADE, related_name='produits'
    )
    reference = models.CharField(max_length=50, unique=True)
    nom = models.CharField(max_length=200)
    description = models.TextField()
    prix = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    image = models.ImageField(upload_to='produits/', null=True, blank=True)

    # --- Gestion des quantités / stock ---
    quantite_totale = models.PositiveIntegerField(
        default=0, verbose_name="Quantité totale"
    )
    quantite_vendue = models.PositiveIntegerField(
        default=0, verbose_name="Quantité vendue"
    )
    quantite_annulee = models.PositiveIntegerField(
        default=0, verbose_name="Quantité annulée"
    )

    disponible = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    @property
    def quantite_restante(self):
        """Calcule le stock disponible restant sans descendre sous 0."""
        restante = self.quantite_totale - self.quantite_vendue
        return max(restante, 0)

    def save(self, *args, **kwargs):
        # Optionnel : mettre à jour automatiquement `disponible` si le stock restant est à 0
        if self.quantite_totale > 0 and self.quantite_restante == 0:
            self.disponible = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nom