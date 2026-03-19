# recursoshumanos/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Max
from django.urls import reverse
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
    data_criacao = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Setor'
        verbose_name_plural = 'Setores'
        ordering = ['codigo']

    def __str__(self):
        return f"{self.codigo} - {self.nome}"


from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, datetime
import os
import hashlib
import json
import qrcode
from io import BytesIO
from django.core.files import File


class Funcionario(models.Model):
    FUNCAO_CHOICES = [
        ('director', 'Director'),
        ('chefe', 'Chefe de Departamento'),
        ('coordenador', 'Coordenador'),
        ('tecnico', 'Técnico Profissional'),
        ('tecnico_superior', 'Técnico Superior'),
        ('motorista', 'Motorista'),
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

    GENERO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Feminino'),
    ]

    BANCO_CHOICES = [
        ('BIM', 'Banco Internacional de Moçambique (BIM)'),
        ('BCI', 'Banco Comercial e de Investimentos (BCI)'),
        ('Standard', 'Standard Bank'),
        ('Barclays', 'Barclays Bank'),
        ('Millennium', 'Millennium BIM'),
        ('Moza', 'Moza Banco'),
        ('UBA', 'United Bank for Africa (UBA)'),
        ('Ecobank', 'Ecobank'),
        ('outro', 'Outro'),
    ]

    TIPO_CONTA_CHOICES = [
        ('poupanca', 'Conta Poupança'),
        ('corrente', 'Conta Corrente'),
        ('salario', 'Conta Salário'),
    ]

    # ========== RELAÇÃO COM USER (OPCIONAL) ==========
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='funcionario',
        verbose_name="Usuário do Sistema"
    )

    # ========== NÚMERO AUTOMÁTICO ==========
    numero_identificacao = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        verbose_name="Número de Funcionário"
    )

    # ========== DADOS PESSOAIS ==========
    nome_completo = models.CharField(max_length=200, verbose_name="Nome Completo")
    data_nascimento = models.DateField(verbose_name="Data de Nascimento")
    genero = models.CharField(max_length=10, choices=GENERO_CHOICES, verbose_name="Gênero")
    estado_civil = models.CharField(max_length=20, choices=ESTADO_CIVIL_CHOICES, verbose_name="Estado Civil")

    # ========== IDENTIFICAÇÃO OFICIAL (MOÇAMBIQUE) ==========
    numero_bi = models.CharField(max_length=20, blank=True, verbose_name="Número do BI")
    data_emissao_bi = models.DateField(null=True, blank=True, verbose_name="Data de Emissão do BI")
    local_emissao_bi = models.CharField(max_length=100, blank=True, verbose_name="Local de Emissão do BI")

    # NUIT (Número Único de Identificação Tributária)
    nuit = models.CharField(max_length=12, verbose_name="NUIT")
    data_emissao_nuit = models.DateField(null=True, blank=True, verbose_name="Data de Emissão do NUIT")

    # NISS (Número de Identificação da Segurança Social)
    niss = models.CharField(max_length=20, verbose_name="NISS")
    data_inscricao_inss = models.DateField(null=True, blank=True, verbose_name="Data de Inscrição no INSS")

    # ========== DADOS PROFISSIONAIS ==========
    sector = models.ForeignKey('Sector', on_delete=models.SET_NULL, null=True, related_name='funcionarios',
                               verbose_name="Setor")
    funcao = models.CharField(max_length=50, choices=FUNCAO_CHOICES, verbose_name="Função")
    data_admissao = models.DateField(verbose_name="Data de Admissão")
    data_saida = models.DateField(null=True, blank=True, verbose_name="Data de Saída")

    # ========== CONTACTOS ==========
    telefone = models.CharField(max_length=15, verbose_name="Telefone")
    telefone_alternativo = models.CharField(max_length=15, blank=True, verbose_name="Telefone Alternativo")
    email_pessoal = models.EmailField(blank=True, verbose_name="Email Pessoal")
    email_institucional = models.EmailField(blank=True, verbose_name="Email Institucional")
    endereco = models.TextField(verbose_name="Endereço Residencial")
    bairro = models.CharField(max_length=100, blank=True, verbose_name="Bairro")
    distrito = models.CharField(max_length=100, blank=True, verbose_name="Distrito")
    provincia = models.CharField(max_length=100, blank=True, verbose_name="Província")

    # ========== DADOS BANCÁRIOS (MOÇAMBIQUE) ==========
    banco = models.CharField(max_length=100, verbose_name="Banco", choices=BANCO_CHOICES)
    nome_banco_outro = models.CharField(max_length=100, blank=True, verbose_name="Nome do Banco (se outro)")
    tipo_conta = models.CharField(max_length=20, verbose_name="Tipo de Conta", choices=TIPO_CONTA_CHOICES,
                                  default='corrente')
    numero_conta = models.CharField(max_length=50, verbose_name="Número da Conta")
    nib = models.CharField(max_length=25, verbose_name="Número de Identificação Bancária (NIB)")
    nub = models.CharField(max_length=25, blank=True, verbose_name="Número Único Bancário (NUB)")

    # ========== SISTEMA DE QR CODE ==========
    foto = models.ImageField(upload_to='funcionarios/fotos/', null=True, blank=True, verbose_name="Foto")
    foto_webcam = models.TextField(blank=True, verbose_name="Foto da Webcam (Base64)")

    # QR CODE
    qr_code = models.ImageField(upload_to='funcionarios/qrcodes/', null=True, blank=True, verbose_name="QR Code")
    qr_code_hash = models.CharField(max_length=64, blank=True, unique=True, verbose_name="Hash do QR Code")
    qr_code_data = models.JSONField(null=True, blank=True, verbose_name="Dados do QR Code")

    # Cartão de identificação
    data_emissao_cartao = models.DateField(null=True, blank=True, verbose_name="Data de Emissão do Cartão")
    data_validade_cartao = models.DateField(null=True, blank=True, verbose_name="Data de Validade do Cartão")
    numero_cartao = models.CharField(max_length=50, blank=True, verbose_name="Número do Cartão")

    # ========== STATUS ==========
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_criacao = models.DateTimeField(null=True, blank=True)
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")

    # ========== INFORMAÇÕES ADICIONAIS ==========
    nacionalidade = models.CharField(max_length=50, default='Moçambicana', verbose_name="Nacionalidade")
    naturalidade = models.CharField(max_length=100, blank=True, verbose_name="Naturalidade")
    nome_pai = models.CharField(max_length=200, blank=True, verbose_name="Nome do Pai")
    nome_mae = models.CharField(max_length=200, blank=True, verbose_name="Nome da Mãe")
    contacto_emergencia = models.CharField(max_length=100, blank=True, verbose_name="Contacto de Emergência")
    parentesco_emergencia = models.CharField(max_length=50, blank=True, verbose_name="Parentesco")

    class Meta:
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'
        ordering = ['numero_identificacao']
        indexes = [
            models.Index(fields=['numero_identificacao']),
            models.Index(fields=['nuit']),
            models.Index(fields=['qr_code_hash']),
            models.Index(fields=['ativo']),
        ]

    def __str__(self):
        return f"{self.nome_completo} ({self.numero_identificacao})"

    def save(self, *args, **kwargs):
        """Gera número automático se for novo funcionário"""
        is_new = self.pk is None

        if is_new and not self.numero_identificacao:
            self.numero_identificacao = self.gerar_proximo_numero()

        # Garante QR Code
        if is_new or not self.qr_code:
            self.gerar_qr_code()

        super().save(*args, **kwargs)

    def gerar_proximo_numero(self):
        """Gera próximo número de funcionário no formato STAE-YYYY-NNNN"""
        import datetime
        from django.db.models import Max
        from django.db import transaction

        ano_atual = datetime.datetime.now().year
        prefixo = f"STAE-{ano_atual}-"

        # Usa transação atômica para evitar números duplicados
        with transaction.atomic():
            # Encontra o último número deste ano
            ultimo_numero = Funcionario.objects.filter(
                numero_identificacao__startswith=prefixo
            ).aggregate(Max('numero_identificacao'))

            ultimo = ultimo_numero['numero_identificacao__max']

            if ultimo:
                try:
                    # Extrai número sequencial
                    numero_atual = int(ultimo.split('-')[-1])
                    proximo_numero = numero_atual + 1
                except (ValueError, IndexError):
                    proximo_numero = 1
            else:
                proximo_numero = 1

            # Formata com 4 dígitos
            return f"{prefixo}{proximo_numero:04d}"

    @classmethod
    def get_proximo_numero_preview(cls):
        """Retorna qual será o próximo número (para preview no formulário)"""
        return cls().gerar_proximo_numero()

    def gerar_qr_code(self):
        """Gera QR Code único com dados do funcionário"""
        try:
            import qrcode
            import json
            import hashlib
            from datetime import datetime
            from io import BytesIO
            from django.core.files import File

            # Dados para o QR Code
            qr_data = {
                "sistema": "STAE-MZ",
                "numero_funcionario": self.numero_identificacao,
                "nome": self.nome_completo,
                "nuit": self.nuit,
                "niss": self.niss,
                "setor": str(self.sector.codigo) if self.sector else "",
                "funcao": self.get_funcao_display(),
                "data_admissao": self.data_admissao.strftime('%d/%m/%Y') if self.data_admissao else "",
                "ativo": "SIM" if self.ativo else "NÃO",
                "timestamp": datetime.now().isoformat(),
                "versao": "1.0"
            }

            # Gerar hash único
            hash_input = f"{self.numero_identificacao}{self.nuit}{datetime.now().timestamp()}"
            self.qr_code_hash = hashlib.sha256(hash_input.encode()).hexdigest()

            # Adicionar hash aos dados
            qr_data["hash"] = self.qr_code_hash
            self.qr_code_data = qr_data

            # Gerar QR Code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )

            qr.add_data(json.dumps(qr_data, ensure_ascii=False))
            qr.make(fit=True)

            # Criar imagem
            img = qr.make_image(fill_color="black", back_color="white")

            # Salvar imagem
            buffer = BytesIO()
            img.save(buffer, format='PNG')

            # Nome do arquivo
            filename = f"qr_{self.numero_identificacao}.png"

            # Salvar no campo ImageField
            self.qr_code.save(filename, File(buffer), save=False)

            # Gerar número do cartão se não existir
            if not self.numero_cartao:
                self.numero_cartao = f"CART-{self.numero_identificacao}"

            # Data de emissão do cartão
            if not self.data_emissao_cartao:
                from datetime import date
                self.data_emissao_cartao = date.today()

            # Data de validade (2 anos)
            if not self.data_validade_cartao and self.data_emissao_cartao:
                from datetime import timedelta
                self.data_validade_cartao = self.data_emissao_cartao + timedelta(days=730)

            return True

        except Exception as e:
            print(f"Erro ao gerar QR Code: {str(e)}")
            return False

    def idade(self):
        """Calcula idade do funcionário"""
        from datetime import date
        hoje = date.today()
        idade = hoje.year - self.data_nascimento.year
        if (hoje.month, hoje.day) < (self.data_nascimento.month, self.data_nascimento.day):
            idade -= 1
        return idade

    def tempo_servico(self):
        """Calcula tempo de serviço"""
        from datetime import date
        if self.data_saida:
            fim = self.data_saida
        else:
            fim = date.today()

        anos = fim.year - self.data_admissao.year
        meses = fim.month - self.data_admissao.month

        if meses < 0:
            anos -= 1
            meses += 12

        return {"anos": anos, "meses": meses}

    def get_tempo_servico_display(self):
        """Retorna tempo de serviço formatado"""
        tempo = self.tempo_servico()
        return f"{tempo['anos']} anos e {tempo['meses']} meses"

    def get_banco_display_completo(self):
        """Retorna nome completo do banco"""
        if self.banco == 'outro' and self.nome_banco_outro:
            return self.nome_banco_outro
        return self.get_banco_display()

    def get_qr_code_url(self):
        """Retorna URL do QR Code"""
        if self.qr_code:
            return self.qr_code.url
        return None

    def cartao_valido(self):
        """Verifica se o cartão está válido"""
        from datetime import date
        if not self.data_validade_cartao:
            return False
        return self.data_validade_cartao >= date.today()

    def renovar_cartao(self):
        """Renova o cartão do funcionário"""
        from datetime import date, timedelta
        self.data_validade_cartao = date.today() + timedelta(days=730)
        self.gerar_qr_code()  # Regenera QR Code
        self.save()
        return True



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


