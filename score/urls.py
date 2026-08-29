
from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.joueurs_view, name='joueurs'),
    path('supprimer/<int:id>', views.suppr_Joueurs, name='suppression_joueurs')
]