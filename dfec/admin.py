# dfec/admin.py - VERSÃO SIMPLIFICADA FUNCIONAL
from django.contrib import admin

# IMPORTS BÁSICOS - APENAS O ESSENCIAL
try:
    from dfec.models.completo import (
        PlanoAtividade, Formacao, Participante, Turma, Brigada,
        Eleicao, DadosEleicao, AnaliseRegiao,
        RelatorioGerado, AlertaSistema
    )
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False
    print("AVISO: Modelos do dfec não disponíveis. Admin será vazio.")

# REGISTRA APENAS SE OS MODELOS EXISTIREM
if MODELS_AVAILABLE:
    @admin.register(PlanoAtividade)
    class PlanoAtividadeAdmin(admin.ModelAdmin):
        list_display = ['nome', 'tipo', 'status', 'data_inicio_planeada', 'data_fim_planeada', 'responsavel_principal']
    
    @admin.register(Formacao)
    class FormacaoAdmin(admin.ModelAdmin):
        list_display = ['nome', 'tipo_formacao', 'local_realizacao', 'vagas_planeadas', 'vagas_preenchidas', 'status']
    
    @admin.register(Participante)
    class ParticipanteAdmin(admin.ModelAdmin):
        list_display = ['nome_completo', 'formacao', 'status', 'provincia', 'distrito', 'idade']
    
    @admin.register(Turma)
    class TurmaAdmin(admin.ModelAdmin):
        list_display = ['nome', 'formacao', 'formador_principal', 'data_inicio', 'data_fim']
    
    @admin.register(Brigada)
    class BrigadaAdmin(admin.ModelAdmin):
        list_display = ['codigo', 'formacao', 'provincia', 'distrito', 'localidade', 'completa', 'ativa']
    
    @admin.register(Eleicao)
    class EleicaoAdmin(admin.ModelAdmin):
        list_display = ['tipo', 'ano', 'descricao', 'dados_carregados', 'data_carregamento']
    
    @admin.register(DadosEleicao)
    class DadosEleicaoAdmin(admin.ModelAdmin):
        list_display = ['eleicao', 'provincia', 'distrito', 'localidade', 'total_inscritos', 'comparecimento']
    
    @admin.register(AnaliseRegiao)
    class AnaliseRegiaoAdmin(admin.ModelAdmin):
        list_display = ['eleicao', 'nivel', 'nome_regiao', 'indicador', 'classificacao', 'prioridade']
    
    @admin.register(RelatorioGerado)
    class RelatorioGeradoAdmin(admin.ModelAdmin):
        list_display = ['titulo', 'tipo', 'formato', 'gerado_por', 'data_geracao']
    
    @admin.register(AlertaSistema)
    class AlertaSistemaAdmin(admin.ModelAdmin):
        list_display = ['tipo', 'nivel', 'titulo', 'resolvido', 'visualizado', 'criado_em']
