
import re

caminho = 'gestaocombustivel/models.py'
with open(caminho, 'r', encoding='utf-8') as f:
    content = f.read()

# Substituir activa/ativo BooleanField default=True por default=True, null=True
# Ex: activa = models.BooleanField(default=True, verbose_name="Ativa")
# Para: activa = models.BooleanField(default=True, null=True, verbose_name="Ativa")

# Patterns
# activa = models.BooleanField(default=True
content = content.replace("activa = models.BooleanField(default=True", "activa = models.BooleanField(default=True, null=True")
content = content.replace("activo = models.BooleanField(default=True", "activo = models.BooleanField(default=True, null=True")
content = content.replace("disponivel = models.BooleanField(default=True", "disponivel = models.BooleanField(default=True, null=True")

# data_criacao também
content = content.replace("data_criacao = models.DateTimeField(auto_now_add=True)", "data_criacao = models.DateTimeField(auto_now_add=True, null=True)")

# confirmado_por_motorista
content = content.replace("confirmado_por_motorista = models.BooleanField(default=False", "confirmado_por_motorista = models.BooleanField(default=False, null=True")

with open(caminho, 'w', encoding='utf-8') as f:
    f.write(content)
print("Campos relaxados para null=True.")
