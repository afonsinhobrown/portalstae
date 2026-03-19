# recursoshumanos/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'recursoshumanos'

urlpatterns = [
    # ========== AUTENTICAÇÃO ==========
    path('login/', auth_views.LoginView.as_view(
        template_name='recursoshumanos/login_rh.html'
    ), name='login_rh'),

    path('accounts/login/', auth_views.LoginView.as_view(
        template_name='recursoshumanos/login_rh.html'
    ), name='login_accounts'),

    path('logout/', auth_views.LogoutView.as_view(
        next_page='/rh/login/'
    ), name='logout'),

    # ========== DASHBOARD ==========
    path('', views.dashboard_completo, name='dashboard'),
    path('dashboard/', views.dashboard_completo, name='dashboard'),

    # ========== FUNCIONÁRIOS ==========
    path('funcionarios/', views.lista_funcionarios, name='lista_funcionarios'),
    path('funcionarios/<int:funcionario_id>/', views.detalhes_funcionario, name='detalhes_funcionario'),
    path('funcionarios/criar/', views.criar_funcionario, name='criar_funcionario'),
    path('funcionario/<int:funcionario_id>/cartao-pdf/', views.gerar_cartao_html_pdf, name='gerar_cartao_html_pdf'),

    # Mantenha esta para compatibilidade se outras partes do sistema usam
    path('funcionario/<int:funcionario_id>/cartao/', views.gerar_cartao_funcionario, name='gerar_cartao_funcionario'),

    # ========== LICENÇAS ==========
    path('licencas/minhas/', views.minhas_licencas, name='minhas_licencas'),
    path('licencas/solicitar/', views.solicitar_licenca, name='solicitar_licenca'),
    path('licencas/pendentes-rh/', views.lista_licencas_pendentes_rh, name='lista_licencas_pendentes_rh'),
    path('licencas/<int:licenca_id>/analisar-rh/', views.analisar_licenca_rh, name='analisar_licenca_rh'),
    path('licenca/<int:licenca_id>/dar-parecer/', views.dar_parecer_licenca, name='dar_parecer_licenca'),
    path('licenca/<int:licenca_id>/editar-parecer/', views.editar_parecer_licenca, name='editar_parecer_licenca'),
    path('licenca/<int:licenca_id>/pdf/', views.download_licenca_pdf, name='download_licenca_pdf'),
    path('licenca/<int:licenca_id>/autorizar/', views.autorizar_licenca, name='autorizar_licenca'),
    path('licenca/<int:licenca_id>/submeter/', views.licenca_submetida_view, name='licenca_submit'),
    path('dashboard-rh/', views.dashboard_rh, name='dashboard_rh'),
    # ========== AVALIAÇÕES ==========
    path('avaliacoes/minhas/', views.minhas_avaliacoes, name='minhas_avaliacoes'),
    path('avaliacoes/realizadas/', views.avaliacoes_realizadas, name='avaliacoes_realizadas'),
    path('avaliacoes/apagar/<int:avaliacao_id>/', views.apagar_avaliacao, name='apagar_avaliacao'),
    path('funcionario/<int:funcionario_id>/avaliar/', views.avaliar_funcionario, name='avaliar_funcionario'),

    # ========== PRESENÇA/QR CODE ==========
    path('presenca/scanner/', views.scanner_presenca, name='scanner_presenca'),


# ========== FÉRIAS (ADICIONAR) ==========
path('ferias/solicitar/', views.solicitar_ferias, name='solicitar_ferias'),
path('ferias/minhas/', views.minhas_ferias, name='minhas_ferias'),
path('ferias/pedidos/', views.lista_pedidos_ferias, name='lista_pedidos_ferias'),
path('ferias/pedido/<int:pedido_id>/aprovar/', views.aprovar_pedido_ferias, name='aprovar_pedido_ferias'),
path('relatorios/ferias/', views.relatorio_ferias, name='relatorio_ferias'),

    # ========== RELATÓRIOS ==========
    path('relatorios/licencas/', views.relatorio_licencas, name='relatorio_licencas'),
    path('relatorios/avaliacoes/', views.relatorio_avaliacoes, name='relatorio_avaliacoes'),
    path('relatorios/presencas/', views.relatorio_presencas, name='relatorio_presencas'),
    path('relatorios/folha-efetividade/', views.folha_efetividade, name='folha_efetividade'),
    path('relatorios/mensal/<int:mes>/<int:ano>/', views.relatorio_mensal_view, name='relatorio_mensal'),

    # ========== COMUNICAÇÃO INTERNA ==========
    path('comunicacao/chat/', views.chat_principal, name='chat_principal'),
    path('comunicacao/chat/criar/', views.criar_canal, name='criar_canal'),
    path('comunicacao/chat/diretas/', views.lista_usuarios_chat, name='lista_usuarios_chat'),
    path('comunicacao/chat/iniciar-conversa/', views.iniciar_conversa_direta, name='iniciar_conversa_direta'),
    path('comunicacao/canal/<int:canal_id>/', views.canal_chat, name='canal_chat'),
    path('comunicacao/canal/<int:canal_id>/enviar-mensagem/', views.enviar_mensagem, name='enviar_mensagem'),
    path('comunicacao/chat/editar/<int:canal_id>/', views.editar_canal, name='editar_canal'),

    # ========== APIs PARA CHAT ==========
    path('api/chat/<int:canal_id>/mensagens/', views.api_chat_mensagens, name='api_chat_mensagens'),
    path('api/chat/upload/', views.upload_arquivo_chat, name='upload_arquivo'),

    # ========== DOCUMENTOS ==========
    path('comunicacao/documentos/', views.documentos_institucionais, name='documentos_institucionais'),
    path('comunicacao/documentos/criar/', views.criar_documento, name='criar_documento'),
    path('comunicacao/documentos/<int:documento_id>/', views.visualizar_documento, name='visualizar_documento'),
    path('comunicacao/documentos/<int:documento_id>/download/', views.download_documento, name='download_documento'),

    # ========== RELATÓRIOS DE ATIVIDADES ==========
    path('comunicacao/relatorios/', views.relatorios_atividades, name='relatorios_atividades'),
    path('comunicacao/relatorios/criar/', views.criar_relatorio, name='criar_relatorio'),


# Licenças - RH
path('licencas/pendentes-rh/', views.lista_licencas_pendentes_rh, name='lista_licencas_pendentes_rh'),path('licencas/<int:licenca_id>/analisar-rh/', views.analisar_licenca_rh, name='analisar_licenca_rh'),

# Licenças - Chefe
path('chefe/licencas-setor/', views.licencas_do_setor, name='licencas_setor'),

# Licenças - Diretor
path('director/licencas-direcao/', views.licencas_da_direcao, name='licencas_direcao'),


    # ========== NOTIFICAÇÕES ==========
    path('notificacoes/minhas/', views.minhas_notificacoes, name='minhas_notificacoes'),
    path('notificacoes/configurar/', views.configurar_notificacoes, name='configurar_notificacoes'),

    # ========== APIs ==========
    path('api/notificacoes/pendentes/', views.api_notificacoes_pendentes, name='api_notificacoes_pendentes'),
    path('api/notificacoes/<int:notificacao_id>/marcar-lida/', views.api_marcar_notificacao_lida,
         name='api_marcar_notificacao_lida'),
    path('api/notificacoes/marcar-todas-lidas/', views.api_marcar_todas_notificacoes_lidas,
         name='api_marcar_todas_notificacoes_lidas'),

    # ========== APIs PARA FÉRIAS E LICENÇAS ==========
    path('api/verificar-ferias/', views.verificar_ferias_view, name='verificar_ferias'),
    path('api/calcular-dias-uteis/', views.calcular_dias_uteis_view, name='calcular_dias_uteis'),

    # ========== PROMOÇÕES ==========
    path('promocoes/', views.lista_promocoes, name='lista_promocoes'),
    path('promocoes/nova/', views.nova_promocao, name='nova_promocao'),
    path('promocoes/<int:promocao_id>/', views.detalhes_promocao, name='detalhes_promocao'),

    # ========== COMPETÊNCIAS ==========
    path('competencias/', views.lista_competencias, name='lista_competencias'),
    path('competencias/gerir/', views.gerir_competencia, name='criar_competencia'),
    path('competencias/gerir/<int:competencia_id>/', views.gerir_competencia, name='editar_competencia'),

    # ========== DIRETÓRIO DE USUÁRIOS ==========
    path('usuarios/diretorio/', views.lista_usuarios_status, name='lista_usuarios_status'),
]