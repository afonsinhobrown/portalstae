import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

from django.db import connection

def reparar_banco():
    print("--- REPARAÇÃO DE EMERGÊNCIA: COCKPIT STAE ---")
    print("Sincronizando estrutura do banco Neon com o modelo restaurado...")
    
    with connection.cursor() as cursor:
        try:
            # 1. Reparar Materiais
            print("Verificando coluna 'localizacao_destino' em MaterialEleitoral...")
            cursor.execute("ALTER TABLE rs_materialeleitoral ADD COLUMN IF NOT EXISTS localizacao_destino VARCHAR(100);")
            
            # 2. Reparar Atividades
            print("Verificando coluna 'responsaveis' em AtividadePlano...")
            cursor.execute("ALTER TABLE rs_atividadeplano ADD COLUMN IF NOT EXISTS responsaveis TEXT;")
            
            print("\n[SUCESSO] Estrutura restaurada com soberania total!")
            print("Já pode carregar a página do Cockpit novamente.")
        except Exception as e:
            print(f"\n[ERRO] Falha na reparação: {e}")

if __name__ == "__main__":
    reparar_banco()
