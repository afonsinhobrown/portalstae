# recursoshumanos/admin.py - VERSÃO CORRIGIDA
from django.contrib import admin
from django.contrib.auth.models import Group, User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils import timezone
from .models import *


# Custom User Admin para adicionar grupos
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_groups')
    list_filter = ('is_staff', 'is_superuser', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')

    def get_groups(self, obj):
        return ", ".join([g.name for g in obj.groups.all()])

    get_groups.short_description = 'Grupos'


# Unregister default User admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# Sector Admin
class SectorAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nome', 'direcao', 'chefe', 'ativo')
    list_filter = ('ativo', 'direcao')
    search_fields = ('codigo', 'nome')
    raw_id_fields = ('chefe', 'direcao')


# Funcionario Admin
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ('nome_completo', 'numero_identificacao', 'sector', 'funcao', 'data_admissao', 'ativo')
    list_filter = ('ativo', 'sector', 'funcao', 'genero', 'estado_civil')
    search_fields = ('nome_completo', 'numero_identificacao', 'numero_bi', 'nuit', 'niss', 'telefone')
    raw_id_fields = ('user', 'sector')
    readonly_fields = ('data_criacao', 'data_atualizacao', 'numero_identificacao', 'qr_code_hash',
                       'qr_code_data', 'tempo_servico', 'idade', 'cartao_valido')

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('numero_identificacao', 'nome_completo', 'foto', 'foto_webcam', 'user')
        }),
        ('Informações Pessoais', {
            'fields': ('data_nascimento', 'genero', 'estado_civil', 'nacionalidade', 'naturalidade',
                       'nome_pai', 'nome_mae')
        }),
        ('Identificação Oficial', {
            'fields': ('numero_bi', 'data_emissao_bi', 'local_emissao_bi',
                       'nuit', 'data_emissao_nuit',
                       'niss', 'data_inscricao_inss')
        }),
        ('Informações Profissionais', {
            'fields': ('sector', 'funcao', 'data_admissao', 'data_saida', 'ativo')
        }),
        ('Contactos', {
            'fields': ('telefone', 'telefone_alternativo', 'email_pessoal', 'email_institucional',
                       'endereco', 'bairro', 'distrito', 'provincia',
                       'contacto_emergencia', 'parentesco_emergencia')
        }),
        ('Informações Bancárias', {
            'fields': ('banco', 'nome_banco_outro', 'tipo_conta', 'numero_conta', 'nib', 'nub')
        }),
        ('Sistema QR Code e Cartão', {
            'fields': ('qr_code', 'qr_code_hash', 'qr_code_data',
                       'numero_cartao', 'data_emissao_cartao', 'data_validade_cartao'),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('data_criacao', 'data_atualizacao'),
            'classes': ('collapse',)
        }),
    )

    def idade(self, obj):
        return obj.idade()

    idade.short_description = 'Idade'

    def tempo_servico(self, obj):
        return obj.get_tempo_servico_display()

    tempo_servico.short_description = 'Tempo de Serviço'

    def cartao_valido(self, obj):
        return obj.cartao_valido()

    cartao_valido.boolean = True
    cartao_valido.short_description = 'Cartão Válido'


# Licenca Admin
class LicencaAdmin(admin.ModelAdmin):
    list_display = ('funcionario', 'tipo', 'data_inicio', 'data_fim', 'dias_utilizados', 'status')
    list_filter = ('status', 'tipo', 'data_inicio', 'funcionario__sector')
    search_fields = ('funcionario__nome_completo', 'motivo')
    raw_id_fields = ('funcionario', 'chefe_aprovador', 'diretor_aprovador')
    readonly_fields = ('data_criacao', 'data_atualizacao', 'hash_documento')
    date_hierarchy = 'data_inicio'


# AvaliacaoDesempenho Admin
class AvaliacaoDesempenhoAdmin(admin.ModelAdmin):
    list_display = ('funcionario', 'periodo', 'nota_final_geral', 'classificacao_final', 'avaliado_por',
                    'data_avaliacao')
    list_filter = ('classificacao_final', 'periodo', 'funcionario__sector', 'status')
    search_fields = ('funcionario__nome_completo', 'observacoes')
    raw_id_fields = ('funcionario', 'avaliado_por')
    readonly_fields = ('data_avaliacao',)


