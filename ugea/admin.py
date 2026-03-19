from django.contrib import admin
from .models import Concurso, Juri, CadernoEncargos, Proposta, AcompanhamentoExecucao, InscricaoConcurso

@admin.register(Concurso)
class ConcursoAdmin(admin.ModelAdmin):
    list_display = ['numero', 'titulo', 'tipo', 'data_abertura', 'status']
    list_filter = ['status', 'tipo']

@admin.register(Juri)
class JuriAdmin(admin.ModelAdmin):
    list_display = ['concurso', 'presidente', 'data_nomeacao']

@admin.register(CadernoEncargos)
class CadernoEncargosAdmin(admin.ModelAdmin):
    list_display = ['concurso', 'prazo_execucao_dias']

@admin.register(Proposta)
class PropostaAdmin(admin.ModelAdmin):
    list_display = ['fornecedor', 'concurso', 'valor_proposto', 'pontuacao_final']
    list_filter = ['concurso']

@admin.register(AcompanhamentoExecucao)
class AcompanhamentoExecucaoAdmin(admin.ModelAdmin):
    list_display = ['concurso', 'percentual_execucao', 'status_pagamento']

@admin.register(InscricaoConcurso)
class InscricaoConcursoAdmin(admin.ModelAdmin):
    list_display = ['empresa_nome', 'concurso', 'valor_pago', 'caderno_entregue']
    list_filter = ['caderno_entregue', 'concurso']
