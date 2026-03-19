import sqlite3, psycopg2, psycopg2.extras, os

SQLITE_DB = "db.sqlite3"
NEON_URL = "postgresql://neondb_owner:npg_xP2dwTc1kLqn@ep-long-king-agnipa9p-pooler.c-2.eu-central-1.aws.neon.tech/portalstae?sslmode=require&channel_binding=require"

APPS = [
    'dfec_', 'gestaocombustivel_', 'gestaoequipamentos_', 'rs_', 
    'recursoshumanos_', 'ugea_', 'candidaturas_', 'apuramento_', 
    'credenciais_', 'circuloseleitorais_', 'partidos_', 'eleicao_',
    'pagina_stae_', 'chatbot_', 'admin_portal_'
]

def clean_val(v):
    if v and isinstance(v, str):
        return "".join([c if ord(c) < 128 else " " for c in v])
    return v

def migrate_massive():
    print("[SPEED-MODE] Ligacao ao Neon...")
    s_conn = sqlite3.connect(SQLITE_DB)
    s_cur = s_conn.cursor()
    p_conn = psycopg2.connect(NEON_URL)
    p_cur = p_conn.cursor()
    
    # 1. Pegar tabelas por ordem de depencia (simples: primeiro as que nao terminam com _m2m)
    p_cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
    all_raw = p_cur.fetchall()
    tables = [t[0] for t in all_raw if any(t[0].startswith(a) for a in APPS)]
    if 'auth_user' in [t[0] for t in all_raw]: tables.append('auth_user')
    
    # Ordenar: primeiro as tabelas base, depois as de ligacao (_membro, _equipa, _m2m)
    tables.sort(key=lambda x: 1 if ('_m2m' in x or '_envolvidos' in x or '_membros' in x) else 0)

    print(f"Migrando {len(tables)} tabelas via TRUNCATE-INSERT...")

    for tname in tables:
        try:
            p_cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{tname}'")
            col_info = p_cur.fetchall()
            bool_cols = {c[0] for c in col_info if c[1] == 'boolean'}
            
            s_cur.execute(f'SELECT * FROM "{tname}"')
            rows = s_cur.fetchall()
            if not rows: continue
            cols = [d[0] for d in s_cur.description]
            
            final_rows = [
                tuple(bool(v) if cols[i] in bool_cols and v is not None else clean_val(v) for i, v in enumerate(r))
                for r in rows
            ]

            print(f"  > {tname:35} | {len(rows):6} registos... ", end="", flush=True)
            
            # TRUNCATE + INSERT (Modo Limpeza Total)
            p_cur.execute(f'TRUNCATE TABLE "{tname}" CASCADE')
            
            placeholders = ",".join(["%s"] * len(cols))
            col_list = ",".join([f'"{c}"' for c in cols])
            sql = f'INSERT INTO "{tname}" ({col_list}) VALUES ({placeholders})'
            
            psycopg2.extras.execute_batch(p_cur, sql, final_rows, page_size=1000)
            p_conn.commit()
            print("OK.", flush=True)
            
        except Exception as e:
            p_conn.rollback()
            print(f"SKIP ({str(e)[:40]}...)")

    print("\n[OK] MIGRACAO CONCLUIDA COM SUCESSO.")
    s_conn.close()
    p_conn.close()

if __name__ == "__main__":
    migrate_massive()
