from django.urls import path
from . import views

app_name = 'circuloseleitorais'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('novo/', views.criar_circulo, name='criar_circulo'),
    path('detalhe/<int:circulo_id>/', views.detalhe_circulo, name='detalhe_circulo'),
    path('editar/<int:circulo_id>/', views.editar_circulo, name='editar_circulo'),
    path('gerar-circulos/<int:eleicao_id>/', views.gerar_circulos_automatico, name='gerar_circulos'),
    path('sincronizar-rs/<int:eleicao_id>/', views.sincronizar_dados_rs, name='sincronizar_rs'),
    path('importar-postos/<int:circulo_id>/', views.importar_postos, name='importar_postos'),
    path('eliminar/<int:circulo_id>/', views.eliminar_circulo, name='eliminar_circulo'),
]
