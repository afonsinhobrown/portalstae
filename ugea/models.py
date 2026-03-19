from django.db import models
from django.conf import settings
from django.utils import timezone
from .vision_service import VisionService
import datetime
import re

class Concurso(models.Model):
    STATUS_CHOICES = [
        ('planeamento', 'Em Planeamento'),
        ('aberto', 'Aberto / Recebendo Propostas'),
        ('avaliacao', 'Em Avaliação'),
        ('adjudicado', 'Adjudicado'),
        ('cancelado', 'Cancelado'),
    ]
    
    CRITERIO_CHOICES = [
        ('menor_preco', 'Menor Preço (Regra Geral)'),
        ('tecnico_preco', 'Critério Técnico-Preço (Excepcional)'),
    ]
    
    titulo = models.CharField(max_length=200)
    numero = models.CharField(max_length=50, unique=True, blank=True, help_text="Gerado automaticamente (Ex: CP/2024/001)")
    tipo = models.CharField(max_length=50, default='Concurso Público')
    criterio_avaliacao = models.CharField(max_length=20, choices=CRITERIO_CHOICES, default='menor_preco', verbose_name="Critério de Avaliação (Decreto 5/2016)")
    
    # Pesos para Critério Técnico-Preço
    peso_tecnico = models.IntegerField(default=70, help_text="Peso da proposta técnica (0-100)")
    peso_financeiro = models.IntegerField(default=30, help_text="Peso da proposta financeira (0-100)")
    
    descricao = models.TextField()
    data_abertura = models.DateTimeField()
    data_encerramento = models.DateTimeField()
    
    # Dados para o Anúncio
    preco_caderno = models.DecimalField(max_digits=10, decimal_places=2, default=500.00, help_text="Custo de aquisição do caderno")
    local_entrega = models.CharField(max_length=200, default="Secretaria da UGEA - STAE Sede", help_text="Local para submissão")
    texto_anuncio = models.TextField(blank=True, help_text="Texto completo do anúncio gerado")
    
    valor_estimado = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planeamento')
    
    # Documentação
    documento_anuncio = models.FileField(upload_to='ugea/anuncios/', null=True, blank=True)
    
    criado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Concursos"
    
    def save(self, *args, **kwargs):
        if not self.numero:
            now = datetime.datetime.now()
            year = now.year
            # Conta concursos deste ano para gerar sequencial
            # Use self.__class__ to avoid circular imports if Concurso was imported elsewhere
            count = self.__class__.objects.filter(criado_em__year=year).count()
            seq = count + 1
            self.numero = f"CP/{year}/{seq:03d}"
        super().save(*args, **kwargs)

    def sugerir_vencedor(self):
        """
        Analisa todas as propostas baseadas nos dados extraídos pelo OCR e critérios do Decreto 5/2016.
        """
        propostas = self.propostas.all()
        if not propostas:
            return None
            
        validas = []
        precos = [p.valor_proposto for p in propostas if p.valor_proposto]
        menor_preco_global = min(precos) if precos else 1.0

        for p in propostas:
            resumo = p.resumo_automatico or ""
            # Se houver alertas críticos (omissão de docs), a proposta é desqualificada
            is_valida = "❌ FALTA/RECUSA" not in resumo
            
            valor = float(p.valor_proposto or 0)
            base_score = 0.0
            
            if self.criterio_avaliacao == 'menor_preco':
                # No menor preço, score é inversamente proporcional ao valor
                base_score = 1000000000.0 - valor if is_valida else -1.0
            else:
                # Critério Técnico-Preço: Score = (T * Pt) + (P * Pp)
                # Onde P = (Menor Preço / Preço da Proposta) * 100
                pont_tecnica = float(p.pontuacao_tecnica or 50) # Default 50 se não avaliado
                pont_financeira = (float(menor_preco_global) / valor * 100) if valor > 0 else 0
                
                base_score = (pont_tecnica * (self.peso_tecnico/100)) + (pont_financeira * (self.peso_financeiro/100))
                if not is_valida: base_score = -1.0

            validas.append({
                'obj': p,
                'valida': is_valida,
                'score': base_score,
                'valor': valor,
                'prazo': p.prazo_entrega_dias or 999
            })
            
        # Ordenar por Score (Maior é melhor) e desempate por Prazo
        sugestao = sorted(validas, key=lambda x: (-x['score'], x['prazo']))
        
        return sugestao[0]['obj'] if sugestao and sugestao[0]['score'] > -1 else None

    def __str__(self):
        return f"{self.numero} - {self.titulo}"