# models.py
class Licenca(models.Model):
    TIPO_CHOICES = [
        ('ferias', 'Férias'),
        ('maternidade', 'Maternidade'),
        ('doenca', 'Doença'),
        ('assuntos_particulares', 'Assuntos Particulares'),
        ('formacao', 'Formação'),
        ('outro', 'Outro'),
    ]

    STATUS_CHOICES = [
        ('pendente', 'Pendente - Aguardando RH'),
        ('aguardando_chefe', 'Aguardando Parecer do Chefe'),
        ('aguardando_diretor', 'Aguardando Autorização do Diretor'),
        ('aprovado', 'Aprovado'),
        ('rejeitado', 'Rejeitado'),
    ]

    STATUS_CHEFIA_CHOICES = [
        ('favoravel', 'Favorável'),
        ('desfavoravel', 'Desfavorável'),
        ('pendente', 'Pendente'),
    ]

    # Relacionamentos
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='licencas')
    # rh_aprovador = models.ForeignKey(
    #     User,
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True,
    #     related_name='licencas_aprovadas_rh',
    #     verbose_name="RH que analisou"
    # )
    chefe_aprovador = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='licencas_aprovadas_chefe'
    )
    diretor_aprovador = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='licencas_aprovadas_diretor'
    )

    # Dados da licença
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    dias_utilizados = models.IntegerField()
    motivo = models.TextField(blank=True, null=True)
    local_ferias = models.CharField(max_length=200, blank=True, null=True)
    contacto_emergencia = models.CharField(max_length=100, blank=True, null=True)

    # Workflow e status
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pendente')
    status_chefia = models.CharField(max_length=50, choices=STATUS_CHEFIA_CHOICES, blank=True, null=True)

    # Pareceres
    observacoes_rh = models.TextField(blank=True, null=True, verbose_name="Observações do RH")
    parecer_chefe = models.TextField(blank=True, null=True)
    parecer_diretor = models.TextField(blank=True, null=True)

    # Ajustes do RH
    dias_autorizados_rh = models.IntegerField(null=True, blank=True, verbose_name="Dias autorizados pelo RH")

    # Documentação
    documento_ferias = models.FileField(upload_to='documentos_ferias/', blank=True, null=True)
    hash_documento = models.CharField(max_length=64, blank=True, null=True)

    # Fluxo de aprovação (para licenças complexas)
    fluxo_aprovacao = models.JSONField(blank=True, null=True, default=dict)

    # Timestamps
    data_criacao = models.DateTimeField(null=True, blank=True)

    data_atualizacao = models.DateTimeField(auto_now=True)
    data_analise_rh = models.DateTimeField(null=True, blank=True, verbose_name="Data análise RH")
    data_parecer_chefe = models.DateTimeField(null=True, blank=True)
    data_parecer_diretor = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-data_criacao']
        verbose_name = 'Licença'
        verbose_name_plural = 'Licenças'
        indexes = [
            models.Index(fields=['status', 'data_inicio']),
            models.Index(fields=['funcionario', 'data_inicio']),
        ]

    def __str__(self):
        return f"{self.funcionario.nome_completo} - {self.get_tipo_display()} ({self.data_inicio} a {self.data_fim})"

    def save(self, *args, **kwargs):
        # Calcular dias utilizados se não definido
        if not self.dias_utilizados and self.data_inicio and self.data_fim:
            self.dias_utilizados = (self.data_fim - self.data_inicio).days + 1

        # Se dias autorizados pelo RH não definido, usar dias utilizados
        if not self.dias_autorizados_rh:
            self.dias_autorizados_rh = self.dias_utilizados

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('recursoshumanos:detalhes_licenca', kwargs={'pk': self.pk})

    @property
    def esta_pendente(self):
        return self.status == 'pendente'

    @property
    def aguardando_chefe(self):
        return self.status == 'aguardando_chefe'

    @property
    def aguardando_diretor(self):
        return self.status == 'aguardando_diretor'

    @property
    def foi_aprovada(self):
        return self.status == 'aprovado'

    @property
    def foi_rejeitada(self):
        return self.status == 'rejeitado'

    @property
    def periodo_formatado(self):
        if self.data_inicio and self.data_fim:
            return f"{self.data_inicio.strftime('%d/%m/%Y')} - {self.data_fim.strftime('%d/%m/%Y')}"
        return ""

    @property
    def chefe_aprovador_nome(self):
        if self.chefe_aprovador:
            # Tentar obter nome do funcionário associado
            try:
                if hasattr(self.chefe_aprovador, 'funcionario'):
                    return self.chefe_aprovador.funcionario.nome_completo
            except Exception:
                pass
            return self.chefe_aprovador.get_full_name() or self.chefe_aprovador.username
        return ""

    def pode_ser_analisada_por(self, user):
        """Verifica se o usuário pode analisar esta licença"""
        from django.contrib.auth.models import Group

        # RH pode analisar se status é pendente
        if self.status == 'pendente':
            return user.is_staff or user.groups.filter(name='rh_staff').exists()

        # Chefe pode analisar se status é aguardando_chefe
        elif self.status == 'aguardando_chefe':
            try:
                funcionario_chefe = Funcionario.objects.get(user=user)
                return funcionario_chefe.funcao in ['chefe', 'coordenador', 'director'] and \
                    funcionario_chefe.sector == self.funcionario.sector
            except Funcionario.DoesNotExist:
                return False

        # Diretor pode analisar se status é aguardando_diretor
        elif self.status == 'aguardando_diretor':
            try:
                funcionario_diretor = Funcionario.objects.get(user=user)
                return funcionario_diretor.funcao == 'director' and \
                    funcionario_diretor.sector.direcao == self.funcionario.sector.direcao
            except Funcionario.DoesNotExist:
                return False

        return False


