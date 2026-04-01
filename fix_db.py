
import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

def fix():
    print("Iniciando injeção de colunas geográficas...")
    with connection.cursor() as cursor:
        try:
            cursor.execute("ALTER TABLE rs_alocacaologistica ADD COLUMN num_distritos INTEGER DEFAULT 0;")
            print("[OK] Coluna num_distritos adicionada.")
        except Exception as e:
            print(f"[AVISO] num_distritos: {e}")
            
        try:
            cursor.execute("ALTER TABLE rs_alocacaologistica ADD COLUMN num_mesas INTEGER DEFAULT 0;")
            print("[OK] Coluna num_mesas adicionada.")
        except Exception as e:
            print(f"[AVISO] num_mesas: {e}")

        try:
            cursor.execute("ALTER TABLE rs_materialeleitoral ALTER COLUMN eleicao_id DROP NOT NULL;")
            print("[OK] Coluna eleicao_id ajustada para permitir nulos.")
        except Exception as e:
            print(f"[AVISO] eleicao_id: {e}")

    print("Processo concluído.")

if __name__ == "__main__":
    fix()
