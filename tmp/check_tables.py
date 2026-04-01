import os
import django
import sys
from django.db import connection

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

def check_tables():
    with connection.cursor() as cursor:
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
        tables = [t[0] for t in cursor.fetchall()]
        print("Tabelas encontradas:")
        print(tables)
        
        target_tables = ['rs_atividadeplano', 'rs_alocacaologistica']
        for table in target_tables:
            if table in tables:
                print(f"EXISTE: {table}")
            else:
                print(f"FALTA: {table}")

if __name__ == "__main__":
    check_tables()
