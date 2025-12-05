from django.urls import path
from . import views

app_name = 'players'

urlpatterns = [
    path('settings/', views.settings_view, name='settings'),
    path('api/import-players/', views.import_players_view, name='import_players'),
    path('players/', views.players_list_view, name='list'),
    path('players/create/', views.player_create_view, name='create'),
    path('players/<int:pk>/', views.player_detail_view, name='detail'),
    path('players/<int:pk>/delete/', views.player_delete_view, name='delete'),
]
