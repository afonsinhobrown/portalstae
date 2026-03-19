from django.urls import path
from . import views

app_name = 'ugea'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('novo/', views.criar_concurso, name='criar_concurso'),
    path('detalhe/<int:concurso_id>/', views.detalhe_concurso, name='detalhe_concurso'),
    path('editar/<int:concurso_id>/', views.editar_concurso, name='editar_concurso'),
    path('cadernos/', views.lista_cadernos, name='lista_cadernos'),
    path('contratos/', views.lista_contratos, name='lista_contratos'),
    path('contratos/novo/', views.novo_contrato, name='novo_contrato'),
    path('contratos/<int:contrato_id>/', views.detalhe_contrato, name='detalhe_contrato'),
    path('contratos/editar/<int:contrato_id>/', views.editar_contrato, name='editar_contrato'),
    path('contratos/<int:contrato_id>/item/novo/', views.adicionar_item_rapido, name='adicionar_item_rapido'),
    path('contratos/item/<int:item_id>/editar/', views.editar_item_contrato, name='editar_item_contrato'),
    path('contratos/<int:contrato_id>/sincronizar/', views.sincronizar_itens_contrato, name='sincronizar_itens_contrato'),
    path('contratos/item/<int:item_id>/excluir/', views.excluir_item_contrato, name='excluir_item_contrato'),
    path('fornecedores/', views.lista_fornecedores, name='lista_fornecedores'),
    path('fornecedores/novo/', views.novo_fornecedor, name='novo_fornecedor'),
    path('aprovacoes/', views.aprovacoes, name='aprovacoes'),
    path('concurso/<int:concurso_id>/caderno/', views.editar_caderno, name='editar_caderno'),
    path('concurso/<int:concurso_id>/caderno/template/', views.carregar_template_caderno, name='carregar_template_caderno'),
    path('concurso/<int:concurso_id>/imprimir-caderno/', views.imprimir_caderno, name='imprimir_caderno'),
    path('anuncio/editar/<int:concurso_id>/', views.editar_anuncio, name='editar_anuncio'),
    path('anuncio/imprimir/<int:concurso_id>/', views.imprimir_anuncio, name='imprimir_anuncio'),
    path('recibo/<int:inscricao_id>/', views.imprimir_recibo, name='imprimir_recibo'),
    path('vendas/<int:concurso_id>/', views.gestao_vendas, name='gestao_vendas'),
    path('avaliar/<int:proposta_id>/', views.avaliar_proposta, name='avaliar_proposta'),
    path('adjudicar/<int:proposta_id>/', views.adjudicar_proposta, name='adjudicar_proposta'),
    path('processar-ocr/<int:proposta_id>/', views.processar_ocr, name='processar_ocr'),
    path('editar-resumo/<int:proposta_id>/', views.editar_resumo, name='editar_resumo'),
    path('eliminar-proposta/<int:proposta_id>/', views.eliminar_proposta, name='eliminar_proposta'),
    path('pedidos/<int:pedido_id>/analisar/', views.avaliar_pedido, name='avaliar_pedido'),
]
