# dfec/models/completo.py - VERSÃO DEFINITIVA
from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.urls import reverse
from django.db.models import Sum, Max  # IMPORTANTE: Adicionar isto
import uuid
import os
from datetime import date


# ============ MODELOS PARA MANUAIS ============

class TipoManual(models.Model):
    """Tipos de manuais (ex: Procedimento, Instrução, Guia)"""
    nome = models.CharField(max_length=100)
    codigo = models.CharField(max_length=10, unique=True)
    descricao = models.TextField(blank=True)
    formato_padrao = models.CharField(max_length=20, default='pdf',
                                      choices=[('pdf', 'PDF'), ('word', 'Word'), ('html', 'HTML')])
    icone = models.CharField(max_length=50, blank=True)
    cor = models.CharField(max_length=20, blank=True, default='#007bff')
    ordem = models.IntegerField(default=0)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Tipo de Manual'
        verbose_name_plural = 'Tipos de Manuais'
        ordering = ['ordem', 'nome']

    def __str__(self):
        return f"{self.codigo} - {self.nome}"


class TemplateManual(models.Model):
    """Templates para manuais"""
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    arquivo_template = models.FileField(upload_to='templates_manuais/')
    formato = models.CharField(max_length=10, default='html',
                               choices=[('html', 'HTML'), ('docx', 'Word'), ('latex', 'LaTeX')])
    cabecalho_padrao = models.TextField(blank=True)
    rodape_padrao = models.TextField(blank=True)
    estilo_css = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        verbose_name = 'Template de Manual'
        verbose_name_plural = 'Templates de Manuais'

    def __str__(self):
        return self.nome


class ManualCompleto(models.Model):
    """Modelo principal para manuais"""
    FORMATO_CHOICES = [
        ('pdf', 'PDF'),
        ('epub', 'ePub'),
        ('word', 'Word'),
        ('html', 'HTML'),
        ('impresso', 'Impresso'),
    ]

    STATUS_CHOICES = [
        ('RASCUNHO', 'Rascunho'),
        ('REVISAO', 'Em Revisão'),
        ('APROVADO', 'Aprovado'),
        ('PUBLICADO', 'Publicado'),
        ('ARQUIVADO', 'Arquivado'),
        ('DESATIVADO', 'Desativado'),
    ]

    # Identificação
    titulo = models.CharField(max_length=200)
    subtitulo = models.CharField(max_length=200, blank=True)
    codigo = models.CharField(max_length=50, unique=True)
    tipo = models.ForeignKey(TipoManual, on_delete=models.PROTECT, related_name='manuais')
    versao = models.CharField(max_length=10, default='1.0')
    idioma = models.CharField(max_length=10, default='pt',
                              choices=[('pt', 'Português'), ('en', 'Inglês'), ('es', 'Espanhol')])

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='RASCUNHO')
    formato = models.CharField(max_length=20, choices=FORMATO_CHOICES, default='pdf')
    data_publicacao = models.DateField(null=True, blank=True)
    pode_imprimir = models.BooleanField(default=True)

    # Autoria
    autor_principal = models.ForeignKey(User, on_delete=models.PROTECT, related_name='manuais_autor')
    colaboradores = models.ManyToManyField(User, related_name='manuais_colaborador', blank=True)
    revisores = models.ManyToManyField(User, related_name='manuais_revisor', blank=True)

    # Conteúdo
    publico_alvo = models.TextField()
    objetivos = models.TextField()
    pre_requisitos = models.TextField(blank=True)
    template = models.ForeignKey(TemplateManual, on_delete=models.SET_NULL, null=True, blank=True)

    # Arquivos
    arquivo_pdf = models.FileField(upload_to='manuais/pdf/', null=True, blank=True)
    arquivo_epub = models.FileField(upload_to='manuais/epub/', null=True, blank=True)
    arquivo_word = models.FileField(upload_to='manuais/word/', null=True, blank=True)

    # Impressão
    quantidade_paginas = models.IntegerField(default=0)
    quantidade_impressoes = models.IntegerField(default=0)
    ultima_impressao = models.DateTimeField(null=True, blank=True)

    # Permissões
    restrito = models.BooleanField(default=False)
    grupos_permitidos = models.ManyToManyField(Group, blank=True)

    # Metadados
    data_criacao = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    data_atualizacao = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = 'Manual'
        verbose_name_plural = 'Manuais'
        ordering = ['-data_atualizacao']

    def __str__(self):
        return f"{self.codigo} - {self.titulo} (v{self.versao})"

    def get_absolute_url(self):
        return reverse('manual_detalhe', kwargs={'pk': self.pk})


