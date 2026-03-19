from django.db import models
from django.contrib.auth.models import User


class FAQEntry(models.Model):
    pergunta = models.TextField()
    resposta = models.TextField()
    tags = models.CharField(max_length=200, blank=True, default='')
    confianca = models.FloatField(default=1.0)
    fonte = models.CharField(max_length=200, default='STAE Moçambique')
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'

    def __str__(self):
        return self.pergunta[:50]


class DocumentoLegal(models.Model):
    titulo = models.CharField(max_length=300)
    conteudo = models.TextField()
    tipo = models.CharField(max_length=50, choices=[
        ('lei', 'Lei'),
        ('regulamento', 'Regulamento'),
        ('portaria', 'Portaria'),
        ('outro', 'Outro')
    ])
    numero = models.CharField(max_length=50)
    data_publicacao = models.DateField()
    arquivo = models.FileField(upload_to='documentos/', blank=True, null=True)

    class Meta:
        verbose_name = 'Documento Legal'
        verbose_name_plural = 'Documentos Legais'

    def __str__(self):
        return f"{self.titulo} ({self.numero})"


class ConversationLog(models.Model):
    user_message = models.TextField()
    bot_response = models.TextField()
    intent_detected = models.CharField(max_length=50)
    confidence = models.FloatField()
    user_feedback = models.IntegerField(null=True, blank=True)
    session_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Log de Conversa'
        verbose_name_plural = 'Logs de Conversas'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.intent_detected}: {self.user_message[:30]}"


class KnowledgeGap(models.Model):
    pergunta_nao_respondida = models.TextField()
    contexto = models.TextField(blank=True)
    frequencia = models.IntegerField(default=1)
    resolvido = models.BooleanField(default=False)
    data_deteccao = models.DateTimeField(auto_now_add=True)
    data_resolucao = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Lacuna de Conhecimento'
        verbose_name_plural = 'Lacunas de Conhecimento'

    def __str__(self):
        return self.pergunta_nao_respondida[:50]