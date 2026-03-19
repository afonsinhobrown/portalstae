from django.contrib import admin
from .models import PlanoLogistico, TipoDocumento, DocumentoGerado

@admin.register(PlanoLogistico)
class PlanoLogisticoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo', 'data_inicio', 'data_fim', 'orcamento_total']
    list_filter = ['tipo']

@admin.register(TipoDocumento)
class TipoDocumentoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'codigo']

@admin.register(DocumentoGerado)
class DocumentoGeradoAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'tipo', 'gerado_em']
    list_filter = ['tipo']
