import os
import django
import sys
from django.db import connection

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

def fix_eleicao_constraint():
    with connection.cursor() as cursor:
        print("Tornando eleicao_id opcional no Neon DB...")
        
        # SQL para alterar a coluna para NULL
        sql_commands = [
            'ALTER TABLE rs_materialeleitoral ALTER COLUMN eleicao_id DROP NOT NULL;',
        ]
        
        for sql in sql_commands:
            try:
                cursor.execute(sql)
                print(f"SUCESSO: {sql}")
            except Exception as e:
                print(f"IGNORADO: {sql} - {e}")
        
        print("Limpeza de constrangimentos concluída.")

if __name__ == "__main__":
    fix_eleicao_constraint()
