from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Max
from django.utils import timezone

from score.forms import JoueurForm
from .models import ListeJoueurs, Partie, Tour, ScoreTour

# Gestion de la liste de joueurs 

def affiche_accueil(request):
    return render(request, 'partie/accueil.html')

def debut_Flechettes(request):
    # Récupère la partie en cours (ou en crée une nouvelle)
    partie_id = request.session.get('partie_flechette_id')
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
            casse = nouveau_total > 501 or nouveau_total == 500

            ScoreTour.objects.create(tour=tour, joueur=joueur, score=score, casse=casse)

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

def fin_partie(request, partie_id):
    partie = get_object_or_404(Partie, id=partie_id)

    # Calcule le score total de chaque joueur sur la partie
    scores_totaux = (
        ScoreTour.objects.filter(tour__partie=partie)
        .values('joueur__joueurNom', 'joueur_id')
        .annotate(total=Sum('score'))
    )

    # Trie selon la règle du jeu
    if partie.typeJeu == 'flechette':
        scores_totaux = scores_totaux.order_by('-total')
    elif partie.typeJeu == 'president':
        scores_totaux = scores_totaux.order_by('total')
    elif partie.typeJeu == 'dumble':
        scores_totaux = scores_totaux.order_by('-total')  # à ajuster selon les règles réelles

    # Enregistre le gagnant et la fin de partie
    if scores_totaux:
        partie.gagnant_id = scores_totaux[0]['joueur_id']
    partie.dateFin = timezone.now()
    partie.save()

    if request.session.get('partie_flechette_id') == partie.id:
        del request.session['partie_flechette_id']

    return render(request, 'partie/recap.html', {
        'partie': partie,
        'scores_totaux': scores_totaux,
        'nb_tours': partie.tours.count(),
    })

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

# Gestion de la tour

#def debut_Partie(request):
    # RAZ de la tour
    # Début d'une tour (donc ajout d'une tour)

#def ajout_Tour(request):
