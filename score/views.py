from ast import Lambda
from pyclbr import Class

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Max
from django.utils import timezone

from score.forms import JoueurForm, CouleurForm, SuggestionForm
from .models import ListeJoueurs, Partie, Suggestion, Tour, ScoreTour, ClassementPartie

def ajout_rapide_joueur(request): # Depuis la sélection des joueurs, permet un ajout rapide et simplifié d'un joueur via JSON (sans request donc sans recharger la page et donc perdre la liste)
    if request.method == "POST":
        nom = request.POST.get('nom','').strip()
        if nom:
            joueur = ListeJoueurs.objects.create(joueurNom=nom)
            return JsonResponse({
                'id' : joueur.id,
                'nom' : joueur.joueurNom,
                'couleur' : joueur.couleur,
            })
    return JsonResponse({'erreur': 'nom invalide'}, status=400) # Si le nom est vide, renvoie erreur

def changer_couleur(request, id):
    joueur = get_object_or_404(ListeJoueurs, id=id)
    if request.method == "POST":
        joueur.couleur = request.POST.get('couleur')
        joueur.save()
    return redirect('gestion_joueurs')


def raz_Partie(request, type_jeu): #RAZ de la partie 
    nom_var_session = f'partie_{type_jeu}_id' # équivaut à 'partie_' + type_jeu + '_id'. f désignant un f-string (string concaténé)
    partie_id = request.session.get(nom_var_session)
    if partie_id:
        Partie.objects.filter(id=partie_id).delete()
        del request.session[nom_var_session]

    cle_selection = f'joueurs_{type_jeu}' # TODO : eclaircir ce point
    if cle_selection in request.session:
        del request.session[cle_selection]

    routes_par_jeu = { #Gestion dynamique des routes de RAZ + regroupement pour ne pas gérer dans urls.py
        'flechette': 'partie_Flechette',
        'president': 'partie_President',
        'dumble': 'partie_Dumble',
    }
    return redirect(routes_par_jeu.get(type_jeu, 'accueil')) # Renvoie la route dynamiquement construite en fonction du type de jeu

def affiche_accueil(request):
    return render(request, 'partie/accueil.html')

def selection_partie(request, type_jeu): # Page de sélection des joueurs avant le lancement de la partie
    joueurs = ListeJoueurs.objects.order_by('joueurNum')

    if request.method == "POST": # TODO : eclaircir ce point
        ids_selectionnes = request.POST.getlist('joueurs_selectionnes')
        request.session[f'joueurs_{type_jeu}'] = ids_selectionnes

        routes_par_jeu = {  # Construit le lien pour le bouton de lancement de partie
            'flechette' : 'partie_Flechette',
            'president': 'partie_President',
            'dumble': 'partie_Dumble',
        }
        return redirect(routes_par_jeu.get(type_jeu, 'accueil'))

    noms_jeu = {
        'flechette': 'Fléchettes',
        'president': 'Président',
        'dumble': 'Dumble',        
    }

    return render(request, 'partie/selection_joueurs.html', {
        'joueurs':joueurs,
        'type_jeu': type_jeu,
        'nom_jeu': noms_jeu.get(type_jeu, type_jeu)
    })


