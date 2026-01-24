from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('editor/<str:datos>/<str:filename>/', views.editor, name='editor'),
    path('open/<str:filename>/', views.abrir, name='abrir'),
    path('abrir/<path:folder>/<str:group_name>/', views.abrir_carpeta, name='abrir_carpeta'),
    path('guarda/', views.guarda, name='guarda'),
]
