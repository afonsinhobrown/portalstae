
import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

def fix_db():
    with connection.cursor() as cursor:
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ugea_itemcadernoencargos'")
        row = cursor.fetchone()
        if not row:
            print("Criando tabela ugea_itemcadernoencargos manualmente...")
            cursor.execute("""
                CREATE TABLE "ugea_itemcadernoencargos" (
                    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                    "descricao" varchar(200) NOT NULL,
                    "quantidade_estimada" decimal NULL,
                    "unidade" varchar(20) NULL,
                    "caderno_id" bigint NOT NULL REFERENCES "ugea_cadernoencargos" ("id") DEFERRABLE INITIALLY DEFERRED
                )
            """)
            print("Tabela criada.")
        else:
            print("Tabela ja existe.")

if __name__ == "__main__":
    fix_db()