class SaldoFerias(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='saldos_ferias')
    ano = models.IntegerField()
    dias_disponiveis = models.IntegerField(default=22)
    dias_gozados = models.IntegerField(default=0)
    dias_saldo = models.IntegerField(default=22)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['funcionario', 'ano']
        verbose_name = 'Saldo de Férias'
        verbose_name_plural = 'Saldos de Férias'
        indexes = [
            models.Index(fields=['ano', 'dias_saldo']),
            models.Index(fields=['funcionario', 'ano']),
        ]

    def calcular_saldo(self):
        self.dias_saldo = self.dias_disponiveis - self.dias_gozados
        if self.dias_saldo < 0:
            self.dias_saldo = 0
        return self.dias_saldo

    def save(self, *args, **kwargs):
        self.calcular_saldo()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.funcionario.nome_completo} - {self.ano}: {self.dias_saldo} dias"

    def adicionar_dias_gozados(self, dias):
        """Adiciona dias gozados ao saldo"""
        self.dias_gozados += dias
        self.calcular_saldo()
        self.save()

    def tem_saldo_suficiente(self, dias_solicitados):
        """Verifica se tem saldo suficiente para os dias solicitados"""
        return self.dias_saldo >= dias_solicitados

    @classmethod
    def criar_ou_atualizar(cls, funcionario, ano, dias_gozados=0):
        """Cria ou atualiza saldo para um funcionário"""
        saldo, created = cls.objects.get_or_create(
            funcionario=funcionario,
            ano=ano,
            defaults={
                'dias_disponiveis': 22,
                'dias_gozados': dias_gozados,
                'dias_saldo': 22 - dias_gozados
            }
        )

        if not created:
            saldo.dias_gozados = dias_gozados
            saldo.calcular_saldo()
            saldo.save()

        return saldo


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
    data_criacao = models.DateTimeField(null=True, blank=True)

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

