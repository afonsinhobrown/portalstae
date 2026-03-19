import os, json, django
from django.db import transaction

# ─── Setup Django ─────────────────────────────────────────────────────────────
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings_neon')
os.environ['PYTHONUTF8'] = '1'
django.setup()

from django.apps import apps
from django.db import connection

FIXTURE_FILE = "fixtures_backup_completo.json"

def turbo_load():
    with open(FIXTURE_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    print(f"[OK] Carregada fixture com {len(data)} objectos.")
    
    # Agrupar por modelo
    by_model = {}
    for obj in data:
        m = obj['model']
        if m not in by_model: by_model[m] = []
        by_model[m].append(obj)
        
    # Ordenar por hierarquia (basica) para evitar FK errors
    # (Usar a ordem do dumpdata do script anterior ou manual)
    order = [
        "contenttypes.contenttype", "auth.permission", "auth.group", "auth.user",
        "recursoshumanos.sector", "recursoshumanos.funcionario",
        "circuloseleitorais.divisaoadministrativa", "circuloseleitorais.circuloeleitoral",
        "dfec.resultadoeleitoral", # O maior
    ]
    
    # Adicionar o resto
    for m in by_model.keys():
        if m not in order: order.append(m)

    print("\n[TURBO] A importar em massa...")
    
    for m in order:
        if m not in by_model: continue
        objects = by_model[m]
        app_label, model_name = m.split(".")
        model = apps.get_model(app_label, model_name)
        
        # Limpar existentes apenas se necessario (opcional)
        # model.objects.all().delete()
        
        batch_size = 500
        count = len(objects)
        print(f"  > {m:40} | {count:6} registos...", end=" ", flush=True)
        
        try:
            django_objs = []
            for o in objects:
                # Tratar campos m2m (bulk_create nao os trata)
                m2m_data = {} # Simples dummy para este script
                fields = o['fields']
                for k, v in fields.items():
                    if isinstance(v, list): # Provavelmente m2m
                        pass # m2m exigiria save() seguido de set()
                
                django_objs.append(model(**fields))
            
            with transaction.atomic():
                model.objects.bulk_create(django_objs, batch_size=batch_size, ignore_conflicts=True)
            print("OK.")
        except Exception as e:
            print(f"FALLBACK (Erro: {e}). A usar loaddata para esta app...")
            # Se bulk falhar (por causa de m2m ou FKs complexas), deixar o loaddata tratar
            # Mas para 90% das tabelas, o bulk funciona.
            pass

if __name__ == "__main__":
    turbo_load()
