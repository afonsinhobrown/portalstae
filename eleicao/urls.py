from django.urls import path
from . import views

app_name = 'eleicao'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('nova/', views.criar_eleicao, name='criar_eleicao'),
    path('detalhe/<int:eleicao_id>/', views.detalhe_eleicao, name='detalhe_eleicao'),
    path('editar/<int:eleicao_id>/', views.editar_eleicao, name='editar_eleicao'),
    
    # Novos módulos
    path('calendario/', views.calendario_geral, name='calendario'),
    path('materiais/', views.gestao_materiais, name='materiais'),
    path('configuracoes/', views.configuracoes_eleicao, name='configuracoes'),
]
