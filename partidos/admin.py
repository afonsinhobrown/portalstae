from django.contrib import admin
from .models import Partido, LiderancaPartido

@admin.register(Partido)
class PartidoAdmin(admin.ModelAdmin):
    list_display = ['sigla', 'nome_completo', 'presidente', 'ativo']
    search_fields = ['sigla', 'nome_completo']
    list_filter = ['ativo', 'suspenso']

@admin.register(LiderancaPartido)
class LiderancaPartidoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cargo', 'partido', 'data_inicio', 'ativo']
    list_filter = ['ativo', 'partido']
