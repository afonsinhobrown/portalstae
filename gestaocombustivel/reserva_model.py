
class ReservaViatura(models.Model):
    viatura = models.ForeignKey(Viatura, on_delete=models.CASCADE, related_name='reservas')
    funcionario = models.ForeignKey('recursoshumanos.Funcionario', on_delete=models.CASCADE)
    motivo = models.CharField(max_length=200)
    data_inicio = models.DateTimeField(auto_now_add=True)
    data_fim = models.DateTimeField(null=True, blank=True)
    ativa = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Reserva de Viatura'
        verbose_name_plural = 'Reservas de Viaturas'

    def __str__(self):
        return f'Reserva {self.viatura} - {self.funcionario}'
