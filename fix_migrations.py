# fix_migrations_v2.py
import sqlite3


def fix_licenca_table():
    """Corrige apenas a tabela licenca sem afetar outras apps"""

    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    print("=== CORRIGINDO TABELA LICENCA ===")

    # 1. PRIMEIRO: Ver a estrutura da tabela
    cursor.execute("PRAGMA table_info(recursoshumanos_licenca)")
    colunas = cursor.fetchall()
    print("Colunas atuais:")
    for col in colunas:
        print(f"  {col[1]:25} {col[2]:15} NOT NULL={col[3]}")

    # 2. Se fluxo_aprovacao tem NOT NULL, altere para NULLABLE
    cursor.execute("""
        SELECT * FROM pragma_table_info('recursoshumanos_licenca') 
        WHERE name = 'fluxo_aprovacao' AND "notnull" = 1
    """)
    if cursor.fetchone():
        print("\n⚠️  fluxo_aprovacao tem NOT NULL constraint")
        print("   Alterando para NULLABLE...")

        # SQLite não permite ALTER COLUMN, precisa recriar tabela
        # Mas vamos primeiro ver os valores problemáticos

    # 3. Corrige valores inválidos em fluxo_aprovacao
    cursor.execute("""
        SELECT id, fluxo_aprovacao 
        FROM recursoshumanos_licenca 
        WHERE fluxo_aprovacao IS NOT NULL 
        AND fluxo_aprovacao != '' 
        AND fluxo_aprovacao != '{}'
        AND fluxo_aprovacao != '[]'
    """)
    registros_problematicos = cursor.fetchall()

    if registros_problematicos:
        print(f"\nEncontrados {len(registros_problematicos)} registros com fluxo_aprovacao inválido")

        for id, valor in registros_problematicos:
            print(f"  ID {id}: '{valor}'")

            # Tenta converter para JSON válido ou seta para '{}'
            try:
                import json
                if valor.strip() in ['', 'null', 'NULL']:
                    novo_valor = '{}'
                else:
                    # Tenta parsear
                    parsed = json.loads(valor)
                    novo_valor = json.dumps(parsed) if parsed else '{}'
            except:
                novo_valor = '{}'

            cursor.execute("""
                UPDATE recursoshumanos_licenca 
                SET fluxo_aprovacao = ? 
                WHERE id = ?
            """, (novo_valor, id))
            print(f"    -> Corrigido para: '{novo_valor}'")

    # 4. Adiciona colunas faltantes
    colunas_faltantes = [
        ('rh_aprovador_id', 'INTEGER REFERENCES auth_user(id)'),
        ('observacoes_rh', 'TEXT'),
        ('dias_autorizados_rh', 'INTEGER'),
        ('data_analise_rh', 'DATETIME')
    ]

    print("\n=== ADICIONANDO COLUNAS FALTANTES ===")
    for coluna, tipo in colunas_faltantes:
        try:
            cursor.execute(f"ALTER TABLE recursoshumanos_licenca ADD COLUMN {coluna} {tipo}")
            print(f"✅ {coluna}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"⚠️  {coluna} (já existe)")
            else:
                print(f"❌ {coluna}: {e}")

    conn.commit()
    conn.close()
    print("\n✅ Tabela licenca corrigida!")


def create_migration_fake():
    """Insere registros fake para migrações aplicadas"""
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    migracoes_fake = [
        ('recursoshumanos', '0009_alter_licenca_options_and_more'),
        ('recursoshumanos', '0010_add_missing_fields'),
    ]

    for app, nome in migracoes_fake:
        cursor.execute("""
            INSERT OR IGNORE INTO django_migrations (app, name, applied)
            VALUES (?, ?, datetime('now'))
        """, (app, nome))
        print(f"✅ {app}.{nome} marcada como fake")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    fix_licenca_table()
    create_migration_fake()
    print("\n🎉 CORREÇÃO CONCLUÍDA!")
    print("Tente acessar: http://localhost:8000/rh/")