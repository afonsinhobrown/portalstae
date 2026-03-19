from django.contrib import admin
from .models import TemplateImportacao, ImportacaoLog, ConfiguracaoSistema

@admin.register(TemplateImportacao)
class TemplateImportacaoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'app_destino', 'modelo_destino', 'data_criacao', 'activo']
    list_filter = ['app_destino', 'activo', 'data_criacao']
    search_fields = ['nome', 'modelo_destino']
    readonly_fields = ['data_criacao']
    list_editable = ['activo']

@admin.register(ImportacaoLog)
class ImportacaoLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'template', 'usuario', 'data_importacao', 'status', 'registros_importados']
    list_filter = ['status', 'data_importacao', 'template__app_destino']
    search_fields = ['template__nome', 'usuario__username']
    readonly_fields = ['data_importacao', 'registros_processados', 'registros_importados', 'erros']
    date_hierarchy = 'data_importacao'

@admin.register(ConfiguracaoSistema)
class ConfiguracaoSistemaAdmin(admin.ModelAdmin):
    list_display = ['chave', 'valor', 'data_atualizacao']
    search_fields = ['chave', 'descricao']
    readonly_fields = ['data_atualizacao']