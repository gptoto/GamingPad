from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction

from score.forms import JoueurForm
from .models import ListeJoueurs

# Gestion de la liste de joueurs 

def affiche_accueil(request):
    return render(request, 'partie/accueil.html')

def debut_Flechettes(request):
    return render(request, 'partie/flechettes.html')

def debut_President(request):
    return render(request, 'partie/president.html')

def debut_Dumble(request):
    return render(request, 'partie/dumble.html')


def joueurs_view(request):
    if request.method == "POST":
        form = JoueurForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('joueurs')
    else:
        form = JoueurForm()

    joueurs = ListeJoueurs.objects.all()
    return render(request, 'partie/joueurs.html', {
        'form': form,
        'joueurs': joueurs,
    })

def suppr_Joueurs(request, id):
    joueur = get_object_or_404(ListeJoueurs, id=id)
    if request.method == "POST":
        joueur.delete()

        # Si suppression d'un joueur qui n'était pas le dernier, alors réattribution des JoueursNum pour garder une consistance
        joueurs_restants = ListeJoueurs.objects.order_by('joueurNum') 
        with transaction.atomic(): # Pas de commit si interrompu
            for index, j in enumerate(joueurs_restants, start=1):
                if j.joueurNum != index:
                    j.joueurNum = index
                    j.save()

        return redirect('joueurs')
    return redirect('joueurs') #else

# Gestion de la manche

#def debut_Partie(request):
    # RAZ de la manche
    # Début d'une manche (donc ajout d'une manche)

#def ajout_Manche(request):
