from django.urls import path
from . import views

urlpatterns = [
    path('', views.bingo_index, name='index'),
    path('board/', views.board_view, name='board_view'),
    path('save_card/', views.save_selected_bingo_card, name='save_card'),
    path("get_wallet_data/", views.get_wallet_data, name="get_wallet_data"),
    path("api/stats/<str:board_number>/", views.get_game_stats, name="get_game_stats"),
    path('api/board-stats/', views.board_stats_api, name='board_stats_api'),
    path('api/call-number/', views.call_number_api, name='call_number'),

]