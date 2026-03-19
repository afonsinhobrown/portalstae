
from django.contrib import admin
from .models import (Viatura, FornecedorCombustivel, PedidoCombustivel,
                     ManutencaoViatura, SeguroViatura, RotaTransporte,
                     PontoRota, FuncionarioRota, RegistroDiarioRota,
                     FornecedorManutencao, ContratoManutencao)

# Configuração de Modelos existentes
@admin.register(Viatura)
class ViaturaAdmin(admin.ModelAdmin):
    list_display = ['matricula', 'marca', 'modelo', 'tipo_viatura', 'tipo_combustivel',
                   'funcionario_afecto', 'estado', 'activa']
    list_filter = ['tipo_viatura', 'tipo_combustivel', 'estado', 'activa', 'ano_fabrico']
    search_fields = ['matricula', 'marca', 'modelo', 'numero_chassi']
    readonly_fields = ['data_criacao']
    list_editable = ['estado', 'activa']

@admin.register(FornecedorCombustivel)
class FornecedorCombustivelAdmin(admin.ModelAdmin):
    list_display = ['nome', 'nuit', 'contacto', 'activo']
    list_filter = ['activo']
    search_fields = ['nome', 'nuit']

@admin.register(PedidoCombustivel)
class PedidoCombustivelAdmin(admin.ModelAdmin):
    list_display = ['id', 'viatura', 'solicitante', 'tipo_pedido', 'quantidade_litros',
                   'custo_total', 'status', 'data_pedido']
    list_filter = ['tipo_pedido', 'status', 'data_pedido', 'fornecedor']
    search_fields = ['viatura__matricula', 'solicitante__nome_completo', 'numero_senha']
    readonly_fields = ['data_pedido', 'custo_total']

@admin.register(ManutencaoViatura)
class ManutencaoViaturaAdmin(admin.ModelAdmin):
    # Adicionado fornecedor e contrato
    list_display = ['viatura', 'tipo_manutencao', 'status', 'data_agendada',
                   'fornecedor', 'custo_real']
    list_filter = ['tipo_manutencao', 'status', 'data_agendada']
    search_fields = ['viatura__matricula', 'fornecedor__nome', 'descricao']
    readonly_fields = ['data_solicitacao']

@admin.register(SeguroViatura)
class SeguroViaturaAdmin(admin.ModelAdmin):
    list_display = ['numero_apolice', 'viatura', 'tipo_seguro', 'companhia_seguros',
                   'data_inicio', 'data_fim', 'activo']
    list_filter = ['tipo_seguro', 'activo', 'data_inicio']
    search_fields = ['numero_apolice', 'viatura__matricula', 'companhia_seguros']
    readonly_fields = ['data_registo']

@admin.register(RotaTransporte)
class RotaTransporteAdmin(admin.ModelAdmin):
    list_display = ['nome_rota', 'viatura', 'motorista', 'hora_partida', 'activa']
    list_filter = ['activa', 'dias_semana']
    search_fields = ['nome_rota', 'viatura__matricula']
    readonly_fields = ['data_criacao']

@admin.register(PontoRota)
class PontoRotaAdmin(admin.ModelAdmin):
    list_display = ['nome_ponto', 'rota', 'ordem', 'hora_estimada']
    list_filter = ['rota']
    ordering = ['rota', 'ordem']

@admin.register(FuncionarioRota)
class FuncionarioRotaAdmin(admin.ModelAdmin):
    list_display = ['funcionario', 'rota', 'ponto_embarque']
    list_filter = ['rota']
    search_fields = ['funcionario__nome_completo']

@admin.register(RegistroDiarioRota)
class RegistroDiarioRotaAdmin(admin.ModelAdmin):
    list_display = ['rota', 'data', 'motorista', 'hora_partida_real', 'confirmado_por_motorista']
    list_filter = ['data', 'confirmado_por_motorista']
    search_fields = ['rota__nome_rota', 'motorista__nome_completo']
    readonly_fields = ['data_registo'] # Alterado de data para data_registo pois data eh editavel

# NOVOS REGISTROS

@admin.register(FornecedorManutencao)
class FornecedorManutencaoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'nuit', 'contacto', 'email', 'activo']
    list_filter = ['activo']
    search_fields = ['nome', 'nuit', 'especialidades']
    readonly_fields = ['data_registo']

@admin.register(ContratoManutencao)
class ContratoManutencaoAdmin(admin.ModelAdmin):
    list_display = ['numero_contrato', 'fornecedor', 'valor_total', 'valor_gasto', 'saldo_disponivel', 'estado']
    list_filter = ['activo', 'data_inicio', 'data_fim']
    search_fields = ['numero_contrato', 'fornecedor__nome']
    readonly_fields = ['data_registo', 'valor_gasto']