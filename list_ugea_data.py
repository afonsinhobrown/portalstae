
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

from ugea.models import PedidoConsumo

print(f"{'ID':<5} | {'SOLICITANTE (Atributo)':<40} | {'DESCRICAO (Atributo)'}")
print("-" * 100)
for p in PedidoConsumo.objects.all():
    print(f"{p.id:<5} | {str(p.solicitante)[:40]:<40} | {str(p.descricao)[:40]}")
