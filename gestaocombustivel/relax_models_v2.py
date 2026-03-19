
import re

caminho = 'gestaocombustivel/models.py'
with open(caminho, 'r', encoding='utf-8') as f:
    content = f.read()

# Relaxar DecimalFields em RotaTransporte e Manutencao
# Regex: models.DecimalField( -> models.DecimalField(null=True, blank=True, 
# Mas só se não tiver null=True já.
# Simplificado: replace string fixa conhecida
content = content.replace("distancia_total = models.DecimalField(max_digits", "distancia_total = models.DecimalField(null=True, blank=True, max_digits")
content = content.replace("combustivel_estimado = models.DecimalField(max_digits", "combustivel_estimado = models.DecimalField(null=True, blank=True, max_digits")

# TimeFields
content = content.replace("hora_partida = models.TimeField(", "hora_partida = models.TimeField(null=True, blank=True, ")
content = content.replace("hora_chegada = models.TimeField(", "hora_chegada = models.TimeField(null=True, blank=True, ")

# DateFields
content = content.replace("data_agendada = models.DateField()", "data_agendada = models.DateField(null=True, blank=True)")

with open(caminho, 'w', encoding='utf-8') as f:
    f.write(content)
print("Campos Decimal/Time relaxados.")
