import psycopg2

URL = "postgresql://neondb_owner:npg_xP2dwTc1kLqn@ep-long-king-agnipa9p-pooler.c-2.eu-central-1.aws.neon.tech/portalstae?sslmode=require&channel_binding=require"

def reset():
    conn = psycopg2.connect(URL)
    cur = conn.cursor()
    cur.execute("""
    DO $$ 
    DECLARE 
        r RECORD;
    BEGIN
        FOR r IN (SELECT table_name FROM information_schema.tables WHERE table_schema = 'public') LOOP
            BEGIN
                EXECUTE 'SELECT setval(pg_get_serial_sequence(' || quote_literal(r.table_name) || ', ''id''), COALESCE(MAX(id), 1)) FROM ' || quote_ident(r.table_name);
            EXCEPTION WHEN OTHERS THEN CONTINUE;
            END;
        END LOOP;
    END $$;
    """)
    conn.commit()
    print("ID Sequences resetados com sucesso no Neon.")
    conn.close()

if __name__ == "__main__":
    reset()
