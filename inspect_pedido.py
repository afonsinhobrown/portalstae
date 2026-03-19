import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

from ugea.models import PedidoConsumo

print("--- Campos do Model PedidoConsumo ---")
for field in PedidoConsumo._meta.get_fields():
    print(field.name)

print("\n--- Último Pedido ---")
last = PedidoConsumo.objects.last()
if last:
    print(f"ID: {last.id}")
    print(f"Solicitante (raw): '{last.solicitante}'")
    # Tentar acessar requisitante se existir
    if hasattr(last, 'requisitante'):
        print(f"Requisitante (raw): '{last.requisitante}'")
    else:
        print("Campo 'requisitante' NÃO existe no model.")
        
    print(f"Descricao (raw): '{last.descricao}'")
else:
    print("Nenhum pedido encontrado.")
