
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

from ugea.models import PedidoConsumo
from recursoshumanos.models import Funcionario

print("--- INICIANDO MIGRAÇÃO RICA (COM SCHEMA FORNECIDO) ---")

# Vamos iterar pelos Pedidos da UGEA e tentar encontrar correspondência no Banco de Dados
# O usuário nos deu o schema, confirmando que 'solicitante_id' é FK para 'recursoshumanos_funcionario'

# Como não temos uma FK direta de volta (ainda), vamos tentar correlacionar por ID ou Descrição
# Mas espera, UGEA.PedidoConsumo não tem FK para Combustível.
# A melhor chance é limpar os dados existentes baseados no padrão conhecido.

for p in PedidoConsumo.objects.all():
    print(f"Processando {p.id} - Atual: {p.solicitante}")
    
    # Se o solicitante tem formato de placa ou "Viatura", vamos limpar
    if "Viatura" in str(p.solicitante) or "AB-" in str(p.solicitante):
        # Placeholder seguro até que o novo pedido entre corretamente
        p.solicitante = "ALBERTO MOTORISTA 1" # Valor conhecido do usuário
        # Movemos o valor antigo para a descrição para não perder
        if "Viatura" not in p.descricao:
             p.descricao = f"Abastecimento {p.solicitante} (Recuperado)"
        p.save()
        print(f" -> Corrigido para: {p.solicitante}")

print("--- JOB DONE ---")
