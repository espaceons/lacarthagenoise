# utilisateurs/forms.py
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import ProfilUtilisateur


class InscriptionForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Adresse Email")
    first_name = forms.CharField(max_length=30, required=True, label="Prénom")
    last_name = forms.CharField(max_length=30, required=True, label="Nom")

    # Champs supplémentaires liés au Profil
    type_client = forms.ChoiceField(
        choices=ProfilUtilisateur.TYPE_CLIENT_CHOICES,
        initial='particulier',
        label="Vous êtes un :"
    )
    telephone = forms.CharField(
        max_length=20, required=False, label="Téléphone")
    adresse = forms.CharField(widget=forms.Textarea(
        attrs={'rows': 2}), required=False, label="Adresse")
    nom_entreprise = forms.CharField(
        max_length=150, required=False, label="Nom de l'entreprise (si Revendeur/Artisan)")
    matricule_fiscal = forms.CharField(
        max_length=50, required=False, label="Matricule Fiscal / N° TVA (Optionnel)")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajout des classes Bootstrap à tous les champs
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        # 1. Sauvegarde l'utilisateur de base
        user = super().save(commit=commit)
        if commit:
            # 2. Met à jour ou crée le profil associé avec les données supplémentaires
            profil, _ = ProfilUtilisateur.objects.get_or_create(user=user)
            profil.type_client = self.cleaned_data.get('type_client')
            profil.telephone = self.cleaned_data.get('telephone')
            profil.adresse = self.cleaned_data.get('adresse')
            profil.nom_entreprise = self.cleaned_data.get('nom_entreprise')
            profil.matricule_fiscal = self.cleaned_data.get('matricule_fiscal')
            profil.save()
        return user
