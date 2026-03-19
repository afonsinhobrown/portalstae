
# ==========================================
# GESTÃO DE MANUTENÇÃO AVANÇADA
# ==========================================

class FornecedorManutencao(models.Model):
    nome = models.CharField(max_length=200)
    nuit = models.CharField(max_length=20, unique=True, verbose_name="NUIT")
    endereco = models.TextField(verbose_name="Endereço")
    contacto = models.CharField(max_length=100, verbose_name="Contacto")
    email = models.EmailField(blank=True, verbose_name="Email")
    especialidades = models.TextField(blank=True, help_text="Ex: Mecânica, Elétrica, Chaparia, etc")
    activo = models.BooleanField(default=True)
    data_registo = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Fornecedor de Manutenção"
        verbose_name_plural = "Fornecedores de Manutenção"

    def __str__(self):
        return self.nome


class ContratoManutencao(models.Model):
    fornecedor = models.ForeignKey(FornecedorManutencao, on_delete=models.PROTECT, related_name='contratos')
    numero_contrato = models.CharField(max_length=50, unique=True, verbose_name="Número do Contrato")
    descricao = models.CharField(max_length=200, verbose_name="Descrição/Objeto")
    
    # Financeiro
    valor_total = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Valor Total do Contrato")
    valor_gasto = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Valor Gasto (Serviços Realizados)")
    valor_pago = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Valor Pago (Financeiro)")
    
    # Vigência
    data_inicio = models.DateField(verbose_name="Data Início")
    data_fim = models.DateField(verbose_name="Data Fim")
    activo = models.BooleanField(default=True)
    
    documento = models.FileField(upload_to='contratos/manutencao/', blank=True, verbose_name="Documento do Contrato")
    observacoes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Contrato de Manutenção"
        verbose_name_plural = "Contratos de Manutenção"

    def __str__(self):
        return f"{self.numero_contrato} - {self.fornecedor.nome}"

    @property
    def saldo_disponivel(self):
        return self.valor_total - self.valor_gasto

    @property
    def valor_divida(self):
        return self.valor_gasto - self.valor_pago
    
    @property
    def estado(self):
        if not self.activo: return "Inativo"
        if self.data_fim < date.today(): return "Expirado"
        if self.saldo_disponivel <= 0: return "Esgotado"
        return "Ativo"


class TipoServicoManutencao(models.Model):
    """Catálogo de Serviços"""
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    categoria = models.CharField(max_length=50, choices=[
        ('preventiva', 'Preventiva'),
        ('correctiva', 'Correctiva'),
        ('pecas', 'Peças'),
        ('servico', 'Mão de Obra'),
        ('outros', 'Outros')
    ], default='servico')
    
    # Preço base referencial (opcional)
    preco_referencia = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = "Tipo de Serviço/Peça"
        verbose_name_plural = "Catálogo de Serviços e Peças"

    def __str__(self):
        return self.nome


class PrecoServicoContrato(models.Model):
    """Preços acordados em contrato específico"""
    contrato = models.ForeignKey(ContratoManutencao, on_delete=models.CASCADE, related_name='tabela_precos')
    servico = models.ForeignKey(TipoServicoManutencao, on_delete=models.CASCADE)
    preco_acordado = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        unique_together = ['contrato', 'servico']
        verbose_name = "Preço Acordado"
        verbose_name_plural = "Tabela de Preços do Contrato"


class PagamentoManutencao(models.Model):
    """Pagamentos realizados referentes a contratos de manutenção"""
    contrato = models.ForeignKey(ContratoManutencao, on_delete=models.PROTECT, related_name='pagamentos')
    valor = models.DecimalField(max_digits=15, decimal_places=2)
    data_pagamento = models.DateField(default=date.today)
    referencia = models.CharField(max_length=100, verbose_name="Referência/Cheque")
    comprovativo = models.FileField(upload_to='pagamentos/manutencao/', blank=True)
    observacoes = models.TextField(blank=True)
    
    registado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    data_registo = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Pagamento de Manutenção"
        verbose_name_plural = "Pagamentos de Manutenção"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Atualizar saldo do contrato
        total_pago = self.contrato.pagamentos.aggregate(Sum('valor'))['valor__sum'] or 0
        self.contrato.valor_pago = total_pago
        self.contrato.save()


# Extender ManutencaoViatura para usar esses novos modelos
# (Isso será feito via alteração na classe ManutencaoViatura existente ou criando uma tabela intermediária se quiser manter compatibilidade)
# Vamos adicionar campos Opcionais em ManutencaoViatura para fazer a ligação
