# dfec/models.py - ARQUIVO COMPLETO COM TODOS OS MODELOS
import uuid
from django.db import models
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.db.models import Sum, Max, Min, Avg
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


# ========== MÓDULO 1: PLANIFICAÇÃO ==========

class PlanoAtividade(models.Model):
    """Plano de atividades do DFEC"""
    ESTADO_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('submetido', 'Submetido'),
        ('aprovado', 'Aprovado'),
        ('execucao', 'Em Execução'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    ]

    # Identificação
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código")
    titulo = models.CharField(max_length=200, verbose_name="Título")
    descricao = models.TextField(verbose_name="Descrição")

    # Período
    data_inicio = models.DateField(verbose_name="Data de Início")
    data_fim = models.DateField(verbose_name="Data de Término")

    # Recursos
    orcamento = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Orçamento")
    responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                    related_name='planos_responsavel', verbose_name="Responsável")

    # Controle
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='rascunho', verbose_name="Estado")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   related_name='planos_criados', verbose_name="Criado por")
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")

    # Metadados
    setor = models.CharField(max_length=100, blank=True, verbose_name="Setor")
    prioridade = models.IntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(5)],
                                     verbose_name="Prioridade")

    class Meta:
        verbose_name = 'Plano de Atividade'
        verbose_name_plural = 'Planos de Atividade'
        ordering = ['-data_criacao']

    def __str__(self):
        return f"{self.codigo} - {self.titulo}"

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = f"PL-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


# ========== MÓDULO 2: FORMAÇÕES ==========

class Formacao(models.Model):
    """Formações do DFEC"""
    ESTADO_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('agendada', 'Agendada'),
        ('ativa', 'Ativa'),
        ('concluida', 'Concluída'),
        ('cancelada', 'Cancelada'),
        ('adiada', 'Adiada'),
    ]

    TIPO_CHOICES = [
        ('presencial', 'Presencial'),
        ('online', 'Online'),
        ('hibrida', 'Híbrida'),
        ('intensiva', 'Intensiva'),
        ('modular', 'Modular'),
    ]

    # Identificação
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código")
    titulo = models.CharField(max_length=200, verbose_name="Título")
    descricao = models.TextField(verbose_name="Descrição")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='presencial', verbose_name="Tipo")

    # Período e local
    data_inicio = models.DateField(verbose_name="Data de Início")
    data_fim = models.DateField(verbose_name="Data de Término")
    local = models.CharField(max_length=200, verbose_name="Local")

    # Capacidade
    capacidade = models.IntegerField(default=30, verbose_name="Capacidade")
    capacidade_minima = models.IntegerField(default=10, verbose_name="Capacidade Mínima")

    # Coordenação
    coordenador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                    related_name='formacoes_coordenadas', verbose_name="Coordenador")
    formadores = models.ManyToManyField(User, blank=True, related_name='formacoes_formador', verbose_name="Formadores")

    # Controle
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='rascunho', verbose_name="Estado")
    plano = models.ForeignKey(PlanoAtividade, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='formacoes', verbose_name="Plano Associado")

    # Metadados
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")

    class Meta:
        verbose_name = 'Formação'
        verbose_name_plural = 'Formações'
        ordering = ['-data_inicio']

    def __str__(self):
        return f"{self.codigo} - {self.titulo}"

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = f"F-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def total_inscritos(self):
        return self.formandos.count()

    def vagas_disponiveis(self):
        return self.capacidade - self.total_inscritos()