# from recursoshumanos.models import Funcionario

class Juri(models.Model):
    concurso = models.ForeignKey(Concurso, on_delete=models.CASCADE, related_name='juris')
    presidente = models.CharField(max_length=200)
    vogal_1 = models.CharField(max_length=200)
    vogal_2 = models.CharField(max_length=200, blank=True)
    secretario = models.CharField(max_length=200, blank=True)
    data_nomeacao = models.DateField()
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"Júri - {self.concurso}"

class CadernoEncargos(models.Model):
    concurso = models.OneToOneField(Concurso, on_delete=models.CASCADE)
    
    # Estrutura Padrão Moçambique
    objeto_concurso = models.TextField(help_text="Descrição clara do projeto, obra ou serviço.")
    especificacoes_tecnicas = models.TextField(help_text="Detalhes sobre a qualidade, padrões e características.")
    condicoes_administrativas = models.TextField(help_text="Prazos, formas de apresentação, critérios, penalidades.")
    clausulas_contratuais = models.TextField(help_text="Disposições legais e regras específicas.")
    obrigacoes_contratante = models.TextField(help_text="Deveres da Entidade Contratante.", blank=True)
    obrigacoes_contratado = models.TextField(help_text="Deveres do Fornecedor/Empreiteiro.", blank=True)
    
    # Financeiro
    prazo_execucao_dias = models.IntegerField()
    garantia_exigida = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    
    documento_pdf = models.FileField(upload_to='ugea/cadernos/', null=True, blank=True)

class ItemCadernoEncargos(models.Model):
    """Itens ou serviços específicos que devem constar no Caderno de Encargos"""
    caderno = models.ForeignKey(CadernoEncargos, on_delete=models.CASCADE, related_name='itens')
    descricao = models.CharField(max_length=200, verbose_name="Item / Serviço Solicitado")
    quantidade_estimada = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    unidade = models.CharField(max_length=20, blank=True, null=True, help_text="Ex: Litros, Horas, Unidades")

    def __str__(self):
        return f"{self.descricao} - {self.caderno.concurso.numero if self.caderno.concurso else 'S/N'}"

class InscricaoConcurso(models.Model):
    concurso = models.ForeignKey(Concurso, on_delete=models.CASCADE, related_name='inscricoes')
    empresa_nome = models.CharField(max_length=200)
    nuit = models.CharField(max_length=20)
    representante_nome = models.CharField(max_length=200)
    representante_contacto = models.CharField(max_length=50)
    
    # Pagamento do Caderno
    valor_pago = models.DecimalField(max_digits=10, decimal_places=2, help_text="Taxa de compra do caderno")
    comprovativo_pagamento = models.FileField(upload_to='ugea/pagamentos/')
    caderno_entregue = models.BooleanField(default=False)
    
    data_inscricao = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.empresa_nome} - {self.concurso.numero}"

