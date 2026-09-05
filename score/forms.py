from django import forms
from django.forms import widgets
from .models import ListeJoueurs, Suggestion

class JoueurForm(forms.ModelForm): # Permet l'ajout de joueurs aux parties à venir
    class Meta:
        model = ListeJoueurs
        fields = ['joueurNom','joueurElim',]
        widgets = {
            'joueurNom' : forms.TextInput(attrs = {
                'class' : 'input w-full', # réfère une apparence DaisyUI ici
                'placeholder' : 'Nom du joueur'
            }),
            'joueurElim' : forms.Select(attrs = {
                'class' : 'input w-full', # réfère une apparence DaisyUI ici
            }),
        }

class SuggestionForm(forms.ModelForm): # Permet de saisir des suggestions en tant qu'invité (aucune connexion requise)
    class Meta:
        model = Suggestion
        fields = ['nom','message']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'input w-full',
                'placeholder': 'Prenom'
            }),
           'message': forms.TextInput(attrs={
                'class': 'textarea w-full',
                'placeholder': 'Décris ta suggestion ou le bug rencontré',
                'rows': 5
            }),
        }