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
- Saisie du score d'une partie de fléchettes 501, par manche et par joueur
- Calcul des scores automatique par joueur
- Affichage récapitulatif du score final et du gagnant 

## Installation

git clone <url-du-repo>
cd GamingPad
python -m venv env
env\Scripts\activate  # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

L'application est accessible après sur `http://127.0.0.1:8000/`.

## Structure du projet

gamingpadsite/    # Configuration principale du projet Django
score/            # Application de gestion des joueurs
  ├── models.py   # Modèles des joueurs et des parties
  ├── forms.py    # Formulaire d'ajout de joueur
  ├── views.py    # Procédures d'Affichage/Ajout/Suppression de joueurs et gestion des parties/manches
  └── templates/  # Templates HTML (DaisyUI)