class CapituloManual(models.Model):
    """Capítulos de manuais"""
    manual = models.ForeignKey(ManualCompleto, on_delete=models.CASCADE, related_name='capitulos')
    titulo = models.CharField(max_length=200)
    numero = models.CharField(max_length=10)  # Ex: "1", "1.1", "Anexo A"
    conteudo_texto = models.TextField()
    conteudo_html = models.TextField(blank=True)
    ordem = models.IntegerField(default=0)
    visivel_publico = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Capítulo de Manual'
        verbose_name_plural = 'Capítulos de Manuais'
        ordering = ['manual', 'ordem', 'numero']
        unique_together = ['manual', 'numero']

    def __str__(self):
        return f"{self.manual.codigo} - {self.numero}. {self.titulo}"


class ImagemManual(models.Model):
    """Imagens para manuais"""
    manual = models.ForeignKey(ManualCompleto, on_delete=models.CASCADE, related_name='imagens')
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    imagem = models.ImageField(upload_to='manuais/imagens/')
    miniatura = models.ImageField(upload_to='manuais/miniaturas/', null=True, blank=True)
    autor = models.CharField(max_length=100, blank=True)
    fonte = models.CharField(max_length=200, blank=True)
    licenca = models.CharField(max_length=50, blank=True)
    tags = models.CharField(max_length=200, blank=True)
    visivel_publico = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Imagem de Manual'
        verbose_name_plural = 'Imagens de Manuais'

    def __str__(self):
        return f"{self.titulo} - {self.manual.titulo}"


class AnexoManual(models.Model):
    """Anexos de manuais"""
    TIPO_CHOICES = [
        ('formulario', 'Formulário'),
        ('checklist', 'Checklist'),
        ('modelo', 'Modelo'),
        ('tabela', 'Tabela'),
        ('fluxograma', 'Fluxograma'),
        ('outro', 'Outro'),
    ]

    manual = models.ForeignKey(ManualCompleto, on_delete=models.CASCADE, related_name='anexos')
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='formulario')
    arquivo = models.FileField(upload_to='manuais/anexos/')
    ordem = models.IntegerField(default=0)
    visivel_publico = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Anexo de Manual'
        verbose_name_plural = 'Anexos de Manuais'
        ordering = ['manual', 'ordem']

    def __str__(self):
        return f"{self.titulo} - {self.manual.titulo}"


class VersaoManual(models.Model):
    """Histórico de versões de manuais"""
    manual = models.ForeignKey(ManualCompleto, on_delete=models.CASCADE, related_name='versoes')
    versao = models.CharField(max_length=10)
    autor_mudanca = models.ForeignKey(User, on_delete=models.PROTECT)
    data_mudanca = models.DateTimeField(auto_now_add=True)
    descricao_mudanca = models.TextField()
    arquivo_anterior = models.FileField(upload_to='manuais/historico/', null=True, blank=True)

    class Meta:
        verbose_name = 'Versão de Manual'
        verbose_name_plural = 'Versões de Manuais'
        ordering = ['manual', '-versao']

    def __str__(self):
        return f"{self.manual.codigo} - v{self.versao}"


class HistoricoUsoManual(models.Model):
    """Histórico de uso de manuais"""
    ACAO_CHOICES = [
        ('VISUALIZOU', 'Visualizou'),
        ('DOWNLOAD', 'Download'),
        ('IMPRESSAO', 'Impressão'),
        ('COMENTOU', 'Comentou'),
        ('REVISOU', 'Revisou'),
        ('PUBLICOU', 'Publicou'),
    ]

    manual = models.ForeignKey(ManualCompleto, on_delete=models.CASCADE, related_name='historico')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    acao = models.CharField(max_length=20, choices=ACAO_CHOICES)
    data_hora = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    detalhes = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name = 'Histórico de Uso de Manual'
        verbose_name_plural = 'Histórico de Uso de Manuais'
        ordering = ['-data_hora']

    def __str__(self):
        return f"{self.usuario} - {self.acao} - {self.manual.titulo}"


