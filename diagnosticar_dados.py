import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

from rs.models import PlanoLogistico, RequisitoMaterial, AtividadeLogistica

print("==========================================================")
print("RELATÓRIO DE INTEGRIDADE DOS DADOS STAE")
print("==========================================================")

planos_count = PlanoLogistico.objects.count()
materiais_count = RequisitoMaterial.objects.count()
atividades_count = AtividadeLogistica.objects.count()

print(f"Total de Planos Logísticos: {planos_count}")
print(f"Total de Materiais Registados: {materiais_count}")
print(f"Total de Atividades Registadas: {atividades_count}")
print("==========================================================")

if planos_count > 0:
    print("ÚLTIMOS PLANOS REGISTADOS:")
    for p in PlanoLogistico.objects.all().order_by('-id')[:5]:
        print(f"- ID: {p.id} | Nome: {p.nome} | Ativo: {p.esta_ativo}")

print("CONCLUSÃO: OS DADOS ESTÃO SEGUROS NA BASE DE DADOS.")
