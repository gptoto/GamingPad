from django.db import models

class ListeJoueurs(models.Model):
    num_choices = [
        (1, 'Actif'),
        (2, 'Inactif'),
    ]

    # Généré automatiquement depuis la bdd et donc non modifiable manuellement par le joueur + évitement de duplicité
    joueurNum = models.DecimalField(max_digits=10, decimal_places=0, editable=False, unique=True ) 
    joueurNom = models.CharField(max_length=50)
    joueurElim = models.DecimalField(choices=num_choices, max_digits=1, decimal_places=0) # 2 choix prédéfini en amont. Enregistré en float en bdd

    def save(self, *args, **kwargs): # Récup du dernier num de joueur stocké en base
        if self.joueurNum is None: # Le formulaire ne remplit jamais ce champ, donc à l'ajout, fait appel automatiquement à cette section
            dernier = ListeJoueurs.objects.aggregate(models.Max('joueurNum'))
            dernier_num = dernier['joueurNum__max']
            self.joueurNum = (dernier_num or 0) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.joueurNom
    
class Partie(models.Model):
    type_choices = [
        ('flechette', 'Fléchette'),
        ('president', 'Président'),
        ('dumble', 'Dumble'),
    ]

    typeJeu = models.CharField(max_length=20, choices=type_choices)
    dateDebut = models.DateTimeField(auto_now_add=True)
    dateFin = models.DateTimeField(null=True, blank=True)
    gagnant = models.ForeignKey(ListeJoueurs, on_delete=models.SET_NULL, null=True, blank=True, related_name='parties_gagnees')


class Manche(models.Model):
    partie = models.ForeignKey(Partie, on_delete=models.CASCADE, related_name='manches')
    numero = models.PositiveIntegerField()


class ScoreManche(models.Model):
    manche = models.ForeignKey(Manche, on_delete=models.CASCADE, related_name='scores')
    joueur = models.ForeignKey(ListeJoueurs, on_delete=models.CASCADE)
    score = models.IntegerField()