import os, sqlite3

db = 'db.sqlite3'
size_mb = os.path.getsize(db) / (1024*1024)
conn = sqlite3.connect(db)
cur = conn.cursor()
tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
print(f"Tamanho: {size_mb:.2f} MB")
print(f"Total de tabelas: {len(tables)}")
print("---TABELAS---")
for t in tables:
    try:
        count = cur.execute(f'SELECT COUNT(*) FROM "{t[0]}"').fetchone()[0]
        print(f"{t[0]}: {count} registos")
    except Exception as e:
        print(f"{t[0]}: ERRO - {e}")
conn.close()