class Proposta(models.Model):
    concurso = models.ForeignKey(Concurso, on_delete=models.CASCADE, related_name='propostas')
    inscricao = models.OneToOneField(InscricaoConcurso, on_delete=models.SET_NULL, null=True, blank=True)
    fornecedor = models.CharField(max_length=200)
    nuit = models.CharField(max_length=20, default='000000000')
    valor_proposto = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Extraído automaticamente ou preenchido manualmente")
    prazo_entrega_dias = models.IntegerField(default=30)
    validade_proposta_dias = models.IntegerField(default=60)
    
    # Novo Workflow: Imagens + IA
    resumo_automatico = models.TextField(blank=True, help_text="Resumo gerado pelo sistema após leitura das imagens")
    
    data_submissao = models.DateTimeField(auto_now_add=True)
    
    # Avaliação
    pontuacao_tecnica = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    pontuacao_financeira = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    pontuacao_final = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    classificacao = models.IntegerField(null=True, blank=True, help_text="1º, 2º, 3º...")
    observacoes_juri = models.TextField(blank=True)
    
    def processar_com_ia(self):
        """
        Lê fisicamente as imagens e gera um resumo estruturado por SECÇÕES
        conforme exigido para a avaliação técnica e administrativa (Anti-Fraude).
        """
        imagens = self.imagens.all()
        if not imagens:
            return "Aguardando carregamento de documentos..."
        
        texto_acumulado = ""
        for img_obj in imagens:
            path = img_obj.imagem.path
            texto_acumulado += VisionService.extrair_texto(path) + "\n"

        res = VisionService.analisar_proposta(texto_acumulado)
        
        # Sincronizar campos do modelo
        self.valor_proposto = res['valor']
        self.prazo_entrega_dias = res['prazo_execucao']
        # self.validade_proposta_dias = res['validade_proposta'] # Caso queira adicionar ao model

        # CONSTRUÇÃO DO RESUMO ESTRUTURADO PARA O JÚRI
        resumo = f"--- RELATÓRIO TÉCNICO DE EXTRAÇÃO AUTOMÁTICA ---\n"
        resumo += f"IDENTIFICAÇÃO: {res['entidade']}\n\n"

        resumo += "1. VERIFICAÇÃO ADMINISTRATIVA (Checklist):\n"
        for doc, status in res['administrativo'].items():
            resumo += f"   [{status}] {doc}\n"
        
        resumo += "\n2. ESPECIFICAÇÕES TÉCNICAS DETECTADAS:\n"
        if res['tecnico']:
            for item, desc in res['tecnico'].items():
                resumo += f"   • {item}: {desc}\n"
        else:
            resumo += "   ⚠ Nenhuma especificação técnica clara foi isolada pelo OCR.\n"

        resumo += "\n3. PROPOSTA FINANCEIRA E PRAZOS:\n"
        for item, val in res['financeiro'].items():
            resumo += f"   • {item}: {val}\n"

        if res['alertas']:
            resumo += "\n⚠️ ALERTAS CRÍTICOS PARA O JÚRI:\n"
            for alerta in res['alertas']:
                resumo += f"   - {alerta}\n"
        else:
            resumo += "\n✅ CONFORMIDADE: Dados preliminares sugerem conformidade documental.\n"
            
        resumo += f"\n--- ORIGEM DOS DADOS ---\nLido de {len(imagens)} ficheiro(s) digitalizado(s)."
        
        self.resumo_automatico = resumo
        self.save()

    def save(self, *args, **kwargs):
        if self.pontuacao_tecnica is not None and self.pontuacao_financeira is not None:
            self.pontuacao_final = (self.pontuacao_tecnica + self.pontuacao_financeira) / 2
        super().save(*args, **kwargs)

    @property
    def resumo_admin(self):
        if not self.resumo_automatico: return ""
        try:
            inicio = self.resumo_automatico.find("1. VERIFICAÇÃO")
            fim = self.resumo_automatico.find("2. ESPECIFICAÇÕES")
            return self.resumo_automatico[inicio:fim].strip() if inicio != -1 else ""
        except: return ""

    @property
    def resumo_tecnico(self):
        if not self.resumo_automatico: return ""
        try:
            inicio = self.resumo_automatico.find("2. ESPECIFICAÇÕES")
            fim = self.resumo_automatico.find("3. PROPOSTA FINANCEIRA")
            return self.resumo_automatico[inicio:fim].strip() if inicio != -1 else ""
        except: return ""

    @property
    def resumo_financeiro(self):
        if not self.resumo_automatico: return ""
        try:
            inicio = self.resumo_automatico.find("3. PROPOSTA FINANCEIRA")
            return self.resumo_automatico[inicio:].strip() if inicio != -1 else ""
        except: return ""

    def __str__(self):
        return f"{self.fornecedor} - {self.valor_proposto} MT"

