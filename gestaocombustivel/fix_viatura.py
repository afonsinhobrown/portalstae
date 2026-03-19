
viatura_model = """
class Viatura(models.Model):
    TIPO_VIATURA_CHOICES = [
        ('ligeiro', 'Ligeiro'),
        ('pick_up', 'Pick-up cabine dupla'),
        ('onibus', 'Autocarro/Micro-bus'),
        ('motociclo', 'Motociclo'),
        ('pesado', 'Pesado/Camião'),
        ('outro', 'Outro'),
    ]

    TIPO_COMBUSTIVEL_CHOICES = [
        ('diesel', 'Diesel'),
        ('gasolina', 'Gasolina'),
    ]

    ESTADO_CHOICES = [
        ('bom', 'Bom'),
        ('razoavel', 'Razoável'),
        ('mau', 'Mau'),
        ('abate', 'Para Abate'),
        ('oficina', 'Na Oficina'),
    ]

    matricula = models.CharField(max_length=20, unique=True, verbose_name="Matrícula")
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    ano_fabrico = models.IntegerField(null=True, blank=True, verbose_name="Ano de Fabrico")
    cor = models.CharField(max_length=30, null=True, blank=True)
    
    tipo_combustivel = models.CharField(max_length=20, choices=TIPO_COMBUSTIVEL_CHOICES, default='diesel', verbose_name="Tipo de Combustível")
    tipo_viatura = models.CharField(max_length=20, choices=TIPO_VIATURA_CHOICES, default='ligeiro')
    
    cilindrada = models.CharField(max_length=20, null=True, blank=True)
    capacidade_tanque = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Capacidade do Tanque (L)")
    kilometragem_actual = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Quilometragem Atual")
    
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='bom')
    activa = models.BooleanField(default=True, verbose_name="Em Atividade")
    disponivel = models.BooleanField(default=True, verbose_name="Disponível para Missão")
    
    funcionario_afecto = models.ForeignKey('recursoshumanos.Funcionario', on_delete=models.SET_NULL, null=True, blank=True, related_name='viaturas', verbose_name="Funcionário Responsável")
    motoristas_autorizados = models.ManyToManyField('recursoshumanos.Funcionario', blank=True, related_name='viaturas_autorizadas')
    
    numero_chassi = models.CharField(max_length=50, blank=True, unique=True, null=True, verbose_name="Nº do Chassi")
    numero_motor = models.CharField(max_length=50, blank=True)
    
    data_ultimo_seguro = models.DateField(null=True, blank=True)
    data_proximo_seguro = models.DateField(null=True, blank=True)
    
    data_ultima_inspecao = models.DateField(null=True, blank=True)
    data_proxima_inspecao = models.DateField(null=True, blank=True)
    
    proxima_manutencao_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    observacoes = models.TextField(blank=True)
    
    data_criacao = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Viatura"
        verbose_name_plural = "Viaturas"
        ordering = ['marca', 'modelo']

    def __str__(self):
        return f"{self.matricula} - {self.marca} {self.modelo}"
        
    def get_tipo_combustivel_display(self):
        return dict(self.TIPO_COMBUSTIVEL_CHOICES).get(self.tipo_combustivel, self.tipo_combustivel)
"""

# Ler o arquivo
with open('gestaocombustivel/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Inserir Logo após os imports (que assumimos terminar antes da primeira classe class ... ou após os imports comuns)
# Vamos inserir logo antes de "class FornecedorCombustivel"
if "class Viatura" not in content:
    if "class FornecedorCombustivel" in content:
        content = content.replace("class FornecedorCombustivel", viatura_model + "\n\nclass FornecedorCombustivel")
        print("Viatura restaurada antes de FornecedorCombustivel")
    else:
        # Se não achou FornecedorCombustivel, insere no fim dos imports
        # Fallback: inserir depois de 'import re'
        if "import re" in content:
             content = content.replace("import re", "import re\n\n" + viatura_model)
             print("Viatura restaurada apos imports")
else:
    print("Viatura ja existe (invisivel?)")

with open('gestaocombustivel/models.py', 'w', encoding='utf-8') as f:
    f.write(content)
