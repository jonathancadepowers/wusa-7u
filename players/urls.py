from django.urls import path
from . import views

app_name = 'players'

urlpatterns = [
    path('settings/', views.settings_view, name='settings'),
    path('api/import-players/', views.import_players_view, name='import_players'),
]