# Competencia Admin
class CompetenciaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'peso', 'ativo')
    list_filter = ('ativo',)
    search_fields = ('nome', 'descricao')


# CompetenciaAvaliada Admin
class CompetenciaAvaliadaAdmin(admin.ModelAdmin):
    list_display = ('avaliacao', 'competencia', 'pontuacao')
    list_filter = ('competencia', 'pontuacao')
    raw_id_fields = ('avaliacao', 'competencia')


# RegistroPresenca Admin
class RegistroPresencaAdmin(admin.ModelAdmin):
    list_display = ('funcionario', 'tipo', 'metodo', 'data_hora', 'ip_address')
    list_filter = ('tipo', 'metodo', 'data_hora')
    search_fields = ('funcionario__nome_completo', 'observacoes')
    raw_id_fields = ('funcionario',)
    date_hierarchy = 'data_hora'


# Promocao Admin
class PromocaoAdmin(admin.ModelAdmin):
    list_display = ('funcionario', 'data_promocao', 'cargo_anterior', 'cargo_atual', 'aprovado_por')
    list_filter = ('data_promocao',)
    search_fields = ('funcionario__nome_completo', 'cargo_atual')
    raw_id_fields = ('funcionario', 'aprovado_por')
    date_hierarchy = 'data_promocao'


# SaldoFerias Admin
class SaldoFeriasAdmin(admin.ModelAdmin):
    list_display = ('funcionario', 'ano', 'dias_disponiveis', 'dias_gozados', 'dias_saldo')
    list_filter = ('ano', 'funcionario__sector')
    search_fields = ('funcionario__nome_completo',)
    raw_id_fields = ('funcionario',)


# CanalComunicacao Admin
class CanalComunicacaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'criado_por', 'data_criacao', 'arquivado', 'membros_count')
    list_filter = ('tipo', 'arquivado')
    search_fields = ('nome', 'descricao')
    raw_id_fields = ('criado_por',)
    filter_horizontal = ('membros',)

    def membros_count(self, obj):
        return obj.membros.count()

    membros_count.short_description = 'Membros'


# Mensagem Admin
class MensagemAdmin(admin.ModelAdmin):
    list_display = ('canal', 'remetente', 'conteudo_truncado', 'data_envio', 'tem_arquivo')
    list_filter = ('canal', 'data_envio')
    search_fields = ('conteudo', 'remetente__username')
    raw_id_fields = ('canal', 'remetente', 'resposta_para')
    date_hierarchy = 'data_envio'

    def conteudo_truncado(self, obj):
        return obj.conteudo[:50] + '...' if len(obj.conteudo) > 50 else obj.conteudo

    conteudo_truncado.short_description = 'Conteúdo'

    def tem_arquivo(self, obj):
        return bool(obj.arquivo)

    tem_arquivo.boolean = True
    tem_arquivo.short_description = 'Arquivo'


# NotificacaoSistema Admin
class NotificacaoSistemaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'tipo', 'titulo_truncado', 'lida', 'data_criacao', 'prioridade')
    list_filter = ('tipo', 'lida', 'data_criacao', 'prioridade')
    search_fields = ('usuario__username', 'titulo', 'mensagem')
    raw_id_fields = ('usuario',)
    readonly_fields = ('data_criacao', 'data_leitura')
    date_hierarchy = 'data_criacao'

    def titulo_truncado(self, obj):
        return obj.titulo[:30] + '...' if len(obj.titulo) > 30 else obj.titulo

    titulo_truncado.short_description = 'Título'


# ========== DOCUMENTOS INSTITUCIONAIS - NOVOS MODELOS ==========

# TipoDocumento Admin
@admin.register(TipoDocumento)
class TipoDocumentoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nome', 'ativo', 'data_criacao']
    list_filter = ['ativo']
    search_fields = ['codigo', 'nome', 'descricao']
    readonly_fields = ['data_criacao']


