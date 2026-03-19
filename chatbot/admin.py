from django.contrib import admin
from .models import FAQEntry, DocumentoLegal, ConversationLog, KnowledgeGap


@admin.register(FAQEntry)
class FAQEntryAdmin(admin.ModelAdmin):
    list_display = ['pergunta', 'tags', 'fonte', 'data_atualizacao']
    search_fields = ['pergunta', 'resposta', 'tags']

    # Texto de ajuda para o campo tags
    fieldsets = (
        (None, {
            'fields': ('pergunta', 'resposta', 'fonte', 'confianca')
        }),
        ('Tags (Opcional)', {
            'fields': ('tags',),
            'description': '📝 <strong>Dica:</strong> Digite palavras separadas por VÍRGULA. Exemplo: votacao,documentos,bi'
        }),
    )


@admin.register(DocumentoLegal)
class DocumentoLegalAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'tipo', 'numero', 'data_publicacao']
    search_fields = ['titulo', 'conteudo']
    list_filter = ['tipo', 'data_publicacao']


@admin.register(ConversationLog)
class ConversationLogAdmin(admin.ModelAdmin):
    list_display = ['user_message_short', 'intent_detected', 'confidence', 'created_at']
    list_filter = ['intent_detected', 'created_at']
    readonly_fields = ['created_at']
    search_fields = ['user_message', 'bot_response']

    def user_message_short(self, obj):
        return obj.user_message[:50] + '...' if len(obj.user_message) > 50 else obj.user_message

    user_message_short.short_description = 'Mensagem'


@admin.register(KnowledgeGap)
class KnowledgeGapAdmin(admin.ModelAdmin):
    list_display = ['pergunta_short', 'frequencia', 'resolvido', 'data_deteccao']
    list_filter = ['resolvido', 'data_deteccao']
    actions = ['marcar_como_resolvido']

    def pergunta_short(self, obj):
        return obj.pergunta_nao_respondida[:60] + '...' if len(
            obj.pergunta_nao_respondida) > 60 else obj.pergunta_nao_respondida

    pergunta_short.short_description = 'Pergunta'

    def marcar_como_resolvido(self, request, queryset):
        updated = queryset.update(resolvido=True)
        self.message_user(request, f'{updated} lacunas marcadas como resolvidas.')

    marcar_como_resolvido.short_description = 'Marcar como resolvido'