class ComentarioManual(models.Model):
    """Comentários em manuais"""
    TIPO_CHOICES = [
        ('SUGESTAO', 'Sugestão'),
        ('ERRO', 'Erro'),
        ('PERGUNTA', 'Pergunta'),
        ('ELOGIO', 'Elogio'),
        ('OUTRO', 'Outro'),
    ]

    STATUS_CHOICES = [
        ('ABERTO', 'Aberto'),
        ('EM_ANALISE', 'Em Análise'),
        ('RESOLVIDO', 'Resolvido'),
        ('ARQUIVADO', 'Arquivado'),
    ]

    manual = models.ForeignKey(ManualCompleto, on_delete=models.CASCADE, related_name='comentarios')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='SUGESTAO')
    texto = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ABERTO')
    data_criacao = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    data_resolucao = models.DateTimeField(null=True, blank=True)
    resolvido_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='comentarios_resolvidos')

    class Meta:
        verbose_name = 'Comentário de Manual'
        verbose_name_plural = 'Comentários de Manuais'
        ordering = ['-data_criacao']

    def __str__(self):
        return f"Comentário de {self.usuario} em {self.manual.titulo}"


# ============ MODELOS DO manualbackup.py ADICIONADOS AQUI ============

class Manual(models.Model):
    """Modelo simplificado para manuais do DFEC"""
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

    FORMATO_PAPEL_CHOICES = [
        ('a4', 'A4 (21 x 29.7 cm)'),
        ('a5', 'A5 (14.8 x 21 cm)'),
        ('16x23', 'Livro (16 x 23 cm)'),
        ('pocket', 'Pocket (10.5 x 17.8 cm)'),
    ]

    # Identificação
    titulo = models.CharField(max_length=200, verbose_name="Título")
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='procedimento', verbose_name="Tipo")
    versao = models.CharField(max_length=10, default='1.0', verbose_name="Versão")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='rascunho', verbose_name="Status")
    formato_papel = models.CharField(max_length=20, choices=FORMATO_PAPEL_CHOICES, default='a4', verbose_name="Formato de Papel")
    ficha_tecnica = models.TextField(blank=True, verbose_name="Ficha Técnica (ISBN, Editora, etc)")
    publicado = models.BooleanField(default=False, verbose_name="Publicado")

    # Relações
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   related_name='manuais_simples_criados', verbose_name="Criado por")
    revisado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='manuais_simples_revisados', verbose_name="Revisado por")
    aprovado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='manuais_simples_aprovados', verbose_name="Aprovado por")

    # Arquivos
    arquivo_pdf = models.FileField(upload_to='manuais_simples/pdf/', null=True, blank=True, verbose_name="PDF")
    arquivo_word = models.FileField(upload_to='manuais_simples/word/', null=True, blank=True, verbose_name="Word")
    capa = models.ImageField(upload_to='manuais_simples/capas/', null=True, blank=True, verbose_name="Capa")

    # Metadados
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")
    data_publicacao = models.DateTimeField(null=True, blank=True, verbose_name="Data de Publicação")
    data_validade = models.DateField(null=True, blank=True, verbose_name="Data de Validade")

    # Controle de acesso
    grupos_permitidos = models.ManyToManyField(Group, blank=True,
                                               related_name='manuais_simples_permitidos', verbose_name="Grupos Permitidos")

    # Estatísticas
    visualizacoes = models.IntegerField(default=0, verbose_name="Visualizações")
    downloads = models.IntegerField(default=0, verbose_name="Downloads")

    class Meta:
        verbose_name = 'Manual Simples'
        verbose_name_plural = 'Manuais Simples'
        ordering = ['-data_atualizacao']
        permissions = [
            ('publicar_manual_simples', 'Pode publicar manuais simples'),
            ('revisar_manual_simples', 'Pode revisar manuais simples'),
            ('gerar_pdf_manual_simples', 'Pode gerar PDF de manuais simples'),
        ]

    def __str__(self):
        return f"{self.codigo} - {self.titulo} (v{self.versao})"

    def get_absolute_url(self):
        return reverse('manual_simples_detalhe', args=[str(self.id)])

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
        return self.capitulos_simples.count()

    def total_paginas(self):
        return self.capitulos_simples.aggregate(total=Sum('num_paginas'))['total'] or 0

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