def debut_Flechettes(request):
    if 'joueurs_flechette' not in request.session:
        return redirect('selection_partie', type_jeu='flechette')

    ids_selectionnes = request.session.get('joueurs_flechette')

    # Récupère la partie en cours (ou en crée une nouvelle)
    partie_id = request.session.get('partie_flechette_id')

    # Si une partie est enregistrée en base sans date_fin (donc en cours), la supprimer pour recommencer une partie propre
    Partie.objects.filter(typeJeu='flechette', dateFin__isnull=True).exclude(id=partie_id).delete()

    partie = None
    if partie_id:
        partie = Partie.objects.filter(id=partie_id, dateFin__isnull=True).first()
    if not partie:
        partie = Partie.objects.create(typeJeu='flechette')
        request.session['partie_flechette_id'] = partie.id

    joueurs_actifs = ListeJoueurs.objects.filter(id__in=ids_selectionnes).order_by('joueurNum')
    tours_jouees = partie.tours.order_by('numero')

    if request.method == "POST" and 'valider_tour' in request.POST:
        dernier_numero = tours_jouees.aggregate(Max('numero'))['numero__max'] or 0
        tour = Tour.objects.create(partie=partie, numero=dernier_numero + 1)

        for joueur in joueurs_actifs:

            # -- Affecter un score de 0 si le joueur actuel a déjà gagné
            deja_fini = ClassementPartie.objects.filter(partie=partie, joueur=joueur).exists()
            if deja_fini:
                ScoreTour.objects.create(tour=tour, joueur=joueur, score=0, casse=False)
                continue
            # -- 

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

        # Si un seul joueur (ou aucun) n'a pas encore fini, la partie est automatiquement terminée
        nb_joueurs_finis = ClassementPartie.objects.filter(partie=partie).count()
        nb_joueurs_total = joueurs_actifs.count()
        if nb_joueurs_total - nb_joueurs_finis <= 1:
            return redirect('fin_partie', partie_id=partie.id)

        return redirect('partie_Flechette')


    if request.method == "POST" and 'fin_partie' in request.POST:
        return redirect('fin_partie', partie_id=partie.id)


    # Récupère le rang de chaque joueur déjà fini . Ex: {3: 1, 7: 2} = joueur id 3 est 1er, joueur id 7 est 2e, etc..
    classements_actuels = {}
    for c in ClassementPartie.objects.filter(partie=partie):
        classements_actuels[c.joueur_id] = c.rang

    # Score restant de chaque joueur, sous forme de liste (joueur, reste)
    joueurs_avec_reste = []
    for joueur in joueurs_actifs:
        total = ScoreTour.objects.filter(tour__partie=partie, joueur=joueur, casse=False).aggregate(Sum('score'))['score__sum'] or 0
        rang = classements_actuels.get(joueur.id)
        joueurs_avec_reste.append((joueur, 501 - total, rang))

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

    ids_selectionnes = request.session.get(f'joueurs_{partie.typeJeu}', [])
    joueurs = ListeJoueurs.objects.filter(id__in=ids_selectionnes)

    if partie.typeJeu == "flechette":
        score_totaux = []

        classements = ClassementPartie.objects.filter(partie=partie).order_by('rang')
        joueurs_finis_ids = []
        for classement in classements: # Pour chaque joueur ayant fini, on va chercher tous ses scores, puis on les additionne pour connaitre son score final (théoriquement 0 car a fini) 
            # ['score_sum'] or 0 permet de renvoyer 0 si la valeur pointée dans le dictionnaire est nulle 
            total = ScoreTour.objects.filter(tour__partie=partie, joueur=classement.joueur, casse=False).aggregate(Sum('score'))['score__sum']  or 0
            score_totaux.append({
                'joueur__joueurNom': classement.joueur.joueurNom,
                'joueur_couleur': classement.joueur.couleur,
                'joueur_id': classement.joueur.id,
                'total': total,
            })
            joueurs_finis_ids.append(classement.joueur.id)

        joueurs_non_finis = joueurs.exclude(id__in=joueurs_finis_ids) # Récupère la liste des joueurs, moins ceux ayant finis
        restants = [] # Pour stocker nom/id/score qu'on fusionnera avec score_totaux plus tard (via .extend). Permet de calculer et stocker le score au passage

        for joueur in joueurs_non_finis: 
            total = ScoreTour.objects.filter(tour__partie=partie, joueur=joueur, casse=False).aggregate(Sum('score'))['score__sum']  or 0
            restants.append({
                'joueur__joueurNom': joueur.joueurNom,
                'joueur_couleur': joueur.couleur,
                'joueur_id': joueur.id,
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
        if partie.typeJeu == 'president':
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
    if request.session.get(f'joueurs_{partie.typeJeu}'):
        del request.session[f'joueurs_{partie.typeJeu}']


    template_recap = { # nommage de l'url dynamique selon le type de jeu
        'flechette': 'partie/recap_flechette.html',
        'president': 'partie/recap_president.html',
        'dumble': 'partie/recap_dumble.html',
    }

    return render(request, template_recap.get(partie.typeJeu, 'partie/recap_flechette.html'), { # Par défaut, renvoie 'partie/recap_flechette.html', sécurité 
        'partie': partie,
        'scores_totaux': score_totaux,
        'nb_tours': partie.tours.count(),
    })

# Gestion de la liste de joueurs 

def gestion_joueurs(request):
    if request.method == "POST":
        form = JoueurForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('gestion_joueurs')
    else:
        form = JoueurForm()

    joueurs = ListeJoueurs.objects.order_by('joueurNum')
    return render(request, 'partie/gestion_joueurs.html', {
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

        return redirect('gestion_joueurs')
    return redirect('gestion_joueurs') #else

# --- Gestion des suggestions

def about_contact(request):
    return render(request, 'partie/about_contact.html')

def about_suggestion(request):
    if request.method == "POST":
        form = SuggestionForm(request.POST)
        if form.is_valid():
            form.save()
            request.session['suggestion_envoyee'] = True
            return redirect('about_suggestion')
    else:
        form = SuggestionForm()

    envoi_reussi = request.session.pop('suggestion_envoyee', False)
    return render(request, 'partie/about_suggestion.html', {'form': form, 'envoi_reussi': envoi_reussi})

@staff_member_required #fonction DJANGO qui vérifie la connexion admin
def about_consultation(request):
    suggestions = Suggestion.objects.order_by('-dateEnvoi') # - pour décroissant
    return render(request, 'partie/about_consultation.html', {'suggestions': suggestions})

@staff_member_required
def suppr_suggestion(request, id):
    suggestion = get_object_or_404(Suggestion, id=id)
    if request.method == "POST":
        suggestion.delete()
    return redirect('about_consultation')

# ---