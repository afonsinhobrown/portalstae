#!/usr/bin/env python
import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

from rs.models import PlanoLogistico
from script_logistica_stae import sync_plano_logistico

print("=== Testing sync_plano_logistico for plano id 5 ===")

# Get plano with id 5
plano5 = PlanoLogistico.objects.filter(id=5).first()
if not plano5:
    print("ERROR: Plano with id 5 not found!")
    sys.exit(1)

print(f"Plano found: {plano5.nome}")
print(f"Eleicao: {plano5.eleicao}")
print(f"Eleicao ID: {plano5.eleicao.id if plano5.eleicao else 'None'}")

# Check if eleicao has circulos
if plano5.eleicao:
    print(f"\nChecking eleicao circulos...")
    circulos = plano5.eleicao.circulos.all()
    print(f"Number of circulos: {circulos.count()}")
    if circulos.count() > 0:
        for c in circulos[:3]:  # Show first 3
            print(f"  - {c.nome}: {c.num_eleitores} eleitores, {c.num_mesas} mesas")

# Run the sync function
print("\n=== Running sync_plano_logistico ===")
try:
    result = sync_plano_logistico(plano5)
    print(f"Sync result: {result}")
    
    # Check if materials were created
    from rs.models import MaterialEleitoral
    materials = MaterialEleitoral.objects.filter(plano=plano5)
    print(f"\nMaterials created for plano 5: {materials.count()}")
    for m in materials:
        print(f"  - {m.item}: {m.quantidade_planeada} (tipo_dinamico: {m.tipo_dinamico})")
        
except Exception as e:
    print(f"ERROR during sync: {e}")
    import traceback
    traceback.print_exc()