class CapituloSimples(models.Model):
    """Capítulos de um manual simples"""
    manual = models.ForeignKey(Manual, on_delete=models.CASCADE,
                               related_name='capitulos_simples', verbose_name="Manual")
    titulo = models.CharField(max_length=200, verbose_name="Título")
    numero = models.IntegerField(verbose_name="Número")
    conteudo = models.TextField(verbose_name="Conteúdo")
    ordem = models.IntegerField(default=0, verbose_name="Ordem")
    
    TIPO_SECAO_CHOICES = [
        ('CAPA', 'Capa'),
        ('PREFACIO', 'Prefácio'),
        ('INTRODUCAO', 'Introdução'),
        ('CAPITULO', 'Capítulo'),
        ('ANEXO', 'Anexo'),
        ('POSFACIO', 'Posfácio'),
    ]
    tipo_secao = models.CharField(max_length=20, choices=TIPO_SECAO_CHOICES, default='CAPITULO', verbose_name="Tipo de Seção")
    
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
        verbose_name = 'Capítulo Simples'
        verbose_name_plural = 'Capítulos Simples'
        ordering = ['manual', 'ordem', 'numero']
        unique_together = ['manual', 'numero']

    def __str__(self):
        return f"{self.manual.codigo} - Cap. {self.numero}: {self.titulo}"

    def save(self, *args, **kwargs):
        # Garantir ordem sequencial
        if not self.ordem:
            max_ordem = CapituloSimples.objects.filter(
                manual=self.manual
            ).aggregate(Max('ordem'))['ordem__max']
            self.ordem = (max_ordem or 0) + 1

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('manual_simples_detalhe', args=[str(self.manual.id)]) + f'#capitulo-{self.id}'


class ImagemManualSimples(models.Model):
    """Imagens para manuais simples"""
    manual = models.ForeignKey(Manual, on_delete=models.CASCADE,
                               related_name='imagens_simples', verbose_name="Manual")
    titulo = models.CharField(max_length=200, verbose_name="Título")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    imagem = models.ImageField(upload_to='manuais_simples/imagens/', verbose_name="Imagem")

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
        verbose_name = 'Imagem de Manual Simples'
        verbose_name_plural = 'Imagens de Manuais Simples'
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


class ComentarioManualSimples(models.Model):
    """Comentários em manuais simples"""
    manual = models.ForeignKey(Manual, on_delete=models.CASCADE,
                               related_name='comentarios_simples', verbose_name="Manual")
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuário")
    texto = models.TextField(verbose_name="Texto")

    # Controle
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")
    resolvido = models.BooleanField(default=False, verbose_name="Resolvido")
    resolvido_por = models.ForeignKey(User, on_delete=models.SET_NULL,
                                      null=True, blank=True,
                                      related_name='comentarios_simples_resolvidos', verbose_name="Resolvido por")
    data_resolucao = models.DateTimeField(null=True, blank=True, verbose_name="Data de Resolução")

    # Referência (opcional)
    capitulo = models.ForeignKey(CapituloSimples, on_delete=models.SET_NULL,
                                 null=True, blank=True, verbose_name="Capítulo Referente")
    pagina = models.IntegerField(null=True, blank=True, verbose_name="Página")

    class Meta:
        verbose_name = 'Comentário de Manual Simples'
        verbose_name_plural = 'Comentários de Manuais Simples'
        ordering = ['-data_criacao']

    def __str__(self):
        return f"Comentário de {self.usuario.username} em {self.manual.codigo}"

    def marcar_como_resolvido(self, usuario):
        self.resolvido = True
        self.resolvido_por = usuario
        self.data_resolucao = models.DateTimeField(auto_now=True)
        self.save()


# ============ MODELOS PARA PLANIFICAÇÃO E ESTRATÉGIA ============

