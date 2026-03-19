from django.db import models
from django.utils import timezone

class Partido(models.Model):
    """Partido Político"""
    
    # Dados Básicos
    sigla = models.CharField(max_length=20, unique=True, verbose_name="Sigla")
    nome_completo = models.CharField(max_length=200, verbose_name="Nome Completo")
    nome_abreviado = models.CharField(max_length=100, blank=True, verbose_name="Nome Abreviado")
    
    # Identificação
    numero_registo = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="Número de Registo")
    data_fundacao = models.DateField(blank=True, null=True, verbose_name="Data de Fundação")
    data_registo = models.DateField(blank=True, null=True, verbose_name="Data de Registo")
    
    # Visual Identity
    simbolo = models.ImageField(upload_to='partidos/simbolos/', blank=True, null=True, verbose_name="Símbolo do Partido")
    cor_primaria = models.CharField(max_length=7, default='#000000', help_text="Cor em hex (#RRGGBB)", verbose_name="Cor Primária")
    cor_secundaria = models.CharField(max_length=7, blank=True, help_text="Cor em hex (#RRGGBB)", verbose_name="Cor Secundária")
    
    # Contatos
    email = models.EmailField(blank=True, verbose_name="Email Oficial")
    telefone = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    website = models.URLField(blank=True, verbose_name="Website")
    
    # Sede
    endereco_sede = models.TextField(blank=True, verbose_name="Endereço da Sede")
    provincia_sede = models.CharField(max_length=100, blank=True, verbose_name="Província")
    distrito_sede = models.CharField(max_length=100, blank=True, verbose_name="Distrito")
    
    # Liderança
    presidente = models.CharField(max_length=200, blank=True, verbose_name="Presidente")
    secretario_geral = models.CharField(max_length=200, blank=True, verbose_name="Secretário-Geral")
    
    # Documentação
    estatutos = models.FileField(upload_to='partidos/documentos/', blank=True, null=True, verbose_name="Estatutos")
    manifesto = models.FileField(upload_to='partidos/documentos/', blank=True, null=True, verbose_name="Manifesto/Programa")
    
    # Status
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    suspenso = models.BooleanField(default=False, verbose_name="Suspenso")
    motivo_suspensao = models.TextField(blank=True, verbose_name="Motivo de Suspensão")
    
    # Observações
    notas = models.TextField(blank=True, verbose_name="Notas/Observações")
    
    # Metadata
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Partido"
        verbose_name_plural = "Partidos"
        ordering = ['sigla']
    
    def __str__(self):
        return f"{self.sigla} - {self.nome_completo}"


class LiderancaPartido(models.Model):
    """Histórico de Liderança do Partido"""
    
    partido = models.ForeignKey(Partido, on_delete=models.CASCADE, related_name='historico_lideranca')
    cargo = models.CharField(max_length=100, verbose_name="Cargo")
    nome = models.CharField(max_length=200, verbose_name="Nome")
    data_inicio = models.DateField(verbose_name="Data de Início")
    data_fim = models.DateField(blank=True, null=True, verbose_name="Data de Fim")
    ativo = models.BooleanField(default=True, verbose_name="Em Exercício")
    
    class Meta:
        verbose_name = "Liderança"
        verbose_name_plural = "Lideranças"
        ordering = ['-data_inicio']
    
    def __str__(self):
        return f"{self.nome} - {self.cargo} ({self.partido.sigla})"
