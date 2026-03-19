# recursoshumanos/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard_completo, name='dashboard'),
    path('dashboard/', views.dashboard_completo, name='dashboard'),

    # Funcionários
    path('funcionarios/', views.lista_funcionarios, name='lista_funcionarios'),
    path('funcionarios/<int:funcionario_id>/', views.detalhes_funcionario, name='detalhes_funcionario'),
    path('funcionarios/criar/', views.criar_funcionario, name='criar_funcionario'),

    # Licenças
    path('licencas/minhas/', views.minhas_licencas, name='minhas_licencas'),
    path('licencas/solicitar/', views.solicitar_licenca, name='solicitar_licenca'),
    path('licenca/<int:licenca_id>/dar-parecer/', views.dar_parecer_licenca, name='dar_parecer_licenca'),
    path('licenca/<int:licenca_id>/autorizar/', views.autorizar_licenca, name='autorizar_licenca'),

    # Avaliações
    path('avaliacoes/minhas/', views.minhas_avaliacoes, name='minhas_avaliacoes'),
    path('funcionario/<int:funcionario_id>/avaliar/', views.avaliar_funcionario, name='avaliar_funcionario'),

    # Presença/QR Code
    path('presenca/scanner/', views.scanner_presenca, name='scanner_presenca'),
    path('funcionario/<int:funcionario_id>/cartao/', views.gerar_cartao_funcionario, name='gerar_cartao_funcionario'),

    # Relatórios
    path('relatorios/licencas/', views.relatorio_licencas, name='relatorio_licencas'),
    path('relatorios/avaliacoes/', views.relatorio_avaliacoes, name='relatorio_avaliacoes'),
    path('relatorios/presencas/', views.relatorio_presencas, name='relatorio_presencas'),
    path('relatorios/folha-efetividade/', views.folha_efetividade, name='folha_efetividade'),

    # Comunicação Interna
    path('comunicacao/chat/', views.chat_principal, name='chat_principal'),
    path('comunicacao/canal/<int:canal_id>/', views.canal_chat, name='canal_chat'),
    path('comunicacao/canal/<int:canal_id>/enviar-mensagem/', views.enviar_mensagem, name='enviar_mensagem'),

    # Documentos
    path('comunicacao/documentos/', views.documentos_institucionais, name='documentos_institucionais'),
    path('comunicacao/documentos/criar/', views.criar_documento, name='criar_documento'),
    path('comunicacao/documentos/<int:documento_id>/', views.visualizar_documento, name='visualizar_documento'),
    path('comunicacao/documentos/<int:documento_id>/download/', views.download_documento, name='download_documento'),

    # Relatórios de Atividades
    path('comunicacao/relatorios/', views.relatorios_atividades, name='relatorios_atividades'),
    path('comunicacao/relatorios/criar/', views.criar_relatorio, name='criar_relatorio'),

    # Notificações
    path('notificacoes/minhas/', views.minhas_notificacoes, name='minhas_notificacoes'),
    path('notificacoes/configurar/', views.configurar_notificacoes, name='configurar_notificacoes'),

    # APIs
    path('api/notificacoes/pendentes/', views.api_notificacoes_pendentes, name='api_notificacoes_pendentes'),
    path('api/notificacoes/<int:notificacao_id>/marcar-lida/', views.api_marcar_notificacao_lida,
         name='api_marcar_notificacao_lida'),
    path('api/notificacoes/marcar-todas-lidas/', views.api_marcar_todas_notificacoes_lidas,
         name='api_marcar_todas_notificacoes_lidas'),
]