PROVINCIA_CHOICES = [
    ('CENTRAL', 'Nível Central'),
    ('CABO_DELGADO', 'Cabo Delgado'),
    ('GAZA', 'Gaza'),
    ('INHAMBANE', 'Inhambane'),
    ('MANICA', 'Manica'),
    ('MAPUTO_CIDADE', 'Maputo Cidade'),
    ('MAPUTO_PROVINCIA', 'Maputo Província'),
    ('NAMPULA', 'Nampula'),
    ('NIASSA', 'Niassa'),
    ('SOFALA', 'Sofala'),
    ('TETE', 'Tete'),
    ('ZAMBEZIA', 'Zambézia'),
]

class ObjetivoInstitucional(models.Model):
    ano = models.IntegerField(default=2025)
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        verbose_name = 'Objetivo Institucional'
        verbose_name_plural = 'Objetivos Institucionais'
        ordering = ['-ano', 'titulo']

    def __str__(self):
        return f"[{self.ano}] {self.titulo}"

# ============ MODELOS EXISTENTES SIMPLIFICADOS ============

class PlanoAtividade(models.Model):
    NIVEL_CHOICES = [
        ('CENTRAL', 'Nacional/Central'),
        ('PROVINCIAL', 'Provincial/Local'),
    ]
    
    codigo = models.CharField(max_length=20, unique=True, blank=True)
    nome = models.CharField(max_length=200)
    objetivo_institucional = models.ForeignKey(ObjetivoInstitucional, on_delete=models.SET_NULL, null=True, related_name='planos')
    nivel = models.CharField(max_length=20, choices=NIVEL_CHOICES, default='CENTRAL')
    provincia = models.CharField(max_length=50, choices=PROVINCIA_CHOICES, default='CENTRAL')
    plano_pai = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='sub_planos', help_text="Referência ao Plano Nacional")
    
    tipo = models.CharField(max_length=50)
    descricao = models.TextField(blank=True)
    objetivos_especificos = models.TextField(blank=True, help_text="Objetivos específicos deste plano")
    status = models.CharField(max_length=50, default='planejado')
    data_inicio_planeada = models.DateField(null=True, blank=True)
    data_fim_planeada = models.DateField(null=True, blank=True)
    orcamento_planeado = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    responsavel_principal = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    extensao_possivel = models.BooleanField(default=False)
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    data_atualizacao = models.DateTimeField(auto_now=True, null=True, blank=True)
    formadores = models.ManyToManyField(User, blank=True, related_name='planos_formador')

    def save(self, *args, **kwargs):
        if not self.codigo:
            import uuid
            prefix = "PL-C" if self.nivel == 'CENTRAL' else f"PL-{self.provincia[:3].upper()}"
            self.codigo = f"{prefix}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} - {self.nome} ({self.get_provincia_display()})"

class Atividade(models.Model):
    plano = models.ForeignKey(PlanoAtividade, on_delete=models.CASCADE, related_name='atividades')
    objetivo_institucional = models.ForeignKey(ObjetivoInstitucional, on_delete=models.SET_NULL, null=True, related_name='atividades')
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    referencia_nacional = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='sub_atividades', help_text="Atividade do Plano Nacional que esta sub-atividade provincial segue")
    
    data_inicio = models.DateField(null=True, blank=True)
    data_fim = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50, default='pendente')
    orcamento_estimado = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.nome} (Plano: {self.plano.codigo})"


class Formacao(models.Model):
    codigo = models.CharField(max_length=20, unique=True, blank=True)
    atividade = models.ForeignKey(Atividade, on_delete=models.CASCADE, related_name='formacoes', null=True)
    nome = models.CharField(max_length=200)
    tipo_formacao = models.CharField(max_length=50)
    nivel = models.CharField(max_length=20, choices=[('CENTRAL', 'Nacional'), ('PROVINCIAL', 'Provincial')], default='CENTRAL')
    provincia = models.CharField(max_length=50, choices=PROVINCIA_CHOICES, default='CENTRAL')
    local_realizacao = models.CharField(max_length=200, blank=True)
    vagas_planeadas = models.IntegerField(default=0)
    vagas_preenchidas = models.IntegerField(default=0)
    status = models.CharField(max_length=50, default='planejada')
    responsavel_principal = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # Datas
    data_inicio_planeada = models.DateField(null=True, blank=True)
    data_fim_planeada = models.DateField(null=True, blank=True)
    data_inicio_real = models.DateField(null=True, blank=True)
    data_fim_real = models.DateField(null=True, blank=True)
    
    # Orçamento
    orcamento_planeado = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    orcamento_executado = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Outros campos
    carga_horaria = models.IntegerField(default=0)
    descricao = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.codigo:
            import uuid
            self.codigo = f"FOR-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} - {self.nome} ({self.get_provincia_display()})"