# DocumentoInstitucional Admin - CORRIGIDO
@admin.register(DocumentoInstitucional)
class DocumentoInstitucionalAdmin(admin.ModelAdmin):
    list_display = [
        'numero_completo',
        'titulo',
        'tipo',
        'data_documento',
        'status',
        'classificacao',
        'criado_por'
    ]

    list_filter = [
        'tipo',
        'status',
        'classificacao',
        'data_documento',
        'publico'
    ]

    search_fields = [
        'numero_completo',
        'titulo',
        'descricao',
        'conteudo_texto'
    ]

    readonly_fields = [
        'numero_completo',
        'numero_sequencial',
        'data_criacao',
        'data_atualizacao',
        'hash_documento',
        'get_status_display_color',
        'tamanho_total_display',
    ]

    fieldsets = (
        ('Identificação', {
            'fields': ('numero_completo', 'tipo', 'titulo', 'descricao')
        }),
        ('Conteúdo', {
            'fields': ('conteudo_json', 'conteudo_html', 'conteudo_texto')
        }),
        ('Arquivos Gerados', {
            'fields': ('arquivo_docx', 'arquivo_pdf', 'arquivo_html')
        }),
        ('Datas', {
            'fields': ('data_documento', 'data_validade', 'data_publicacao')
        }),
        ('Status e Classificação', {
            'fields': ('status', 'classificacao', 'publico')
        }),
        ('Autoria', {
            'fields': ('criado_por', 'aprovado_por', 'revisado_por')
        }),
        ('Destinatários', {
            'fields': ('setores_destino', 'funcionarios_destino')
        }),
        ('Versões', {
            'fields': ('versao', 'versao_anterior')
        }),
        ('Informações Técnicas', {
            'fields': ('hash_documento', 'data_criacao', 'data_atualizacao')
        }),
    )

    filter_horizontal = ['setores_destino', 'funcionarios_destino']

    date_hierarchy = 'data_documento'

    ordering = ['-data_documento', '-numero_sequencial']

    # Actions personalizadas
    actions = ['marcar_como_publicado', 'marcar_como_arquivado']

    def marcar_como_publicado(self, request, queryset):
        updated = queryset.update(status='publicado', data_publicacao_field=timezone.now())
        self.message_user(request, f"{updated} documentos marcados como publicados.")

    marcar_como_publicado.short_description = "Marcar como publicado"

    def marcar_como_arquivado(self, request, queryset):
        updated = queryset.update(status='arquivado')
        self.message_user(request, f"{updated} documentos arquivados.")

    marcar_como_arquivado.short_description = "Arquivar documentos"

    def get_status_display_color(self, obj):
        """Exibe status com cor no admin"""
        cores = {
            'rascunho': 'warning',
            'revisao': 'info',
            'aprovado': 'primary',
            'publicado': 'success',
            'arquivado': 'secondary',
            'cancelado': 'danger',
        }
        color = cores.get(obj.status, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, obj.get_status_display())

    get_status_display_color.short_description = "Status"

    def tamanho_total_display(self, obj):
        """Exibe tamanho total formatado"""
        tamanho = obj.tamanho_total
        if tamanho < 1:
            return f"{tamanho * 1024:.1f} KB"
        return f"{tamanho:.2f} MB"

    tamanho_total_display.short_description = "Tamanho Total"


# AnexoDocumento Admin
@admin.register(AnexoDocumento)
class AnexoDocumentoAdmin(admin.ModelAdmin):
    list_display = ['documento', 'titulo', 'tipo', 'get_tamanho_formatado', 'data_upload', 'upload_por']
    list_filter = ['tipo', 'data_upload']
    search_fields = ['titulo', 'descricao', 'documento__titulo']
    readonly_fields = ['tamanho', 'data_upload']

    def get_tamanho_formatado(self, obj):
        if obj.tamanho < 1024:
            return f"{obj.tamanho} B"
        elif obj.tamanho < 1024 * 1024:
            return f"{obj.tamanho / 1024:.1f} KB"
        else:
            return f"{obj.tamanho / (1024 * 1024):.1f} MB"

    get_tamanho_formatado.short_description = "Tamanho"


