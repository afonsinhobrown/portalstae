#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

from rs.models import MaterialEleitoral, PlanoLogistico, CategoriaMaterial, TipoMaterial
from django.db.models import Sum

print("=== Debugging script_logistica_stae.py ===")

# Simulate what the script does
plano5 = PlanoLogistico.objects.get(id=5)
eleicao = plano5.eleicao

print(f"Plano: {plano5.nome}")
print(f"Eleicao: {eleicao}")

# Check the calculations in the script
total_eleitores = eleicao.circulos.aggregate(total=Sum('num_eleitores'))['total'] or 0
total_mesas = eleicao.circulos.aggregate(total=Sum('num_mesas'))['total'] or 0

print(f"\nOriginal calculations:")
print(f"  total_eleitores from circulos: {total_eleitores}")
print(f"  total_mesas from circulos: {total_mesas}")

# Check the contingency logic
if total_mesas == 0:
    total_mesas = plano5.materiais.filter(item__icontains='Mesa').aggregate(total=Sum('quantidade_planeada'))['total'] or 0
    print(f"  After checking materiais with 'Mesa': {total_mesas}")
    if total_mesas == 0: 
        total_mesas = 10231 # Facto real detetado no ecrã do utilizador
        print(f"  Using default: {total_mesas}")

if total_eleitores == 0:
    total_eleitores = total_mesas * 800 # Média móvel estimada p/ Moçambique
    print(f"  Calculated total_eleitores: {total_eleitores}")

# Check the sovereignty items
itens_soberania = [
    ('Boletins de Voto Oficial (Soberania Nacional)', int(total_eleitores * 1.1)),
    ('Toner para Impressoras de Cartões (Neon Sync)', 500),
    ('Discos de Upgrading para Servidores Centrais', 50),
    ('Kits de Resiliência Logística (Stock Central)', 100)
]

print(f"\nSovereignty items to create:")
for nome, qtd in itens_soberania:
    print(f"  '{nome}': {qtd}")
    
    # Check if it already exists
    existing = MaterialEleitoral.objects.filter(
        plano=plano5,
        eleicao=eleicao,
        item=nome
    ).first()
    
    if existing:
        print(f"    Already exists: ID {existing.id}, qtd={existing.quantidade_planeada}")
    else:
        print(f"    Does not exist yet")

# Check encoding issues
print("\n=== Checking for encoding/string issues ===")
all_items = MaterialEleitoral.objects.filter(plano=plano5).values_list('item', flat=True)
for item in all_items:
    print(f"Item in DB: {repr(item)}")
    
# Check if there are any materials with similar names but different encoding
import unicodedata
print("\n=== Normalized item names ===")
for item in all_items:
    normalized = unicodedata.normalize('NFKD', item).encode('ASCII', 'ignore').decode()
    print(f"Original: {repr(item[:50])}")
    print(f"Normalized: {repr(normalized[:50])}")
    print()