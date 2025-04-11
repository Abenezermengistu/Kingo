from django.urls import path
from . import views

urlpatterns = [
    path('', views.bingo_index, name='index'),
    path('board/', views.board_view, name='board_view'),
]