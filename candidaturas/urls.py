from django.urls import path
from . import views

app_name = 'candidaturas'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('inscrever-partido/', views.registrar_partido_eleicao, name='inscrever_partido'),
    path('presidente/novo/', views.registrar_presidente, name='registrar_presidente'),
    
    path('modelo/excel/<int:lista_id>/', views.baixar_modelo_excel, name='baixar_modelo_excel'),
    path('modelo/excel/teste/', views.baixar_dados_teste_excel, name='baixar_dados_teste_excel'),
    path('modelo/excel/teste/servir/<str:tipo>/', views.baixar_ficheiro_teste, name='baixar_ficheiro_teste'),
    path('modelo/vazio/<int:inscricao_id>/', views.baixar_modelo_vazio, name='baixar_modelo_vazio'),
    
    path('listas/<int:inscricao_id>/', views.gerenciar_listas, name='gerenciar_listas'),
    path('lista/<int:lista_id>/', views.detalhe_lista, name='detalhe_lista'),
    path('lista/<int:lista_id>/dossier/', views.gerar_dossier_lista, name='gerar_dossier_lista'),
    path('importar/partido/<int:inscricao_id>/', views.processar_submissao_excel, name='central_importacao'),
    
    path('lista/<int:lista_id>/reorganizar/', views.reorganizar_posicoes, name='reorganizar_posicoes'),
    path('lista/<int:lista_id>/remover/', views.remover_lista, name='remover_lista'),
    path('eleicao/<int:eleicao_id>/relatorios/', views.relatorios_eleicao, name='relatorios_eleicao'),
    path('eleicao/<int:eleicao_id>/relatorios/global/a3/', views.relatorio_global_a3, name='relatorio_global_a3'),
    path('eleicao/<int:eleicao_id>/relatorios/excel/', views.exportar_relatorio_excel, name='exportar_relatorio_excel'),
    path('eleicao/<int:eleicao_id>/relatorios/pdf/', views.exportar_relatorio_pdf, name='exportar_relatorio_pdf'),
    path('eleicao/<int:eleicao_id>/relatorios/word/', views.exportar_relatorio_word, name='exportar_relatorio_word'),
    path('candidato/remover/<int:candidato_id>/', views.remover_candidato, name='remover_candidato'),
    path('candidato/<int:candidato_id>/', views.detalhe_candidato, name='detalhe_candidato'),
    path('inscricao/remover/<int:inscricao_id>/', views.remover_inscricao, name='remover_inscricao'),
    path('api/get-circulos/', views.api_get_circulos, name='api_get_circulos'),
]
