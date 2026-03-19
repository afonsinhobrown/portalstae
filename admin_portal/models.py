from django.db import models
from django.contrib.auth.models import User


class TemplateImportacao(models.Model):
    app_label = 'admin_portal'
    TIPO_APP_CHOICES = [
        ('recursoshumanos', 'Recursos Humanos'),
        ('gestaoequipamentos', 'Gestão de Equipamentos'),
        ('gestaocombustivel', 'Gestão de Combustível'),
    ]

    nome = models.CharField(max_length=100, unique=True)
    app_destino = models.CharField(max_length=50, choices=TIPO_APP_CHOICES)
    modelo_destino = models.CharField(max_length=100)
    ficheiro_template = models.FileField(upload_to='templates_importacao/')
    mapeamento_campos = models.JSONField()
    data_criacao = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(User, on_delete=models.CASCADE)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Template de Importação"
        verbose_name_plural = "Templates de Importação"
        ordering = ['-data_criacao']

    def __str__(self):
        return f"{self.nome} ({self.get_app_destino_display()})"


class ImportacaoLog(models.Model):
    app_label = 'admin_portal'
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('processando', 'Processando'),
        ('sucesso', 'Sucesso'),
        ('erro', 'Erro'),
        ('cancelado', 'Cancelado'),
    ]

    template = models.ForeignKey(TemplateImportacao, on_delete=models.CASCADE)
    ficheiro_importado = models.FileField(upload_to='importacoes/')
    data_importacao = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    registros_processados = models.IntegerField(default=0)
    registros_importados = models.IntegerField(default=0)
    erros = models.JSONField(default=list, blank=True)
    relatorio_importacao = models.TextField(blank=True)

    class Meta:
        verbose_name = "Log de Importação"
        verbose_name_plural = "Logs de Importação"
        ordering = ['-data_importacao']

    def __str__(self):
        return f"Importação {self.id} - {self.template.nome}"


class ConfiguracaoSistema(models.Model):
    app_label = 'admin_portal'
    chave = models.CharField(max_length=100, unique=True)
    valor = models.TextField()
    descricao = models.TextField(blank=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuração do Sistema"
        verbose_name_plural = "Configurações do Sistema"

    def __str__(self):
        return self.chave