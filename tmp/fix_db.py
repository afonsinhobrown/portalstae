import os
import django
import sys
from django.db import connection

# Adiciona o diretório atual ao path do Python
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
try:
    django.setup()
except Exception as e:
    print(f"Erro no setup do Django: {e}")
    sys.exit(1)

def fix():
    with connection.cursor() as cursor:
        print("Limpando colunas obsoletas no Neon DB...")
        
        # Tabelas a limpar
        sql_commands = [
            'ALTER TABLE rs_materialeleitoral DROP COLUMN IF EXISTS localizacao_destino CASCADE;',
            'ALTER TABLE rs_materialeleitoral DROP COLUMN IF EXISTS tipo CASCADE;',
            'ALTER TABLE rs_materialeleitoral DROP COLUMN IF EXISTS equipamentos_vinculados CASCADE;',
            'ALTER TABLE rs_planologistico DROP COLUMN IF EXISTS tipo CASCADE;',
        ]
        
        for sql in sql_commands:
            try:
                cursor.execute(sql)
                print(f"SUCESSO: {sql}")
            except Exception as e:
                print(f"IGNORADO: {sql} - {e}")
        
        print("Limpeza concluída com sucesso.")

if __name__ == "__main__":
    fix()
