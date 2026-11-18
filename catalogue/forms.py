# catalogue/forms.py
from django import forms
from .models import Produit

class ProduitForm(forms.ModelForm):
    class Meta:
        model = Produit
        # On liste les champs du modèle (sans date_creation qui est automatique)
        fields = ['reference', 'nom', 'categorie', 'description', 'prix', 'image', 'disponible']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajout dynamique des classes Bootstrap à tous les champs du formulaire
        for field_name, field in self.fields.items():
            if field_name == 'disponible':
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'