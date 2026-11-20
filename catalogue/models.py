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
    categorie = models.ForeignKey( Categorie, on_delete=models.CASCADE, related_name='produits', verbose_name="Catégorie", )
    reference = models.CharField(max_length=50, unique=True, verbose_name="Référence")
    nom = models.CharField(max_length=200, verbose_name="Nom du produit")
    description = models.TextField(verbose_name="Description")
    prix = models.DecimalField( max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Prix unitaire", )
    image = models.ImageField( upload_to='produits/', null=True, blank=True, verbose_name="Image", )

    # --- Gestion des quantités / stock ---
    quantite_totale = models.PositiveIntegerField( default=0, verbose_name="Quantité totale"    )
    quantite_vendue = models.PositiveIntegerField( default=0, verbose_name="Quantité vendue"    )
    quantite_annulee = models.PositiveIntegerField(default=0, verbose_name="Quantité annulée"    )

    disponible = models.BooleanField(default=True, verbose_name="Disponible")
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        ordering = ['-date_creation']

    def _quantite_par_statut(self, statut):
        """Somme des quantités demandées pour ce produit selon le statut du devis."""
        # Si la vue a déjà annoté l'objet, on évite une requête SQL supplémentaire
        annotation_map = {
            'attente': 'qte_attente',
            'valide': 'qte_valide',
            'Livraison': 'qte_livraison',
            'termine': 'qte_termine',
            'annule': 'qte_annule',
        }
        attr_name = annotation_map.get(statut)
        if attr_name and hasattr(self, attr_name):
            valeur_annotee = getattr(self, attr_name)
            if valeur_annotee is not None:
                return valeur_annotee

        from devis.models import LigneDevis
        total = LigneDevis.objects.filter(
            produit=self,
            devis__statut=statut,
        ).aggregate(total=Sum('quantite'))['total']
        return total or 0

    @property
    def quantite_en_attente(self):
        """En Attente de Validation ('attente')."""
        return self._quantite_par_statut('attente')

    @property
    def quantite_validee(self):
        """Validé ('valide')."""
        return self._quantite_par_statut('valide')

    @property
    def quantite_en_livraison(self):
        """En Cour de Livraison ('Livraison')."""
        return self._quantite_par_statut('Livraison')

    @property
    def quantite_livree(self):
        """Livré / Prêt ('termine')."""
        return self._quantite_par_statut('termine')

    @property
    def quantite_statut_annule(self):
        """Annulé ('annule')."""
        return self._quantite_par_statut('annule')

    @property
    def quantite_restante(self):
        """Calcule le stock disponible restant sans descendre sous 0."""
        totale = self.quantite_totale or 0
        vendue = self.quantite_vendue or 0
        return max(totale - vendue, 0)

    def save(self, *args, **kwargs):
        totale = self.quantite_totale or 0
        vendue = self.quantite_vendue or 0
        restante = max(totale - vendue, 0)

        self.disponible = restante > 0
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nom