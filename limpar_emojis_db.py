import sqlite3

DB_FILE = "db.sqlite3"
SEARCH_CHAR = "\u2705" # The checkmark emoji

def clean_database():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # Obter todas as tabelas
    tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    
    for t in tables:
        tname = t[0]
        try:
            # Identifica colunas de texto
            columns_info = cur.execute(f'PRAGMA table_info("{tname}")').fetchall()
            text_cols = [c[1] for c in columns_info if "CHAR" in str(c[2]).upper() or "TEXT" in str(c[2]).upper()]
            
            for col in text_cols:
                # Selecionar registos que têm carateres não-ASCII
                rows = cur.execute(f'SELECT rowid, "{col}" FROM "{tname}"').fetchall()
                for rowid, val in rows:
                    if val and any(ord(c) > 127 for c in str(val)):
                        # Limpar carateres especiais
                        new_val = "".join([c if ord(c) < 128 else " " for c in str(val)])
                        cur.execute(f'UPDATE "{tname}" SET "{col}" = ? WHERE rowid = ?', (new_val, rowid))
                        print(f"[FIX] Limpou especial em {tname}.{col} (row {rowid})")
        except Exception as e:
            pass
            
    conn.commit()
    conn.close()
    print("[LIMPEZA GLOBAL CONCLUIDA]")

if __name__ == "__main__":
    clean_database()