class Formando(models.Model):
    """Formandos nas formações"""
    GENERO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Feminino'),
    ]

    # Identificação
    nome_completo = models.CharField(max_length=200, verbose_name="Nome Completo")
    numero_identificacao = models.CharField(max_length=50, unique=True, verbose_name="Número de Identificação")
    email = models.EmailField(verbose_name="Email")
    telefone = models.CharField(max_length=20, blank=True, verbose_name="Telefone")

    # Dados pessoais
    genero = models.CharField(max_length=1, choices=GENERO_CHOICES, default='M', verbose_name="Gênero")
    data_nascimento = models.DateField(null=True, blank=True, verbose_name="Data de Nascimento")
    instituicao = models.CharField(max_length=200, blank=True, verbose_name="Instituição")
    cargo = models.CharField(max_length=100, blank=True, verbose_name="Cargo")

    # Formações
    formacoes = models.ManyToManyField(Formacao, related_name='formandos', through='InscricaoFormacao',
                                       verbose_name="Formações")

    # Controle
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")

    # QR Code
    qr_code = models.TextField(blank=True, verbose_name="QR Code")

    class Meta:
        verbose_name = 'Formando'
        verbose_name_plural = 'Formandos'
        ordering = ['nome_completo']

    def __str__(self):
        return f"{self.nome_completo} ({self.numero_identificacao})"

    def idade(self):
        if self.data_nascimento:
            today = timezone.now().date()
            return today.year - self.data_nascimento.year - (
                    (today.month, today.day) < (self.data_nascimento.month, self.data_nascimento.day)
            )
        return None


class InscricaoFormacao(models.Model):
    """Relação entre formando e formação"""
    formando = models.ForeignKey(Formando, on_delete=models.CASCADE, verbose_name="Formando")
    formacao = models.ForeignKey(Formacao, on_delete=models.CASCADE, verbose_name="Formação")

    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('confirmada', 'Confirmada'),
        ('presente', 'Presente'),
        ('ausente', 'Ausente'),
        ('cancelada', 'Cancelada'),
        ('concluida', 'Concluída'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente', verbose_name="Status")
    data_inscricao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Inscrição")
    data_confirmacao = models.DateTimeField(null=True, blank=True, verbose_name="Data de Confirmação")
    data_conclusao = models.DateTimeField(null=True, blank=True, verbose_name="Data de Conclusão")

    # Avaliação
    nota_final = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, verbose_name="Nota Final")
    certificado_emitido = models.BooleanField(default=False, verbose_name="Certificado Emitido")

    class Meta:
        verbose_name = 'Inscrição em Formação'
        verbose_name_plural = 'Inscrições em Formações'
        unique_together = ['formando', 'formacao']

    def __str__(self):
        return f"{self.formando} - {self.formacao}"


class Turma(models.Model):
    """Turmas dentro de uma formação"""
    formacao = models.ForeignKey(Formacao, on_delete=models.CASCADE, related_name='turmas', verbose_name="Formação")
    codigo = models.CharField(max_length=50, verbose_name="Código")
    nome = models.CharField(max_length=100, verbose_name="Nome")
    capacidade_maxima = models.IntegerField(default=25, verbose_name="Capacidade Máxima")

    # Coordenação
    coordenador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                    related_name='turmas_coordenadas', verbose_name="Coordenador")
    sala = models.CharField(max_length=100, blank=True, verbose_name="Sala")

    # Formandos
    formandos = models.ManyToManyField(Formando, related_name='turmas', blank=True, verbose_name="Formandos")

    class Meta:
        verbose_name = 'Turma'
        verbose_name_plural = 'Turmas'
        unique_together = ['formacao', 'codigo']

    def __str__(self):
        return f"{self.codigo} - {self.nome}"

    def total_formandos(self):
        return self.formandos.count()

    def vagas_disponiveis(self):
        return self.capacidade_maxima - self.total_formandos()


class Brigada(models.Model):
    """Brigadas dentro de uma turma"""
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name='brigadas', verbose_name="Turma")
    codigo = models.CharField(max_length=50, verbose_name="Código")
    nome = models.CharField(max_length=100, verbose_name="Nome")

    # Liderança
    lider = models.ForeignKey(Formando, on_delete=models.SET_NULL, null=True,
                              related_name='brigadas_lideradas', verbose_name="Líder")
    coordenador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                    related_name='brigadas_coordenadas', verbose_name="Coordenador")

    # Membros
    membros = models.ManyToManyField(Formando, related_name='brigadas', blank=True, verbose_name="Membros")

    class Meta:
        verbose_name = 'Brigada'
        verbose_name_plural = 'Brigadas'
        unique_together = ['turma', 'codigo']

    def __str__(self):
        return f"{self.codigo} - {self.nome}"

    def total_membros(self):
        return self.membros.count()


