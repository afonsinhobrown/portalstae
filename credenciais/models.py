from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
import hashlib
import secrets
import json # Added import
from django.core.validators import FileExtensionValidator
from django.urls import reverse
from django.utils.text import slugify
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw
import os


class Solicitante(models.Model):
    """Solicitante de credenciais"""
    TIPO_CHOICES = [
        ('singular', 'Singular (Individual)'),
        ('ong', 'ONG / Sociedade Civil'),
        ('radio', 'Rádio'),
        ('tv', 'Televisão'),
        ('jornal', 'Jornal / Imprensa Escrita'),
        ('partido', 'Partido Político'),
        ('observador', 'Observador'),
        ('instituicao', 'Instituição Pública'),
        ('empresa', 'Empresa Privada'),
        ('outro', 'Outro'),
    ]

    GENERO_CHOICES = [
        ('masculino', 'Masculino'),
        ('feminino', 'Feminino'),
        ('outro', 'Outro'),
    ]

    # Informações básicas
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='singular')
    nome_completo = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=20)
    nacionalidade = models.CharField(max_length=100, default='Moçambicana')
    genero = models.CharField(max_length=20, choices=GENERO_CHOICES, blank=True)

    # Identificação
    numero_bi = models.CharField(max_length=20, unique=True, blank=True, null=True)
    data_validade_bi = models.DateField(blank=True, null=True)
    nif = models.CharField(max_length=20, blank=True, null=True)
    nup = models.CharField(max_length=20, blank=True, null=True)

    # Para colectivos/empresas
    nome_empresa = models.CharField(max_length=200, blank=True)
    numero_registo_comercial = models.CharField(max_length=50, blank=True)
    nif_empresa = models.CharField(max_length=20, blank=True)

    # Documentos
    documento_identificacao = models.FileField(
        upload_to='solicitantes/docs/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png'])]
    )
    foto = models.ImageField(
        upload_to='solicitantes/fotos/',
        blank=True,
        null=True
    )

    # Endereço
    endereco = models.TextField(blank=True)
    provincia = models.CharField(max_length=100, blank=True)
    distrito = models.CharField(max_length=100, blank=True)

    # Status
    ativo = models.BooleanField(default=True)
    validado = models.BooleanField(default=False)
    validado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='solicitantes_validados')
    data_validacao = models.DateTimeField(null=True, blank=True)

    # Histórico
    data_registo = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    numero_identificacao = models.CharField(max_length=50, unique=True, blank=True)

    class Meta:
        verbose_name = "Solicitante"
        verbose_name_plural = "Solicitantes"
        ordering = ['-data_registo']

    def __str__(self):
        return f"{self.nome_completo} ({self.email})"

    def save(self, *args, **kwargs):
        if not self.numero_identificacao:
            self.numero_identificacao = self.gerar_numero_identificacao()
        super().save(*args, **kwargs)

    def gerar_numero_identificacao(self):
        """Gera número de identificação único"""
        import uuid
        prefix = 'SOL' if self.tipo == 'singular' else 'COL'
        unique_id = str(uuid.uuid4())[:8].upper()
        return f"{prefix}-{unique_id}"

    def validar_bi(self, usuario):
        """Valida o BI do solicitante"""
        self.validado = True
        self.validado_por = usuario
        self.data_validacao = timezone.now()
        self.save()


