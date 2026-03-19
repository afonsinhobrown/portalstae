# dfec/urls.py
from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views_manuais
from . import views_analise
from . import views  # Para outras views do DFEC

app_name = 'dfec'  # ← ESSENCIAL para o namespace funcionar

urlpatterns = [
    # ========== AUTENTICAÇÃO ==========
    path('analise-eleitoral/dashboard/', views_analise.DashboardAnaliseEleitoral.as_view(), name='dashboard_analise_eleitoral'),
    path('analise-eleitoral/upload/', views_analise.UploadResultadosView.as_view(), name='upload_resultados'),
    path('analise-eleitoral/relatorio-pdf/', views_analise.RelatorioPDFView.as_view(), name='relatorio_pdf'),
    path('analise-eleitoral/comparar/', views_analise.CompararEleicoesView.as_view(), name='comparar_eleicoes'),
    path('analise-eleitoral/mapa/', views_analise.MapaInterativoView.as_view(), name='mapa_interativo'),
    path('analise-eleitoral/recomendacoes/', views_analise.RecomendacoesView.as_view(), name='recomendacoes'),
    
    path('login/', LoginView.as_view(
        template_name='dfec/login_dfec.html',
        redirect_authenticated_user=True,
        extra_context={'titulo': 'Acesso DFEC - Sistema de Documentação Técnica'}
    ), name='login'),

    path('logout/', LogoutView.as_view(
        next_page='home'
    ), name='logout'),

    # ========== DASHBOARD ==========
    path('', views_manuais.manuais_dashboard, name='dashboard'),

    # ========== MÓDULO MANUAIS ==========
    path('manuais/', views_manuais.ManualListView.as_view(), name='manuais_lista'),
    path('manuais/<int:pk>/', views_manuais.manual_detalhe, name='manual_detalhe'),

    # ADICIONE ESTA LINHA (era a que faltava):
    path('manuais/criar/', views_manuais.manual_criar, name='manual_criar'),

    path('manuais/<int:pk>/editar/', views_manuais.manual_editar, name='manual_editar'),
    path('manuais/<int:pk>/pdf/', views_manuais.gerar_pdf_manual, name='gerar_pdf'),
    path('manuais/<int:pk>/imprimir/', views_manuais.solicitar_impressao, name='solicitar_impressao'),
    path('manuais/<int:pk>/publicar/', views_manuais.publicar_manual, name='publicar_manual'),
    path('manuais/editor/upload/', views_manuais.upload_imagem_editor, name='upload_imagem_editor'),

    # Capítulos
    path('manuais/<int:manual_id>/capitulo/criar/', views_manuais.capitulo_criar, name='capitulo_criar'),
    path('capitulo/<int:pk>/editar/', views_manuais.capitulo_editar, name='capitulo_editar'),
    path('capitulo/<int:pk>/excluir/', views_manuais.capitulo_excluir, name='capitulo_excluir'),

    # Imagens
    path('biblioteca/imagens/', views_manuais.biblioteca_imagens, name='biblioteca_imagens'),
    path('api/imagens/upload/', views_manuais.upload_imagem, name='upload_imagem'),

    # Comentários
    path('manuais/<int:manual_id>/comentario/', views_manuais.comentario_adicionar, name='comentario_adicionar'),

    # ========== APIs ==========
    path('api/manuais/tipo/<str:tipo_codigo>/', views_manuais.api_manuais_tipo, name='api_manuais_tipo'),
    path('api/estatisticas/manuais/', views_manuais.api_estatisticas_manuais, name='api_estatisticas_manuais'),

    # ========== MÓDULO PLANOS DE ATIVIDADE ==========
    path('planos/', views.lista_planos, name='planos_lista'),
    path('planos/<int:pk>/', views.detalhe_plano, name='plano_detalhe'),
    path('planos/<int:pk>/formadores/', views.gerir_formadores_plano, name='plano_formadores'),
    path('planos/criar/', views.criar_plano, name='plano_criar'),
    path('planos/<int:pk>/editar/', views.editar_plano, name='plano_editar'),
    path('planos/<int:pk>/aprovar/', views.aprovar_plano, name='plano_aprovar'),
    path('planos/<int:pk>/executar/', views.executar_plano, name='plano_executar'),
    path('planos/<int:pk>/excluir/', views.excluir_plano, name='plano_excluir'),
    path('planos/<int:plano_id>/atividades/criar/', views.criar_atividade, name='atividade_criar'),
    path('atividades/<int:pk>/editar/', views.editar_atividade, name='atividade_editar'),
    path('atividades/<int:pk>/excluir/', views.excluir_atividade, name='atividade_excluir'),

    # ========== MÓDULO OBJETIVOS INSTITUCIONAIS ==========
    path('objetivos/', views.lista_objetivos, name='objetivos_lista'),
    path('objetivos/criar/', views.criar_objetivo, name='objetivo_criar'),
    path('objetivos/<int:pk>/editar/', views.editar_objetivo, name='objetivo_editar'),

    # ========== MÓDULO FORMAÇÕES ==========
    path('formacoes/', views.lista_formacoes, name='formacoes_lista'),
    path('formacoes/<int:pk>/', views.formacao_detalhe, name='formacao_detalhe'),
    path('formacoes/<int:pk>/editar/', views.editar_formacao, name='formacao_editar'),
    path('participantes/', views.lista_participantes, name='participantes_lista'),
    path('formacoes/criar/', views.criar_formacao, name='formacao_criar'),
    path('brigadas/', views.lista_brigadas, name='brigadas_lista'),
    path('brigadas/<int:pk>/', views.detalhe_brigada, name='brigada_detalhe'),
    path('brigadas/criar/', views.criar_brigada, name='brigada_criar'),
    path('brigadas/<int:pk>/editar/', views.editar_brigada, name='brigada_editar'),
    path('brigadas/<int:pk>/membros/', views.gerenciar_membros_brigada, name='brigada_membros'),
    path('brigadas/<int:pk>/treinamento/', views.registrar_treinamento, name='brigada_treinamento'),

    path('formacoes/<int:formacao_id>/turmas/nova/', views.turma_criar_manual, name='turma_criar'),
    path('turmas/<int:turma_id>/', views.turma_detalhe, name='turma_detalhe'),
    path('formacoes/<int:formacao_id>/turmas/limpar/', views.limpar_turmas, name='turma_limpar'),
    path('formacoes/<int:formacao_id>/gerar-turmas/', views.gerar_turmas_inteligente, name='gerar_turmas_inteligente'),
    path('formacoes/<int:formacao_id>/pdf-participantes/', views.gerar_pdf_lista_participantes, name='gerar_pdf_participantes'),
    path('participantes/template/', views.download_template_participantes, name='download_template_participantes'),
    path('formacoes/<int:formacao_id>/importar-csv/', views.carregar_participantes_csv, name='carregar_participantes'),
    path('formacoes/<int:formacao_id>/participantes/novo/', views.participante_criar, name='participante_criar'),
    path('formacoes/<int:formacao_id>/limpar/', views.limpar_participantes_formacao, name='limpar_participantes'),
    path('formacoes/<int:formacao_id>/simular/', views.simular_participantes, name='simular_participantes'),
    path('formacoes/<int:formacao_id>/gerar-brigadas/', views.gerar_brigadas_automatico, name='gerar_brigadas_automatico'),
    
    # ========== MÓDULO RELATÓRIOS ==========
    path('relatorios/manuais/', views.relatorio_manuais, name='relatorio_manuais'),
    path('relatorios/planos/', views.relatorio_planos, name='relatorio_planos'),
    path('relatorios/brigadas/', views.relatorio_brigadas, name='relatorio_brigadas'),
    path('relatorios/atividades/', views.relatorio_atividades_executadas, name='relatorio_atividades'),

    # ========== MÓDULO LOGÍSTICA (DFEC) ==========
    path('logistica/', views.lista_logistica_dfec, name='logistica_lista'),
    path('logistica/novo/', views.criar_material_dfec, name='logistica_criar'),
    
    # ========== UTILITÁRIOS ==========
    path('configuracoes/', views.configuracoes_dfec, name='configuracoes'),
    path('ajuda/', views.ajuda_sistema, name='ajuda'),
    path('api/calendario/eventos/', views.api_eventos_calendario, name='api_eventos_calendario'),
    
]