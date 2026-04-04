import sqlite3
import os

def auditoria_base_dados():
    db_path = 'db.sqlite3'
    if not os.path.exists(db_path):
        print(f"ERRO: Ficheiro {db_path} não encontrado na raiz.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. LISTAR ELEIÇÕES (A VERDADE ÓBVIA)
        print("\n--- [AUDITORIA] ELEIÇÕES CONFIGURADAS ---")
        try:
            cursor.execute("SELECT id, nome, ano, tipo, ativo FROM eleicao_eleicao ORDER BY ano DESC")
            eleicoes = cursor.fetchall()
            for e in eleicoes:
                print(f"ID: {e[0]} | NOME: {e[1]} | ANO: {e[2]} | TIPO: {e[3]} | ATIVO: {e[4]}")
        except:
            print("Tabela eleicao_eleicao não encontrada.")

        # 2. LISTAR PLANOS LOGÍSTICOS ATIVOS
        print("\n--- [AUDITORIA] PLANOS LOGÍSTICOS ---")
        try:
            cursor.execute("SELECT id, nome, eleicao_id, esta_ativo FROM rs_planologistico")
            planos = cursor.fetchall()
            for p in planos:
                print(f"ID: {p[0]} | NOME: {p[1]} | ELEICAO_ID: {p[2]} | STATUS: {p[3]}")
        except:
            print("Tabela rs_planologistico não encontrada.")

        conn.close()
    except Exception as e:
        print(f"ERRO DE ACESSO: {e}")

if __name__ == "__main__":
    auditoria_base_dados()
