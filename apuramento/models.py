from django.db import models
from circuloseleitorais.models import PostoVotacao
from partidos.models import Partido

class ResultadoMesa(models.Model):
    mesa = models.CharField(max_length=50, help_text="Número ou Código da Mesa")
    posto = models.ForeignKey(PostoVotacao, on_delete=models.CASCADE, null=True, blank=True)
    partido = models.ForeignKey(Partido, on_delete=models.CASCADE)
    votos_validos = models.IntegerField(default=0)
    votos_nulos = models.IntegerField(default=0)
    votos_brancos = models.IntegerField(default=0)
    reclamacoes = models.TextField(blank=True, null=True)
    data_apuramento = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Resultados por Mesa"
    
    def __str__(self):
        return f"Mesa {self.mesa} - {self.partido.sigla}"
