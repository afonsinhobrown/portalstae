
# Script para restaurar classes perdidas e evitar migrations destrutivas

if __name__ == "__main__":
    caminho = 'gestaocombustivel/models.py'
    with open(caminho, 'r', encoding='utf-8') as f:
        content = f.read()

    # Se a classe Infraccao não estiver no arquivo, vamos adicioná-la
    if 'class Infraccao' not in content:
        extra_models = """

class Infraccao(models.Model):
    TIPO_CHOICES = [
        ('excesso_velocidade', 'Excesso de Velocidade'),
        ('estacionamento', 'Estacionamento Proibido'),
        ('sinalizacao', 'Desrespeito à Sinalização'),
        ('documentos', 'Documentação em Falta'),
        ('alcool', 'Condução sob Influência'),
        ('outro', 'Outro'),
    ]
    viatura = models.ForeignKey('Viatura', on_delete=models.CASCADE, related_name='infraccoes')
    motorista = models.ForeignKey('recursoshumanos.Funcionario', on_delete=models.SET_NULL, null=True, blank=True, related_name='infraccoes')
    data_infracao = models.DateTimeField()
    local = models.CharField(max_length=200)
    tipo_infracao = models.CharField(max_length=30, choices=TIPO_CHOICES)
    descricao = models.TextField()
    valor_multa = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='pendente')
    data_registo = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Infracção/Multa'
        verbose_name_plural = 'Infrações/Multas'
        ordering = ['-data_infracao']
        indexes = [
            models.Index(fields=['viatura', 'status']),
            models.Index(fields=['motorista', 'data_infracao']),
        ]

class AcidenteViatura(models.Model):
    data_acidente = models.DateTimeField()
    viatura = models.ForeignKey('Viatura', on_delete=models.CASCADE, related_name='acidentes')
    motorista = models.ForeignKey('recursoshumanos.Funcionario', on_delete=models.SET_NULL, null=True, related_name='acidentes_motorista')
    local = models.CharField(max_length=200)
    descricao = models.TextField()
    fotos = models.ImageField(upload_to='acidentes/fotos/', blank=True)
    data_registo = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Acidente de Viatura'
        verbose_name_plural = 'Acidentes de Viaturas'
"""
        with open(caminho, 'a', encoding='utf-8') as f:
            f.write(extra_models)
        print("Modelos Infraccao e Acidente restaurados.")
    else:
        print("Modelos já presentes.")
