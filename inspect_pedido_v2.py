import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

from ugea.models import PedidoConsumo

print("FIELDS:")
names = [f.name for f in PedidoConsumo._meta.get_fields()]
print(names)

print("LAST ITEM:")
last = PedidoConsumo.objects.last()
if last:
    print(f"ID: {last.id}")
    print(f"solicitante: {last.solicitante}")
    print(f"descricao: {last.descricao}")
    if 'requisitante' in names:
        print(f"requisitante: {getattr(last, 'requisitante')}")
    else:
        print("NO requisitante FIELD")
