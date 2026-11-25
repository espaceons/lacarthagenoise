from django import forms


class ContactForm(forms.Form):
    nom = forms.CharField(
        label="Nom complet",
        max_length=120,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre nom et prénom',
        }),
    )
    email = forms.EmailField(
        label="Adresse email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'exemple@domaine.com',
        }),
    )
    telephone = forms.CharField(
        label="Téléphone",
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex : +216 25 229 447',
        }),
    )
    sujet = forms.CharField(
        label="Sujet",
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Demande de devis, information produit...',
        }),
    )
    message = forms.CharField(
        label="Message",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Précisez votre demande ou les références souhaitées...',
        }),
    )
