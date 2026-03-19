from django.db import models
from eleicao.models import Eleicao

class CirculoEleitoral(models.Model):
    eleicao = models.ForeignKey(Eleicao, on_delete=models.CASCADE, related_name='circulos', verbose_name="Eleição")
    nome = models.CharField(max_length=200)
    codigo = models.CharField(max_length=20) # Removido unique pois o mesmo código pode existir em eleições diferentes
    provincia = models.CharField(max_length=100)
    num_eleitores = models.IntegerField(default=0)
    num_mandatos = models.IntegerField(default=0, verbose_name="Número de Mandatos")
    num_mesas = models.IntegerField(default=0)
    ativo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Círculo Eleitoral"
        verbose_name_plural = "Círculos Eleitorais"
        unique_together = ['eleicao', 'codigo'] # Garantir unicidade do código dentro da mesma eleição
    
    def __str__(self):
        return f"{self.nome} - {self.eleicao}"

class PostoVotacao(models.Model):
    circulo = models.ForeignKey(CirculoEleitoral, on_delete=models.CASCADE)
    nome = models.CharField(max_length=200)
    codigo = models.CharField(max_length=20)
    endereco = models.TextField()
    num_mesas = models.IntegerField(default=1)
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"

class DivisaoAdministrativa(models.Model):
    LEVELS = [
        ('provincia', 'Província'),
        ('distrito', 'Distrito'),
        ('posto', 'Posto Administrativo'),
    ]
    nome = models.CharField(max_length=200)
    codigo = models.CharField(max_length=20, unique=True)
    nivel = models.CharField(max_length=20, choices=LEVELS)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subdivisoes')

    class Meta:
        verbose_name = "Divisão Administrativa"
        verbose_name_plural = "Divisões Administrativas"
        ordering = ['codigo']

    def __str__(self):
        return f"{self.nivel.capitalize()}: {self.nome} ({self.codigo})"