# ========== MÓDULO 3: ANÁLISE ELEITORAL ==========

class Eleicao(models.Model):
    """Eleições para análise"""
    nome = models.CharField(max_length=200, verbose_name="Nome")
    tipo = models.CharField(max_length=100, verbose_name="Tipo")
    data = models.DateField(verbose_name="Data")
    descricao = models.TextField(blank=True, verbose_name="Descrição")

    class Meta:
        verbose_name = 'Eleição'
        verbose_name_plural = 'Eleições'
        ordering = ['-data']

    def __str__(self):
        return f"{self.nome} ({self.data.year})"


class RegiaoEleitoral(models.Model):
    """Regiões eleitorais"""
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código")
    nome = models.CharField(max_length=200, verbose_name="Nome")
    provincia = models.CharField(max_length=100, verbose_name="Província")
    municipio = models.CharField(max_length=100, verbose_name="Município")
    distrito = models.CharField(max_length=100, blank=True, verbose_name="Distrito")

    # Dados demográficos
    populacao = models.IntegerField(default=0, verbose_name="População")
    eleitores_registrados = models.IntegerField(default=0, verbose_name="Eleitores Registrados")

    class Meta:
        verbose_name = 'Região Eleitoral'
        verbose_name_plural = 'Regiões Eleitorais'
        ordering = ['provincia', 'municipio', 'nome']

    def __str__(self):
        return f"{self.codigo} - {self.nome}"


class ResultadoEleicao(models.Model):
    """Resultados de eleições por região"""
    eleicao = models.ForeignKey(Eleicao, on_delete=models.CASCADE, related_name='resultados', verbose_name="Eleição")
    regiao = models.ForeignKey(RegiaoEleitoral, on_delete=models.CASCADE, related_name='resultados',
                               verbose_name="Região")

    # Dados eleitorais
    total_eleitores = models.IntegerField(default=0, verbose_name="Total de Eleitores")
    votos_validos = models.IntegerField(default=0, verbose_name="Votos Válidos")
    votos_brancos = models.IntegerField(default=0, verbose_name="Votos em Branco")
    votos_nulos = models.IntegerField(default=0, verbose_name="Votos Nulos")
    abstencao = models.IntegerField(default=0, verbose_name="Abstenção")

    # Detalhes adicionais (JSON)
    dados_json = models.JSONField(default=dict, blank=True, verbose_name="Dados Adicionais")

    class Meta:
        verbose_name = 'Resultado de Eleição'
        verbose_name_plural = 'Resultados de Eleições'
        unique_together = ['eleicao', 'regiao']

    def __str__(self):
        return f"{self.eleicao} - {self.regiao}"

    def participacao_percent(self):
        if self.total_eleitores > 0:
            return (self.votos_validos / self.total_eleitores) * 100
        return 0


class AnaliseRegiao(models.Model):
    """Análises de regiões eleitorais"""
    TIPO_ANALISE_CHOICES = [
        ('participacao', 'Participação'),
        ('tendencia', 'Tendência'),
        ('comparativa', 'Comparativa'),
        ('geral', 'Geral'),
    ]

    regiao = models.ForeignKey(RegiaoEleitoral, on_delete=models.CASCADE, related_name='analises',
                               verbose_name="Região")
    eleicao = models.ForeignKey(Eleicao, on_delete=models.CASCADE, related_name='analises', verbose_name="Eleição")

    tipo_analise = models.CharField(max_length=20, choices=TIPO_ANALISE_CHOICES, default='geral',
                                    verbose_name="Tipo de Análise")
    resultado_analise = models.JSONField(default=dict, verbose_name="Resultado da Análise")

    # Controle
    analista = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                 related_name='analises_realizadas', verbose_name="Analista")
    data_analise = models.DateTimeField(auto_now_add=True, verbose_name="Data da Análise")

    class Meta:
        verbose_name = 'Análise de Região'
        verbose_name_plural = 'Análises de Regiões'
        ordering = ['-data_analise']

    def __str__(self):
        return f"Análise {self.get_tipo_analise_display()} - {self.regiao}"


