from django.urls import path
from . import views

app_name = 'rs'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('eleicoes/', views.lista_eleicoes_rs, name='lista_eleicoes'),
    path('divisao-eleicao/', views.divisao_eleicao_index, name='divisao_eleicao_index'),
    path('eleicao/nova/', views.criar_eleicao_rs, name='criar_eleicao'),
    path('eleicao/<int:pk>/editar/', views.editar_eleicao_rs, name='editar_eleicao'),
    path('eleicao/<int:pk>/eliminar/', views.eliminar_eleicao_rs, name='eliminar_eleicao'),
    path('planos/', views.lista_planos, name='lista_planos'),
    path('novo/', views.criar_plano, name='criar_plano'),
    path('plano/<int:plano_id>/', views.detalhes_plano, name='detalhes_plano'),
    path('plano/<int:plano_id>/importar-modelo/', views.importar_distribuicao_plano, name='importar_modelo_plano'),
    path('plano/<int:pk>/editar/', views.editar_plano, name='editar_plano'),
    path('plano/<int:plano_id>/add-material/', views.adicionar_material_plano, name='adicionar_material'),
    path('plano/<int:plano_id>/add-atividade/', views.adicionar_atividade_plano, name='adicionar_atividade'),
    path('plano/<int:plano_id>/sugerir-ia/', views.sugerir_ia_logistica, name='sugerir_ia'),
    path('material/<int:material_id>/distribuir/', views.distribuir_material, name='distribuir_material'),
    
    # Documentos
    path('documentos/', views.documentos_view, name='documentos'),
    path('documentos/novo/', views.criar_tipo_documento, name='criar_tipo_documento'),
    path('documentos/editar/<int:tipo_id>/', views.editar_tipo_documento, name='editar_tipo_documento'),
    path('documentos/eliminar/<int:tipo_id>/', views.eliminar_tipo_documento, name='eliminar_tipo_documento'),
    path('documentos/inicializar/', views.inicializar_docs_padrao, name='inicializar_docs'),
    path('documentos/preview/cartao/', views.preview_cartao_eleitor, name='preview_cartao'),
    path('documentos/preview/generico/<int:tipo_id>/', views.preview_generico, name='preview_generico'),
    
    # Apuramento e Lançamento
    path('edital/lancar/', views.lancar_edital, name='lancar_edital'),
    path('edital/controlo/', views.documentos_view, name='controlo_editais'),
    
    path('gerar-plano-auto/<int:eleicao_id>/', views.gerar_plano_logistico_auto, name='gerar_plano_auto'),
    path('modelo-visual/decidir/<int:modelo_id>/<str:decisao>/', views.decidir_modelo_visual, name='decidir_modelo_visual'),
    
    # Gestão de Material
    path('material/editar/<int:material_id>/', views.editar_material, name='editar_material'),
    path('material/eliminar/<int:material_id>/', views.eliminar_material, name='eliminar_material'),
    path('material/novo/', views.criar_requisito_material, name='novo_material'),
    path('material/categorias/', views.gestao_categorias_materiais, name='gestao_categorias'),
    path('material/tipos/', views.gestao_tipos_materiais, name='gestao_tipos'),
    path('material/tipo/eliminar/<int:pk>/', views.eliminar_tipo_material, name='eliminar_tipo'),
    
    # Documentos — Galeria e Construtor
    path('documentos/tipo/<int:tipo_id>/templates/', views.galeria_templates, name='galeria_templates'),
    path('documentos/construtor/<int:tipo_id>/', views.construtor_documento, name='construtor_documento'),
    path('documentos/guardar/', views.guardar_documento_ajax, name='guardar_documento'),
    path('documentos/exportar-pdf/', views.exportar_pdf_documento, name='exportar_pdf_doc'),
    path('documentos/exportar-pdf/<int:doc_id>/', views.exportar_pdf_documento, name='exportar_pdf_doc_id'),
    path('documentos/inicializar-templates/', views.inicializar_templates_padrao, name='inicializar_templates'),

    # API Eleição (para sincronização no construtor)
    path('api/dados-eleicao/<int:eleicao_id>/', views.api_dados_eleicao, name='api_dados_eleicao'),

    # Gestão de Atividades
    path('atividade/editar/<int:atividade_id>/', views.editar_atividade, name='editar_atividade'),
    path('atividade/eliminar/<int:atividade_id>/', views.eliminar_atividade, name='eliminar_atividade'),
    
    # Relatórios
    path('plano/<int:plano_id>/report-selector/', views.selecao_relatorio_material, name='selecao_relatorio'),
    path('plano/<int:plano_id>/gerar-pdf/', views.gerar_pdf_plano, name='gerar_pdf'),
    path('material/inicializar-catalogo/', views.inicializar_catalogo_stae, name='inicializar_catalogo'),

    # --- NOVO HUB DE PLANEAMENTO (11 PONTOS) ---
    path('planeamento/', views.planeamento_hub, name='planeamento_hub'),
    path('planeamento/calendario/', views.calendario_eleitoral, name='calendario_eleitoral'),
    path('planeamento/rh/', views.gestao_rh_plano, name='gestao_rh_plano'),
    path('planeamento/riscos/', views.matriz_riscos, name='matriz_riscos'),
    path('planeamento/financeiro/', views.planeamento_financeiro, name='planeamento_financeiro'),
    path('planeamento/territorial/', views.planeamento_territorial, name='planeamento_territorial'),
]
