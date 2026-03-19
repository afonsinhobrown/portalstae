from django.contrib import admin
from .models import Eleicao, EventoEleitoral

@admin.register(Eleicao)
class EleicaoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo', 'ano', 'data_votacao', 'ativo']
    list_filter = ['tipo', 'ano', 'ativo']
    search_fields = ['nome']

@admin.register(EventoEleitoral)
class EventoEleitoralAdmin(admin.ModelAdmin):
    list_display = ['nome', 'eleicao', 'data_inicio', 'data_fim']
    list_filter = ['eleicao']
