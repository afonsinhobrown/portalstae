import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

from circuloseleitorais.models import DivisaoAdministrativa, DivisaoEleicao
from eleicao.models import Eleicao

print("-" * 30)
print("DIAGNÓSTICO ADMINISTRATIVO")
print("-" * 30)

provs = DivisaoAdministrativa.objects.filter(nivel='provincia').count()
dists = DivisaoAdministrativa.objects.filter(nivel='distrito').count()
print(f"Base de Dados - Províncias: {provs}")
print(f"Base de Dados - Distritos: {dists}")

if provs == 0:
    print("ALERTA: A tabela administrativa base está VAZIA.")

eleicoes = Eleicao.objects.all().count()
print(f"Eleições Cadastradas: {eleicoes}")

associacoes = DivisaoEleicao.objects.all().count()
print(f"Associações Existentes (DivisaoEleicao): {associacoes}")

if associacoes > 0:
    print("\nÚLTIMAS ASSOCIAÇÕES:")
    for assoc in DivisaoEleicao.objects.all()[:5]:
        print(f"- [{assoc.eleicao.ano}] {assoc.nivel}: {assoc.nome}")
else:
    print("\nERRO: Nenhuma associação encontrada na tabela DivisaoEleicao.")
print("-" * 30)
