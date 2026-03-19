from django.urls import path
from . import views

app_name = 'admin_portal'

urlpatterns = [
    # Dashboard
    path('', views.dashboard_admin, name='dashboard_admin'),

    # Templates
    path('templates/', views.lista_templates, name='lista_templates'),
    path('templates/novo/', views.criar_template, name='criar_template'),
    path('templates/editar/<int:template_id>/', views.editar_template, name='editar_template'),

    # Importação
    path('importar/', views.importar_dados, name='importar_dados'),
    path('importacoes/', views.lista_importacoes, name='lista_importacoes'),
    path('importacoes/<int:importacao_id>/', views.detalhe_importacao, name='detalhe_importacao'),

    # Configuração
    path('configuracao/', views.configuracao_sistema, name='configuracao_sistema'),
]