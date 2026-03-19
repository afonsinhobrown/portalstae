from django.contrib import admin
from .models import InscricaoPartidoEleicao, ListaCandidatura, Candidato

class CandidatoInline(admin.TabularInline):
    model = Candidato
    extra = 1

@admin.register(InscricaoPartidoEleicao)
class InscricaoPartidoEleicaoAdmin(admin.ModelAdmin):
    list_display = ['partido', 'eleicao', 'status', 'data_inscricao']
    list_filter = ['eleicao', 'status']

@admin.register(ListaCandidatura)
class ListaCandidaturaAdmin(admin.ModelAdmin):
    list_display = ['inscricao_partido', 'circulo', 'cargo_disputado', 'validada']
    list_filter = ['circulo', 'validada']
    inlines = [CandidatoInline]

    def inscricao_partido(self, obj):
        return obj.inscricao.partido.sigla

@admin.register(Candidato)
class CandidatoAdmin(admin.ModelAdmin):
    list_display = ['nome_completo', 'lista', 'posicao', 'tipo', 'status_eleitor']
    list_filter = ['tipo', 'status_eleitor']
    search_fields = ['nome_completo', 'bi_numero']
