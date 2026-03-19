from datetime import timezone

from django.contrib import admin
from .models import (
    Solicitante, TipoCredencial, Evento, PedidoCredencial,
    ModeloCredencial, CredencialEmitida,
    CredencialFuncionario, AuditoriaCredencial, ConfiguracaoEmergencia, ConfiguracaoCredenciais
)


@admin.register(Solicitante)
class SolicitanteAdmin(admin.ModelAdmin):
    list_display = ['nome_completo', 'tipo', 'validado', 'nacionalidade', 'email', 'ativo']
    list_filter = ['tipo', 'genero', 'nacionalidade', 'ativo', 'validado']
    search_fields = ['nome_completo', 'email', 'numero_bi', 'nif']
    readonly_fields = ['data_registo', 'numero_identificacao']
    list_editable = ['validado']
    actions = ['validar_bi_selecionados']

    # Corrigido: campos que não existem no modelo
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('tipo', 'nome_completo', 'email', 'telefone', 'genero', 'nacionalidade')
        }),
        ('Identificação', {
            'fields': ('numero_bi', 'data_validade_bi', 'nif', 'nup', 'numero_identificacao')
        }),
        ('Empresa/Coletivo', {
            'fields': ('nome_empresa', 'numero_registo_comercial', 'nif_empresa'),
            'classes': ('collapse',)
        }),
        ('Endereço', {
            'fields': ('endereco', 'provincia', 'distrito')
        }),
        ('Documentos', {
            'fields': ('documento_identificacao', 'foto')
        }),
        ('Status', {
            'fields': ('ativo', 'validado', 'validado_por', 'data_validacao')
        }),
        ('Metadados', {
            'fields': ('data_registo', 'data_atualizacao'),
            'classes': ('collapse',)
        }),
    )

    def validar_bi_selecionados(self, request, queryset):
        for solicitante in queryset:
            solicitante.validar_bi(request.user)
        self.message_user(request, f'{queryset.count()} BI(s) validados')


@admin.register(TipoCredencial)
class TipoCredencialAdmin(admin.ModelAdmin):
    list_display = ['nome', 'ordem', 'permite_acesso_geral', 'ativo']
    list_filter = ['permite_acesso_geral', 'ativo']
    list_editable = ['ordem', 'ativo']
    search_fields = ['nome', 'descricao']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'descricao', 'cor', 'ordem', 'ativo')
        }),
        ('Permissões', {
            'fields': ('permite_acesso_geral', 'zonas_permitidas', 'horario_acesso')
        }),
    )


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'data_inicio', 'data_fim', 'local', 'provincia', 'ativo']
    list_filter = ['provincia', 'ativo', 'permite_pedidos_remotos']
    search_fields = ['nome', 'local', 'descricao']
    list_editable = ['ativo']
    date_hierarchy = 'data_inicio'

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'descricao', 'local', 'provincia')
        }),
        ('Datas', {
            'fields': ('data_inicio', 'data_fim')
        }),
        ('Configurações', {
            'fields': ('limite_participantes', 'permite_pedidos_remotos', 'ativo')
        }),
        ('Documentos', {
            'fields': ('regulamento', 'logotipo')
        }),
        ('Responsáveis', {
            'fields': ('responsavel', 'criado_por')
        }),
        ('Metadados', {
            'fields': ('data_criacao',),
            'classes': ('collapse',)
        }),
    )


