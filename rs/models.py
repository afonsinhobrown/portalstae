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
    nome = models.CharField(max_length=100)
    codigo = models.CharField(max_length=20, unique=True)
    template_html = models.TextField(help_text="Template HTML padrão", blank=True)
    icone = models.CharField(max_length=50, default='fas fa-file-alt')
    categoria = models.CharField(max_length=30, choices=[
        ('votacao', 'Documentos de Votação'),
        ('recenseamento', 'Documentos de Recenseamento'),
        ('credencial', 'Credenciais'),
        ('logistica', 'Logística'),
    ], default='votacao')

    def __str__(self):
        return self.nome

class TemplateDocumento(models.Model):
    """10+ templates visuais pré-desenhados por tipo de documento"""
    CATEGORIAS = [
        ('classico', 'Clássico Oficial'),
        ('moderno', 'Moderno Premium'),
        ('minimalista', 'Minimalista'),
        ('colorido', 'Colorido Institucional'),
        ('compacto', 'Compacto'),
    ]
    tipo = models.ForeignKey(TipoDocumento, on_delete=models.CASCADE, related_name='templates')
    nome = models.CharField(max_length=100)
    descricao = models.CharField(max_length=200, blank=True)
    categoria_visual = models.CharField(max_length=20, choices=CATEGORIAS, default='classico')
    cores_principal = models.CharField(max_length=7, default='#003399', help_text="Cor principal em hex")
    cores_secundaria = models.CharField(max_length=7, default='#ffffff')
    html_base = models.TextField(help_text="HTML do template completo com variáveis Django")
    thumbnail_css = models.TextField(blank=True, help_text="CSS de miniatura para pré-visualização")
    ordem = models.IntegerField(default=0)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordem', 'nome']
        verbose_name = "Template de Documento"
        verbose_name_plural = "Templates de Documentos"

    def __str__(self):
        return f"{self.tipo.nome} – {self.nome}"

class ComponenteDocumento(models.Model):
    """Biblioteca de componentes arrastáveis para o construtor"""
    TIPOS = [
        ('cabecalho', 'Cabeçalho Institucional'),
        ('rodape', 'Rodapé com Assinaturas'),
        ('tabela_candidatos', 'Tabela de Candidatos'),
        ('quadricula_voto', 'Quadrícula de Votação'),
        ('qrcode', 'QR Code de Autenticidade'),
        ('logo_stae', 'Logo STAE'),
        ('dados_eleicao', 'Dados da Eleição'),
        ('circulo_eleitoral', 'Informação do Círculo'),
        ('lista_partidos', 'Lista de Partidos'),
        ('campo_assinatura', 'Campos de Assinatura'),
        ('tabela_resultados', 'Tabela de Resultados'),
        ('numero_mesa', 'Número da Mesa'),
        ('separador', 'Separador Visual'),
        ('texto_livre', 'Texto Livre Editável'),
        ('imagem', 'Imagem / Emblema'),
    ]
    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=30, choices=TIPOS)
    icone = models.CharField(max_length=50, default='fas fa-puzzle-piece')
    html_snippet = models.TextField(help_text="HTML do componente com variáveis")
    descricao = models.CharField(max_length=200, blank=True)
    compativel_com = models.JSONField(default=list, help_text="Lista de codigos TipoDocumento compatíveis")
    ordem = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordem', 'nome']
        verbose_name = "Componente de Documento"
        verbose_name_plural = "Componentes de Documentos"

    def __str__(self):
        return self.nome

class DocumentoPersonalizado(models.Model):
    """Documento construído pelo utilizador com template + componentes"""
    tipo = models.ForeignKey(TipoDocumento, on_delete=models.CASCADE)
    template_base = models.ForeignKey(TemplateDocumento, on_delete=models.SET_NULL, null=True, blank=True)
    eleicao = models.ForeignKey('eleicao.Eleicao', on_delete=models.SET_NULL, null=True, blank=True)
    circulo = models.ForeignKey('circuloseleitorais.CirculoEleitoral', on_delete=models.SET_NULL, null=True, blank=True)
    nome_documento = models.CharField(max_length=200)
    componentes_json = models.JSONField(default=list, help_text="Lista ordenada de componentes e suas configurações")
    dados_contexto = models.JSONField(default=dict, help_text="Dados sincronizados da eleição")
    html_final = models.TextField(blank=True, help_text="HTML montado final")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    criado_por = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = "Documento Personalizado"
        verbose_name_plural = "Documentos Personalizados"
        ordering = ['-atualizado_em']

    def __str__(self):
        return f"{self.tipo.nome} – {self.nome_documento}"

