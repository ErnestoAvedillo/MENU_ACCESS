from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='muelles_index'),
    path('calculadora/', views.calculadora, name='muelles_calculadora'),
]