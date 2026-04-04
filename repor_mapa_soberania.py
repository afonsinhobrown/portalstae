import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

from circuloseleitorais.models import DivisaoAdministrativa, CirculoEleitoral
from django.db import transaction

def restore_map():
    print("--- RESTAURANDO SOBERANIA GEOGRÁFICA (STAE) ---")
    
    # Buscar todos os distritos cadastrados pela equipe de 1000 técnicos
    circulos = CirculoEleitoral.objects.all()
    if not circulos.exists():
        print("[ERRO] Nao foram encontrados dados em CirculoEleitoral. O backup precisa ser carregado primeiro.")
        return

    print(f"Encontrados {circulos.count()} registros geográficos.")

    with transaction.atomic():
        for c in circulos:
            # 1. Garantir a Província
            provincia, created = DivisaoAdministrativa.objects.get_or_create(
                nome=c.provincia.upper(),
                nivel='provincia',
                defaults={'codigo': c.codigo[:2]} # Simplificação do código
            )
            if created: print(f" > Provincia Criada: {provincia.nome}")

            # 2. Garantir o Distrito vinculado à Província
            distrito, created = DivisaoAdministrativa.objects.get_or_create(
                nome=c.nome.upper(),
                nivel='distrito',
                parent=provincia,
                defaults={'codigo': c.codigo}
            )
            if created: print(f"   + Distrito Criado: {distrito.nome}")

    print("\n[SUCESSO] Mapa de Moçambique restaurado no Cockpit Estratégico!")

if __name__ == "__main__":
    restore_map()
