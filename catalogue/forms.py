# catalogue/forms.py
from django import forms
from .models import Produit


class ProduitForm(forms.ModelForm):
    class Meta:
        model = Produit
        # On liste les champs du modèle (sans date_creation qui est automatique ;
        # quantite_restante est une @property calculée dynamiquement)
        fields = [
            'reference',
            'nom',
            'categorie',
            'description',
            'prix',
            'quantite_totale',
            'quantite_vendue',
            'quantite_annulee',
            'image',
            'disponible',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'quantite_totale': forms.NumberInput(attrs={'min': 0}),
            'quantite_vendue': forms.NumberInput(attrs={'min': 0}),
            'quantite_annulee': forms.NumberInput(attrs={'min': 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajout dynamique des classes Bootstrap à tous les champs du formulaire
        for field_name, field in self.fields.items():
            if field_name == 'disponible':
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'