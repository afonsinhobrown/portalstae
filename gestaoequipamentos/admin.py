from django.contrib import admin
from .models import CategoriaEquipamento, TipoEquipamento, Equipamento, MovimentacaoEquipamento, Armazem, Inventario

@admin.register(CategoriaEquipamento)
class CategoriaEquipamentoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'codigo']
    search_fields = ['nome', 'codigo']

@admin.register(TipoEquipamento)
class TipoEquipamentoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'categoria']
    list_filter = ['categoria']
    search_fields = ['nome']

@admin.register(Equipamento)
class EquipamentoAdmin(admin.ModelAdmin):
    list_display = ['tipo', 'marca', 'modelo', 'numero_serie', 'sector_atual', 'estado']
    list_filter = ['tipo__categoria', 'estado', 'sector_atual']
    search_fields = ['numero_serie', 'matricula', 'marca', 'modelo']

@admin.register(MovimentacaoEquipamento)
class MovimentacaoEquipamentoAdmin(admin.ModelAdmin):
    list_display = ['equipamento', 'sector_origem', 'sector_destino', 'status', 'data_solicitacao']
    list_filter = ['status', 'data_solicitacao']
    search_fields = ['equipamento__numero_serie', 'motivo']

@admin.register(Armazem)
class ArmazemAdmin(admin.ModelAdmin):
    list_display = ['nome', 'sector', 'responsavel', 'capacidade']
    list_filter = ['sector']
    search_fields = ['nome', 'localizacao']

@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ['equipamento', 'armazem', 'quantidade']
    list_filter = ['armazem']
    search_fields = ['equipamento__numero_serie']