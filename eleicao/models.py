from django.db import models

class Eleicao(models.Model):
    TIPO_CHOICES = [
        ('presidencial', 'Presidencial'),
        ('legislativa', 'Legislativa'),
        ('provincial', 'Provincial'),
        ('autarquica', 'Autárquica'),
        ('geral', 'Gerais (Presidencial + Legislativa + Provincial)'),
    ]
    
    nome = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    ano = models.IntegerField()
    data_votacao = models.DateField()
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    
    # Configurações Adicionais
    limite_candidatos = models.IntegerField(default=0)
    percentual_apuramento = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    data_limite_candidaturas = models.DateField(null=True, blank=True)
    vagas_assembleia = models.IntegerField(default=250)
    obs_legais = models.TextField(blank=True, verbose_name="Observações Legais")
    
    class Meta:
        verbose_name = "Eleição"
        verbose_name_plural = "Eleições"
        ordering = ['-ano', '-data_votacao']
    
    def __str__(self):
        return f"{self.nome} ({self.ano})"

class EventoEleitoral(models.Model):
    """Eventos do calendário eleitoral (ex: Campanha, Reflexão, Votação)"""
    eleicao = models.ForeignKey(Eleicao, on_delete=models.CASCADE, related_name='eventos')
    nome = models.CharField(max_length=200)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    descricao = models.TextField(blank=True)
    
    class Meta:
        ordering = ['data_inicio']
    
    def __str__(self):
        return f"{self.nome} - {self.eleicao}"
