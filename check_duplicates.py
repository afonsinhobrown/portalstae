#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

from rs.models import MaterialEleitoral, PlanoLogistico

print("=== Checking for potential duplicate materials ===")

# Get plano 5
plano5 = PlanoLogistico.objects.get(id=5)

# Check materials for plano 5
materials_plano5 = MaterialEleitoral.objects.filter(plano=plano5)
print(f"\nMaterials with plano=5: {materials_plano5.count()}")

# Check materials with same eleicao but plano=None or different plano
eleicao = plano5.eleicao
if eleicao:
    print(f"\nChecking eleicao {eleicao.id} materials:")
    
    # All materials for this eleicao
    all_materials = MaterialEleitoral.objects.filter(eleicao=eleicao)
    print(f"Total materials for eleicao {eleicao.id}: {all_materials.count()}")
    
    # Group by item to find duplicates
    from collections import defaultdict
    items_dict = defaultdict(list)
    
    for m in all_materials:
        items_dict[m.item].append(m)
    
    print("\nItems with multiple entries:")
    for item, materials in items_dict.items():
        if len(materials) > 1:
            print(f"\n  '{item}': {len(materials)} entries")
            for m in materials:
                print(f"    - ID {m.id}: plano={m.plano.id if m.plano else 'None'}, qtd={m.quantidade_planeada}")
    
    # Check for materials with plano=None but same item
    print("\n=== Materials with plano=None that might conflict ===")
    null_plano_materials = MaterialEleitoral.objects.filter(eleicao=eleicao, plano__isnull=True)
    print(f"Materials with plano=None: {null_plano_materials.count()}")
    
    for m in null_plano_materials[:10]:  # Show first 10
        print(f"  - {m.item}: ID {m.id}, qtd={m.quantidade_planeada}")

# Check the specific sovereignty items from the script
sovereignty_items = [
    'Boletins de Voto Oficial (Soberania Nacional)',
    'Toner para Impressoras de Cartões (Neon Sync)',
    'Discos de Upgrading para Servidores Centrais',
    'Kits de Resiliência Logística (Stock Central)'
]

print("\n=== Checking sovereignty items specifically ===")
for item in sovereignty_items:
    matches = MaterialEleitoral.objects.filter(eleicao=eleicao, item__icontains=item)
    print(f"\n'{item}': {matches.count()} matches")
    for m in matches:
        print(f"  - ID {m.id}: plano={m.plano.id if m.plano else 'None'}, qtd={m.quantidade_planeada}")