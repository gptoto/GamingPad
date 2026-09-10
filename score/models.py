import random
from django.db import models

class ListeJoueurs(models.Model):
    couleurs = {
        '#e74c3c': 'Rouge',
        '#3498db': 'Bleu',
        '#2ecc71': 'Vert',
        '#f1c40f': 'Jaune',
        '#9b59b6': 'Violet',
        '#e91e63': 'Rose',
        '#e67e22': 'Orange',
        '#2980b9': 'Bleu océan',
        '#27ae60': 'Vert émeraude',
        '#f39c12': 'Ambre',
        '#16a085': 'Turquoise',
        '#7f8c8d': 'Gris',
        '#f1948a': 'Corail',
        '#5dade2': 'Bleu ciel',
        '#58d68d': 'Vert menthe',
        '#bb8fce': 'Lavande',
        '#f8c471': 'Abricot',
        '#76d7c4': "Vert d'eau",
        '#af601a': 'Marron',
        '#f0b27a': 'Peche',
        '#a569bd': 'Améthyste',
        '#1f618d': 'Bleu marine',
    }

    # Généré automatiquement depuis la bdd et donc non modifiable manuellement par le joueur + évitement de duplicité
    joueurNum = models.DecimalField(max_digits=10, decimal_places=0, editable=False, unique=True ) 
    joueurNom = models.CharField(max_length=50)
    couleur = models.CharField(max_length=10, choices=list(couleurs.items()), blank=True)

    def save(self, *args, **kwargs): # Récup du dernier num de joueur stocké en base
        if self.joueurNum is None: # Le formulaire ne remplit jamais ce champ, donc à l'ajout, fait appel automatiquement à cette section
            dernier = ListeJoueurs.objects.aggregate(models.Max('joueurNum'))
            dernier_num = dernier['joueurNum__max']
            self.joueurNum = (dernier_num or 0) + 1

        # Attribue une couleur random si n'en a pas d'enregistrée, en evitant au maximum les doublons
        if not self.couleur:
            couleurs_utilisees = ListeJoueurs.objects.exclude(pk=self.pk).values_list('couleur', flat=True)
            couleurs_dispo = [code for code in self.couleurs if code not in couleurs_utilisees]
            if couleurs_dispo:
                self.couleur = random.choice(couleurs_dispo)
            else:
                self.couleur = random.choice(list(self.couleurs))

        super().save(*args, **kwargs)

    def __str__(self):
        return self.joueurNom

# Décomposition des parties pour stocker et récupérer le détail plus tard 
class Partie(models.Model):
    type_choices = [ # Type de  partie
        ('flechette', 'Fléchette'),
        ('president', 'Président'),
        ('dumble', 'Dumble'),
    ]

    typeJeu = models.CharField(max_length=20, choices=type_choices)
    dateDebut = models.DateTimeField(auto_now_add=True)
    dateFin = models.DateTimeField(null=True, blank=True)
    gagnant = models.ForeignKey(ListeJoueurs, on_delete=models.SET_NULL, null=True, blank=True, related_name='parties_gagnees')

class Tour(models.Model): 
    # on_delete pour supprimer de façon récursive. Ex : Si ma partie est supprimée en amont, alors je supprime aussi le tour (logique)
    partie = models.ForeignKey(Partie, on_delete=models.CASCADE, related_name='tours') 
    numero = models.PositiveIntegerField()
    valide = models.BooleanField(default=False)  # Utilisé seulement pour le president pour l'instant : vaut True au clic sur "Manche suivante"

class ScoreTour(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='scores')
    joueur = models.ForeignKey(ListeJoueurs, on_delete=models.CASCADE)
    score = models.IntegerField()
    casse = models.BooleanField(null=True, blank=True) # Que pour fléchettes 501

class ClassementPartie(models.Model): # Enregistrement du classement de chaque joueur à chaque partie
    partie = models.ForeignKey(Partie, on_delete=models.CASCADE, related_name = "classements")
    joueur = models.ForeignKey(ListeJoueurs, on_delete=models.CASCADE)
    rang = models.PositiveBigIntegerField() # N'accepte que des entiers positifs comme rang

class ClassementManche(models.Model): # Classement pour une manche (utilisée pour le président notamment) avec calcul du rôle selon l'ordre
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='classements_manche')
    joueur = models.ForeignKey(ListeJoueurs, on_delete=models.CASCADE)
    ordre_arrivee = models.PositiveIntegerField() 
    role = models.CharField(max_length=20, blank=True)  

class Suggestion(models.Model): # Gestion des suggestions et remontées de bug, stockés en base (pour éviter de créer un SMTP) et affichés sur une page réservée aux admins
    nom = models.CharField(max_length=50)
    message = models.TextField()
    dateEnvoi = models.DateTimeField(auto_now_add=True)