class DocumentoGerado(models.Model):
    tipo = models.ForeignKey(TipoDocumento, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    arquivo_pdf = models.FileField(upload_to='rs/documentos/')
    gerado_em = models.DateTimeField(auto_now_add=True)
    dados_json = models.JSONField(default=dict, help_text="Dados usados na geração")

    def __str__(self):
        return f"{self.tipo.nome} - {self.titulo}"

class FaseEleitoral(models.Model):
    """PONTO 1: Define as fases da linha temporal (Recenseamento, Votação, etc.)"""
    plano = models.ForeignKey(PlanoLogistico, on_delete=models.CASCADE, related_name='fases')
    nome = models.CharField(max_length=100)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    cor_identificacao = models.CharField(max_length=7, default='#003399')
    ordem = models.IntegerField(default=0)
    depende_de = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    completada = models.BooleanField(default=False)

    class Meta:
        ordering = ['ordem', 'data_inicio']
        verbose_name = "Fase do Calendário"

    def __str__(self):
        return f"{self.nome} ({self.plano.nome})"

class MarcoCritico(models.Model):
    """PONTO 1: Alertas e prazos críticos de soberania"""
    fase = models.ForeignKey(FaseEleitoral, on_delete=models.CASCADE, related_name='marcos')
    titulo = models.CharField(max_length=200)
    data_limite = models.DateField()
    alerta_enviado = models.BooleanField(default=False)
    nivel_prioridade = models.CharField(max_length=20, choices=[('alta', 'Alta'), ('media', 'Média'), ('baixa', 'Baixa')], default='alta')

    def __str__(self):
        return self.titulo

class NecessidadePessoal(models.Model):
    """PONTO 3: Planeamento de RH - Quantos perfis por mesa/localização"""
    plano = models.ForeignKey(PlanoLogistico, on_delete=models.CASCADE, related_name='rh_necessidades')
    perfil = models.CharField(max_length=100, help_text="Ex: Mesário, Técnico de Informática, MMVs")
    quantidade_por_mesa = models.IntegerField(default=0)
    custo_estimado_diario = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    formacao_obrigatoria = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Necessidade de Pessoal"

class RiscoPlaneamento(models.Model):
    """PONTO 7: Antecipação de problemas e classificação de risco"""
    plano = models.ForeignKey(PlanoLogistico, on_delete=models.CASCADE, related_name='riscos')
    area = models.CharField(max_length=100, help_text="Ex: Logística, Segurança, Acesso")
    descricao = models.TextField()
    nivel_probabilidade = models.IntegerField(choices=[(1, 'Baixa'), (2, 'Média'), (3, 'Alta')], default=1)
    nivel_impacto = models.IntegerField(choices=[(1, 'Baixo'), (2, 'Médio'), (3, 'Crítico')], default=1)
    plano_mitigacao = models.TextField()
    estado = models.CharField(max_length=30, choices=[('monitorizado', 'Monitorizado'), ('critico', 'Crítico'), ('mitigado', 'Mitigado')], default='monitorizado')

    @property
    def severidade(self):
        res = self.nivel_probabilidade * self.nivel_impacto
        if res >= 6: return 'ALTA'
        if res >= 3: return 'MÉDIA'
        return 'BAIXA'

class DetalheTerritorial(models.Model):
    """PONTO 2: Planeamento Territorial Avançado (Simulações)"""
    plano = models.ForeignKey(PlanoLogistico, on_delete=models.CASCADE, related_name='territorio')
    localizacao_id = models.UUIDField(help_text="ID da Província ou Distrito")
    nome_localizacao = models.CharField(max_length=200)
    total_eleitores_estimado = models.IntegerField(default=0)
    mesas_voto_planeadas = models.IntegerField(default=0)
    zonas_criticas_geograficas = models.TextField(blank=True)
    risco_acesso_chuva = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Planeamento Territorial"

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
    
    # Automatização Geográfica e Distribuição Provincial
    por_distrito = models.BooleanField(default=False, verbose_name="É calculado por Distrito?")
    localizacao_destino = models.CharField(max_length=100, blank=True, null=True, verbose_name="Província/Círculo Eleitoral de Destino")
    
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
        ('recenseamento', 'Operação de Recenseamento'),
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
    
    sector_responsavel = models.ForeignKey('recursoshumanos.Sector', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Departamento/Área Responsável")
    funcionario_responsavel = models.ForeignKey('recursoshumanos.Funcionario', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Funcionário Responsável")
    responsaveis = models.TextField(blank=True, verbose_name="Responsáveis Pela Atividade", help_text="Equipa ou Pessoal envolvido diretamente")
    envolvidos = models.TextField(blank=True, help_text="Pessoal de apoio extra")
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

class OrcamentoPlaneamento(models.Model):
    """PONTO 5: Gestão Financeira por Fase e Categoria"""
    plano = models.ForeignKey(PlanoLogistico, on_delete=models.CASCADE, related_name='orcamento_detalhes')
    categoria = models.CharField(max_length=50, choices=[('logistica', 'Logística'), ('rh', 'Recursos Humanos'), ('tecnologia', 'Tecnologia'), ('comunicacao', 'Comunicação')])
    valor_previsto = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    valor_executado = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.categoria} - {self.plano.nome}"

class IndicadorPlaneamento(models.Model):
    """PONTO 9: KPIs para medir a solidez do planeamento"""
    plano = models.ForeignKey(PlanoLogistico, on_delete=models.CASCADE, related_name='kpis')
    nome = models.CharField(max_length=100)
    valor_meta = models.FloatField(default=0)
    valor_atual = models.FloatField(default=0)
    unidade = models.CharField(max_length=20, default='%')

    def __str__(self):
        return self.nome

from .models_apuramento import ControleEdital, ResultadoEdital, VotoPartidoEdital
