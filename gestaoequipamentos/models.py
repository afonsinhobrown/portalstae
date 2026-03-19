from django.db import models
from django.contrib.auth.models import User
from datetime import date


class CategoriaEquipamento(models.Model):
    nome = models.CharField(max_length=100)
    codigo = models.CharField(max_length=20, unique=True)
    descricao = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categorias de Equipamento"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class TipoEquipamento(models.Model):
    categoria = models.ForeignKey(CategoriaEquipamento, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    atributos_especificos = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name_plural = "Tipos de Equipamento"
        ordering = ['categoria', 'nome']

    def __str__(self):
        return f"{self.categoria.nome} - {self.nome}"


class Equipamento(models.Model):
    ESTADO_CHOICES = [
        ('excelente', 'Excelente'),
        ('bom', 'Bom'),
        ('regular', 'Regular'),
        ('precisa_manutencao', 'Precisa de Manutenção'),
        ('inutilizado', 'Inutilizado'),
    ]

    tipo = models.ForeignKey(TipoEquipamento, on_delete=models.PROTECT)
    numero_serie = models.CharField(max_length=100, unique=True, blank=True, null=True)
    matricula = models.CharField(max_length=20, blank=True, null=True)
    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    ano_aquisicao = models.IntegerField()
    fornecedor = models.CharField(max_length=200)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='bom')
    atributos_especificos = models.JSONField(default=dict, blank=True)

    # Localização atual
    sector_atual = models.ForeignKey('recursoshumanos.Sector', on_delete=models.PROTECT)
    funcionario_responsavel = models.ForeignKey('recursoshumanos.Funcionario', on_delete=models.SET_NULL, null=True,
                                                blank=True)
    em_uso = models.BooleanField(default=True)

    data_criacao = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = "Equipamentos"
        ordering = ['tipo', 'marca', 'modelo']

    def __str__(self):
        identificador = self.numero_serie or self.matricula or f"ID{self.id}"
        return f"{self.tipo.nome} - {identificador}"


class MovimentacaoEquipamento(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aprovada', 'Aprovada'),
        ('rejeitada', 'Rejeitada'),
        ('concluida', 'Concluída'),
    ]

    equipamento = models.ForeignKey(Equipamento, on_delete=models.CASCADE)
    sector_origem = models.ForeignKey('recursoshumanos.Sector', on_delete=models.PROTECT,
                                      related_name='movimentacoes_origem')
    sector_destino = models.ForeignKey('recursoshumanos.Sector', on_delete=models.PROTECT,
                                       related_name='movimentacoes_destino')
    solicitado_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='movimentacoes_solicitadas')
    aprovado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='movimentacoes_aprovadas')

    motivo = models.TextField()
    data_solicitacao = models.DateTimeField(auto_now_add=True)
    data_aprovacao = models.DateTimeField(null=True, blank=True)
    data_conclusao = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')

    observacoes = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Movimentações de Equipamento"
        ordering = ['-data_solicitacao']

    def __str__(self):
        return f"Movimentação {self.equipamento} - {self.sector_origem} → {self.sector_destino}"


class Armazem(models.Model):
    sector = models.ForeignKey('recursoshumanos.Sector', on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    localizacao = models.CharField(max_length=200)
    responsavel = models.ForeignKey('recursoshumanos.Funcionario', on_delete=models.PROTECT)
    capacidade = models.IntegerField(help_text="Capacidade total em unidades")

    class Meta:
        verbose_name_plural = "Armazéns"
        ordering = ['sector', 'nome']

    def __str__(self):
        return f"{self.nome} - {self.sector.nome}"


class Inventario(models.Model):
    equipamento = models.ForeignKey(Equipamento, on_delete=models.CASCADE)
    armazem = models.ForeignKey(Armazem, on_delete=models.CASCADE)
    quantidade = models.IntegerField(default=1)
    localizacao_especifica = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name_plural = "Inventários"
        unique_together = ['equipamento', 'armazem']

    def __str__(self):
        return f"{self.equipamento} em {self.armazem} ({self.quantidade})"