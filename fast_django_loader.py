import os
import json
import django
from django.core import serializers
from django.db import transaction

# Definir o ambiente do Neon
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings_neon')
os.environ['PYTHONUTF8'] = '1'
django.setup()

def load_super_fast():
    print("A carregar JSON...")
    with open('small_data.json', 'r', encoding='utf-8') as f:
        file_content = f.read()

    print("A deserializar os objectos...")
    objects = list(serializers.deserialize('json', file_content))
    
    # Agrupar por modelo conservando a ordem original
    groups = []
    current_model = None
    current_group = []
    
    for obj in objects:
        if current_model != type(obj.object):
            if current_group:
                groups.append((current_model, current_group))
            current_model = type(obj.object)
            current_group = []
        current_group.append(obj)
    if current_group:
        groups.append((current_model, current_group))
    
    print(f"Preparados {len(objects)} registos em {len(groups)} blocos de modelos.")
    
    count = 0
    for model_class, group in groups:
        print(f"-> A inserir {len(group)} registos na tabela {model_class._meta.db_table}...", end=' ', flush=True)
        try:
            with transaction.atomic():
                instances = [o.object for o in group]
                # bulk_create é 1000x mais rapido que save, ignorando conflitos
                model_class.objects.bulk_create(instances, batch_size=500, ignore_conflicts=True)
                
                # Tratar chaves estrangeiras M2M que bulk_create não grava
                for obj in group:
                    if obj.m2m_data:
                        # salvar separadamente m2ms se existirem
                        for accessor_name, object_list in obj.m2m_data.items():
                            getattr(obj.object, accessor_name).set(object_list)
            print("OK!")
        except Exception as e:
            # Fallback se bulk_create falhar (por ex. herança multi-table que nao suporta bulk_create)
            print(f"Falhou o bulk_create ({str(e)[:40]}). A tentar individualmente...", end=' ')
            try:
                with transaction.atomic():
                    for o in group:
                        o.save()
                print("OK!")
            except Exception as e2:
                print(f"ERRO: {str(e2)[:40]}")
        
        count += len(group)
    
    print(f"\nFinalizado! Total={count} registos inseridos em tempo recorde.")

if __name__ == '__main__':
    load_super_fast()