# ========== MÓDULO 5: MANUAIS ==========

class Manual(models.Model):
    """Modelo para manuais do DFEC"""
    TIPO_CHOICES = [
        ('procedimento', 'Manual de Procedimentos'),
        ('operacional', 'Manual Operacional'),
        ('formacao', 'Manual de Formação'),
        ('seguranca', 'Manual de Segurança'),
        ('tecnico', 'Manual Técnico'),
        ('eleitoral', 'Manual Eleitoral'),
        ('administrativo', 'Manual Administrativo'),
    ]

    STATUS_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('revisao', 'Em Revisão'),
        ('aprovado', 'Aprovado'),
        ('publicado', 'Publicado'),
        ('arquivado', 'Arquivado'),
    ]

    # Identificação
    titulo = models.CharField(max_length=200, verbose_name="Título")
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='procedimento', verbose_name="Tipo")
    versao = models.CharField(max_length=10, default='1.0', verbose_name="Versão")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='rascunho', verbose_name="Status")
    publicado = models.BooleanField(default=False, verbose_name="Publicado")

    # Relações
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   related_name='manuais_criados', verbose_name="Criado por")
    revisado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='manuais_revisados', verbose_name="Revisado por")
    aprovado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='manuais_aprovados', verbose_name="Aprovado por")

    # Arquivos
    arquivo_pdf = models.FileField(upload_to='manuais/pdf/', null=True, blank=True, verbose_name="PDF")
    arquivo_word = models.FileField(upload_to='manuais/word/', null=True, blank=True, verbose_name="Word")
    capa = models.ImageField(upload_to='manuais/capas/', null=True, blank=True, verbose_name="Capa")

    # Metadados
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")
    data_publicacao = models.DateTimeField(null=True, blank=True, verbose_name="Data de Publicação")
    data_validade = models.DateField(null=True, blank=True, verbose_name="Data de Validade")

    # Controle de acesso
    grupos_permitidos = models.ManyToManyField(Group, blank=True,
                                               related_name='manuais_permitidos', verbose_name="Grupos Permitidos")

    # Estatísticas
    visualizacoes = models.IntegerField(default=0, verbose_name="Visualizações")
    downloads = models.IntegerField(default=0, verbose_name="Downloads")

    class Meta:
        verbose_name = 'Manual'
        verbose_name_plural = 'Manuais'
        ordering = ['-data_atualizacao']
        permissions = [
            ('publicar_manual', 'Pode publicar manuais'),
            ('revisar_manual', 'Pode revisar manuais'),
            ('gerar_pdf_manual', 'Pode gerar PDF de manuais'),
        ]

    def __str__(self):
        return f"{self.codigo} - {self.titulo} (v{self.versao})"

    def get_absolute_url(self):
        return reverse('manual_detalhe', args=[str(self.id)])

    def save(self, *args, **kwargs):
        # Gerar código automático se não fornecido
        if not self.codigo:
            prefix = {
                'procedimento': 'MPROC',
                'operacional': 'MOPER',
                'formacao': 'MFORM',
                'seguranca': 'MSEG',
                'tecnico': 'MTEC',
                'eleitoral': 'MELE',
                'administrativo': 'MADM',
            }.get(self.tipo, 'MAN')

            ultimo_num = Manual.objects.filter(
                codigo__startswith=prefix
            ).aggregate(Max('codigo'))['codigo__max']

            if ultimo_num:
                try:
                    num = int(ultimo_num.split('-')[-1]) + 1
                except:
                    num = 1
            else:
                num = 1

            self.codigo = f"{prefix}-{num:03d}"

        super().save(*args, **kwargs)

    def total_capitulos(self):
        return self.capitulos.count()

    def total_paginas(self):
        return self.capitulos.aggregate(total=Sum('num_paginas'))['total'] or 0

    def incrementar_visualizacao(self):
        self.visualizacoes += 1
        self.save(update_fields=['visualizacoes'])

    def incrementar_download(self):
        self.downloads += 1
        self.save(update_fields=['downloads'])

    def get_status_color(self):
        colors = {
            'rascunho': 'warning',
            'revisao': 'info',
            'aprovado': 'primary',
            'publicado': 'success',
            'arquivado': 'secondary',
        }
        return colors.get(self.status, 'secondary')