class PropostaImagem(models.Model):
    proposta = models.ForeignKey(Proposta, on_delete=models.CASCADE, related_name='imagens')
    imagem = models.ImageField(upload_to='ugea/propostas/imagens/')
    ordem = models.IntegerField(default=0)
    data_upload = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordem']

class Contrato(models.Model):
    """
    Contrato Centralizado na UGEA.
    Deve substituir ou alimentar os contratos específicos (como Combustível).
    """
    concurso = models.OneToOneField(Concurso, on_delete=models.CASCADE, related_name='contrato_ativo')
    proposta_vencedora = models.OneToOneField(Proposta, on_delete=models.PROTECT, related_name='contrato_resultante')
    
    numero_contrato = models.CharField(max_length=50, unique=True, verbose_name="Número do Contrato")
    data_assinatura = models.DateField(auto_now_add=True)
    data_inicio = models.DateField(verbose_name="Início da Vigência")
    data_fim = models.DateField(verbose_name="Fim da Vigência")
    
    
    # Controle Financeiro
    valor_total = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Valor Total (MT)")
    valor_executado = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Valor Executado")
    
    # Detalhes do Serviço
    tipo_servico = models.CharField(max_length=100, verbose_name="Tipo de Serviço", default="Geral")
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço Unitário (MT)", default=0)
    sector = models.ForeignKey('recursoshumanos.Sector', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Setor Solicitante")

    # Arquivo Digital
    documento = models.FileField(upload_to='ugea/contratos/', null=True, blank=True)
    
    # Estado (Ativo/Cancelado/Concluído)
    ativo = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            # Importar serviços do Caderno de Encargos se existirem
            caderno = getattr(self.concurso, 'cadernoencargos', None)
            if caderno:
                # Evita problemas de importação circular referenciando pelo nome da classe
                ItemContratoModel = self.itens.model
                for item_caderno in caderno.itens.all():
                    ItemContratoModel.objects.get_or_create(
                        contrato=self,
                        descricao=item_caderno.descricao,
                        defaults={'preco_unitario': 0}
                    )

    @property
    def saldo_disponivel(self):
        """
        Saldo que ainda pode ser autorizado para consumo.
        Total do Contrato - Soma de todos os pedidos já aprovados.
        """
        consumo = self.pedidos_consumo.filter(status='aprovado').aggregate(models.Sum('valor_estimado'))['valor_estimado__sum'] or 0
        return self.valor_total - consumo

    @property
    def saldo_financeiro(self):
        """
        Saldo que ainda não foi pago ao fornecedor (inclui o que ainda não foi consumido).
        Total do Contrato - Pagamentos Reais.
        """
        return self.valor_total - self.valor_executado

    def __str__(self):
        return f"Contrato {self.numero_contrato} - {self.proposta_vencedora.fornecedor}"

class ItemContrato(models.Model):
    """
    Itens específicos cobertos pleo contrato (ex: Gasolina, Diesel, Manutenção A, Manutenção B).
    Permite preços diferenciados dentro do mesmo contrato.
    """
    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE, related_name='itens')
    descricao = models.CharField(max_length=200, verbose_name="Item / Produto")
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço Unitário (MT)")
    
    def __str__(self):
        return f"{self.descricao} ({self.preco_unitario} MT)"

