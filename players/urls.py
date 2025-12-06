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
    path('players/<int:pk>/assign-team/', views.assign_player_team_view, name='assign_team'),
    path('teams/<str:team_secret>/', views.team_detail_view, name='team_detail'),
    path('managers/', views.managers_list_view, name='managers_list'),
    path('managers/create/', views.manager_create_view, name='manager_create'),
    path('managers/<int:pk>/', views.manager_detail_view, name='manager_detail'),
    path('managers/<int:pk>/delete/', views.manager_delete_view, name='manager_delete'),
    path('managers/<int:pk>/assign-team/', views.assign_manager_team_view, name='assign_manager_team'),
]
