
from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.affiche_accueil, name='accueil'),

    # Gestion des joueurs/partie
    path('joueurs/', views.gestion_joueurs, name='gestion_joueurs'),
    path('joueurs/couleur/<int:id>/', views.changer_couleur, name='changer_couleur'),
    path('joueurs/supprimer/<int:id>/', views.suppr_Joueurs, name='suppression_joueurs'),
    path('selection/<str:type_jeu>/', views.selection_partie, name='selection_partie'),
    path('raz/<str:type_jeu>/', views.raz_Partie, name='raz_partie'),

    # flechette
    path('flechette/', views.debut_Flechettes, name='partie_Flechette'),
    path('flechette/fin/<int:partie_id>', views.fin_partie, name='fin_partie'),

    # President
    path('president/', views.debut_President, name='partie_President'),

    # Dumble
    path('dumble/', views.debut_Dumble, name='partie_Dumble'),

    # About
    path('about/contact/', views.about_contact, name='about_contact'),
    path('about/suggestion/', views.about_suggestion, name='about_suggestion'),
    path('about/consultation/', views.about_consultation, name='about_consultation'),
    path('about/consultation/supprimer/<int:id>/', views.suppr_suggestion, name='suppr_suggestion'),
]