class Participante(models.Model):
    CATEGORIA_CHOICES = [
        ('BRIGADISTA', 'Brigadista'),
        ('MMV', 'Membro MMV'),
        ('AGENTE_EC', 'Agente de Educação Cívica'),
        ('TECNICO', 'Técnico de Apoio'),
        ('OUTRO', 'Outro'),
    ]
    nome_completo = models.CharField(max_length=200)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default='BRIGADISTA')
    formacao = models.ForeignKey(Formacao, on_delete=models.CASCADE, related_name='participantes')
    status = models.CharField(max_length=50, default='inscrito')
    bilhete_identidade = models.CharField(max_length=50, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    genero = models.CharField(max_length=1, default='M')
    provincia = models.CharField(max_length=50, choices=PROVINCIA_CHOICES, default='CENTRAL')
    distrito = models.CharField(max_length=100, blank=True)
    data_nascimento = models.DateField(null=True, blank=True)
    codigo_qr = models.CharField(max_length=100, blank=True)

    @property
    def idade(self):
        if self.data_nascimento:
            today = date.today()
            return today.year - self.data_nascimento.year - (
                    (today.month, today.day) < (self.data_nascimento.month, self.data_nascimento.day)
            )
        return 0

    def __str__(self):
        return self.nome_completo


class Avaliacao(models.Model):
    participante = models.OneToOneField(Participante, on_delete=models.CASCADE, related_name='avaliacao')
    classificacao_final = models.DecimalField(max_digits=4, decimal_places=2, default=0, verbose_name="Classificação (0-20)")
    comentarios = models.TextField(blank=True)
    data_avaliacao = models.DateTimeField(auto_now=True)
    avaliado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Atualizar status do participante
        if self.classificacao_final >= 10:
            self.participante.status = 'APROVADO'
        else:
            self.participante.status = 'REPROVADO'
        self.participante.save()

    @property
    def aprovado(self):
        return self.classificacao_final >= 10

    @property
    def status_final(self):
        return "Aprovado" if self.aprovado else "Reprovado"
    
    @property
    def suplente(self):
        return False

    def __str__(self):
        return f"Avaliação de {self.participante.nome_completo}: {self.classificacao_final}"


class Turma(models.Model):
    nome = models.CharField(max_length=100)
    formacao = models.ForeignKey(Formacao, on_delete=models.CASCADE, related_name='turmas')
    formador_principal = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='turmas_formador')
    data_inicio = models.DateField(null=True, blank=True)
    data_fim = models.DateField(null=True, blank=True)
    participantes_atribuidos = models.ManyToManyField(Participante, blank=True)
    formadores_auxiliares = models.ManyToManyField(User, blank=True, related_name='turmas_auxiliar')

    @property
    def percentual_preenchimento(self):
        total = self.participantes_atribuidos.count()
        if total > 0:
            # Assumindo uma capacidade padrão de 60 se não houver campo específico
            return min(100, int((total / 60) * 100))
        return 0

    @property
    def homens_count(self):
        return self.participantes_atribuidos.filter(genero='M').count()

    @property
    def mulheres_count(self):
        return self.participantes_atribuidos.filter(genero='F').count()

    @property
    def outros_count(self):
        return self.participantes_atribuidos.filter(genero='O').count()

    def __str__(self):
        return f"{self.nome} - {self.formacao.nome}"


class Brigada(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    formacao = models.ForeignKey(Formacao, on_delete=models.CASCADE, related_name='brigadas')
    provincia = models.CharField(max_length=50, choices=PROVINCIA_CHOICES, default='CENTRAL')
    distrito = models.CharField(max_length=100)
    localidade = models.CharField(max_length=200, blank=True)
    supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='brigadas_supervisor')
    digitador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='brigadas_digitador')
    entrevistador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='brigadas_entrevistador')
    completa = models.BooleanField(default=False)
    ativa = models.BooleanField(default=True)
    membros = models.ManyToManyField('Participante', blank=True, related_name='brigadas_membro')

    def __str__(self):
        return f"{self.codigo} - {self.provincia}/{self.distrito}"