class Fornecedor(models.Model):
    """
    Base de Dados Central de Fornecedores do Estado (UGEA).
    Integra fornecedores de Combustível, Papelaria, Obras, etc.
    """
    CATEGORIA_CHOICES = [
        ('bens', 'Fornecimento de Bens'),
        ('servicos', 'Prestação de Serviços'),
        ('empreitadas', 'Empreitadas de Obras Públicas'),
        ('consultoria', 'Consultoria'),
        ('combustivel', 'Combustíveis e Lubrificantes'),
        ('misto', 'Misto / Geral'),
    ]

    nome = models.CharField(max_length=255, verbose_name="Designação Social")
    nuit = models.CharField(max_length=20, unique=True, verbose_name="NUIT")
    endereco = models.TextField(verbose_name="Endereço Físico", blank=True)
    email = models.EmailField(verbose_name="Email Oficial", blank=True)
    telefone = models.CharField(max_length=50, verbose_name="Contacto", blank=True)
    
    categoria = models.CharField(max_length=50, choices=CATEGORIA_CHOICES, default='misto')
    
    # Dados Bancários
    banco = models.CharField(max_length=100, blank=True)
    nib = models.CharField(max_length=50, blank=True, verbose_name="NIB")
    
    # Status
    ativo = models.BooleanField(default=True)
    bloqueado = models.BooleanField(default=False, help_text="Impedido de contratar com o Estado?")
    motivo_bloqueio = models.TextField(blank=True)
    
    data_registo = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome} ({self.nuit})"

class PedidoConsumo(models.Model):
    """
    Pedidos de consumo que afetam contratos (ex: Pedido de Combustível).
    Devem ser aprovados pela UGEA antes de libertar o bem/serviço.
    """
    STATUS_CHOICES = [
        ('pendente', 'Pendente de Aprovação'),
        ('aprovado', 'Aprovado'),
        ('rejeitado', 'Rejeitado'),
    ]

    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE, related_name='pedidos_consumo')
    item_contrato = models.ForeignKey(ItemContrato, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Item Específico")
    solicitante = models.CharField(max_length=200, help_text="Quem pediu? (Nome/Departamento)")
    descricao = models.TextField(verbose_name="Descrição do Pedido")
    
    # Detalhes Financeiros/Qtd
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, help_text="Litros, Unidades, etc.")
    valor_estimado = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Estimado (MT)")
    
    data_pedido = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    
    observacao_aprovacao = models.TextField(blank=True, verbose_name="Obs da UGEA")
    
    # Rastreabilidade para módulos específicos
    modulo_origem = models.CharField(max_length=50, blank=True, null=True, help_text="Ex: gestaocombustivel")
    ref_id = models.PositiveIntegerField(blank=True, null=True, help_text="ID do pedido no módulo de origem")

    def __str__(self):
        return f"Pedido {self.id} - {self.solicitante} ({self.status})"

class Pagamento(models.Model):
    """
    Registo de execução financeira (Pagamentos Reais).
    Abate ao Saldo do Contrato.
    """
    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE, related_name='pagamentos')
    data_pagamento = models.DateField(default=timezone.now)
    valor = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Pago (MT)")
    referencia = models.CharField(max_length=100, help_text="Nº Factura / Ordem de Pagamento", verbose_name="Referência")
    descricao = models.TextField(blank=True, verbose_name="Notas")
    comprovativo = models.FileField(upload_to='ugea/pagamentos/', blank=True, null=True)
    
    registado_em = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Atualizar o valor executado do contrato automaticamente
        total = self.contrato.pagamentos.aggregate(models.Sum('valor'))['valor__sum'] or 0
        self.contrato.valor_executado = total
        self.contrato.save()

    def __str__(self):
        return f"Pagamento {self.referencia} - {self.valor} MT"

class AcompanhamentoExecucao(models.Model):
    concurso = models.OneToOneField(Concurso, on_delete=models.CASCADE)
    contrato_assinado = models.BooleanField(default=False)
    data_inicio_real = models.DateField(null=True, blank=True)
    percentual_execucao = models.IntegerField(default=0)
    status_pagamento = models.CharField(max_length=50, default='Pendente')
    relatorio_progresso = models.TextField(blank=True)
