from django.db import models

class Provincia(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    codigo = models.CharField(max_length=10, blank=True, null=True, unique=True)
    
    def __str__(self):
        return self.nome
    
    class Meta:
        ordering = ['nome']

class Distrito(models.Model):
    provincia = models.ForeignKey(Provincia, on_delete=models.CASCADE, related_name='distritos')
    nome = models.CharField(max_length=100)
    codigo = models.CharField(max_length=10, blank=True, null=True)
    
    def __str__(self):
        return f"{self.nome} ({self.provincia.nome})"
    
    class Meta:
        ordering = ['provincia', 'nome']
        unique_together = ['provincia', 'nome']

class ResultadoEleitoral(models.Model):
    """
    Armazena os resultados detalhados das eleições (Mesa a Mesa).
    Foco em análise de qualidade do voto (Nulos e Abstenções).
    """
    TIPO_ELEICAO_CHOICES = (
        ('AM', 'Assembleia Municipal'),
        ('PCM', 'Presidente Conselho Municipal'),
        ('AP', 'Assembleia Provincial'),
    )

    # Identificação da Mesa de Voto
    codigo_assembleia = models.CharField(max_length=50, help_text="Código único da mesa/assembleia") # Removed unique=True to allow multiple years
    
    # Dados Originais (Auditoria)
    provincia_original = models.CharField(max_length=100, db_column='provincia')
    distrito_original = models.CharField(max_length=100, db_column='distrito')
    posto_administrativo = models.CharField(max_length=100, blank=True, null=True)
    localidade = models.CharField(max_length=100, blank=True, null=True)
    local_votacao = models.CharField(max_length=255, help_text="Nome da Escola ou Local")
    
    # Links Canônicos (Normalização)
    provincia_ref = models.ForeignKey(Provincia, on_delete=models.SET_NULL, null=True, blank=True, related_name='resultados')
    distrito_ref = models.ForeignKey(Distrito, on_delete=models.SET_NULL, null=True, blank=True, related_name='resultados')
    
    # Metadados
    tipo_eleicao = models.CharField(max_length=10, choices=TIPO_ELEICAO_CHOICES, default='AM')
    ano = models.IntegerField(default=2018)
    
    # Dados Numéricos Principais
    eleitores_inscritos = models.IntegerField(default=0)
    total_votantes = models.IntegerField(default=0)
    votos_validos = models.IntegerField(default=0)
    votos_nulos = models.IntegerField(default=0)
    votos_branco = models.IntegerField(default=0)
    abstencoes = models.IntegerField(default=0)
    
    # Timestamps
    data_importacao = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['provincia_original', 'distrito_original', 'codigo_assembleia']
        verbose_name = "Resultado Eleitoral"
        verbose_name_plural = "Resultados Eleitorais"
        unique_together = ['codigo_assembleia', 'ano', 'tipo_eleicao'] # Composite key for uniqueness
        indexes = [
            models.Index(fields=['provincia_original', 'distrito_original']),
            models.Index(fields=['votos_nulos']),
            models.Index(fields=['abstencoes']),
            models.Index(fields=['ano']),
        ]

    def __str__(self):
        return f"{self.distrito_original} - {self.codigo_assembleia} ({self.ano})"

    @property
    def provincia(self):
        return self.provincia_original

    @property
    def distrito(self):
        return self.distrito_original

    @property
    def taxa_abstencao(self):
        if self.eleitores_inscritos > 0:
            return (self.abstencoes / self.eleitores_inscritos) * 100
        return 0

    @property
    def taxa_nulos(self):
        if self.total_votantes > 0:
            return (self.votos_nulos / self.total_votantes) * 100
        return 0

    @property
    def taxa_brancos(self):
        if self.total_votantes > 0:
            return (self.votos_branco / self.total_votantes) * 100
        return 0

class MatrizRecomendacao(models.Model):
    METRICA_CHOICES = [
        ('taxa_abstencao', 'Taxa de Abstenção'),
        ('taxa_nulos', 'Taxa de Votos Nulos'),
        ('taxa_brancos', 'Taxa de Votos em Branco'),
    ]
    NIVEL_CHOICES = [
        ('todos', 'Qualquer Nível'),
        ('provincial', 'Provincial'),
        ('distrital', 'Distrital'),
        ('posto', 'Posto/Localidade'),
    ]
    PRIORIDADE_CHOICES = [
        ('media', 'Média'), 
        ('alta', 'Alta'), 
        ('critica', 'Crítica')
    ]
    
    metrica = models.CharField(max_length=20, choices=METRICA_CHOICES, verbose_name="Métrica Analisada")
    nivel_analise = models.CharField(max_length=20, choices=NIVEL_CHOICES, default='todos', verbose_name="Nível de Aplicação")
    
    min_valor = models.DecimalField(max_digits=5, decimal_places=2, help_text="Ativar regra a partir de %")
    max_valor = models.DecimalField(max_digits=5, decimal_places=2, help_text="Até %", default=100.00)
    
    titulo = models.CharField(max_length=200, verbose_name="Título do Alerta")
    acao_sugerida = models.TextField(help_text="Ação estratégica recomendada. Use {unidade} para o nome dinâmico.")
    prioridade = models.CharField(max_length=20, choices=PRIORIDADE_CHOICES, default='media')
    
    def __str__(self):
        return f"{self.get_metrica_display()} > {self.min_valor}% ({self.prioridade})"
    
    class Meta:
        verbose_name = "Matriz de Recomendação"
        verbose_name_plural = "Matrizes de Recomendação"
        ordering = ['metrica', 'min_valor']
