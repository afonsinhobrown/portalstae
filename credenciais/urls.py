from django.urls import path
from . import views, views_dfec, views_funcionarios, views_certificados

app_name = 'credenciais'

urlpatterns = [
    # Dashboard
    path('', views.dashboard_credenciais, name='dashboard_credenciais'),

    # Solicitantes
    path('solicitantes/', views.lista_solicitantes, name='lista_solicitantes'),
    path('solicitantes/adicionar/', views.adicionar_solicitante, name='adicionar_solicitante'),

    # Eventos
    path('eventos/', views.lista_eventos, name='lista_eventos'),
    path('eventos/novo/', views.adicionar_evento, name='adicionar_evento'),
    path('eventos/<int:evento_id>/', views.detalhe_evento, name='detalhe_evento'),
    path('eventos/<int:evento_id>/editar/', views.editar_evento, name='editar_evento'),
    
    # Rastreio
    path('rastreio/', views.rastrear_pedido, name='rastrear_pedido'),

    # Tipos de Credencial
    path('tipos-credencial/', views.lista_tipos_credencial, name='lista_tipos_credencial'),
    path('tipos-credencial/novo/', views.adicionar_tipo_credencial, name='adicionar_tipo_credencial'),
    path('tipos-credencial/<int:tipo_id>/editar/', views.editar_tipo_credencial, name='editar_tipo_credencial'),

    # Pedidos
    path('pedidos/', views.lista_pedidos, name='lista_pedidos'),
    path('pedir-credencial/', views.pedir_credencial, name='pedir_credencial'),
    path('pedidos/novo/', views.pedir_credencial, name='pedidos_novo'),
    path('pedir-credencial-remoto/', views.pedir_credencial_remoto, name='pedir_credencial_remoto'),
    path('pedido-remoto/', views.pedir_credencial_remoto, name='pedido_remoto'),
    path('pedido-sucesso/', views.pedido_sucesso, name='pedido_sucesso'),
    path('analisar-pedido/<int:pedido_id>/', views.analisar_pedido, name='analisar_pedido'),

    # Emissão de Credenciais
    # Emissão de Credenciais
    path('emitir-credencial/<int:pedido_id>/', views.emitir_credencial, name='emitir_credencial'),
    path('emitir-em-lote/', views.emitir_em_lote, name='emitir_em_lote'),

    # Credenciais Emitidas
    path('credencial/<int:credencial_id>/', views.detalhe_credencial, name='detalhe_credencial'),
    path('credencial/pdf/<int:credencial_id>/', views.visualizar_pdf_credencial, name='visualizar_pdf'),
    path('credencial/download/<int:credencial_id>/', views.download_pdf_credencial, name='download_pdf'),
    path('credencial/imprimir/<int:credencial_id>/', views.imprimir_credencial, name='imprimir_credencial'),
    path('auditoria/', views.auditoria_view, name='auditoria'), # Mantendo link legado se necessário

    # Reimpressão e Cartão
    path('credencial/reimprimir/<int:credencial_id>/', views.reimprimir_credencial, name='reimprimir_credencial'),
    path('credencial/<int:credencial_id>/imprimir/', views.visualizar_para_impressao, name='imprimir_cartao'),
    path('credencial/<int:credencial_id>/png/', views.exportar_cartao_png, name='exportar_png'),

    path('gerar-qrcode/<int:pk>/', views.gerar_qrcode, name='gerar_qrcode'),

    # PDFs de Cartão (Rotas diretas para download/visualização)
    path('credencial/cartao/pdf/<int:credencial_id>/', views.visualizar_pdf_cartao_credencial, name='visualizar_pdf_cartao'),
    path('credencial/cartao/download/<int:credencial_id>/', views.download_pdf_cartao_credencial, name='download_pdf_cartao'),
    # Credenciais de Funcionários
    path('funcionarios/', views.lista_credenciais_funcionarios, name='lista_credenciais_funcionarios'),
    path('funcionarios/emitir/', views.emitir_credencial_funcionario, name='emitir_credencial_funcionario'),
    path('funcionarios/pdf/<int:credencial_id>/', views.pdf_credencial_funcionario, name='pdf_funcionario'),

    # Verificação
    path('verificar/', views.verificar_credencial, name='verificar_credencial'),
    path('verificar-offline/', views.verificar_credencial_offline, name='verificar_offline'),

    # Emergência
    path('emergencia/', views.emergencia_bloqueio, name='emergencia_bloqueio'),
    path('emergencia/desativar/<int:config_id>/', views.desativar_bloqueio_emergencia,
         name='desativar_bloqueio_emergencia'),

    # Relatórios e Auditoria
    path('relatorios/', views.relatorios_credenciais, name='relatorios_credenciais'),
    path('relatorios/pdf/', views.relatorio_credenciais_pdf, name='relatorio_pdf'),
    path('auditoria/', views.auditoria_credenciais, name='auditoria_credenciais'),

    # Utilitários
    path('download-zip/', views.download_credenciais_zip, name='download_zip'),

    # Módulo DFEC (Formação)
    path('dfec/', views_dfec.dashboard_dfec, name='dfec_dashboard'),
    path('dfec/curso/<int:evento_id>/', views_dfec.detalhe_curso, name='dfec_detalhe_curso'),
    path('dfec/curso/<int:evento_id>/inscrever/', views_dfec.inscrever_lote, name='dfec_inscrever_lote'),
    path('dfec/curso/<int:evento_id>/download-zip/', views_dfec.baixar_todas_credenciais, name='dfec_download_zip'),

    # Módulo Funcionários (Lote STAE)
    path('funcionarios/lote/', views_funcionarios.configurar_emissao_lote, name='func_configurar_lote'),
    path('funcionarios/lote/processar/', views_funcionarios.processar_emissao_lote, name='func_processar_lote'),

    # Módulo Certificação (Diplomas)
    path('certificacao/', views_certificados.dashboard, name='cert_dashboard'),
    path('certificacao/novo/', views_certificados.novo_projeto, name='cert_novo'),
    path('certificacao/editor/<int:projeto_id>/', views_certificados.editor_projeto, name='cert_editor'),
    path('certificacao/beneficiarios/<int:projeto_id>/', views_certificados.gerir_beneficiarios, name='cert_beneficiarios'),
    path('certificacao/download/<int:doc_id>/', views_certificados.baixar_pdf_unico, name='cert_download_unico'),
    path('certificacao/download-lote/<int:projeto_id>/', views_certificados.baixar_lote_certificado, name='cert_download_lote'),
    path('certificacao/remover/<int:doc_id>/', views_certificados.remover_beneficiario, name='cert_remover_beneficiario'),
    
    # API
    path('api/verificar-offline/', views.api_verificar_offline, name='api_verificar_offline'),
    path('api/evento-detalhes/<int:evento_id>/', views.api_get_evento_detalhes, name='api_evento_detalhes'),
    path('api/buscar-solicitante/', views.api_buscar_solicitante, name='api_buscar_solicitante'),
]
