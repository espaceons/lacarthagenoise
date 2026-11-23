# catalogue/forms.py
from django import forms
from .models import Produit, Categorie, Catalogue


class CatalogueForm(forms.ModelForm):
    class Meta:
        model = Catalogue
        fields = ['nom', 'description', 'actif']
        widgets = {
            'nom': forms.TextInput(attrs={
                'placeholder': 'Ex. : Catalogue Général, Collection Été...',
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Description courte du catalogue...',
            }),
            'actif': forms.CheckboxInput(),
        }
        labels = {
            'nom': 'Nom du catalogue',
            'description': 'Description',
            'actif': 'Afficher dans la vitrine',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            existing = field.widget.attrs.get('class', '')
            css = 'form-check-input' if field_name == 'actif' else 'form-control'
            field.widget.attrs['class'] = f"{existing} {css}".strip()


class CategorieForm(forms.ModelForm):
    class Meta:
        model = Categorie
        fields = ['nom']
        widgets = {
            'nom': forms.TextInput(attrs={
                'placeholder': 'Ex. : Poterie, Céramique, Cuivre...',
            }),
        }
        labels = {
            'nom': 'Nom de la catégorie',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f"{existing} form-control".strip()


class ProduitForm(forms.ModelForm):
    class Meta:
        model = Produit
        # quantite_restante est une @property calculée dynamiquement ;
        # date_creation est automatique.
        # quantite_vendue et quantite_annulee sont gérées par les statuts des devis,
        # mais restent modifiables en cas de correction manuelle par le staff.
        fields = [
            'reference',
            'nom',
            'categorie',
            'catalogues',
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
            'catalogues': forms.SelectMultiple(attrs={'size': 4}),
            'prix': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'quantite_totale': forms.NumberInput(attrs={'min': 0}),
            'quantite_vendue': forms.NumberInput(attrs={'min': 0}),
            'quantite_annulee': forms.NumberInput(attrs={'min': 0}),
        }
        labels = {
            'catalogues': 'Catalogues associés',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            existing_class = field.widget.attrs.get('class', '')
            if field_name == 'disponible':
                bootstrap_class = 'form-check-input'
            elif field_name in ('categorie', 'catalogues'):
                bootstrap_class = 'form-select'
            else:
                bootstrap_class = 'form-control'
            field.widget.attrs['class'] = f"{existing_class} {bootstrap_class}".strip(
            )

    def clean(self):
        cleaned_data = super().clean()
        totale = cleaned_data.get('quantite_totale')
        vendue = cleaned_data.get('quantite_vendue')

        if totale is None:
            totale = 0
        if vendue is None:
            vendue = 0

        if totale > 0 and vendue > totale:
            self.add_error(
                'quantite_vendue',
                "La quantité vendue ne peut pas dépasser la quantité totale."
            )

        restante = max(totale - vendue, 0)
        if totale > 0 and restante == 0:
            cleaned_data['disponible'] = False

        return cleaned_data
