# pagina_stae/models.py - MODELO COMPLETO
from django.db import models
from django.contrib.auth.models import User
from ckeditor.fields import RichTextField
from django.urls import reverse
from django.utils import timezone


class STAEConfiguracao(models.Model):
    """Configurações gerais do portal STAE"""
    titulo_portal = models.CharField(max_length=200, default="Moçambique")
    lema = models.CharField(max_length=300, default="Por Eleições livres, transparentes e justas")
    logo = models.ImageField(upload_to='config/', blank=True)
    favicon = models.ImageField(upload_to='config/', blank=True)

    # Contactos
    telefone = models.CharField(max_length=20, default="+244 222 123 456")
    email = models.EmailField(default="info@stae.gov.mz")
    endereco = models.TextField(default="Maputo, Moçambique")

    # Social Media
    facebook = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    youtube = models.URLField(blank=True)
    instagram = models.URLField(blank=True)

    # SEO
    meta_description = models.TextField(blank=True)
    keywords = models.TextField(blank=True)

    ativo = models.BooleanField(default=True)


class MenuItem(models.Model):
    """Menu de navegação"""
    TIPO_CHOICES = [
        ('PAGINA', 'Página'),
        ('LINK', 'Link Externo'),
        ('DROPDOWN', 'Dropdown'),
    ]

    titulo = models.CharField(max_length=100)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='PAGINA')
    url = models.CharField(max_length=200, blank=True)
    pagina = models.ForeignKey('Pagina', on_delete=models.CASCADE, blank=True, null=True)
    ordem = models.IntegerField(default=0)
    ativo = models.BooleanField(default=True)
    pai = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        ordering = ['ordem', 'titulo']


class Pagina(models.Model):
    """Páginas estáticas do site"""
    titulo = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    conteudo = RichTextField()
    imagem_destaque = models.ImageField(upload_to='paginas/', blank=True)
    meta_description = models.TextField(blank=True)
    ativa = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_actualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data_criacao']

    def __str__(self):
        return self.titulo

    def get_absolute_url(self):
        return reverse('pagina_stae:pagina_detalhe', kwargs={'slug': self.slug})


class CategoriaNoticia(models.Model):
    """Categorias para notícias"""
    nome = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    descricao = models.TextField(blank=True)
    cor = models.CharField(max_length=7, default='#3B82F6')

    class Meta:
        verbose_name = "Categoria de Notícia"
        verbose_name_plural = "Categorias de Notícias"

    def __str__(self):
        return self.nome


class Noticia(models.Model):
    titulo = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    resumo = models.TextField(max_length=300)
    conteudo = models.TextField()
    categoria = models.ForeignKey(CategoriaNoticia, on_delete=models.SET_NULL, null=True, blank=True)  # ← ADD blank=True
    autor = models.ForeignKey(User, on_delete=models.CASCADE, default=1)  # ← ADD default=1
    imagem_destaque = models.ImageField(upload_to='noticias/', blank=True)  # ← ADD blank=True
    destaque = models.BooleanField(default=False)
    publicado = models.BooleanField(default=False)
    data_publicacao = models.DateTimeField(default=timezone.now)  # ← ADD default
    visualizacoes = models.IntegerField(default=0)


    class Meta:
        verbose_name = "Notícia"
        verbose_name_plural = "Notícias"
        ordering = ['-data_publicacao']

    def __str__(self):
        return self.titulo

    def get_absolute_url(self):
        return reverse('pagina_stae:noticia_detalhe', kwargs={'slug': self.slug})

    def aumentar_visualizacao(self):
        self.visualizacoes += 1
        self.save(update_fields=['visualizacoes'])


class Galeria(models.Model):
    """Sistema de galerias de imagens"""
    titulo = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    descricao = models.TextField(blank=True)
    capa = models.ImageField(upload_to='galerias/')
    data_criacao = models.DateTimeField(auto_now_add=True)
    publica = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Galeria"
        verbose_name_plural = "Galerias"
        ordering = ['-data_criacao']

    def __str__(self):
        return self.titulo


class ImagemGaleria(models.Model):
    """Imagens dentro das galerias"""
    galeria = models.ForeignKey(Galeria, on_delete=models.CASCADE, related_name='imagens')
    imagem = models.ImageField(upload_to='galerias/imagens/')
    titulo = models.CharField(max_length=200, blank=True)
    descricao = models.TextField(blank=True)
    ordem = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordem', 'id']

    def __str__(self):
        return self.titulo or f"Imagem {self.id}"