class Capitulo(models.Model):
    """Capítulos de um manual"""
    manual = models.ForeignKey(Manual, on_delete=models.CASCADE,
                               related_name='capitulos', verbose_name="Manual")
    titulo = models.CharField(max_length=200, verbose_name="Título")
    numero = models.IntegerField(verbose_name="Número")
    conteudo = models.TextField(verbose_name="Conteúdo")
    ordem = models.IntegerField(default=0, verbose_name="Ordem")
    num_paginas = models.IntegerField(default=1, verbose_name="Número de Páginas")

    # Controle de versão
    versao = models.CharField(max_length=10, default='1.0', verbose_name="Versão")
    revisado_por = models.ForeignKey(User, on_delete=models.SET_NULL,
                                     null=True, blank=True, verbose_name="Revisado por")
    data_revisao = models.DateTimeField(null=True, blank=True, verbose_name="Data de Revisão")

    # Metadados
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")

    class Meta:
        verbose_name = 'Capítulo'
        verbose_name_plural = 'Capítulos'
        ordering = ['manual', 'ordem', 'numero']
        unique_together = ['manual', 'numero']

    def __str__(self):
        return f"{self.manual.codigo} - Cap. {self.numero}: {self.titulo}"

    def save(self, *args, **kwargs):
        # Garantir ordem sequencial
        if not self.ordem:
            max_ordem = Capitulo.objects.filter(
                manual=self.manual
            ).aggregate(Max('ordem'))['ordem__max']
            self.ordem = (max_ordem or 0) + 1

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('manual_detalhe', args=[str(self.manual.id)]) + f'#capitulo-{self.id}'


class ImagemManual(models.Model):
    """Imagens para manuais"""
    manual = models.ForeignKey(Manual, on_delete=models.CASCADE,
                               related_name='imagens', verbose_name="Manual")
    titulo = models.CharField(max_length=200, verbose_name="Título")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    imagem = models.ImageField(upload_to='manuais/imagens/', verbose_name="Imagem")

    # Metadados
    formato = models.CharField(max_length=10, blank=True, verbose_name="Formato")
    tamanho = models.IntegerField(default=0, verbose_name="Tamanho (bytes)")
    resolucao = models.CharField(max_length=20, blank=True, verbose_name="Resolução")
    legenda = models.CharField(max_length=300, blank=True, verbose_name="Legenda")

    # Controle
    upload_por = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, verbose_name="Upload por")
    data_upload = models.DateTimeField(auto_now_add=True, verbose_name="Data de Upload")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = 'Imagem de Manual'
        verbose_name_plural = 'Imagens de Manuais'
        ordering = ['-data_upload']

    def __str__(self):
        return f"{self.titulo} ({self.manual.codigo})"

    def save(self, *args, **kwargs):
        # Detectar formato e tamanho
        if self.imagem:
            self.formato = self.imagem.name.split('.')[-1].lower()
            self.tamanho = self.imagem.size

        super().save(*args, **kwargs)

    def get_url(self):
        return self.imagem.url if self.imagem else ''


