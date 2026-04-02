from django.contrib import admin
from .models import CirculoEleitoral, PostoVotacao, DivisaoAdministrativa, DivisaoEleicao

@admin.register(DivisaoEleicao)
class DivisaoEleicaoAdmin(admin.ModelAdmin):
    list_display = ('eleicao', 'nivel', 'nome', 'codigo', 'parent')
    list_filter = ('eleicao', 'nivel')
    search_fields = ('nome', 'codigo')

@admin.register(CirculoEleitoral)
class CirculoEleitoralAdmin(admin.ModelAdmin):
    list_display = ['eleicao', 'codigo', 'nome', 'provincia', 'num_eleitores', 'num_mandatos', 'num_mesas', 'ativo']
    list_filter = ['eleicao', 'provincia', 'ativo']
    search_fields = ['nome', 'codigo']

@admin.register(PostoVotacao)
class PostoVotacaoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nome', 'circulo', 'num_mesas']
    list_filter = ['circulo__eleicao', 'circulo']

@admin.register(DivisaoAdministrativa)
class DivisaoAdministrativaAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nome', 'nivel', 'parent']
    list_filter = ['nivel']
    search_fields = ['nome', 'codigo']
