from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='muelles_index'),
    path('calculadora/compresion/', views.calculadora_compresion, name='muelles_calculadora_compresion'),
    path('calculadora/traccion/', views.calculadora_traccion, name='muelles_calculadora_traccion'),
]