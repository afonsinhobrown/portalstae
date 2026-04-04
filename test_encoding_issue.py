#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

from rs.models import MaterialEleitoral, PlanoLogistico, CategoriaMaterial, TipoMaterial

print("=== Testing encoding issue ===")

plano5 = PlanoLogistico.objects.get(id=5)
eleicao = plano5.eleicao

# The strings from the script (with correct Portuguese characters)
script_items = [
    'Boletins de Voto Oficial (Soberania Nacional)',
    'Toner para Impressoras de Cartões (Neon Sync)',
    'Discos de Upgrading para Servidores Centrais',
    'Kits de Resiliência Logística (Stock Central)'
]

# What's actually in the database
db_items = MaterialEleitoral.objects.filter(plano=plano5).values_list('item', flat=True)

print("\nComparing script strings vs database strings:")
for script_item in script_items:
    print(f"\nScript: '{script_item}'")
    
    # Try exact match
    exact_match = MaterialEleitoral.objects.filter(
        plano=plano5,
        eleicao=eleicao,
        item=script_item
    ).first()
    
    print(f"  Exact match: {'YES' if exact_match else 'NO'}")
    
    # Try case-insensitive contains
    contains_match = MaterialEleitoral.objects.filter(
        plano=plano5,
        eleicao=eleicao,
        item__icontains=script_item[:20]  # First part of string
    ).first()
    
    if contains_match and not exact_match:
        print(f"  Contains match: YES - DB has '{contains_match.item}'")
        print(f"  Strings equal? {script_item == contains_match.item}")
        print(f"  Script repr: {repr(script_item)}")
        print(f"  DB repr: {repr(contains_match.item)}")

# Test what happens with update_or_create
print("\n=== Testing update_or_create with encoding issue ===")
test_item = 'Toner para Impressoras de Cartões (Neon Sync)'

# First, let's see what's in DB for this
db_version = MaterialEleitoral.objects.filter(
    plano=plano5,
    eleicao=eleicao,
    item__icontains='Toner'
).first()

if db_version:
    print(f"DB has: '{db_version.item}'")
    print(f"Looking for: '{test_item}'")
    print(f"Are they equal? {db_version.item == test_item}")
    
    # Try to get_or_create
    print("\nTrying get with exact match...")
    try:
        match = MaterialEleitoral.objects.get(
            plano=plano5,
            eleicao=eleicao,
            item=test_item
        )
        print(f"Found exact match: {match.id}")
    except MaterialEleitoral.DoesNotExist:
        print("No exact match found!")
    except MaterialEleitoral.MultipleObjectsReturned:
        print("Multiple matches found!")

# Check database encoding
print("\n=== Database encoding check ===")
import sys
print(f"Python default encoding: {sys.getdefaultencoding()}")
print(f"File system encoding: {sys.getfilesystemencoding()}")

# Check if we can fix the encoding
print("\n=== Attempting to fix encoding ===")
for material in MaterialEleitoral.objects.filter(plano=plano5):
    original = material.item
    # Try to encode/decode
    try:
        # The issue might be that the string is already corrupted
        print(f"ID {material.id}: '{original}'")
        print(f"  Length: {len(original)}")
        # Try to encode as latin-1 then decode as utf-8
        try:
            encoded = original.encode('latin-1').decode('utf-8')
            print(f"  After latin-1->utf-8: '{encoded}'")
        except:
            print(f"  Cannot convert latin-1->utf-8")
    except Exception as e:
        print(f"  Error: {e}")