class ComentarioManual(models.Model):
    """Comentários em manuais"""
    manual = models.ForeignKey(Manual, on_delete=models.CASCADE,
                               related_name='comentarios', verbose_name="Manual")
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuário")
    texto = models.TextField(verbose_name="Texto")

    # Controle
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")
    resolvido = models.BooleanField(default=False, verbose_name="Resolvido")
    resolvido_por = models.ForeignKey(User, on_delete=models.SET_NULL,
                                      null=True, blank=True,
                                      related_name='comentarios_resolvidos', verbose_name="Resolvido por")
    data_resolucao = models.DateTimeField(null=True, blank=True, verbose_name="Data de Resolução")

    # Referência (opcional)
    capitulo = models.ForeignKey(Capitulo, on_delete=models.SET_NULL,
                                 null=True, blank=True, verbose_name="Capítulo Referente")
    pagina = models.IntegerField(null=True, blank=True, verbose_name="Página")

    class Meta:
        verbose_name = 'Comentário de Manual'
        verbose_name_plural = 'Comentários de Manuais'
        ordering = ['-data_criacao']

    def __str__(self):
        return f"Comentário de {self.usuario.username} em {self.manual.codigo}"

    def marcar_como_resolvido(self, usuario):
        self.resolvido = True
        self.resolvido_por = usuario
        self.data_resolucao = timezone.now()
        self.save()


# dfec/models.py - ADICIONE ESTA CLASSE NO FINAL DO ARQUIVO:

class HistoricoUsoManual(models.Model):
    """Histórico de uso/visualização de manuais"""
    TIPO_ACAO_CHOICES = [
        ('visualizacao', 'Visualização'),
        ('download', 'Download'),
        ('impressao', 'Impressão'),
        ('comentario', 'Comentário'),
        ('avaliacao', 'Avaliação'),
        ('compartilhamento', 'Compartilhamento'),
    ]

    manual = models.ForeignKey(Manual, on_delete=models.CASCADE,
                               related_name='historico_uso', verbose_name="Manual")
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL,
                                null=True, verbose_name="Usuário")
    tipo_acao = models.CharField(max_length=20, choices=TIPO_ACAO_CHOICES,
                                 default='visualizacao', verbose_name="Tipo de Ação")

    # Detalhes da ação
    detalhes = models.JSONField(default=dict, blank=True, verbose_name="Detalhes")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="Endereço IP")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")

    # Timestamps
    data_acao = models.DateTimeField(auto_now_add=True, verbose_name="Data da Ação")
    duracao = models.IntegerField(null=True, blank=True, verbose_name="Duração (segundos)")

    class Meta:
        verbose_name = 'Histórico de Uso de Manual'
        verbose_name_plural = 'Histórico de Uso de Manuais'
        ordering = ['-data_acao']
        indexes = [
            models.Index(fields=['manual', 'usuario']),
            models.Index(fields=['data_acao']),
            models.Index(fields=['tipo_acao']),
        ]

    def __str__(self):
        return f"{self.usuario} - {self.get_tipo_acao_display()} - {self.manual.codigo}"

    @classmethod
    def registrar_visualizacao(cls, manual, usuario, request=None):
        """Registra uma visualização de manual"""
        historico = cls.objects.create(
            manual=manual,
            usuario=usuario,
            tipo_acao='visualizacao',
            detalhes={'pagina': 'visualizacao'},
        )

        if request:
            historico.ip_address = request.META.get('REMOTE_ADDR')
            historico.user_agent = request.META.get('HTTP_USER_AGENT', '')
            historico.save()

        return historico

    @classmethod
    def registrar_download(cls, manual, usuario, formato, request=None):
        """Registra um download de manual"""
        historico = cls.objects.create(
            manual=manual,
            usuario=usuario,
            tipo_acao='download',
            detalhes={'formato': formato},
        )

        if request:
            historico.ip_address = request.META.get('REMOTE_ADDR')
            historico.user_agent = request.META.get('HTTP_USER_AGENT', '')
            historico.save()

        # Incrementar contador no manual
        manual.incrementar_download()

        return historico