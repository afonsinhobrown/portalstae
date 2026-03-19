import os, dj_database_url, psycopg2

URL = "postgresql://neondb_owner:npg_xP2dwTc1kLqn@ep-long-king-agnipa9p-pooler.c-2.eu-central-1.aws.neon.tech/portalstae?sslmode=require&channel_binding=require"

def check():
    conn = psycopg2.connect(URL)
    cur = conn.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
    tables = [t[0] for t in cur.fetchall()]
    
    counts = []
    for t in tables:
        try:
            cur.execute(f'SELECT COUNT(*) FROM "{t}"')
            count = cur.fetchone()[0]
            if count > 0:
                counts.append((t, count))
        except: pass
        
    print(f"Tabelas com dados: {len(counts)} / {len(tables)}")
    # Mostrar as top 5 com mais registos
    counts.sort(key=lambda x: x[1], reverse=True)
    for t, c in counts[:10]:
        print(f"  - {t:30}: {c} registos")
    
    conn.close()

if __name__ == "__main__":
    check()