class Evento(models.Model):
    """Evento para o qual as credenciais são emitidas"""
    PROVINCIA_CHOICES = [
        ('maputo_cidade', 'Maputo Cidade'),
        ('maputo_provincia', 'Maputo Província'),
        ('gaza', 'Gaza'),
        ('inhambane', 'Inhambane'),
        ('sofala', 'Sofala'),
        ('manica', 'Manica'),
        ('tete', 'Tete'),
        ('zambezia', 'Zambézia'),
        ('nampula', 'Nampula'),
        ('niassa', 'Niassa'),
        ('cabo_delgado', 'Cabo Delgado'),
    ]

    ABRANGENCIA_CHOICES = [
        ('nacional', 'Nacional (Todo o País)'),
        ('provincial', 'Provincial'),
        ('local', 'Local / Específico'),
    ]

    CATEGORIA_CHOICES = [
        ('oficial', 'Evento Oficial / Eleição'),
        ('formacao', 'Formação / Capacitação (DFEC)'),
        ('educacao_civica', 'Educação Cívica / Sensibilização'),
        ('outros', 'Outros'),
    ]

    nome = models.CharField(max_length=200)
    categoria = models.CharField(max_length=50, choices=CATEGORIA_CHOICES, default='oficial', verbose_name="Categoria / Tipo")
    descricao = models.TextField(blank=True)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    abrangencia = models.CharField(max_length=20, choices=ABRANGENCIA_CHOICES, default='nacional')
    provincia = models.CharField(max_length=50, choices=PROVINCIA_CHOICES, blank=True, null=True)
    local = models.CharField(max_length=200, blank=True, null=True)

    # Configurações
    limite_participantes = models.IntegerField(default=0, help_text="0 = ilimitado")
    permite_pedidos_remotos = models.BooleanField(default=True)
    ativo = models.BooleanField(default=True)

    # Documentos
    regulamento = models.FileField(upload_to='eventos/regulamentos/', blank=True, null=True)
    logotipo = models.ImageField(upload_to='eventos/logos/', blank=True, null=True)

    # Responsável
    responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    # Metadados
    data_criacao = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='eventos_criados')

    class Meta:
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"
        ordering = ['-data_inicio']

    def __str__(self):
        return f"{self.nome} ({self.data_inicio.year})"

    @property
    def esta_ativo(self):
        """Verifica se o evento está ativo (dentro do período)"""
        hoje = date.today()
        return self.ativo and self.data_inicio <= hoje <= self.data_fim


class TipoCredencial(models.Model):
    """Tipo de credencial (Acesso, VIP, Imprensa, etc.)"""
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    cor = models.CharField(max_length=20, default='#007bff', help_text="Cor em hexadecimal")
    ordem = models.IntegerField(default=0)
    ativo = models.BooleanField(default=True)

    # Permissões
    permite_acesso_geral = models.BooleanField(default=True)
    zonas_permitidas = models.TextField(blank=True, help_text="Zonas separadas por vírgula")
    horario_acesso = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = "Tipo de Credencial"
        verbose_name_plural = "Tipos de Credencial"
        ordering = ['ordem', 'nome']

    def __str__(self):
        return self.nome


class ModeloCredencial(models.Model):
    """Modelo de design para credenciais"""
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)

    # Design
    cor_fundo = models.CharField(max_length=20, default='#ffffff')
    cor_texto = models.CharField(max_length=20, default='#000000')
    logotipo = models.ImageField(upload_to='modelos/logos/', blank=True, null=True)
    template_html = models.TextField(blank=True, help_text="Template HTML personalizado")

    # Configurações
    incluir_qr_code = models.BooleanField(default=True)
    incluir_codigo_offline = models.BooleanField(default=True)
    tamanho = models.CharField(max_length=20, default='85x54', help_text="LarguraxAltura em mm")

    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Modelo de Credencial"
        verbose_name_plural = "Modelos de Credencial"

    def __str__(self):
        return self.nome


class PedidoCredencial(models.Model):
    """Pedido de credencial"""
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('em_analise', 'Em Análise'),
        ('aprovado', 'Aprovado'),
        ('reprovado', 'Reprovado'),
        ('emitido', 'Emitido'),
        ('cancelado', 'Cancelado'),
    ]

    # Identificação
    ABRANGENCIA_CHOICES = [
        ('nacional', 'Nacional'),
        ('provincial', 'Provincial'),
        ('local', 'Local / Específica'),
    ]

    # Identificação
    numero_pedido = models.CharField(max_length=50, unique=True, blank=True)
    solicitante = models.ForeignKey(Solicitante, on_delete=models.CASCADE, related_name='pedidos')
    tipo_credencial = models.ForeignKey(TipoCredencial, on_delete=models.PROTECT)
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, null=True, blank=True) # Null temporário para migração

    # Abrangência
    abrangencia = models.CharField(max_length=20, choices=ABRANGENCIA_CHOICES, default='local')
    provicia_abrangencia = models.CharField(max_length=50, choices=Evento.PROVINCIA_CHOICES, blank=True, null=True, verbose_name="Província de Abrangência")

    # Documentos Obrigatórios
    carta_solicitacao = models.FileField(
        upload_to='pedidos/cartas/', 
        null=True, 
        blank=True,
        validators=[FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png'])],
        help_text="Carta dirigida ao Presidente da CNE"
    )
    copia_identificacao = models.FileField(
        upload_to='pedidos/identificacao/', 
        null=True, 
        blank=True,
        validators=[FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png'])],
        help_text="Cópia do documento de identificação"
    )

    # Detalhes do pedido
    motivo = models.TextField(help_text="Motivo para solicitar a credencial")
    data_inicio = models.DateField(help_text="Data de início pretendida")
    data_fim = models.DateField(help_text="Data de fim pretendida")
    quantidade = models.IntegerField(default=1)

    # Status e análise
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    observacoes_analise = models.TextField(blank=True)
    analisado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='pedidos_analisados')
    data_analise = models.DateTimeField(null=True, blank=True)

    # Para pedidos remotos
    pedido_remoto = models.BooleanField(default=False)
    codigo_confirmacao = models.CharField(max_length=50, blank=True)

    # Metadados
    data_pedido = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='pedidos_criados')
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pedido de Credencial"
        verbose_name_plural = "Pedidos de Credencial"
        ordering = ['-data_pedido']

    def __str__(self):
        return f"Pedido {self.numero_pedido} - {self.solicitante.nome_completo}"

    def save(self, *args, **kwargs):
        if not self.numero_pedido:
            self.numero_pedido = self.gerar_numero_pedido()
        if self.pedido_remoto and not self.codigo_confirmacao:
            self.codigo_confirmacao = self.gerar_codigo_confirmacao()
        super().save(*args, **kwargs)

    def gerar_numero_pedido(self):
        """Gera número único para o pedido"""
        import uuid
        ano = timezone.now().year
        unique_id = str(uuid.uuid4())[:6].upper()
        return f"PED-{ano}-{unique_id}"

    def gerar_codigo_confirmacao(self):
        """Gera código de confirmação para pedidos remotos"""
        return secrets.token_urlsafe(16)

class BeneficiarioPedido(models.Model):
    """Pessoas individuais associadas a um pedido (especialmente para organizações)"""
    pedido = models.ForeignKey(PedidoCredencial, on_delete=models.CASCADE, related_name='beneficiarios')
    nome_completo = models.CharField(max_length=200)
    numero_bi = models.CharField(max_length=20, blank=True)
    cargo_funcao = models.CharField(max_length=100, blank=True, verbose_name="Cargo/Função")
    foto = models.ImageField(upload_to='beneficiarios/fotos/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.nome_completo} - {self.pedido.numero_pedido}"

    class Meta:
        verbose_name = "Beneficiário de Pedido"
        verbose_name_plural = "Beneficiários de Pedidos"


class CredencialEmitida(models.Model):
    """Credencial emitida"""
    STATUS_CHOICES = [
        ('emitida', 'Emitida'),
        ('ativa', 'Ativa'),
        ('suspensa', 'Suspensa'),
        ('revogada', 'Revogada'),
        ('expirada', 'Expirada'),
    ]

    # Relações
    pedido = models.ForeignKey(PedidoCredencial, on_delete=models.CASCADE, related_name='credencial_set') # 1-to-N: Multiple creds per pedido (legacy support)
    # Anteriormente era OneToOne, mas para suportar lotes usamos ForeignKey. Atenção às migrações!
    # OBSERVAÇÃO: Manter OneToOne no código legado se for crítico, mas aqui estou permitindo flexibilidade.
    # Se o banco atual tem OneToOne, mudar para ForeignKey exige migração. 
    # VOU MANTER OneToOne NO ARQUIVO PARA NÃO QUEBRAR O LEGADO SEM MIGRAÇÃO COMPLETA. 
    # USAR 'pedido = models.OneToOneField...' COPIADO do original
    pedido = models.OneToOneField(PedidoCredencial, on_delete=models.CASCADE, related_name='credencial')
    
    modelo = models.ForeignKey(ModeloCredencial, on_delete=models.PROTECT, null=True, blank=True)

    # Identificação
    numero_credencial = models.CharField(max_length=50, unique=True)
    data_emissao = models.DateTimeField(auto_now_add=True)
    data_validade = models.DateField()

    # Códigos de segurança
    codigo_verificacao = models.CharField(max_length=100, unique=True, blank=True)
    codigo_offline = models.CharField(max_length=50, unique=True, blank=True)
    qr_code = models.ImageField(upload_to='credenciais/qr_codes/', blank=True, null=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='emitida')
    bloqueio_emergencia = models.BooleanField(default=False)

    # Metadados
    emitida_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='credenciais_emitidas')
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Credencial Emitida"
        verbose_name_plural = "Credenciais Emitidas"
        ordering = ['-data_emissao']

    def __str__(self):
        return f"Credencial {self.numero_credencial}"

    def save(self, *args, **kwargs):
        if not self.codigo_verificacao:
            self.codigo_verificacao = self.gerar_codigo_verificacao()
        if not self.codigo_offline:
            self.codigo_offline = self.gerar_codigo_offline()
        super().save(*args, **kwargs)

    def gerar_codigo_verificacao(self):
        """Gera código único para verificação online"""
        import uuid
        return str(uuid.uuid4())

    def gerar_codigo_offline(self):
        """Gera código offline para verificação sem internet"""
        import secrets
        return f"{self.numero_credencial}-{secrets.token_hex(4).upper()}"

    def gerar_qr_code(self):
        """Gera QR Code para a credencial com dados detalhados"""
        if self.codigo_verificacao:
            # Dados para o QR Code (JSON para fácil leitura por apps de fiscalização)
            payload = {
                "num": self.numero_credencial,
                "evento": self.pedido.evento.nome if self.pedido.evento else "Geral",
                "solicitante": self.pedido.solicitante.nome_completo,
                "doc": self.pedido.solicitante.numero_bi,
                "tipo": self.pedido.tipo_credencial.nome,
                "validade": self.data_validade.strftime("%d/%m/%Y") if self.data_validade else "N/A",
                "verificacao": self.codigo_verificacao
            }
            
            qr = qrcode.QRCode(
                version=None, # Auto
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=2,
            )
            qr.add_data(json.dumps(payload))
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')

            filename = f'qr_{self.numero_credencial}.png'
            self.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)

    def esta_valida(self):
        """Verifica se a credencial é válida"""
        hoje = date.today()
        return (
                self.status in ['emitida', 'ativa'] and
                not self.bloqueio_emergencia and
                self.data_validade >= hoje
        )

    def verificar_offline(self, codigo):
        """Verifica código offline"""
        return self.codigo_offline == codigo and self.esta_valida()

    def registrar_uso(self, latitude=None, longitude=None):
        """Registra uso da credencial"""
        AuditoriaCredencial.objects.create(
            acao='uso',
            credencial=self,
            detalhes={
                'latitude': latitude,
                'longitude': longitude,
                'data_hora': timezone.now().isoformat()
            }
        )


class CredencialFuncionario(models.Model):
    """Credencial especial para funcionários do STAE"""
    funcionario = models.ForeignKey('recursoshumanos.Funcionario', on_delete=models.CASCADE, related_name='credenciais')
    tipo_credencial = models.ForeignKey(TipoCredencial, on_delete=models.PROTECT)
    modelo = models.ForeignKey(ModeloCredencial, on_delete=models.PROTECT)

    # Identificação
    numero_credencial = models.CharField(max_length=50, unique=True)
    data_emissao = models.DateTimeField(auto_now_add=True)
    data_validade = models.DateField()

    # Códigos
    codigo_verificacao = models.CharField(max_length=100, unique=True, blank=True)
    codigo_offline = models.CharField(max_length=50, unique=True, blank=True)
    qr_code = models.ImageField(upload_to='credenciais_funcionarios/qr_codes/', blank=True, null=True)

    # Status
    ativa = models.BooleanField(default=True)
    emitida_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = "Credencial de Funcionário"
        verbose_name_plural = "Credenciais de Funcionários"

    def __str__(self):
        return f"Credencial Funcionário {self.numero_credencial}"

    def save(self, *args, **kwargs):
        if not self.codigo_verificacao:
            self.codigo_verificacao = self.gerar_codigo_verificacao()
        if not self.codigo_offline:
            self.codigo_offline = self.gerar_codigo_offline()
        super().save(*args, **kwargs)

    def gerar_codigo_verificacao(self):
        import uuid
        return str(uuid.uuid4())

    def gerar_codigo_offline(self):
        import secrets
        return f"FUNC-{self.numero_credencial}-{secrets.token_hex(3).upper()}"


class AuditoriaCredencial(models.Model):
    """Auditoria de ações no sistema de credenciais"""
    TIPO_ACAO = [
        ('criacao', 'Criação'),
        ('edicao', 'Edição'),
        ('exclusao', 'Exclusão'),
        ('validacao', 'Validação'),
        ('analise', 'Análise'),
        ('emissao', 'Emissão'),
        ('rejeicao', 'Rejeição'),
        ('verificacao', 'Verificação'),
        ('uso', 'Uso'),
        ('bloqueio', 'Bloqueio'),
        ('desbloqueio', 'Desbloqueio'),
        ('download', 'Download'),
    ]

    acao = models.CharField(max_length=20, choices=TIPO_ACAO)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    # Relações opcionais
    solicitante = models.ForeignKey(Solicitante, on_delete=models.SET_NULL, null=True, blank=True)
    pedido = models.ForeignKey(PedidoCredencial, on_delete=models.SET_NULL, null=True, blank=True)
    credencial = models.ForeignKey(CredencialEmitida, on_delete=models.SET_NULL, null=True, blank=True)

    # Detalhes
    detalhes = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    # Timestamp
    data_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Auditoria de Credencial"
        verbose_name_plural = "Auditoria de Credenciais"
        ordering = ['-data_hora']

    def __str__(self):
        return f"{self.get_acao_display()} - {self.data_hora.strftime('%Y-%m-%d %H:%M')}"

    @classmethod
    def registrar(cls, acao, **kwargs):
        """Método para registrar ações de auditoria"""
        data = {
            'acao': acao,
            'usuario': kwargs.get('usuario'),
            'solicitante': kwargs.get('solicitante'),
            'pedido': kwargs.get('pedido'),
            'credencial': kwargs.get('credencial'),
            'detalhes': kwargs.get('detalhes', {}),
        }

        # Adicionar informações da requisição se disponível
        request = kwargs.get('request')
        if request:
            data['ip_address'] = request.META.get('REMOTE_ADDR')
            data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')

        return cls.objects.create(**data)


class ConfiguracaoEmergencia(models.Model):
    """Configuração para bloqueios de emergência"""
    TIPO_BLOQUEIO = [
        ('total', 'Bloqueio Total'),
        ('evento', 'Por Evento'),
        ('tipo_credencial', 'Por Tipo de Credencial'),
        ('provincia', 'Por Província'),
    ]

    nome = models.CharField(max_length=200)
    tipo_bloqueio = models.CharField(max_length=20, choices=TIPO_BLOQUEIO)

    # Filtros específicos
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, null=True, blank=True)
    tipo_credencial = models.ForeignKey(TipoCredencial, on_delete=models.CASCADE, null=True, blank=True)
    provincia = models.CharField(max_length=100, blank=True)

    # Configuração
    motivo = models.TextField()
    ativo = models.BooleanField(default=False)
    data_ativacao = models.DateTimeField(null=True, blank=True)
    data_desativacao = models.DateTimeField(null=True, blank=True)

    # Histórico
    ativado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='bloqueios_ativados')
    credenciais_afetadas = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Configuração de Emergência"
        verbose_name_plural = "Configurações de Emergência"

    def __str__(self):
        return f"{self.nome} ({'Ativo' if self.ativo else 'Inativo'})"

    def ativar(self, usuario):
        """Ativa o bloqueio de emergência"""
        from django.db.models import Q

        # Construir filtro baseado no tipo
        filtro = Q()
        if self.tipo_bloqueio == 'evento' and self.evento:
            filtro = Q(pedido__evento=self.evento)
        elif self.tipo_bloqueio == 'tipo_credencial' and self.tipo_credencial:
            filtro = Q(pedido__tipo_credencial=self.tipo_credencial)
        elif self.tipo_bloqueio == 'provincia' and self.provincia:
            filtro = Q(pedido__solicitante__provincia=self.provincia)

        # Aplicar bloqueio
        credenciais = CredencialEmitida.objects.filter(
            filtro,
            status__in=['emitida', 'ativa']
        )

        afetadas = credenciais.count()
        credenciais.update(bloqueio_emergencia=True)

        # Atualizar configuração
        self.ativo = True
        self.data_ativacao = timezone.now()
        self.ativado_por = usuario
        self.credenciais_afetadas = afetadas
        self.save()

        # Registrar auditoria
        AuditoriaCredencial.registrar(
            acao='bloqueio',
            usuario=usuario,
            detalhes={
                'configuracao': self.nome,
                'tipo': self.tipo_bloqueio,
                'afetadas': afetadas
            }
        )

        return afetadas

    def desativar(self, usuario):
        """Desativa o bloqueio de emergência"""
        from django.db.models import Q

        # Construir filtro
        filtro = Q()
        if self.tipo_bloqueio == 'evento' and self.evento:
            filtro = Q(pedido__evento=self.evento)
        elif self.tipo_bloqueio == 'tipo_credencial' and self.tipo_credencial:
            filtro = Q(pedido__tipo_credencial=self.tipo_credencial)
        elif self.tipo_bloqueio == 'provincia' and self.provincia:
            filtro = Q(pedido__solicitante__provincia=self.provincia)

        # Remover bloqueio
        CredencialEmitida.objects.filter(filtro).update(bloqueio_emergencia=False)

        # Atualizar configuração
        self.ativo = False
        self.data_desativacao = timezone.now()
        self.save()

        # Registrar auditoria
        AuditoriaCredencial.registrar(
            acao='desbloqueio',
            usuario=usuario,
            detalhes={'configuracao': self.nome}
        )


class ConfiguracaoCredenciais(models.Model):
    """Configurações gerais do sistema de credenciais"""
    chave = models.CharField(max_length=100, unique=True)
    valor = models.TextField()
    descricao = models.TextField(blank=True)
    tipo = models.CharField(max_length=50, default='texto',
                            choices=[('texto', 'Texto'), ('numero', 'Número'),
                                     ('booleano', 'Booleano'), ('json', 'JSON')])
    categoria = models.CharField(max_length=50, default='geral')
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuração do Sistema"
        verbose_name_plural = "Configurações do Sistema"
        ordering = ['categoria', 'chave']

    def __str__(self):
        return f"{self.chave}: {self.valor[:50]}..."

    def get_valor_formatado(self):
        """Retorna o valor no tipo correto"""
        if self.tipo == 'numero':
            try:
                return int(self.valor)
            except:
                try:
                    return float(self.valor)
                except:
                    return 0
        elif self.tipo == 'booleano':
            return self.valor.lower() in ['true', '1', 'yes', 'sim', 'verdadeiro']
        elif self.tipo == 'json':
            try:
                import json
                return json.loads(self.valor)
            except:
                return self.valor
        else:
            return self.valor

    @classmethod
    def get_config(cls, chave, default=None):
        """Obtém uma configuração pelo nome"""
        try:
            config = cls.objects.get(chave=chave, ativo=True)
            return config.get_valor_formatado()
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_config(cls, chave, valor, descricao='', tipo='texto', categoria='geral'):
        """Define uma configuração"""
        config, created = cls.objects.update_or_create(
            chave=chave,
            defaults={
                'valor': str(valor),
                'descricao': descricao,
                'tipo': tipo,
                'categoria': categoria,
                'ativo': True
            }
        )
        return config


# =========================================================
# MÓDULO DE CERTIFICAÇÃO (Diplomas e Certificados)
# =========================================================

class ModeloDocumento(models.Model):
    """Templates base para certificados/diplomas"""
    nome = models.CharField(max_length=100) # Ex: Padrão STAE, Honra ao Mérito
    fundo_padrao = models.ImageField(upload_to='certificados/fundos/', blank=True, null=True)
    html_template = models.TextField(help_text="Usar {{ nome }}, {{ texto }}, {{ data }}, {{ assinaturas }}", default="<div class='certificado'>...</div>")
    ativo = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nome

class ProjetoCertificacao(models.Model):
    """Um lote de certificados a serem emitidos"""
    nome = models.CharField(max_length=200, help_text="Ex: Formação de Brigadistas 2024")
    modelo = models.ForeignKey(ModeloDocumento, on_delete=models.PROTECT)
    evento = models.ForeignKey(Evento, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Personalização
    titulo = models.CharField(max_length=200, default="CERTIFICADO")
    entidade_emissora = models.CharField(
        max_length=10, 
        choices=[('stae','STAE'), ('cne','CNE')], 
        default='stae',
        verbose_name="Entidade Emissora (Cabeçalho)"
    )
    texto_corpo = models.TextField(default="Certificamos que {{ nome }} participou com êxito...", help_text="Pode usar variáveis dinâmicas")
    data_extenso = models.CharField(max_length=200, blank=True, help_text="Ex: Maputo, 10 de Janeiro de 2025")
    
    # Assinaturas
    nome_assinatura_1 = models.CharField(max_length=100, blank=True)
    cargo_assinatura_1 = models.CharField(max_length=100, blank=True)
    nome_assinatura_2 = models.CharField(max_length=100, blank=True)
    cargo_assinatura_2 = models.CharField(max_length=100, blank=True)
    
    fundo_personalizado = models.ImageField(upload_to='certificados/projetos/', blank=True, null=True)
    
    status = models.CharField(max_length=20, default='rascunho', choices=[('rascunho', 'Rascunho'), ('aprovado', 'Aprovado')])
    
    created_at = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.nome} ({self.status})"

class DocumentoEmitido(models.Model):
    projeto = models.ForeignKey(ProjetoCertificacao, on_delete=models.CASCADE, related_name='documentos')
    nome_beneficiario = models.CharField(max_length=200)
    detalhe_extra = models.CharField(max_length=200, blank=True) # Ex: "Com distinção"
    
    codigo_validacao = models.CharField(max_length=50, unique=True, blank=True)
    data_emissao = models.DateTimeField(auto_now_add=True)
    
    # Arquivo gerado (opcional, ou gerado on-fly)
    # arquivo = models.FileField(...)
    
    def save(self, *args, **kwargs):
        if not self.codigo_validacao:
            import uuid
            self.codigo_validacao = str(uuid.uuid4())[:12].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nome_beneficiario} - {self.projeto.nome}"