import sqlite3

def check():
    conn = sqlite3.connect('db.sqlite3')
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cur.fetchall() if not t[0].startswith('sqlite_')]
    
    counts = []
    for t in tables:
        try:
            cur.execute(f'SELECT COUNT(*) FROM "{t}"')
            count = cur.fetchone()[0]
            if count > 0:
                counts.append((t, count))
        except: pass
        
    print(f"Tabelas com dados (SQLite local): {len(counts)} / {len(tables)}")
    counts.sort(key=lambda x: x[1], reverse=True)
    for t, c in counts[:15]:
        print(f"  - {t:40}: {c} registos")
    
    conn.close()

if __name__ == "__main__":
    check()
