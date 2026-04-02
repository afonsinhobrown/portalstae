from django.db import models
from django.utils.timezone import now

class PlanoLogistico(models.Model):
    """Centraliza a planificação logística para um evento eleitoral"""
    TIPO_OPERACAO = [
        ('RECENSEAMENTO', 'Operação de Recenseamento'),
        ('VOTACAO', 'Operação de Votação'),
    ]
    nome = models.CharField(max_length=200, verbose_name="Nome do Plano")
    tipo_operacao = models.CharField(max_length=20, choices=TIPO_OPERACAO, default='VOTACAO', verbose_name="Tipo de Operação")
    eleicao = models.ForeignKey('eleicao.Eleicao', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Eleição Associada")
    eleicao_referencia = models.ForeignKey('eleicao.Eleicao', on_delete=models.SET_NULL, null=True, blank=True, related_name='planos_ref', verbose_name="Eleição Passada (Referência)", help_text="Ciclo anterior usado como base.")
    
    data_inicio = models.DateField(default=now)
    data_fim = models.DateField(null=True, blank=True)
    
    orcamento_total = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    responsavel = models.CharField(max_length=100, blank=True)
    descricao = models.TextField(blank=True)
    esta_ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Planos Logísticos"

    def __str__(self):
        return f"{self.get_tipo_operacao_display()}: {self.nome}"

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

class CategoriaMaterial(models.Model):
    """Categorias para organização de materiais (ex: Logística, Tecnologia, Papelaria)"""
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)

    class Meta:
        verbose_name = "Categoria de Material"
        verbose_name_plural = "Categorias de Materiais"
        ordering = ['nome']

    def __str__(self):
        return self.nome

class TipoMaterial(models.Model):
    """Tipos específicos de materiais definidos pelo usuário (ex: Urna Média, Boletim A4)"""
    categoria = models.ForeignKey(CategoriaMaterial, on_delete=models.CASCADE, related_name='tipos')
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    icone = models.CharField(max_length=50, default='fas fa-cube', help_text="Classe FontAwesome (ex: fas fa-box)")

    class Meta:
        verbose_name = "Tipo de Material"
        verbose_name_plural = "Tipos de Materiais"
        ordering = ['categoria', 'nome']

    def __str__(self):
        return f"{self.categoria.nome} - {self.nome}"

