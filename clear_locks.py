import psycopg2

URL = "postgresql://neondb_owner:npg_xP2dwTc1kLqn@ep-long-king-agnipa9p-pooler.c-2.eu-central-1.aws.neon.tech/portalstae?sslmode=require&channel_binding=require"

try:
    conn = psycopg2.connect(URL)
    conn.autocommit = True
    cur = conn.cursor()
    
    # Check what is locking
    cur.execute("""
        SELECT pg_terminate_backend(pid) 
        FROM pg_stat_activity 
        WHERE datname='portalstae' AND state in ('idle in transaction', 'active') 
        AND pid <> pg_backend_pid();
    """)
    res = cur.fetchall()
    print("Terminated processes:", len(res))
    
    conn.close()
except Exception as e:
    print("Error:", e)
