# catalogue/admin.py
from django.contrib import admin
from .models import Categorie, Produit


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nom', 'slug')


@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ('nom', 'reference', 'categorie', 'prix', 'disponible')
    list_filter = ('categorie', 'disponible')
    search_fields = ('nom', 'reference')
    # Optionnel, pour faciliter la référence
    prepopulated_fields = {'reference': ('nom',)}
