import csv, sqlite3, psycopg2, os

SQLITE_DB = "db.sqlite3"
NEON_URL = "postgresql://neondb_owner:npg_xP2dwTc1kLqn@ep-long-king-agnipa9p-pooler.c-2.eu-central-1.aws.neon.tech/portalstae?sslmode=require&channel_binding=require"
TMP_CSV = "resultados.csv"

def fast_copy():
    # 1. Exportar SQLite para CSV
    print("[1/3] A extrair Resultados do SQLite para CSV...")
    s_conn = sqlite3.connect(SQLITE_DB)
    cur = s_conn.cursor()
    cur.execute("SELECT * FROM dfec_resultadoeleitoral")
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    
    with open(TMP_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(cols)
        writer.writerows(rows)
    s_conn.close()
    
    # 2. Upload para Neon via COPY (Brutalmente rapido)
    print(f"[2/3] Uploading {len(rows)} registos para o Neon via TURBO-COPY...")
    p_conn = psycopg2.connect(NEON_URL)
    p_cur = p_conn.cursor()
    
    with open(TMP_CSV, "r", encoding="utf-8") as f:
        next(f) # Skip header
        p_cur.copy_from(f, "dfec_resultadoeleitoral", sep=",", columns=cols)
    
    p_conn.commit()
    print("[3/3] Dados de resultados no Neon com sucesso!")
    p_conn.close()
    
    if os.path.exists(TMP_CSV): os.remove(TMP_CSV)

if __name__ == "__main__":
    fast_copy()
