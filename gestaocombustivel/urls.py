from django.urls import path
from . import views

app_name = 'gestaocombustivel'

urlpatterns = [
    # Dashboard
    path('', views.dashboard_combustivel, name='dashboard_combustivel'),

    # Viaturas
    path('viaturas/', views.lista_viaturas, name='lista_viaturas'),
    path('viaturas/nova/', views.ViaturaCreateView.as_view(), name='nova_viatura'),
    path('viaturas/<int:viatura_id>/', views.detalhe_viatura, name='detalhe_viatura'),
    path('viaturas/<int:viatura_id>/editar/', views.ViaturaUpdateView.as_view(), name='editar_viatura'),
    path('viaturas/<int:viatura_id>/desactivar/', views.desactivar_viatura, name='desactivar_viatura'),
    path('viaturas/<int:viatura_id>/activar/', views.activar_viatura, name='activar_viatura'),
    path('viaturas/<int:viatura_id>/historico/', views.historico_viatura, name='historico_viatura'),

    # Combustível
    path('combustivel/pedir/', views.pedir_combustivel, name='pedir_combustivel'),
    path('combustivel/pedidos/', views.lista_pedidos_combustivel, name='lista_pedidos'),
    path('combustivel/pedidos/<int:pedido_id>/aprovar/', views.aprovar_pedido_combustivel, name='aprovar_pedido'),

    # Fornecedores
    path('fornecedores/', views.lista_fornecedores, name='lista_fornecedores'),
    path('fornecedores/novo/', views.criar_fornecedor, name='novo_fornecedor'),
    path('fornecedores/editar/<int:fornecedor_id>/', views.editar_fornecedor, name='editar_fornecedor'),
    path('fornecedores/<int:fornecedor_id>/desactivar/', views.desactivar_fornecedor, name='desactivar_fornecedor'),
    path('fornecedores/<int:fornecedor_id>/activar/', views.activar_fornecedor, name='activar_fornecedor'),

    # Contratos
    path('contratos/', views.lista_contratos, name='lista_contratos'),
    path('contratos/novo/', views.criar_contrato, name='novo_contrato'),
    path('contratos/editar/<int:contrato_id>/', views.editar_contrato, name='editar_contrato'),
    path('contratos/<int:contrato_id>/detalhes/', views.detalhe_contrato, name='detalhe_contrato'),
    path('contratos/<int:contrato_id>/pagamento/', views.registrar_pagamento_contrato, name='registrar_pagamento'),
    path('pagamentos/<int:pagamento_id>/eliminar/', views.eliminar_pagamento, name='eliminar_pagamento'),

    # Impressão
    path('combustivel/pedidos/<int:pedido_id>/imprimir/', views.imprimir_requisicao, name='imprimir_requisicao'),


    # Seguros
    path('seguros/', views.lista_seguros, name='lista_seguros'),
    path('seguros/novo/', views.SeguroCreateView.as_view(), name='novo_seguro'),
    path('seguros/<int:seguro_id>/renovar/', views.renovar_seguro, name='renovar_seguro'),

    # Manutenções
    path('manutencao/solicitar/', views.solicitar_manutencao, name='solicitar_manutencao'),
    path('manutencao/lista/', views.lista_manutencoes, name='lista_manutencoes'),
    path('manutencao/<int:manutencao_id>/concluir/', views.concluir_manutencao, name='concluir_manutencao'),


    # Oficinas e Contratos Manutenção
    path('manutencao/oficinas/', views.lista_oficinas, name='lista_oficinas'),
    path('manutencao/oficinas/nova/', views.nova_oficina, name='nova_oficina'),
    path('manutencao/contratos/', views.lista_contratos_manutencao, name='lista_contratos_manutencao'),
    path('manutencao/contratos/novo/', views.novo_contrato_manutencao, name='novo_contrato_manutencao'),
    path('manutencao/contratos/<int:contrato_id>/', views.detalhe_contrato_manutencao, name='detalhe_contrato_manutencao'),
    path('manutencao/contratos/<int:contrato_id>/editar/', views.editar_contrato_manutencao, name='editar_contrato_manutencao'),
    path('manutencao/<int:manutencao_id>/imprimir/', views.imprimir_ordem_manutencao, name='imprimir_ordem_manutencao'),

    # Rotas
    path('rotas/', views.lista_rotas, name='lista_rotas'),
    path('rotas/imprimir-lista/', views.imprimir_lista_rotas, name='imprimir_lista_rotas'),
    path('rotas/nova/', views.criar_rota, name='nova_rota'),
    path('rotas/<int:rota_id>/', views.detalhe_rota, name='detalhe_rota'),
    path('rotas/<int:rota_id>/pontos/novo/', views.adicionar_ponto_rota, name='novo_ponto_rota'),
    path('rotas/<int:rota_id>/editar/', views.editar_rota, name='editar_rota'),
    path('rotas/<int:rota_id>/imprimir/', views.imprimir_rota, name='imprimir_rota'),
    path('rotas/<int:rota_id>/funcionarios/adicionar/', views.adicionar_funcionario_rota, name='add_funcionario_rota'),
    path('rotas/registro-diario/', views.registro_diario_rota, name='registro_diario'),

    # Relatórios
    path('relatorios/', views.relatorios_combustivel, name='relatorios'),
    path('relatorios/exportar/', views.exportar_relatorio_csv, name='exportar_relatorio'),

    # Configuração
    path('configuracao/', views.configuracao_sistema, name='configuracao_sistema'),
]