# recursoshumanos/models.py
# recursoshumanos/models.py - CORREÇÃO DO MODELO CanalComunicacao
class CanalComunicacao(models.Model):
    TIPO_CHOICES = [
        ('geral', 'Geral'),
        ('departamento', 'Departamento'),
        ('projeto', 'Projeto'),
        ('grupo', 'Grupo'),
        ('privado', 'Privado'),
        ('direto', 'Mensagem Direta'),
    ]

    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='grupo')
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   related_name='canais_criados')
    membros = models.ManyToManyField(User, related_name='canais_participantes', blank=True)
    enviar_para_todos = models.BooleanField(default=False, verbose_name="Público para todos")
    arquivado = models.BooleanField(default=False)
    data_criacao = models.DateTimeField(null=True, blank=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    # Campo para conversas diretas entre 2 pessoas
    eh_conversa_direta = models.BooleanField(default=False)

    class Meta:
        ordering = ['-data_atualizacao']
        verbose_name = 'Canal de Comunicação'
        verbose_name_plural = 'Canais de Comunicação'
        # REMOVA OU COMENTE A CONSTRAINT QUE USA ManyToManyField
        # constraints = [
        #     models.UniqueConstraint(
        #         fields=['eh_conversa_direta', 'membros'],  # ← 'membros' é ManyToManyField
        #         condition=models.Q(eh_conversa_direta=True),
        #         name='unique_direct_chat'
        #     )
        # ]

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        # Para conversas diretas, nome automático
        if self.eh_conversa_direta and not self.nome:
            membros = list(self.membros.all())
            if len(membros) == 2:
                self.nome = f"{membros[0].username} ↔ {membros[1].username}"
                self.tipo = 'direto'
        super().save(*args, **kwargs)

    def validar_conversa_direta(self):
        """Validação personalizada para conversas diretas"""
        if self.eh_conversa_direta:
            # Verifica se já existe conversa direta com os mesmos membros
            membros_ids = sorted([m.id for m in self.membros.all()])
            if len(membros_ids) != 2:
                raise ValueError("Conversa direta deve ter exatamente 2 membros")

            # Verifica duplicatas (lógica implementada no clean)
            return True
        return True

    def clean(self):
        """Validação do modelo"""
        from django.core.exceptions import ValidationError

        if self.eh_conversa_direta:
            # Verifica se tem exatamente 2 membros
            if self.membros.count() != 2:
                raise ValidationError("Conversa direta deve ter exatamente 2 membros")

            # Verifica se já existe conversa direta entre esses membros
            if self.pk:  # Se já existe no banco
                conversas_existentes = CanalComunicacao.objects.filter(
                    eh_conversa_direta=True,
                    membros__in=self.membros.all()
                ).exclude(pk=self.pk).distinct()

                # Para cada conversa existente, verifica se tem os mesmos membros
                for conversa in conversas_existentes:
                    membros_conversa = set(conversa.membros.values_list('id', flat=True))
                    membros_atual = set(self.membros.values_list('id', flat=True))
                    if membros_conversa == membros_atual:
                        raise ValidationError(
                            "Já existe uma conversa direta entre esses membros"
                        )


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
    """Modelo para notificações do sistema de Recursos Humanos"""

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
        ('info', 'Informação'),
        ('aviso', 'Aviso'),
        ('alerta', 'Alerta'),
        ('sucesso', 'Sucesso'),
    ]

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notificacoes_sistema',
        null=True,
        blank=True
    )

    tipo = models.CharField(
        max_length=50,
        choices=TIPO_CHOICES,
        default='info'
    )

    titulo = models.CharField(max_length=200)
    mensagem = models.TextField()

    # Status
    lida = models.BooleanField(default=False)

    # Datas
    data_criacao = models.DateTimeField(null=True, blank=True)
    data_leitura = models.DateTimeField(null=True, blank=True)

    # Link para ação (opcional)
    url_link = models.CharField(max_length=500, blank=True, null=True)
    modelo_relacionado = models.CharField(max_length=100, blank=True, null=True)
    objeto_id = models.IntegerField(null=True, blank=True)

    # Prioridade
    PRIORIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]
    prioridade = models.CharField(
        max_length=20,
        choices=PRIORIDADE_CHOICES,
        default='media'
    )

    # Ícone/Faixa de cor
    icone = models.CharField(max_length=50, blank=True, default='bell')
    cor = models.CharField(max_length=20, blank=True, default='#007bff')

    class Meta:
        db_table = 'recursoshumanos_notificacaosistema'
        verbose_name = 'Notificação do Sistema'
        verbose_name_plural = 'Notificações do Sistema'
        ordering = ['-data_criacao']
        indexes = [
            models.Index(fields=['usuario', 'lida']),
            models.Index(fields=['data_criacao']),
        ]

    def __str__(self):
        return f"{self.titulo} - {self.get_tipo_display()}"

    def marcar_como_lida(self):
        """Marca a notificação como lida"""
        if not self.lida:
            self.lida = True
            self.data_leitura = timezone.now()
            self.save(update_fields=['lida', 'data_leitura'])

    @classmethod
    def criar_notificacao(cls, usuario, tipo, titulo, mensagem, **kwargs):
        """Método helper para criar notificações"""
        return cls.objects.create(
            usuario=usuario,
            tipo=tipo,
            titulo=titulo,
            mensagem=mensagem,
            **kwargs
        )

    @property
    def tempo_decorrido(self):
        """Retorna o tempo decorrido desde criação"""
        from django.utils import timezone
        from django.utils.timesince import timesince

        return timesince(self.data_criacao, timezone.now())


