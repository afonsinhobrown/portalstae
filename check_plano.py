#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

from rs.models import PlanoLogistico, MaterialEleitoral

print("=== Checking Plano with id 5 ===")
plano5 = PlanoLogistico.objects.filter(id=5).first()
if plano5:
    print(f"Plano 5 found: {plano5.nome}")
    print(f"Eleicao: {plano5.eleicao}")
    print(f"Tipo operacao: {plano5.tipo_operacao}")
    
    # Check existing materials for this plano
    materials = MaterialEleitoral.objects.filter(plano=plano5)
    print(f"\nMaterials already linked to plano 5: {materials.count()}")
    for m in materials:
        print(f"  - {m.item}: {m.quantidade_planeada}")
else:
    print("Plano with id 5 does not exist!")
    
print("\n=== All Planos ===")
planos = PlanoLogistico.objects.all().order_by('id')
for p in planos:
    print(f"Plano {p.id}: {p.nome} (Eleicao: {p.eleicao})")