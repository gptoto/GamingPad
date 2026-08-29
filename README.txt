# GamingPad

Application web développée avec Django permettant de gérer une liste de joueurs pour une partie : ajout, suppression, et suivi du statut (actif/inactif).

## Technologies utilisées

- **Backend** : Django 3.2
- **Frontend** : Tailwind CSS (DaisyUI)
- **Base de données** : SQLite (local)

## Fonctionnalités

- Ajout d'un joueur via un formulaire (nom + statut)
- Numérotation automatique et incrémentale des joueurs
- Suppression d'un joueur depuis la liste
- Renumérotation automatique après suppression d'un joueur

## Installation

```bash
git clone <url-du-repo>
cd GamingPad
python -m venv env
env\Scripts\activate  # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

L'application est accessible après sur `http://127.0.0.1:8000/`.

## Structure du projet

```
gamingpadsite/    # Configuration principale du projet Django
score/            # Application de gestion des joueurs
  ├── models.py   # Modèle ListeJoueurs
  ├── forms.py    # Formulaire d'ajout de joueur
  ├── views.py    # Procédures d'affichage, ajout et suppression
  └── templates/  # Templates HTML (DaisyUI)
```