class ConfiguracaoNotificacao(models.Model):
    """Configurações de notificação para usuários"""

    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='configuracao_notificacao')

    # Configurações de exibição
    mostrar_licencas = models.BooleanField(default=True, verbose_name="Mostrar Notificações de Licenças")
    mostrar_avaliacoes = models.BooleanField(default=True, verbose_name="Mostrar Notificações de Avaliações")
    mostrar_documentos = models.BooleanField(default=True, verbose_name="Mostrar Notificações de Documentos")
    mostrar_mensagens = models.BooleanField(default=True, verbose_name="Mostrar Notificações de Mensagens")
    mostrar_sistema = models.BooleanField(default=True, verbose_name="Mostrar Notificações do Sistema")

    # Configurações de som
    som_notificacoes = models.BooleanField(default=True, verbose_name="Som de Notificações")

    # Frequência de notificações
    notificar_licencas_pendentes = models.BooleanField(default=True, verbose_name="Notificar Licenças Pendentes")
    notificar_avaliacoes_pendentes = models.BooleanField(default=True, verbose_name="Notificar Avaliações Pendentes")
    notificar_documentos_vencendo = models.BooleanField(default=True, verbose_name="Notificar Documentos a Vencer")

    # Timestamps
    data_criacao = models.DateTimeField(null=True, blank=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuração de Notificação'
        verbose_name_plural = 'Configurações de Notificação'

    def __str__(self):
        return f"Configurações de Notificação - {self.usuario.username}"



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
    data_criacao = models.DateTimeField(null=True, blank=True)
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


# models.py (parte dos documentos)

class TipoDocumento(models.Model):
    """Tipos de documentos institucionais com templates"""
    TIPO_CHOICES = [
        ('relatorio_anual', 'Relatório Anual de Atividades'),
        ('relatorio_mensal', 'Relatório Mensal'),
        ('oficio_circulacao', 'Ofício de Circulação'),
        ('memorando', 'Memorando Interno'),
        ('ata_reuniao', 'Ata de Reunião'),
        ('portaria', 'Portaria'),
        ('despacho', 'Despacho'),
        ('circular', 'Circular'),
        ('normativo', 'Normativo Interno'),
        ('plano_trabalho', 'Plano de Trabalho'),
    ]

    codigo = models.CharField(max_length=50, unique=True)
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    template_html = models.TextField(help_text="Template em HTML para visualização")
    template_docx = models.FileField(
        upload_to='templates_documentos/',
        blank=True,
        null=True,
        help_text="Template em .docx para geração automática"
    )
    campos_obrigatorios = models.JSONField(
        default=list,
        help_text="Lista de campos obrigatórios para este tipo"
    )
    campos_opcionais = models.JSONField(
        default=list,
        help_text="Lista de campos opcionais para este tipo"
    )
    estrutura = models.JSONField(
        default=list,
        help_text="Estrutura das seções do documento"
    )
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Tipo de Documento"
        verbose_name_plural = "Tipos de Documentos"
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.codigo})"


