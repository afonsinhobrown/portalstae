from django.urls import path
from . import views

app_name = 'partidos'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('lista/', views.lista_partidos, name='lista_partidos'),
    path('liderancas/', views.lista_liderancas, name='lista_liderancas'),
    path('documentos/', views.lista_documentos, name='lista_documentos'),
    path('novo/', views.criar_partido, name='criar_partido'),
    path('detalhe/<int:partido_id>/', views.detalhe_partido, name='detalhe_partido'),
    path('editar/<int:partido_id>/', views.editar_partido, name='editar_partido'),
    path('apagar/<int:partido_id>/', views.apagar_partido, name='apagar_partido'),
]
