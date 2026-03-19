from django.urls import path
from . import views

app_name = 'rs'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('novo/', views.criar_plano, name='criar_plano'),
    path('plano/<int:plano_id>/', views.detalhes_plano, name='detalhes_plano'),
    
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
    path('edital/controlo/', views.documentos_view, name='controlo_editais'), # Placeholder por agora
    
    path('gerar-plano-auto/<int:eleicao_id>/', views.gerar_plano_logistico_auto, name='gerar_plano_auto'),
    path('modelo-visual/decidir/<int:modelo_id>/<str:decisao>/', views.decidir_modelo_visual, name='decidir_modelo_visual'),
    
    # Gestão de Material
    path('material/editar/<int:material_id>/', views.editar_material, name='editar_material'),
    path('material/eliminar/<int:material_id>/', views.eliminar_material, name='eliminar_material'),
]