class DocumentoInstitucional(models.Model):
    """Documentos institucionais gerados"""
    STATUS_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('revisao', 'Em Revisão'),
        ('aprovado', 'Aprovado'),
        ('publicado', 'Publicado'),
        ('arquivado', 'Arquivado'),
        ('cancelado', 'Cancelado'),
    ]

    CLASSIFICACAO_CHOICES = [
        ('publico', 'Público'),
        ('interno', 'Uso Interno'),
        ('confidencial', 'Confidencial'),
        ('secreto', 'Secreto'),
    ]

    # Identificação básica
    tipo = models.ForeignKey(TipoDocumento, on_delete=models.PROTECT, related_name='documentos')
    numero_sequencial = models.IntegerField(default=0, help_text="Número sequencial por ano/tipo")
    numero_completo = models.CharField(max_length=100, unique=True, blank=True)
    titulo = models.CharField(max_length=500)
    descricao = models.TextField(blank=True)

    # Conteúdo
    conteudo_json = models.JSONField(default=dict, help_text="Dados preenchidos nos campos do formulário")
    conteudo_html = models.TextField(blank=True, help_text="Conteúdo renderizado em HTML")
    conteudo_texto = models.TextField(blank=True, help_text="Conteúdo em texto puro")

    # Arquivos gerados
    arquivo_docx = models.FileField(upload_to='documentos_gerados/docx/', null=True, blank=True)
    arquivo_pdf = models.FileField(upload_to='documentos_gerados/pdf/', null=True, blank=True)
    arquivo_html = models.FileField(upload_to='documentos_gerados/html/', null=True, blank=True)

    # Metadados
    data_documento = models.DateField(default=date.today, help_text="Data de emissão do documento")
    data_validade = models.DateField(null=True, blank=True, help_text="Data de validade (se aplicável)")
    data_publicacao = models.DateField(null=True, blank=True, help_text="Data de publicação oficial")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='rascunho')
    classificacao = models.CharField(max_length=20, choices=CLASSIFICACAO_CHOICES, default='interno')

    # Autoria
    criado_por = models.ForeignKey(User, on_delete=models.PROTECT, related_name='documentos_criados')
    aprovado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documentos_aprovados'
    )
    revisado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documentos_revisados'
    )

    # Destinatários
    setores_destino = models.ManyToManyField('Sector', blank=True, related_name='documentos_recebidos')
    funcionarios_destino = models.ManyToManyField('Funcionario', blank=True, related_name='documentos_recebidos')
    publico = models.BooleanField(default=False, help_text="Documento público para todos os funcionários")

    # Controle de versões
    versao = models.IntegerField(default=1)
    versao_anterior = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='versoes_posteriores'
    )

    # Logs
    data_criacao = models.DateTimeField(null=True, blank=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    data_aprovacao = models.DateTimeField(null=True, blank=True)
    data_publicacao_field = models.DateTimeField(null=True, blank=True)

    # Campos para assinatura digital (futuro)
    hash_documento = models.CharField(max_length=255, blank=True)
    assinatura_digital = models.TextField(blank=True)

    class Meta:
        verbose_name = "Documento Institucional"
        verbose_name_plural = "Documentos Institucionais"
        ordering = ['-data_documento', '-numero_sequencial']
        indexes = [
            models.Index(fields=['numero_completo']),
            models.Index(fields=['data_documento']),
            models.Index(fields=['status']),
            models.Index(fields=['criado_por', 'data_criacao']),
        ]

    def __str__(self):
        return f"{self.numero_completo} - {self.titulo}"

    def save(self, *args, **kwargs):
        # Gerar número completo automaticamente
        if not self.numero_completo:
            self.numero_completo = self.gerar_numero_documento()

        # Atualizar data de publicação se status mudar para publicado
        if self.status == 'publicado' and not self.data_publicacao_field:
            self.data_publicacao_field = timezone.now()

        # Atualizar data de aprovação se status mudar para aprovado
        if self.status == 'aprovado' and not self.data_aprovacao:
            self.data_aprovacao = timezone.now()

        # Gerar hash para integridade do documento
        if not self.hash_documento:
            self.hash_documento = self.gerar_hash()

        super().save(*args, **kwargs)

    def gerar_numero_documento(self):
        """Gera número de documento no formato: STAE-DOC-ANO-SEQUENCIAL"""
        ano = self.data_documento.year
        sigla_tipo = self.tipo.codigo.upper()[:4]

        # Obter último número sequencial para este tipo/ano
        ultimo = DocumentoInstitucional.objects.filter(
            tipo=self.tipo,
            data_documento__year=ano
        ).aggregate(Max('numero_sequencial'))['numero_sequencial__max'] or 0

        self.numero_sequencial = ultimo + 1

        return f"STAE-{sigla_tipo}-{ano}-{self.numero_sequencial:04d}"

    def gerar_hash(self):
        """Gera hash para verificação de integridade"""
        import hashlib
        conteudo = f"{self.titulo}{self.conteudo_texto}{self.data_documento}"
        return hashlib.sha256(conteudo.encode()).hexdigest()

    def verificar_integridade(self):
        """Verifica se o conteúdo não foi alterado"""
        return self.hash_documento == self.gerar_hash()

    def gerar_conteudo_html(self):
        """Gera conteúdo HTML a partir do template e dados"""
        from django.template import Context, Template

        try:
            template = Template(self.tipo.template_html)
            context = Context(self.conteudo_json)
            return template.render(context)
        except:
            # Fallback simples
            html = f"""
            <div class="documento-institucional">
                <h1>{self.titulo}</h1>
                <div class="numero-documento">Nº: {self.numero_completo}</div>
                <div class="data-documento">Data: {self.data_documento.strftime('%d/%m/%Y')}</div>
                <div class="conteudo">
                    {self.conteudo_texto}
                </div>
            </div>
            """
            return html

    def get_absolute_url(self):
        return reverse('visualizar_documento', args=[str(self.id)])

    def pode_visualizar(self, usuario):
        """Verifica se usuário pode visualizar este documento"""
        if self.publico:
            return True

        if self.criado_por == usuario:
            return True

        # Verificar se usuário é funcionário em setor destinatário
        try:
            funcionario = Funcionario.objects.get(user=usuario)
            if self.setores_destino.filter(id=funcionario.sector.id).exists():
                return True

            if self.funcionarios_destino.filter(id=funcionario.id).exists():
                return True
        except Funcionario.DoesNotExist:
            pass

        return False

    def get_status_display_color(self):
        """Retorna cor Bootstrap para o status"""
        cores = {
            'rascunho': 'warning',
            'revisao': 'info',
            'aprovado': 'primary',
            'publicado': 'success',
            'arquivado': 'secondary',
            'cancelado': 'danger',
        }
        return cores.get(self.status, 'secondary')

    @property
    def tamanho_total(self):
        """Retorna tamanho total dos arquivos em MB"""
        total = 0

        if self.arquivo_docx:
            total += self.arquivo_docx.size

        if self.arquivo_pdf:
            total += self.arquivo_pdf.size

        if self.arquivo_html:
            total += self.arquivo_html.size

        return total / (1024 * 1024)  # Convert to MB


class AnexoDocumento(models.Model):
    """Anexos de documentos"""
    documento = models.ForeignKey(DocumentoInstitucional, on_delete=models.CASCADE, related_name='anexos')
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    arquivo = models.FileField(upload_to='documentos_anexos/')
    tipo = models.CharField(max_length=50, blank=True)
    tamanho = models.IntegerField(default=0, help_text="Tamanho em bytes")
    ordem = models.IntegerField(default=0, help_text="Ordem de exibição")

    data_upload = models.DateTimeField(auto_now_add=True)
    upload_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['ordem', 'titulo']
        verbose_name = "Anexo de Documento"
        verbose_name_plural = "Anexos de Documentos"

    def __str__(self):
        return f"{self.titulo} - {self.documento.titulo}"

    def save(self, *args, **kwargs):
        if self.arquivo:
            self.tamanho = self.arquivo.size
            if not self.tipo:
                import os
                self.tipo = os.path.splitext(self.arquivo.name)[1].lower()
        super().save(*args, **kwargs)


class HistoricoDocumento(models.Model):
    """Histórico de alterações do documento"""
    ACAO_CHOICES = [
        ('criado', 'Documento Criado'),
        ('editado', 'Documento Editado'),
        ('revisado', 'Documento Revisado'),
        ('aprovado', 'Documento Aprovado'),
        ('publicado', 'Documento Publicado'),
        ('assinado', 'Documento Assinado'),
        ('arquivado', 'Documento Arquivado'),
        ('cancelado', 'Documento Cancelado'),
        ('versao', 'Nova Versão Criada'),
    ]

    documento = models.ForeignKey(DocumentoInstitucional, on_delete=models.CASCADE, related_name='historico')
    acao = models.CharField(max_length=20, choices=ACAO_CHOICES)
    descricao = models.TextField()
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    data_acao = models.DateTimeField(auto_now_add=True)

    # Campos para auditoria
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    alteracoes = models.JSONField(default=dict, help_text="Detalhes das alterações")

    class Meta:
        ordering = ['-data_acao']
        verbose_name = "Histórico de Documento"
        verbose_name_plural = "Históricos de Documentos"

    def __str__(self):
        return f"{self.documento.numero_completo} - {self.get_acao_display()} - {self.data_acao.strftime('%d/%m/%Y %H:%M')}"


# ========== PEDIDOS DE FÉRIAS ==========

class PedidoFerias(models.Model):
    """Modelo específico para pedidos de férias"""

    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aprovado', 'Aprovado'),
        ('rejeitado', 'Rejeitado'),
        ('cancelado', 'Cancelado'),
    ]

    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='pedidos_ferias')

    # Datas
    data_inicio = models.DateField(verbose_name="Data de Início")
    data_fim = models.DateField(verbose_name="Data de Término")
    dias_solicitados = models.IntegerField(verbose_name="Dias Solicitados")

    # Informações
    observacao = models.TextField(blank=True, verbose_name="Observações do Funcionário")
    observacoes_rh = models.TextField(blank=True, verbose_name="Observações do RH")
    local_ferias = models.CharField(max_length=200, blank=True, verbose_name="Local das Férias")
    contacto_emergencia = models.CharField(max_length=100, blank=True, verbose_name="Contacto de Emergência")

    # Status e aprovação
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    aprovado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ferias_aprovadas'
    )

    # Timestamps
    data_solicitacao = models.DateTimeField(auto_now_add=True)
    data_aprovacao = models.DateTimeField(null=True, blank=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pedido de Férias"
        verbose_name_plural = "Pedidos de Férias"
        ordering = ['-data_solicitacao']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['funcionario', 'data_solicitacao']),
        ]

    def __str__(self):
        return f"Férias de {self.funcionario.nome_completo} - {self.data_inicio} a {self.data_fim}"

    def calcular_dias(self):
        """Calcula dias automaticamente se não especificado"""
        if not self.dias_solicitados and self.data_inicio and self.data_fim:
            self.dias_solicitados = (self.data_fim - self.data_inicio).days + 1
        return self.dias_solicitados

    def save(self, *args, **kwargs):
        # Calcular dias se não especificado
        self.calcular_dias()
        super().save(*args, **kwargs)

    def criar_licenca_apos_aprovacao(self):
        """Cria licença automaticamente quando o pedido é aprovado"""
        if self.status == 'aprovado':
            licenca = Licenca.objects.create(
                funcionario=self.funcionario,
                tipo='ferias',
                data_inicio=self.data_inicio,
                data_fim=self.data_fim,
                dias_utilizados=self.dias_solicitados,
                motivo=f"Férias aprovadas - Pedido #{self.id}",
                status='aprovado',
                observacoes_rh=self.observacoes_rh,
                rh_aprovador=self.aprovado_por,
                data_analise_rh=timezone.now()
            )
            return licenca
        return None