
from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.affiche_accueil, name='accueil'),
    path('score/', views.joueurs_view, name='joueurs'),
    path('flechette/', views.debut_Flechettes, name='partie_Flechette'),
    path('president/', views.debut_President, name='partie_President'),
    path('dumble/', views.debut_Dumble, name='partie_Dumble'),
    path('supprimer/<int:id>', views.suppr_Joueurs, name='suppression_joueurs')
]