class MaterialEleitoral(models.Model):
    """Previsão de Novo Material (Nivel Nacional)"""
    TIPO_OPERACAO = [
        ('RECENSEAMENTO', 'Material de Recenseamento'),
        ('VOTACAO', 'Material de Votação'),
    ]
    plano = models.ForeignKey(PlanoLogistico, on_delete=models.CASCADE, related_name='materiais', null=True, blank=True)
    eleicao = models.ForeignKey('eleicao.Eleicao', on_delete=models.CASCADE, related_name='materiais_logistica', verbose_name="Eleição", null=True, blank=True)
    
    tipo_operacao = models.CharField(max_length=20, choices=TIPO_OPERACAO, default='VOTACAO', verbose_name="Tipo de Operação")
    item = models.CharField(max_length=100, verbose_name="Item / Material Nacional")
    tipo_dinamico = models.ForeignKey(TipoMaterial, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Tipo de Catálogo")
    
    ano_referencia = models.IntegerField(null=True, blank=True, verbose_name="Ano de Referência")
    eleicao_referencia = models.ForeignKey('eleicao.Eleicao', on_delete=models.SET_NULL, null=True, blank=True, related_name='materiais_ref', verbose_name="Eleição de Referência")

    quantidade_adquirida_referencia = models.IntegerField(default=0, verbose_name="Qtd. Adquirida Ref.")
    preco_unitario_referencia = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Preço Unit. Ref.")
    
    quantidade_existente = models.IntegerField(default=0, verbose_name="Stock Existente")
    quantidade_planeada = models.IntegerField(default=0, verbose_name="Previsão Necessária")
    
    preco_unitario = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Preço Unit. Estimado")
    descricao = models.TextField(blank=True, null=True, verbose_name="Notas")
    
    # Automatização Geográfica
    por_distrito = models.BooleanField(default=False, verbose_name="É calculado por Distrito?")

    
    class Meta:
        verbose_name = "Previsão de Material"
        verbose_name_plural = "Previsões de Materiais"

    def __str__(self):
        return f"Previsão: {self.item}"
    
    @property
    def margem_seguranca_qtd(self):
        return int(self.quantidade_adquirida_referencia * 0.3)

    @property
    def margem_seguranca_preco(self):
        return float(self.preco_unitario_referencia) * 0.3

    @property
    def previsao_sugerida(self):
        return self.quantidade_adquirida_referencia + self.margem_seguranca_qtd

    @property
    def reforco_nacional(self):
        return max(0, self.quantidade_planeada - self.quantidade_existente)

    @property
    def total_distribuido(self):
        return sum(a.quantidade_necessaria for a in self.alocacoes.all())

    @property
    def saldo_a_distribuir(self):
        return max(0, self.quantidade_planeada - self.total_distribuido)

    @property
    def custo_total(self):
        return self.reforco_nacional * self.preco_unitario

class AlocacaoLogistica(models.Model):
    """Distribuição Regional/Provincial do Material Nivel 0 (Nacional)"""
    DIRECOES_STAE = [
        ('CENTRAL', 'STAE Central'),
        ('MAPUTO_C', 'DPP Maputo Cidade'),
        ('MAPUTO_P', 'DPP Maputo Província'),
        ('GAZA', 'DPP Gaza'),
        ('INHAMBANE', 'DPP Inhambane'),
        ('SOFALA', 'DPP Sofala'),
        ('MANICA', 'DPP Manica'),
        ('TETE', 'DPP Tete'),
        ('ZAMBEZIA', 'DPP Zambézia'),
        ('NAMPULA', 'DPP Nampula'),
        ('NIASSA', 'DPP Niassa'),
        ('CABO_D', 'DPP Cabo Delgado'),
    ]
    material_nacional = models.ForeignKey(MaterialEleitoral, on_delete=models.CASCADE, related_name='alocacoes')
    unidade = models.CharField(max_length=50, choices=DIRECOES_STAE)
    quantidade_necessaria = models.IntegerField(default=0)
    quantidade_existente = models.IntegerField(default=0)
    
    # Metadados Geográficos Editáveis
    num_distritos = models.IntegerField(default=0, verbose_name="Nº de Distritos")
    num_mesas = models.IntegerField(default=0, verbose_name="Nº de Mesas")

    class Meta:
        verbose_name = "Alocação Provincial"
        verbose_name_plural = "Alocações Provinciais"
        unique_together = ['material_nacional', 'unidade']

    @property
    def reforco(self):
        return max(0, self.quantidade_necessaria - self.quantidade_existente)

class AtividadePlano(models.Model):
    """Registo de atividades programadas para um plano logístico"""
    TIPO_ATIVIDADE = [
        ('formacao', 'Formação'),
        ('distribuicao', 'Distribuição/Logística'),
        ('fiscalizacao', 'Fiscalização'),
        ('sensibilizacao', 'Sensibilização/Publicidade'),
        ('montagem', 'Montagem de Mesas/Assembleias'),
        ('outros', 'Outros'),
    ]
    plano = models.ForeignKey(PlanoLogistico, on_delete=models.CASCADE, related_name='atividades')
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    responsaveis = models.CharField(max_length=255, blank=True, help_text="Quem gere a atividade")
    envolvidos = models.TextField(blank=True, help_text="Pessoal envolvido")
    custo_estimado = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    material_necessario = models.TextField(blank=True, help_text="Lista de material de suporte")
    tipo_atividade = models.CharField(max_length=50, choices=TIPO_ATIVIDADE, default='outros')
    data_prevista = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Atividade do Plano"
        verbose_name_plural = "Atividades dos Planos"

    def __str__(self):
        return self.nome

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
