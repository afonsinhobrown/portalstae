
import re

nova_classe_ponto = """class PontoRota(models.Model):
    rota = models.ForeignKey(RotaTransporte, on_delete=models.CASCADE, related_name='pontos')
    nome_ponto = models.CharField(max_length=200, verbose_name="Nome do Ponto")
    tipo_ponto = models.CharField(max_length=50, choices=[
        ('paragem', 'Paragem'), 
        ('terminal', 'Terminal'),
        ('escola', 'Escola/Destino'),
        ('residencia', 'Residência')
    ], default='paragem')
    localizacao = models.CharField(max_length=200, blank=True, verbose_name="Localização/Referência")
    ordem = models.IntegerField(default=0, verbose_name="Ordem na Rota")
    hora_estimada = models.TimeField(null=True, blank=True, verbose_name="Hora Estimada")
    observacoes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['ordem']
        verbose_name = "Ponto de Rota"
        verbose_name_plural = "Pontos de Rota"

    def __str__(self):
        return f"{self.nome_ponto} ({self.rota})"
"""

with open('gestaocombustivel/models.py', 'rb') as f:
    content = f.read()

content = content.replace(b'\x00', b'')

try:
    decoded = content.decode('utf-8')
except:
    decoded = content.decode('latin-1')

# Procurar definicao antiga de PontoRota
# Começa com "class PontoRota(models.Model):" e termina com __str__
pattern = r"class PontoRota\(models\.Model\):.*?def __str__\(self\):\s+return f[\"']\{self\.nome\} \(\{self\.rota\}\)[\"']"

import re
match = re.search(pattern, decoded, re.DOTALL)

if match:
    print("Encontrada definicao simplificada de PontoRota. Substituindo...")
    decoded = decoded.replace(match.group(0), nova_classe_ponto)
else:
    print("Definicao antiga nao encontrada via regex. Usando substituição de bloco manual.")
    # Fallback
    start_idx = decoded.find("class PontoRota(models.Model):")
    next_idx = decoded.find("class FuncionarioRota(models.Model):")
    
    if start_idx != -1:
        if next_idx != -1:
            decoded = decoded[:start_idx] + nova_classe_ponto + "\n\n" + decoded[next_idx:]
        else:
            # Se for o ultimo ou FuncionarioRota nao achado, substituir ate o fim ou proxima classe
            # Assumindo que FuncionarioRota foi adicionado logo depois
            pass

with open('gestaocombustivel/models.py', 'w', encoding='utf-8') as f:
    f.write(decoded)