class Video(models.Model):
    """Sistema de gestão de vídeos"""
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    url = models.URLField(help_text="URL do YouTube ou Vimeo")
    miniatura = models.ImageField(upload_to='videos/miniaturas/', blank=True)
    data_publicacao = models.DateTimeField(auto_now_add=True)
    destaque = models.BooleanField(default=False)

    class Meta:
        ordering = ['-data_publicacao']

    def __str__(self):
        return self.titulo


class Departamento(models.Model):
    """Departamentos/órgãos do STAE"""
    nome = models.CharField(max_length=200)
    sigla = models.CharField(max_length=20, blank=True)
    descricao = models.TextField(blank=True)
    responsavel = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    icone = models.CharField(max_length=50, help_text="Classe Font Awesome")
    ordem = models.IntegerField(default=0)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ['ordem', 'nome']

    def __str__(self):
        return self.nome


class Servico(models.Model):
    """Serviços prestados pelo STAE"""
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE)
    nome = models.CharField(max_length=200)
    descricao = models.TextField()
    icone = models.CharField(max_length=50)
    url = models.CharField(max_length=200, blank=True)
    ordem = models.IntegerField(default=0)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ['ordem', 'nome']

    def __str__(self):
        return self.nome


class Documento(models.Model):
    """Sistema de documentos públicos"""
    TIPO_CHOICES = [
        ('LEI', 'Lei'),
        ('DECRETO', 'Decreto'),
        ('REGULAMENTO', 'Regulamento'),
        ('RELATORIO', 'Relatório'),
        ('OUTRO', 'Outro'),
    ]

    titulo = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    arquivo = models.FileField(upload_to='documentos/')
    descricao = models.TextField(blank=True)
    data_publicacao = models.DateField()
    numero = models.CharField(max_length=50, blank=True)
    publico = models.BooleanField(default=True)

    class Meta:
        ordering = ['-data_publicacao']

    def __str__(self):
        return self.titulo


class FAQ(models.Model):
    """Perguntas frequentes"""
    pergunta = models.CharField(max_length=300)
    resposta = models.TextField()
    categoria = models.CharField(max_length=100, blank=True)
    ordem = models.IntegerField(default=0)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
        ordering = ['ordem', 'id']

    def __str__(self):
        return self.pergunta


class Banner(models.Model):
    """Banners do site"""
    titulo = models.CharField(max_length=200)
    imagem = models.ImageField(upload_to='banners/')
    link = models.CharField(max_length=200, blank=True)
    texto_botao = models.CharField(max_length=50, blank=True)
    ativo = models.BooleanField(default=True)
    ordem = models.IntegerField(default=0)
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField()

    class Meta:
        ordering = ['ordem', '-data_inicio']


# ========== MODELOS ELECTORAIS (os que já tinha) ==========
class Eleicao(models.Model):
    TIPO_CHOICES = [
        ('PRESIDENCIAL', 'Eleições Presidenciais'),
        ('LEGISLATIVAS', 'Eleições Legislativas'),
        ('AUTARQUICAS', 'Eleições Autárquicas'),
    ]

    nome = models.CharField(max_length=200, verbose_name="Nome da Eleição")
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    data = models.DateField(verbose_name="Data da Eleição")
    ativa = models.BooleanField(default=False, verbose_name="Eleição Ativa")
    total_eleitores = models.IntegerField(default=0)
    total_secoes = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Eleição"
        verbose_name_plural = "Eleições"

    def percentual_apuracao(self):
        from django.db.models import Count
        if self.total_secoes == 0:
            return 0
        apuradas = ResultadoSecao.objects.filter(eleicao=self).values('secao').distinct().count()
        return round((apuradas / self.total_secoes) * 100, 2)


class Candidato(models.Model):
    eleicao = models.ForeignKey(Eleicao, on_delete=models.CASCADE)
    nome = models.CharField(max_length=200)
    partido = models.CharField(max_length=100)
    numero = models.IntegerField()
    foto = models.ImageField(upload_to='candidatos/')
    cor_campanha = models.CharField(max_length=7, default='#000000')
    biografia = models.TextField()

    class Meta:
        unique_together = ['eleicao', 'numero']


class ResultadoSecao(models.Model):
    eleicao = models.ForeignKey(Eleicao, on_delete=models.CASCADE)
    secao = models.ForeignKey('SecaoEleitoral', on_delete=models.CASCADE)
    candidato = models.ForeignKey(Candidato, on_delete=models.CASCADE)
    votos = models.IntegerField(default=0)
    hora_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['eleicao', 'secao', 'candidato']


class SecaoEleitoral(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    provincia = models.CharField(max_length=50)
    municipio = models.CharField(max_length=50)
    total_eleitores = models.IntegerField(default=0)


class LogAuditoria(models.Model):
    usuario = models.CharField(max_length=100)
    acao = models.CharField(max_length=200)
    dados = models.JSONField()
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)