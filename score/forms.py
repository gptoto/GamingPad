from django import forms
from django.forms import widgets
from .models import ListeJoueurs

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