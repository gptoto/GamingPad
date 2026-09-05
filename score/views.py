from ast import Lambda
from pyclbr import Class

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Max
from django.utils import timezone

from score.forms import JoueurForm
from .models import ListeJoueurs, Partie, Tour, ScoreTour, ClassementPartie


def raz_Partie(request, type_jeu): #RAZ de la partie 
    nom_var_session = f'partie_{type_jeu}_id' # équivaut à 'partie_' + type_jeu + '_id'. f désignant un f-string (string concaténé)
    partie_id = request.session.get(nom_var_session)
    if partie_id:
        Partie.objects.filter(id=partie_id).delete()
        del request.session[nom_var_session]

    routes_par_jeu = { #Gestion dynamique des routes de RAZ + regroupement pour ne pas gérer dans urls.py
        'flechette': 'partie_Flechette',
        'president': 'partie_President',
        'dumble': 'partie_Dumble',
    }
    return redirect(routes_par_jeu.get(type_jeu, 'accueil')) # Renvoie la route dynamiquement construite en fonction du type de jeu

def affiche_accueil(request):
    return render(request, 'partie/accueil.html')

def debut_Flechettes(request):
    # Récupère la partie en cours (ou en crée une nouvelle)
    partie_id = request.session.get('partie_flechette_id')

    # Si une partie est enregistrée en base sans date_fin (donc en cours), la supprimer pour recommencer une partie propre
    Partie.objects.filter(typeJeu='', dateFin__isnull=True).exclude(id=partie_id).delete()

    partie = None
    if partie_id:
        partie = Partie.objects.filter(id=partie_id, dateFin__isnull=True).first()
    if not partie:
        partie = Partie.objects.create(typeJeu='flechette')
        request.session['partie_flechette_id'] = partie.id

    joueurs_actifs = ListeJoueurs.objects.filter(joueurElim=1).order_by('joueurNum')
    tours_jouees = partie.tours.order_by('numero')

    if request.method == "POST" and 'valider_tour' in request.POST:
        dernier_numero = tours_jouees.aggregate(Max('numero'))['numero__max'] or 0
        tour = Tour.objects.create(partie=partie, numero=dernier_numero + 1)

        for joueur in joueurs_actifs:
            score_str = request.POST.get(f'score_{joueur.id}')
            if not score_str:
                continue
            score = int(score_str)

            total_actuel = ScoreTour.objects.filter(
                tour__partie=partie, joueur=joueur, casse=False
            ).aggregate(Sum('score'))['score__sum'] or 0

            nouveau_total = total_actuel + score
            casse = nouveau_total > 501

            ScoreTour.objects.create(tour=tour, joueur=joueur, score=score, casse=casse)

            # Si le joueur vient d'atteindre 501 pile, on lui attribue le prochain rang disponible
            if not casse and nouveau_total == 501:
                deja_classe = ClassementPartie.objects.filter(partie=partie, joueur=joueur).exists()
                if not deja_classe:
                    dernier_rang = ClassementPartie.objects.filter(partie=partie).aggregate(Max('rang'))['rang__max'] or 0
                    ClassementPartie.objects.create(partie=partie, joueur=joueur, rang=dernier_rang + 1)

        return redirect('partie_Flechette')

    if request.method == "POST" and 'fin_partie' in request.POST:
        return redirect('fin_partie', partie_id=partie.id)

    # Score restant de chaque joueur, sous forme de liste (joueur, reste)
    joueurs_avec_reste = []
    for joueur in joueurs_actifs:
        total = ScoreTour.objects.filter(
            tour__partie=partie, joueur=joueur, casse=False
        ).aggregate(Sum('score'))['score__sum'] or 0
        joueurs_avec_reste.append((joueur, 501 - total))

    prochain_numero = (tours_jouees.aggregate(Max('numero'))['numero__max'] or 0) + 1

    return render(request, 'partie/flechettes.html', {
        'joueurs': joueurs_actifs,
        'joueurs_avec_reste': joueurs_avec_reste,
        'tours': tours_jouees,
        'numero_tour_active': prochain_numero,
    })

def debut_President(request):
    return render(request, 'partie/president.html')

def debut_Dumble(request):
    return render(request, 'partie/dumble.html')

def fin_partie(request, partie_id): # Calcul le score final des joueurs, qui gagne la partie (en fonction du type de jeu), enregistre ces infos puis les affiche
    partie = get_object_or_404(Partie, id=partie_id)

    joueurs = ListeJoueurs.objects.filter(joueurElim=1) # Récupère uniquement les joueurs actifs (1 = Actif, cf la bdd) via un filtre

    if partie.typeJeu == "flechette":
        score_totaux = []

        classements = ClassementPartie.objects.filter(partie=partie).order_by('rang')
        joueurs_finis_ids = []
        for classement in classements: # Pour chaque joueur ayant fini, on va chercher tous ses scores, puis on les additionne pour connaitre son score final (théoriquement 0 car a fini) 
            # ['score_sum'] or 0 permet de renvoyer 0 si la valeur pointée dans le dictionnaire est nulle 
            total = ScoreTour.objects.filter(tour__partie=partie, joueur=classement.joueur, casse=False).aggregate(Sum('score'))['score__sum']  or 0
            score_totaux.append({
                'joueur__joueurNom': classement.joueur.joueurNom,
                'joueurs_id': classement.joueur.id,
                'total': 501 - total,
            })
            joueurs_finis_ids.append(classement.joueur.id)

        joueurs_non_finis = joueurs.exclude(id__in=joueurs_finis_ids) # Récupère la liste des joueurs, moins ceux ayant finis
        restants = [] # Pour stocker nom/id/score qu'on fusionnera avec score_totaux plus tard (via .extend). Permet de calculer et stocker le score au passage

        for joueur in joueurs_non_finis: 
            total = ScoreTour.objects.filter(tour__partie=partie, joueur=classement.joueur, casse=False).aggregate(Sum('score'))['score__sum']  or 0
            restants.append({
                'joueur__joueurNom': joueur.joueurNom,
                'joueurs_id': joueur.id,
                'total': 501 - total,
            })

        # Trie la liste "restants" par ordre croissant ("pour chaque élément s de la liste, prends sa valeur 'total'")
        # Ici 'lambda' désigne une mini-fonction jetable sans nom, la fonction étant ce qui vient après (et qui explique comment trier le .sort())
        restants.sort(key=lambda s :s['total']) 
        score_totaux.extend(restants)

    else:
        score_totaux = list(
            ScoreTour.objects.filter(tour__partie=partie)
            .values('joueur__joueurNom', 'joueur_id')
            .annotate(total=Sum('score'))
        )
        if partie.typeJeu == 'president': # TODO: A CLARIFIER (pourquoi le placé ici et pas dans un elif à la suite de "if partie.typeJeu == 'flechette'")
            score_totaux.sort(key=lambda s: s['total'])
        else:
            score_totaux.sort(key=lambda s: -s['total'])


    # Enregistre le gagnant et la fin de partie
    if score_totaux:
        partie.gagnant_id = score_totaux[0]['joueur_id']
    partie.dateFin = timezone.now()
    partie.save()

    if request.session.get('partie_flechette_id') == partie.id:
        del request.session['partie_flechette_id']

    return render(request, 'partie/recap.html', {
        'partie': partie,
        'scores_totaux': score_totaux,
        'nb_tours': partie.tours.count(),
    })

# Gestion de la liste de joueurs 

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
        for index, j in enumerate(joueurs_restants, start=1):
            if j.joueurNum != index:
                j.joueurNum = index
                j.save()

        return redirect('joueurs')
    return redirect('joueurs') #else