@admin.register(PedidoCredencial)
class PedidoCredencialAdmin(admin.ModelAdmin):
    list_display = ['numero_pedido', 'solicitante', 'tipo_credencial', 'evento', 'status', 'data_pedido']
    list_filter = ['status', 'tipo_credencial', 'data_pedido', 'pedido_remoto']
    search_fields = ['numero_pedido', 'solicitante__nome_completo', 'motivo']
    readonly_fields = ['numero_pedido', 'data_pedido', 'codigo_confirmacao']
    list_editable = ['status']
    actions = ['aprovar_pedidos', 'reprovar_pedidos']

    fieldsets = (
        ('Identificação', {
            'fields': ('numero_pedido', 'solicitante', 'evento', 'tipo_credencial')
        }),
        ('Detalhes do Pedido', {
            'fields': ('motivo', 'data_inicio', 'data_fim', 'quantidade')
        }),
        ('Status e Análise', {
            'fields': ('status', 'observacoes_analise', 'analisado_por', 'data_analise')
        }),
        ('Configurações', {
            'fields': ('pedido_remoto', 'codigo_confirmacao')
        }),
        ('Metadados', {
            'fields': ('data_pedido', 'criado_por', 'data_atualizacao'),
            'classes': ('collapse',)
        }),
    )

    def aprovar_pedidos(self, request, queryset):
        updated = queryset.filter(status__in=['pendente', 'em_analise']).update(
            status='aprovado',
            analisado_por=request.user,
            data_analise=timezone.now()
        )
        self.message_user(request, f'{updated} pedido(s) aprovado(s)')

    def reprovar_pedidos(self, request, queryset):
        updated = queryset.filter(status__in=['pendente', 'em_analise']).update(
            status='reprovado',
            analisado_por=request.user,
            data_analise=timezone.now()
        )
        self.message_user(request, f'{updated} pedido(s) reprovado(s)')


@admin.register(ModeloCredencial)
class ModeloCredencialAdmin(admin.ModelAdmin):
    list_display = ['nome', 'incluir_qr_code', 'incluir_codigo_offline', 'tamanho', 'ativo']
    list_filter = ['incluir_qr_code', 'incluir_codigo_offline', 'ativo']
    search_fields = ['nome', 'descricao']
    list_editable = ['ativo']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'descricao', 'ativo')
        }),
        ('Design', {
            'fields': ('cor_fundo', 'cor_texto', 'logotipo', 'tamanho')
        }),
        ('Funcionalidades', {
            'fields': ('incluir_qr_code', 'incluir_codigo_offline', 'template_html')
        }),
        ('Metadados', {
            'fields': ('data_criacao',),
            'classes': ('collapse',)
        }),
    )


@admin.register(CredencialEmitida)
class CredencialEmitidaAdmin(admin.ModelAdmin):
    list_display = ['numero_credencial', 'pedido', 'modelo', 'data_emissao', 'data_validade', 'status',
                    'bloqueio_emergencia']
    list_filter = ['status', 'data_emissao', 'modelo', 'bloqueio_emergencia']
    search_fields = ['numero_credencial', 'pedido__solicitante__nome_completo', 'codigo_offline']
    readonly_fields = ['data_emissao', 'codigo_verificacao', 'codigo_offline', 'numero_credencial']
    actions = ['gerar_qr_codes', 'ativar_credenciais', 'revogar_credenciais']

    fieldsets = (
        ('Identificação', {
            'fields': ('numero_credencial', 'pedido', 'modelo')
        }),
        ('Datas', {
            'fields': ('data_emissao', 'data_validade')
        }),
        ('Códigos de Segurança', {
            'fields': ('codigo_verificacao', 'codigo_offline', 'qr_code')
        }),
        ('Status', {
            'fields': ('status', 'bloqueio_emergencia', 'emitida_por')
        }),
        ('Metadados', {
            'fields': ('data_atualizacao',),
            'classes': ('collapse',)
        }),
    )

    def gerar_qr_codes(self, request, queryset):
        for credencial in queryset:
            if not credencial.qr_code:
                credencial.gerar_qr_code()
                credencial.save()
        self.message_user(request, f'{queryset.count()} QR Code(s) gerado(s)')

    def ativar_credenciais(self, request, queryset):
        updated = queryset.filter(status='emitida').update(status='ativa')
        self.message_user(request, f'{updated} credencial(is) ativada(s)')

    def revogar_credenciais(self, request, queryset):
        updated = queryset.update(status='revogada')
        self.message_user(request, f'{updated} credencial(is) revogada(s)')


