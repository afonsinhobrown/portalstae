from django.db import models
from eleicao.models import Eleicao
from circuloseleitorais.models import CirculoEleitoral
from partidos.models import Partido

class ControleEdital(models.Model):
    """Controlo de segurança para lançamento de editais"""
    MODALIDADE_CHOICES = [
        ('MESA', 'Mesa de Voto'),
        ('DISTRITAL', 'Centralização Distrital'),
    ]
    
    modalidade = models.CharField(max_length=20, choices=MODALIDADE_CHOICES)
    eleicao = models.ForeignKey(Eleicao, on_delete=models.CASCADE)
    circulo = models.ForeignKey(CirculoEleitoral, on_delete=models.CASCADE)
    
    identificador_geografico = models.CharField(max_length=100, help_text="Código da Mesa ou Nome do Distrito")
    codigo_edital = models.CharField(max_length=50, unique=True, verbose_name="Código do Edital (Pre-impresso)")
    codigo_validacao = models.CharField(max_length=50, unique=True, verbose_name="Código de Validação de Segurança")
    
    usado = models.BooleanField(default=False)
    data_geracao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Controlo de Edital"
        verbose_name_plural = "Controlo de Editais"

    def __str__(self):
        return f"{self.codigo_edital} - {self.identificador_geografico}"

class ResultadoEdital(models.Model):
    """Resultados oficiais lançados via Edital"""
    controle = models.OneToOneField(ControleEdital, on_delete=models.CASCADE, related_name='resultado')
    
    votos_brancos = models.PositiveIntegerField(default=0)
    votos_nulos = models.PositiveIntegerField(default=0)
    total_votantes = models.PositiveIntegerField(default=0)
    reclamacoes = models.TextField(blank=True)
    
    data_lancamento = models.DateTimeField(auto_now_add=True)
    utilizador_lancamento = models.CharField(max_length=100) # User que lançou

    def __str__(self):
        return f"Resultado Edital {self.controle.codigo_edital}"

class VotoPartidoEdital(models.Model):
    """Votos por partido num determinado Edital"""
    resultado = models.ForeignKey(ResultadoEdital, on_delete=models.CASCADE, related_name='votos_partidos')
    partido = models.ForeignKey(Partido, on_delete=models.CASCADE)
    quantidade_votos = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ['resultado', 'partido']