# HistoricoDocumento Admin
@admin.register(HistoricoDocumento)
class HistoricoDocumentoAdmin(admin.ModelAdmin):
    list_display = ['documento', 'acao', 'usuario', 'data_acao']
    list_filter = ['acao', 'data_acao']
    search_fields = ['documento__titulo', 'descricao', 'usuario__username']
    readonly_fields = ['data_acao', 'ip_address', 'user_agent']
    date_hierarchy = 'data_acao'

    # Não permitir adicionar histórico manualmente
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# ========== MODELOS ANTIGOS (MANTER PARA COMPATIBILIDADE) ==========

# DocumentoInstitucional ANTIGO (para compatibilidade)
class DocumentoInstitucionalAntigoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'data_documento', 'status', 'publico', 'criado_por')
    list_filter = ('tipo', 'status', 'publico', 'data_documento')
    search_fields = ('titulo', 'descricao')
    raw_id_fields = ('criado_por', 'revisado_por', 'aprovado_por')
    filter_horizontal = ('setores_destino', 'funcionarios_destino')
    readonly_fields = ('data_criacao', 'data_atualizacao')
    date_hierarchy = 'data_documento'

    # Removido 'numero' e 'formato' que não existem
    def tamanho(self, obj):
        if obj.arquivo:
            return f"{obj.arquivo.size / 1024:.1f} KB"
        return "0 KB"

    tamanho.short_description = 'Tamanho'


# RelatorioAtividade Admin
class RelatorioAtividadeAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'periodo_inicio', 'periodo_fim', 'criado_por', 'publico')
    list_filter = ('tipo', 'publico', 'periodo_inicio')
    search_fields = ('titulo', 'descricao')
    raw_id_fields = ('criado_por', 'setor')
    filter_horizontal = ('compartilhar_com',)
    readonly_fields = ('data_criacao', 'data_atualizacao', 'visualizacoes')
    date_hierarchy = 'periodo_inicio'


# ConfiguracaoNotificacao Admin
class ConfiguracaoNotificacaoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'mostrar_licencas', 'mostrar_avaliacoes', 'mostrar_documentos', 'som_notificacoes')
    list_filter = ('mostrar_licencas', 'mostrar_avaliacoes', 'mostrar_documentos')
    search_fields = ('usuario__username',)
    raw_id_fields = ('usuario',)


# ConfiguracaoFerias Admin
class ConfiguracaoFeriasAdmin(admin.ModelAdmin):
    list_display = ('dias_base_ferias', 'dias_maximo_acumulo', 'prazo_marcacao_ferias', 'data_atualizacao')
    readonly_fields = ('data_atualizacao', 'atualizado_por')


# Registrar todos os modelos ANTIGOS
admin.site.register(Sector, SectorAdmin)
admin.site.register(Funcionario, FuncionarioAdmin)
admin.site.register(Licenca, LicencaAdmin)
admin.site.register(AvaliacaoDesempenho, AvaliacaoDesempenhoAdmin)
admin.site.register(Competencia, CompetenciaAdmin)
admin.site.register(CompetenciaAvaliada, CompetenciaAvaliadaAdmin)
admin.site.register(RegistroPresenca, RegistroPresencaAdmin)
admin.site.register(Promocao, PromocaoAdmin)
admin.site.register(SaldoFerias, SaldoFeriasAdmin)
admin.site.register(CanalComunicacao, CanalComunicacaoAdmin)
admin.site.register(Mensagem, MensagemAdmin)
admin.site.register(NotificacaoSistema, NotificacaoSistemaAdmin)
admin.site.register(ConfiguracaoNotificacao, ConfiguracaoNotificacaoAdmin)

# Registrar modelo antigo apenas se existir
try:
    # Verificar se o modelo antigo ainda existe
    from .models import DocumentoInstitucional as DocumentoInstitucionalAntigo

    admin.site.register(DocumentoInstitucionalAntigo, DocumentoInstitucionalAntigoAdmin)
except:
    pass

try:
    from .models import RelatorioAtividade

    admin.site.register(RelatorioAtividade, RelatorioAtividadeAdmin)
except:
    pass

try:
    from .models import ConfiguracaoFerias

    admin.site.register(ConfiguracaoFerias, ConfiguracaoFeriasAdmin)
except:
    pass

# Personalizar título do admin
admin.site.site_header = 'Portal STAE - Administração'
admin.site.site_title = 'Portal STAE'
admin.site.index_title = 'Administração do Sistema de Recursos Humanos'