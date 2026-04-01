import psycopg2
try:
    print("Connecting to Neon...")
    conn = psycopg2.connect("postgresql://neondb_owner:npg_xP2dwTc1kLqn@ep-long-king-agnipa9p-pooler.c-2.eu-central-1.aws.neon.tech/portalstae?sslmode=require&channel_binding=require")
    conn.autocommit = True
    cur = conn.cursor()
    print("Dropping problematic tables...")
    cur.execute("DROP TABLE IF EXISTS rs_categoriamaterial CASCADE; DROP TABLE IF EXISTS rs_tipomaterial CASCADE;")
    print("Cleaning migration state...")
    cur.execute("DELETE FROM django_migrations WHERE app = 'rs' AND name LIKE '0008%';")
    print("Cleaning MaterialEleitoral orphans...")
    cur.execute("UPDATE rs_materialeleitoral SET tipo_dinamico_id = NULL WHERE tipo_dinamico_id IS NOT NULL;")
    print("DATABASE READY FOR INITIALIZATION.")
except Exception as e:
    print(f"ERROR: {e}")
