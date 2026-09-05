
from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.affiche_accueil, name='accueil'),

    # Gestion des joueurs/partie
    path('score/', views.joueurs_view, name='joueurs'),
    path('supprimer/<int:id>', views.suppr_Joueurs, name='suppression_joueurs'),
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
]