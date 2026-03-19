from django.db import models

class PlanoLogistico(models.Model):
    nome = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20)  # recenseamento/votacao
    descricao = models.TextField()
    data_inicio = models.DateField()
    data_fim = models.DateField()
    orcamento_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    class Meta:
        verbose_name_plural = "Planos Logísticos"
    
    def __str__(self):
        return self.nome

class TipoDocumento(models.Model):
    nome = models.CharField(max_length=100) # Cartão Eleitor, Boletim Voto
    codigo = models.CharField(max_length=20, unique=True)
    template_html = models.TextField(help_text="Caminho do template HTML ou conteúdo")
    
    def __str__(self):
        return self.nome

class DocumentoGerado(models.Model):
    tipo = models.ForeignKey(TipoDocumento, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    arquivo_pdf = models.FileField(upload_to='rs/documentos/')
    gerado_em = models.DateTimeField(auto_now_add=True)
    dados_json = models.JSONField(default=dict, help_text="Dados usados na geração")
    
    def __str__(self):
        return f"{self.tipo.nome} - {self.titulo}"

class MaterialEleitoral(models.Model):
    """Definição de necessidades e requisitos de materiais no módulo RS (Logística)"""
    TIPO_CHOICES = [
        ('urna_v', 'Urnas de Votação (Standard)'),
        ('urna_a', 'Urnas de Apuramento (Grandes)'),
        ('cabine', 'Cabines de Votação (Privacidade)'),
        ('boletim', 'Boletins de Voto Oficiais'),
        ('acta_v', 'Cadernos de Actas de Votação'),
        ('acta_a', 'Cadernos de Actas de Apuramento'),
        ('edital', 'Editais de Resultados (A3/A2)'),
        ('mapa', 'Mapas de Apuramento Distrital'),
        ('tinta_f', 'Tinta Indelével (Frascos 15ml)'),
        ('tinta_a', 'Almofadas de Tinta Indelével'),
        ('carimbo_v', 'Carimbos "VOTOU"'),
        ('carimbo_s', 'Carimbos Oficiais STAE'),
        ('almofada', 'Almofadas de Tinta (Azul/Preta)'),
        ('envelope_s', 'Envelopes de Segurança (Invioláveis)'),
        ('envelope_o', 'Envelopes Oficiais (A/B/C)'),
        ('saco_u', 'Sacos de Plástico p/ Urnas'),
        ('fita_l', 'Fita Adesiva Logotipada'),
        ('selo_p', 'Selos de Urna (Plástico Numerado)'),
        ('selo_g', 'Selos de Urna (Papel Engomado)'),
        ('caneta', 'Canetas Esferográficas'),
        ('lapis', 'Lápis de Carvão e Borrachas'),
        ('regua', 'Réguas Graduadas (30cm)'),
        ('agrafador', 'Agrafadores e Agrafos'),
        ('lanterna', 'Lanternas LED e Pilhas (AA/AAA)'),
        ('petromax', 'Candeeiros/Iluminação de Emergência'),
        ('megafone', 'Megafones p/ Gestão de Filas'),
        ('calculadora', 'Calculadoras Solares de Mesa'),
        ('tesoura', 'Tesouras e Colas de Bastão'),
        ('colete_m', 'Coletes Oficiais MMV (Azul)'),
        ('colete_p', 'Coletes de Polícia (Refletor)'),
        ('credencial', 'Credenciais e Crachás Oficiais'),
        ('distico', 'Dísticos de Sinalética e Numeração'),
        ('senha', 'Blocos de Senhas de Fila'),
        ('quadro', 'Quadros e Tripés p/ Editais'),
        ('corda', 'Corda de Balizamento (Metros)'),
        ('maleta', 'Maletas de Transporte de Kit'),
        ('infra', 'Mobiliário de Campanha (Mesas/Cadeiras)'),
    ]
    eleicao = models.ForeignKey('eleicao.Eleicao', on_delete=models.CASCADE, related_name='materiais_logistica')
    item = models.CharField(max_length=100, verbose_name="Item Necessário")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    quantidade_planeada = models.IntegerField(default=0, help_text="Quantidade estimada/necessária para a eleição")
    
    # Campo para ligar ao inventário real gerido na App Equipamentos
    equipamentos_vinculados = models.ManyToManyField('gestaoequipamentos.Equipamento', blank=True, related_name='necessidades_rs', help_text="Equipamentos reais alocados para esta necessidade")
    
    localizacao_destino = models.CharField(max_length=100, default="Armazém Central")
    
    class Meta:
        verbose_name = "Requisito de Material Eleitoral"
        verbose_name_plural = "Requisitos de Materiais Eleitorais"

    def __str__(self):
        return f"Necessidade: {self.item} - {self.eleicao}"
    
    @property
    def quantidade_alocada(self):
        return self.equipamentos_vinculados.count()

class DadosRecenseamento(models.Model):
    """Dados oficiais de recenseamento geridos pelo RS"""
    provincia = models.CharField(max_length=100)
    distrito = models.CharField(max_length=100)
    posto_administrativo = models.CharField(max_length=100, blank=True)
    localidade = models.CharField(max_length=100, blank=True)
    
    ano = models.IntegerField(default=2024)
    total_eleitores = models.IntegerField(default=0)
    total_mesas = models.IntegerField(default=0)
    
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Dados de Recenseamento"
        verbose_name_plural = "Dados de Recenseamento"
        unique_together = ['provincia', 'distrito', 'ano']

    def __str__(self):
        return f"{self.distrito} ({self.total_eleitores} eleitores)"

class Eleitor(models.Model):
    """Cadastro único de eleitores em Moçambique"""
    nome_completo = models.CharField(max_length=200)
    numero_cartao = models.CharField(max_length=20, unique=True)
    nascimento = models.DateField()
    nuit = models.CharField(max_length=15, blank=True, null=True)
    
    provincia = models.CharField(max_length=100)
    distrito = models.CharField(max_length=100)
    local_voto = models.CharField(max_length=200)
    
    ativo = models.BooleanField(default=True)
    data_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Eleitor"
        verbose_name_plural = "Eleitores"
        indexes = [
            models.Index(fields=['numero_cartao']),
            models.Index(fields=['nuit']),
        ]

    def __str__(self):
        return f"{self.nome_completo} ({self.numero_cartao})"

class ModeloVisualArtefacto(models.Model):
    """Gestão Iterativa de Propostas Visuais para Artefactos de Soberania"""
    STATUS_CHOICES = [
        ('pendente', 'Proposta Pendente'),
        ('aceite', 'Oficializado/Aceite'),
        ('reprovado', 'Reprovado/Iterar'),
    ]
    TIPO_ARTEFACTO = [
        ('urna', 'Urna de Votação'),
        ('cabine', 'Cabine de Votação'),
        ('colete', 'Colete/Indumentária'),
        ('distico', 'Dístico/Sinalética'),
        ('boletim', 'Layout de Boletim'),
    ]
    
    eleicao = models.ForeignKey('eleicao.Eleicao', on_delete=models.CASCADE, related_name='modelos_visuais')
    tipo = models.CharField(max_length=20, choices=TIPO_ARTEFACTO)
    versao = models.IntegerField(default=1, help_text="Número da tentativa (Máximo 50)")
    imagem = models.ImageField(upload_to='rs/modelos/', verbose_name="Proposta Visual")
    descricao_tecnica = models.TextField(blank=True, verbose_name="Memória Descritiva")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    data_criacao = models.DateTimeField(auto_now_add=True)
    feedback_admin = models.TextField(blank=True, help_text="Razão da aprovação ou reprovação")

    class Meta:
        verbose_name = "Proposta de Modelo Visual"
        verbose_name_plural = "Propostas de Modelos Visuais"
        ordering = ['eleicao', 'tipo', '-versao']

    def __str__(self):
        return f"{self.get_tipo_display()} - V{self.versao} ({self.status})"

    def iterar(self, nova_imagem, nova_descricao=""):
        """Gera uma nova tentativa se a anterior foi reprovada (Máximo 50)"""
        if self.versao >= 50:
            return None
        return ModeloVisualArtefacto.objects.create(
            eleicao=self.eleicao,
            tipo=self.tipo,
            versao=self.versao + 1,
            imagem=nova_imagem,
            descricao_tecnica=nova_descricao
        )

from .models_apuramento import ControleEdital, ResultadoEdital, VotoPartidoEdital