@admin.register(CredencialFuncionario)
class CredencialFuncionarioAdmin(admin.ModelAdmin):
    list_display = ['numero_credencial', 'funcionario', 'tipo_credencial', 'data_emissao', 'data_validade', 'ativa']
    list_filter = ['tipo_credencial', 'ativa']
    search_fields = ['numero_credencial']
    readonly_fields = ['data_emissao', 'codigo_verificacao', 'codigo_offline']

    fieldsets = (
        ('Identificação', {
            'fields': ('numero_credencial', 'funcionario', 'tipo_credencial', 'modelo')
        }),
        ('Datas', {
            'fields': ('data_emissao', 'data_validade')
        }),
        ('Códigos de Segurança', {
            'fields': ('codigo_verificacao', 'codigo_offline', 'qr_code')
        }),
        ('Status', {
            'fields': ('ativa', 'emitida_por')
        }),
    )


@admin.register(AuditoriaCredencial)
class AuditoriaCredencialAdmin(admin.ModelAdmin):
    list_display = ['acao', 'usuario', 'solicitante', 'data_hora', 'ip_address']
    list_filter = ['acao', 'data_hora']
    search_fields = ['usuario__username', 'ip_address', 'detalhes']
    readonly_fields = ['data_hora', 'ip_address', 'user_agent', 'detalhes', 'acao', 'usuario']
    date_hierarchy = 'data_hora'

    fieldsets = (
        ('Ação', {
            'fields': ('acao', 'usuario', 'ip_address', 'user_agent')
        }),
        ('Objetos Relacionados', {
            'fields': ('solicitante', 'pedido', 'credencial')
        }),
        ('Detalhes', {
            'fields': ('detalhes',)
        }),
        ('Tempo', {
            'fields': ('data_hora',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ConfiguracaoEmergencia)
class ConfiguracaoEmergenciaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo_bloqueio', 'ativo', 'data_ativacao', 'credenciais_afetadas']
    list_filter = ['tipo_bloqueio', 'ativo']
    readonly_fields = ['data_ativacao', 'data_desativacao', 'credenciais_afetadas']
    actions = ['ativar_bloqueio', 'desativar_bloqueio']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'tipo_bloqueio', 'motivo')
        }),
        ('Filtros Específicos', {
            'fields': ('evento', 'tipo_credencial', 'provincia')
        }),
        ('Status', {
            'fields': ('ativo', 'ativado_por', 'credenciais_afetadas')
        }),
        ('Datas', {
            'fields': ('data_ativacao', 'data_desativacao')
        }),
    )

    def ativar_bloqueio(self, request, queryset):
        for config in queryset:
            if not config.ativo:
                config.ativar(request.user)
        self.message_user(request, f'{queryset.count()} bloqueio(s) ativado(s)')

    def desativar_bloqueio(self, request, queryset):
        for config in queryset:
            if config.ativo:
                config.desativar(request.user)
        self.message_user(request, f'{queryset.count()} bloqueio(s) desativado(s)')


@admin.register(ConfiguracaoCredenciais)
class ConfiguracaoCredenciaisAdmin(admin.ModelAdmin):
    list_display = ['chave', 'valor', 'tipo', 'categoria', 'ativo']
    list_filter = ['tipo', 'categoria', 'ativo']
    search_fields = ['chave', 'descricao', 'valor']
    list_editable = ['valor', 'ativo']
    readonly_fields = ['data_criacao', 'data_atualizacao']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('chave', 'valor', 'descricao')
        }),
        ('Classificação', {
            'fields': ('tipo', 'categoria', 'ativo')
        }),
        ('Metadados', {
            'fields': ('data_criacao', 'data_atualizacao'),
            'classes': ('collapse',)
        }),
    )