class Eleicao(models.Model):
    tipo = models.CharField(max_length=50)
    ano = models.IntegerField()
    descricao = models.TextField(blank=True)
    dados_carregados = models.BooleanField(default=False)
    data_carregamento = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.tipo} {self.ano}"

# ============ NOVO: LOGÍSTICA E MATERIAL DE FORMAÇÃO (DFEC) ============

class LogisticaMaterialDFEC(models.Model):
    """Definição de requisitos de materiais para Formação e Educação Cívica"""
    TIPO_CHOICES = [
        ('KIT_FORMADOR', 'Kit do Formador'),
        ('KIT_PARTICIPANTE', 'Kit do Participante'),
        ('MANUAL_IMPRESSO', 'Manuais e Guias Impressos'),
        ('EQUIPAMENTO_PROJECAO', 'Equipamento de Projeção'),
        ('MATERIAL_ESCRITORIO', 'Material de Escritório de Apoio'),
        ('OUTRO', 'Outro Material de Formação'),
    ]

    item = models.CharField(max_length=200, verbose_name="Requisito de Material")
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    quantidade_necessaria = models.IntegerField(default=0, help_text="Quantidade planeada para a atividade")
    
    # Ligação ao Inventário Real
    equipamentos_vinculados = models.ManyToManyField('gestaoequipamentos.Equipamento', blank=True, related_name='necessidades_dfec', help_text="Items reais registados no património")
    
    # Relação com Formação ou Plano específico
    plano = models.ForeignKey(PlanoAtividade, on_delete=models.SET_NULL, null=True, blank=True, related_name='requisitos_logistica')
    formacao = models.ForeignKey(Formacao, on_delete=models.SET_NULL, null=True, blank=True, related_name='requisitos_formacao')
    
    observacoes = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Requisito de Material DFEC'
        verbose_name_plural = 'Requisitos de Materiais DFEC'

    def __str__(self):
        return f"Req: {self.item} ({self.get_tipo_display()})"
    
    @property
    def total_vinculado(self):
        return self.equipamentos_vinculados.count()


class DadosEleicao(models.Model):
    eleicao = models.ForeignKey(Eleicao, on_delete=models.CASCADE)
    provincia = models.CharField(max_length=100)
    distrito = models.CharField(max_length=100)
    localidade = models.CharField(max_length=200, blank=True)
    posto_votacao = models.CharField(max_length=200, blank=True)
    total_inscritos = models.IntegerField(default=0)
    comparecimento = models.IntegerField(default=0)

    @property
    def abstencoes_calculadas(self):
        return self.total_inscritos - self.comparecimento

    @property
    def hash_registo(self):
        return f"{self.eleicao.id}-{self.provincia}-{self.distrito}"

    def __str__(self):
        return f"{self.eleicao.tipo} {self.eleicao.ano} - {self.provincia}/{self.distrito}"


class AnaliseRegiao(models.Model):
    eleicao = models.ForeignKey(Eleicao, on_delete=models.CASCADE)
    nivel = models.CharField(max_length=50)  # provincial, distrital, etc.
    nome_regiao = models.CharField(max_length=200)
    indicador = models.CharField(max_length=100)
    classificacao = models.CharField(max_length=50)  # boa, regular, crítica
    prioridade = models.CharField(max_length=50)  # alta, média, baixa
    recomendacao = models.TextField(blank=True)

    def __str__(self):
        return f"Análise {self.nivel} - {self.nome_regiao}"


class RelatorioGerado(models.Model):
    titulo = models.CharField(max_length=200)
    tipo = models.CharField(max_length=50)
    formato = models.CharField(max_length=10)  # pdf, excel, word
    gerado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    data_geracao = models.DateTimeField(auto_now_add=True)
    arquivo = models.FileField(upload_to='relatorios/', null=True, blank=True)

    def __str__(self):
        return self.titulo


class AlertaSistema(models.Model):
    tipo = models.CharField(max_length=50)
    nivel = models.CharField(max_length=50)  # info, aviso, erro, critico
    titulo = models.CharField(max_length=200)
    mensagem = models.TextField()
    resolvido = models.BooleanField(default=False)
    visualizado = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nivel}: {self.titulo}"