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
        Categorie, on_delete=models.CASCADE, related_name='produits')
    reference = models.CharField(max_length=50, unique=True)
    nom = models.CharField(max_length=200)
    description = models.TextField()
    prix = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to='produits/', null=True, blank=True)
    disponible = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom
