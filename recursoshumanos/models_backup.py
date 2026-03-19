# recursoshumanos/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, datetime
import os
import hashlib
import qrcode
from io import BytesIO
from django.core.files import File


class Sector(models.Model):
    codigo = models.CharField(max_length=10, unique=True)
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    direcao = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subsectores')
    chefe = models.ForeignKey('Funcionario', on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='sector_chefiado')
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Setor'
        verbose_name_plural = 'Setores'
        ordering = ['codigo']

    def __str__(self):
        return f"{self.codigo} - {self.nome}"


class Funcionario(models.Model):
    FUNCAO_CHOICES = [
        ('director', 'Director'),
        ('chefe', 'Chefe de Departamento'),
        ('coordenador', 'Coordenador'),
        ('tecnico', 'Técnico'),
        ('assistente', 'Assistente'),
        ('auxiliar', 'Auxiliar'),
        ('estagiario', 'Estagiário'),
        ('outro', 'Outro'),
    ]

    ESTADO_CIVIL_CHOICES = [
        ('solteiro', 'Solteiro(a)'),
        ('casado', 'Casado(a)'),
        ('divorciado', 'Divorciado(a)'),
        ('viuvo', 'Viúvo(a)'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='funcionario')
    numero_identificacao = models.CharField(max_length=20, unique=True)
    nome_completo = models.CharField(max_length=200)
    data_nascimento = models.DateField()
    genero = models.CharField(max_length=10, choices=[('M', 'Masculino'), ('F', 'Feminino')])
    estado_civil = models.CharField(max_length=20, choices=ESTADO_CIVIL_CHOICES)
    nif = models.CharField(max_length=20, blank=True)
    niss = models.CharField(max_length=20, blank=True)

    sector = models.ForeignKey(Sector, on_delete=models.SET_NULL, null=True, related_name='funcionarios')
    funcao = models.CharField(max_length=50, choices=FUNCAO_CHOICES)
    data_admissao = models.DateField()
    data_saida = models.DateField(null=True, blank=True)

    # Contactos
    telefone = models.CharField(max_length=15)
    email_pessoal = models.EmailField(blank=True)
    endereco = models.TextField()

    # Informações bancárias
    banco = models.CharField(max_length=100, blank=True)
    numero_conta = models.CharField(max_length=50, blank=True)
    nib = models.CharField(max_length=25, blank=True)

    # Sistema de presença/QR Code
    foto = models.ImageField(upload_to='funcionarios/fotos/', null=True, blank=True)
    qr_code = models.ImageField(upload_to='funcionarios/qrcodes/', null=True, blank=True)
    qr_code_hash = models.CharField(max_length=64, blank=True, unique=True)
    data_emissao_cartao = models.DateField(null=True, blank=True)
    data_validade_cartao = models.DateField(null=True, blank=True)

    # Status
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'
        ordering = ['nome_completo']

    def __str__(self):
        return f"{self.nome_completo} ({self.numero_identificacao})"

    def idade(self):
        hoje = date.today()
        return hoje.year - self.data_nascimento.year - (
                    (hoje.month, hoje.day) < (self.data_nascimento.month, self.data_nascimento.day))

    def tempo_servico(self):
        hoje = date.today()
        return hoje.year - self.data_admissao.year - (
                    (hoje.month, hoje.day) < (self.data_admissao.month, self.data_admissao.day))

    def gerar_qr_code(self):
        """Gera QR code único para o funcionário"""
        import qrcode

        # Dados únicos
        dados = f"STAE|{self.id}|{self.numero_identificacao}|{hashlib.sha256(str(self.id).encode()).hexdigest()[:10]}"
        self.qr_code_hash = hashlib.sha256(dados.encode()).hexdigest()

        # Gerar QR
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(dados)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        # Salvar imagem
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        self.qr_code.save(f'qr_{self.numero_identificacao}.png', File(buffer), save=False)
        self.save()

    def get_chefe_imediato(self):
        """Retorna o chefe do setor do funcionário"""
        try:
            if self.sector and self.sector.chefe:
                return self.sector.chefe
            # Se não houver chefe definido, busca funcionário com função de chefia no setor
            return Funcionario.objects.filter(
                sector=self.sector,
                funcao__in=['chefe', 'director', 'coordenador']
            ).exclude(id=self.id).first()
        except:
            return None


class Competencia(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    peso = models.FloatField(default=1.0)  # Peso na avaliação
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Competência'
        verbose_name_plural = 'Competências'

    def __str__(self):
        return self.nome


class AvaliacaoDesempenho(models.Model):
    CLASSIFICACAO_CHOICES = [
        ('Excelente', 'Excelente'),
        ('Bom', 'Bom'),
        ('Satisfatório', 'Satisfatório'),
        ('Regular', 'Regular'),
        ('Insuficiente', 'Insuficiente'),
    ]

    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='avaliacoes')
    avaliado_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='avaliacoes_realizadas')
    periodo = models.CharField(max_length=50)  # Ex: "2024", "1º Trimestre 2024"

    # Notas
    nota_final_geral = models.FloatField(default=0)
    classificacao_final = models.CharField(max_length=20, choices=CLASSIFICACAO_CHOICES)

    # Detalhes
    observacoes = models.TextField(blank=True)
    pontos_fortes = models.TextField(blank=True)
    areas_melhoria = models.TextField(blank=True)

    # Controle
    data_avaliacao = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='concluido', choices=[
        ('pendente', 'Pendente'),
        ('em_avaliacao', 'Em Avaliação'),
        ('concluido', 'Concluído'),
        ('revisao', 'Em Revisão'),
    ])

    class Meta:
        verbose_name = 'Avaliação de Desempenho'
        verbose_name_plural = 'Avaliações de Desempenho'
        ordering = ['-data_avaliacao']

    def __str__(self):
        return f"Avaliação de {self.funcionario.nome_completo} - {self.periodo}"


class CompetenciaAvaliada(models.Model):
    avaliacao = models.ForeignKey(AvaliacaoDesempenho, on_delete=models.CASCADE, related_name='competencias_avaliadas')
    competencia = models.ForeignKey(Competencia, on_delete=models.CASCADE)
    pontuacao = models.IntegerField(default=0)  # 1-5
    observacao = models.TextField(blank=True)

    class Meta:
        unique_together = ['avaliacao', 'competencia']


class Licenca(models.Model):
    TIPO_CHOICES = [
        ('ferias', 'Férias'),
        ('maternidade', 'Licença de Maternidade'),
        ('paternidade', 'Licença de Paternidade'),
        ('doenca', 'Licença por Doença'),
        ('assuntos_particulares', 'Assuntos Particulares'),
        ('outro', 'Outro'),
    ]

    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aguardando_chefe', 'Aguardando Parecer do Chefe'),
        ('aguardando_diretor', 'Aguardando Autorização do Diretor'),
        ('aprovado', 'Aprovado'),
        ('rejeitado', 'Rejeitado'),
        ('cancelado', 'Cancelado'),
        ('concluido', 'Concluído'),
    ]

    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='licencas')
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, default='ferias')

    # Período
    data_inicio = models.DateField()
    data_fim = models.DateField()
    dias_utilizados = models.IntegerField()

    # Detalhes
    motivo = models.TextField()
    local_ferias = models.CharField(max_length=200, blank=True)
    contacto_emergencia = models.CharField(max_length=100, blank=True)

    # Fluxo de aprovação
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pendente')
    fluxo_aprovacao = models.CharField(max_length=20, default='chefia', choices=[
        ('direto', 'Direto RH'),
        ('chefia', 'Via Chefia')
    ])

    # Parecer da chefia
    parecer_chefe = models.TextField(blank=True)
    status_chefia = models.CharField(max_length=20, default='pendente', choices=[
        ('pendente', 'Pendente'),
        ('favoravel', 'Favorável'),
        ('desfavoravel', 'Desfavorável'),
        ('com_reservas', 'Com Reservas')
    ])
    data_parecer_chefe = models.DateTimeField(null=True, blank=True)
    chefe_aprovador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='licencas_aprovadas_chefe')

    # Autorização diretor/RH
    parecer_diretor = models.TextField(blank=True)
    data_parecer_diretor = models.DateTimeField(null=True, blank=True)
    diretor_aprovador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name='licencas_autorizadas')

    # Documento gerado
    documento_ferias = models.FileField(upload_to='documentos/ferias/', null=True, blank=True)
    hash_documento = models.CharField(max_length=64, blank=True)

    # Controle
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Licença'
        verbose_name_plural = 'Licenças'
        ordering = ['-data_inicio']

    def __str__(self):
        return f"Licença de {self.funcionario.nome_completo} - {self.get_tipo_display()}"

    def save(self, *args, **kwargs):
        # Calcular dias utilizados se não definido
        if not self.dias_utilizados and self.data_inicio and self.data_fim:
            delta = self.data_fim - self.data_inicio
            self.dias_utilizados = delta.days + 1
        super().save(*args, **kwargs)


class SaldoFerias(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='saldo_ferias')
    ano = models.IntegerField()
    dias_disponiveis = models.IntegerField(default=22)
    dias_gozados = models.IntegerField(default=0)
    dias_saldo = models.IntegerField(default=22)
    dias_vencimento_proximo = models.IntegerField(default=0)  # Dias prestes a vencer

    # Controle
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Saldo de Férias'
        verbose_name_plural = 'Saldos de Férias'
        unique_together = ['funcionario', 'ano']

    def __str__(self):
        return f"Saldo {self.ano} - {self.funcionario.nome_completo}: {self.dias_saldo} dias"

    def atualizar_saldo(self):
        self.dias_saldo = self.dias_disponiveis - self.dias_gozados
        self.save()


class Promocao(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='promocoes')
    data_promocao = models.DateField()

    # Cargos
    cargo_anterior = models.CharField(max_length=100)
    cargo_atual = models.CharField(max_length=100)
    nivel_anterior = models.CharField(max_length=50)
    nivel_atual = models.CharField(max_length=50)

    # Remuneração
    salario_anterior = models.DecimalField(max_digits=10, decimal_places=2)
    salario_atual = models.DecimalField(max_digits=10, decimal_places=2)

    # Detalhes
    motivo = models.TextField()
    observacoes = models.TextField(blank=True)

    # Aprovação
    aprovado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    data_aprovacao = models.DateTimeField(null=True, blank=True)

    # Controle
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Promoção'
        verbose_name_plural = 'Promoções'
        ordering = ['-data_promocao']

    def __str__(self):
        return f"Promoção de {self.funcionario.nome_completo} - {self.data_promocao}"


class RegistroPresenca(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='registros_presenca')
    data_hora = models.DateTimeField(auto_now_add=True)
    tipo = models.CharField(max_length=10, choices=[
        ('entrada', 'Entrada'),
        ('saida', 'Saída'),
        ('intervalo', 'Intervalo'),
        ('retorno', 'Retorno de Intervalo')
    ])
    metodo = models.CharField(max_length=20, choices=[
        ('qr_code', 'QR Code'),
        ('manual', 'Manual RH'),
        ('biometria', 'Biometria'),
        ('sistema', 'Sistema')
    ], default='qr_code')

    # Localização
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # Controle
    observacoes = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    dispositivo = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = 'Registro de Presença'
        verbose_name_plural = 'Registros de Presença'
        ordering = ['-data_hora']
        indexes = [
            models.Index(fields=['funcionario', 'data_hora']),
        ]

    def __str__(self):
        return f"{self.funcionario.nome_completo} - {self.get_tipo_display()} - {self.data_hora.strftime('%d/%m/%Y %H:%M')}"


# ========== SISTEMA DE COMUNICAÇÃO INTERNA ==========

class CanalComunicacao(models.Model):
    TIPO_CHOICES = [
        ('departamento', 'Departamento'),
        ('projeto', 'Projeto'),
        ('grupo', 'Grupo de Trabalho'),
        ('geral', 'Geral'),
    ]

    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='grupo')
    setor = models.ForeignKey(Sector, on_delete=models.CASCADE, null=True, blank=True)

    # Membros
    membros = models.ManyToManyField(User, related_name='canais', blank=True)
    enviar_para_todos = models.BooleanField(default=False)  # Canal geral para todos

    # Controle
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    arquivado = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Canal de Comunicação'
        verbose_name_plural = 'Canais de Comunicação'
        ordering = ['-data_criacao']

    def __str__(self):
        return f"{self.nome} ({self.get_tipo_display()})"


class Mensagem(models.Model):
    canal = models.ForeignKey(CanalComunicacao, on_delete=models.CASCADE, related_name='mensagens')
    remetente = models.ForeignKey(User, on_delete=models.CASCADE)
    conteudo = models.TextField()

    # Anexos
    arquivo = models.FileField(upload_to='comunicacao/arquivos/', null=True, blank=True)
    nome_arquivo = models.CharField(max_length=255, blank=True)

    # Controle
    data_envio = models.DateTimeField(auto_now_add=True)
    editada = models.BooleanField(default=False)
    data_edicao = models.DateTimeField(null=True, blank=True)

    # Para respostas
    resposta_para = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='respostas')

    class Meta:
        ordering = ['data_envio']

    def __str__(self):
        return f"{self.remetente.username}: {self.conteudo[:50]}..."

    def get_extensao_arquivo(self):
        if self.arquivo:
            return os.path.splitext(self.arquivo.name)[1].lower()
        return ''


class NotificacaoSistema(models.Model):
    TIPO_CHOICES = [
        ('licenca_submetida', 'Licença Submetida'),
        ('licenca_parecer_chefe', 'Parecer do Chefe na Licença'),
        ('licenca_autorizada', 'Licença Autorizada'),
        ('licenca_rejeitada', 'Licença Rejeitada'),
        ('avaliacao_realizada', 'Avaliação Realizada'),
        ('documento_compartilhado', 'Documento Compartilhado'),
        ('mensagem_recebida', 'Nova Mensagem'),
        ('promocao_concedida', 'Promoção Concedida'),
        ('evento_proximo', 'Evento Próximo'),
        ('lembrete_ferias', 'Lembrete de Férias'),
        ('sistema', 'Atualização do Sistema'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificacoes_sistema')
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    titulo = models.CharField(max_length=200)
    mensagem = models.TextField()

    # Link para ação
    link_url = models.CharField(max_length=500, blank=True)
    link_texto = models.CharField(max_length=100, blank=True)

    # Status
    lida = models.BooleanField(default=False)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_leitura = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-data_criacao']
        indexes = [
            models.Index(fields=['usuario', 'lida', 'data_criacao']),
        ]

    def __str__(self):
        return f"{self.usuario.username} - {self.get_tipo_display()}"


class ConfiguracaoNotificacao(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='config_notificacoes')

    # Tipos de notificações para mostrar
    mostrar_licencas = models.BooleanField(default=True)
    mostrar_avaliacoes = models.BooleanField(default=True)
    mostrar_documentos = models.BooleanField(default=True)
    mostrar_mensagens = models.BooleanField(default=True)
    mostrar_sistema = models.BooleanField(default=True)

    # Som
    som_notificacoes = models.BooleanField(default=True)

    data_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Configurações de {self.usuario.username}"


class DocumentoInstitucional(models.Model):
    TIPO_CHOICES = [
        ('relatorio', 'Relatório'),
        ('oficio', 'Ofício'),
        ('circular', 'Circular'),
        ('memorando', 'Memorando'),
        ('ata', 'Ata'),
        ('portaria', 'Portaria'),
        ('instrucao', 'Instrução de Serviço'),
        ('outro', 'Outro'),
    ]

    STATUS_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('revisao', 'Em Revisão'),
        ('aprovado', 'Aprovado'),
        ('publicado', 'Publicado'),
        ('arquivado', 'Arquivado'),
    ]

    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='relatorio')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='rascunho')

    # Arquivo
    arquivo = models.FileField(upload_to='documentos/institucionais/')
    formato = models.CharField(max_length=10, blank=True)
    tamanho = models.BigIntegerField(default=0)  # Em bytes

    # Metadados
    numero = models.CharField(max_length=50, blank=True)
    data_documento = models.DateField(default=date.today)
    data_publicacao = models.DateTimeField(null=True, blank=True)

    # Autoria
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='documentos_criados')
    revisado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='documentos_revisados')
    aprovado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='documentos_aprovados')

    # Destinatários
    publico = models.BooleanField(default=False)
    setores_destino = models.ManyToManyField(Sector, blank=True)
    funcionarios_destino = models.ManyToManyField(Funcionario, blank=True)

    # Controle
    versao = models.IntegerField(default=1)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Documento Institucional'
        verbose_name_plural = 'Documentos Institucionais'
        ordering = ['-data_documento', '-data_criacao']

    def __str__(self):
        return f"{self.titulo} ({self.get_tipo_display()})"

    def save(self, *args, **kwargs):
        if self.arquivo:
            self.formato = os.path.splitext(self.arquivo.name)[1].lower().replace('.', '')
            self.tamanho = self.arquivo.size
        super().save(*args, **kwargs)

    def tamanho_formatado(self):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.tamanho < 1024.0:
                return f"{self.tamanho:.1f} {unit}"
            self.tamanho /= 1024.0
        return f"{self.tamanho:.1f} GB"


class RelatorioAtividade(models.Model):
    TIPO_CHOICES = [
        ('diario', 'Relatório Diário'),
        ('semanal', 'Relatório Semanal'),
        ('mensal', 'Relatório Mensal'),
        ('trimestral', 'Relatório Trimestral'),
        ('anual', 'Relatório Anual'),
        ('projeto', 'Relatório de Projeto'),
        ('auditoria', 'Relatório de Auditoria'),
        ('desempenho', 'Relatório de Desempenho'),
    ]

    titulo = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='mensal')
    descricao = models.TextField()

    # Período
    periodo_inicio = models.DateField()
    periodo_fim = models.DateField()

    # Conteúdo
    objetivos = models.TextField(blank=True)
    atividades_realizadas = models.TextField()
    resultados = models.TextField(blank=True)
    dificuldades = models.TextField(blank=True)
    recomendacoes = models.TextField(blank=True)

    # Autoria
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    setor = models.ForeignKey(Sector, on_delete=models.SET_NULL, null=True)

    # Compartilhamento
    publico = models.BooleanField(default=False)
    compartilhar_com = models.ManyToManyField(User, related_name='relatorios_compartilhados', blank=True)

    # Arquivos
    arquivo_principal = models.FileField(upload_to='relatorios/', null=True, blank=True)
    anexos = models.FileField(upload_to='relatorios/anexos/', null=True, blank=True)

    # Controle
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    visualizacoes = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Relatório de Atividade'
        verbose_name_plural = 'Relatórios de Atividade'
        ordering = ['-periodo_inicio']

    def __str__(self):
        return f"{self.titulo} - {self.periodo_inicio} a {self.periodo_fim}"


class ConfiguracaoFerias(models.Model):
    dias_base_ferias = models.IntegerField(default=22)
    dias_maximo_acumulo = models.IntegerField(default=44)
    prazo_marcacao_ferias = models.IntegerField(default=30)  # Dias antes do vencimento
    tolerancia_entrada = models.IntegerField(default=15)  # Minutos de tolerância
    tolerancia_saida = models.IntegerField(default=15)  # Minutos de tolerância

    # Controle
    data_atualizacao = models.DateTimeField(auto_now=True)
    atualizado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = 'Configuração de Férias'
        verbose_name_plural = 'Configurações de Férias'

    def __str__(self):
        return "Configurações do Sistema de Férias"
class NotificacaoSistema(models.Model):
    """Modelo para notifica��es do sistema"""
    TIPO_CHOICES = [
        ('info', 'Informa��o'),
        ('aviso', 'Aviso'),
        ('alerta', 'Alerta'),
        ('sucesso', 'Sucesso'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='info')
    titulo = models.CharField(max_length=200)
    mensagem = models.TextField()
    lida = models.BooleanField(default=False)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_leitura = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Notifica��o do Sistema'
        verbose_name_plural = 'Notifica��es do Sistema'
        ordering = ['-data_criacao']
    
    def __str__(self):
        return f"{self.get_tipo_display()}: {self.titulo}"


class ConfiguracaoNotificacao(models.Model):
    """Configura��es de notifica��o por usu�rio"""
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    receber_email = models.BooleanField(default=True)
    receber_push = models.BooleanField(default=True)
    notificar_licencas = models.BooleanField(default=True)
    notificar_avaliacoes = models.BooleanField(default=True)
    notificar_presencas = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Configura��o de Notifica��o'
        verbose_name_plural = 'Configura��es de Notifica��o'
    
    def __str__(self):
        return f"Configura��es de {self.usuario.username}"

