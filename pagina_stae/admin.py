# pagina_stae/admin.py - VERSÃO CORRIGIDA
from django.contrib import admin
from django.utils.html import format_html
from .models import *


class ConteudoAdmin(admin.ModelAdmin):
    """Admin base para todos os conteúdos"""
    list_per_page = 20
    save_on_top = True


# pagina_stae/admin.py - ATUALIZAR NoticiaAdmin
@admin.register(Noticia)
class NoticiaAdmin(ConteudoAdmin):
    list_display = ['titulo', 'categoria', 'autor', 'publicado', 'destaque', 'data_publicacao', 'visualizacoes']
    list_filter = ['categoria', 'publicado', 'destaque', 'data_publicacao']
    list_editable = ['publicado', 'destaque']
    search_fields = ['titulo', 'resumo', 'conteudo']
    prepopulated_fields = {'slug': ['titulo']}
    date_hierarchy = 'data_publicacao'

    # ADICIONAR ESTE MÉTODO PARA PREENCHER AUTOMATICAMENTE
    def save_model(self, request, obj, form, change):
        if not obj.autor_id:  # Se não tem autor
            obj.autor = request.user  # Define o usuário atual como autor
        obj.save()

    # ADICIONAR ESTE FIELDSET
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('titulo', 'slug', 'categoria', 'resumo', 'autor')  # ← INCLUIR autor aqui
        }),
        ('Conteúdo', {
            'fields': ('conteudo', 'imagem_destaque')
        }),
        ('Configurações', {
            'fields': ('destaque', 'publicado', 'data_publicacao')
        }),
    )


class ImagemGaleriaInline(admin.TabularInline):
    model = ImagemGaleria
    extra = 3
    fields = ['imagem', 'titulo', 'descricao', 'ordem']


@admin.register(Galeria)  # ← APENAS UM REGISTRO PARA GALERIA
class GaleriaAdmin(ConteudoAdmin):
    list_display = ['titulo', 'publica', 'data_criacao', 'quantidade_imagens']
    list_filter = ['publica', 'data_criacao']
    search_fields = ['titulo', 'descricao']
    prepopulated_fields = {'slug': ['titulo']}
    inlines = [ImagemGaleriaInline]

    def quantidade_imagens(self, obj):
        return obj.imagens.count()

    quantidade_imagens.short_description = 'Imagens'


@admin.register(Video)
class VideoAdmin(ConteudoAdmin):
    list_display = ['titulo', 'destaque', 'data_publicacao']
    list_filter = ['destaque', 'data_publicacao']
    search_fields = ['titulo', 'descricao']


@admin.register(Departamento)
class DepartamentoAdmin(ConteudoAdmin):
    list_display = ['nome', 'sigla', 'ativo', 'ordem', 'responsavel']
    list_filter = ['ativo']
    list_editable = ['ativo', 'ordem']
    search_fields = ['nome', 'sigla', 'responsavel']


@admin.register(Servico)
class ServicoAdmin(ConteudoAdmin):
    list_display = ['nome', 'departamento', 'ativo', 'ordem']
    list_filter = ['departamento', 'ativo']
    list_editable = ['ativo', 'ordem']
    search_fields = ['nome', 'descricao']


@admin.register(Documento)
class DocumentoAdmin(ConteudoAdmin):
    list_display = ['titulo', 'tipo', 'data_publicacao', 'publico']
    list_filter = ['tipo', 'publico', 'data_publicacao']
    search_fields = ['titulo', 'descricao', 'numero']


@admin.register(FAQ)
class FAQAdmin(ConteudoAdmin):
    list_display = ['pergunta', 'categoria', 'ativo', 'ordem']
    list_filter = ['categoria', 'ativo']
    list_editable = ['ativo', 'ordem']
    search_fields = ['pergunta', 'resposta']


@admin.register(STAEConfiguracao)
class STAEConfiguracaoAdmin(ConteudoAdmin):
    list_display = ['titulo_portal', 'ativo']

    def has_add_permission(self, request):
        # Só permite uma configuração
        return not STAEConfiguracao.objects.exists()


# REGISTAR OS MODELOS SIMPLES (sem decorador duplicado)
admin.site.register(CategoriaNoticia, ConteudoAdmin)
admin.site.register(Pagina, ConteudoAdmin)

# REMOVER estes se existirem (causam duplicação):
# admin.site.register(Galeria, GaleriaAdmin)  ← REMOVER
# admin.site.register(Noticia, NoticiaAdmin)  ← REMOVER