import os
import django
import sys
from django.db import connection

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

def check_columns():
    with connection.cursor() as cursor:
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'rs_materialeleitoral';")
        cols = [c[0] for c in cursor.fetchall()]
        print("Colunas de rs_materialeleitoral:")
        print(cols)

if __name__ == "__main__":
    check_columns()
