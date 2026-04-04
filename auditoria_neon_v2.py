import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

from eleicao.models import Eleicao
from circuloseleitorais.models import DivisaoAdministrativa, DivisaoEleicao, CirculoEleitoral

print("--- AUDITORIA DE SOBERANIA ---")
e_count = Eleicao.objects.all().count()
print(f"Eleicoes no Neon: {e_count}")
for e in Eleicao.objects.all()[:5]:
    print(f" - {e.nome} ({e.ano})")

da_count = DivisaoAdministrativa.objects.all().count()
print(f"DivisaoAdministrativa (Mapa Pais): {da_count}")

de_count = DivisaoEleicao.objects.all().count()
print(f"DivisaoEleicao (Associações Feitas): {de_count}")

ce_count = CirculoEleitoral.objects.all().count()
print(f"Circulos Eleitorais: {ce_count}")

if da_count == 0:
    print("\nALERTA: O Mapa do Pais esta vazio no Neon!")
    # Tentar ver se ha dados no DFEC como fallback
    from django.apps import apps
    if apps.is_installed('dfec'):
        print("Verificando DFEC para dados geograficos...")
        # (Depende de como estao os modelos no DFEC)
