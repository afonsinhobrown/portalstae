"""
MIGRAR_PARA_NEON.py
===================
Script de preparação para migrar o Portal STAE do SQLite para PostgreSQL no Neon.tech.
Base de dados de destino: portal_stae

PASSOS:
1. Cria o ficheiro settings_neon.py com as credenciais do Neon
2. Exporta os dados actuais do SQLite para JSON (fixtures)
3. Cria a base de dados no Neon via psycopg2
4. Executa as migrations Django no Neon
5. Importa os dados (fixtures) para o Neon

PRÉ-REQUISITOS:
  pip install psycopg2-binary dj-database-url

EXECUTA:
  python MIGRAR_PARA_NEON.py --connection "postgresql://USER:PASS@HOST/portal_stae?sslmode=require"
"""

import os
import sys
import subprocess
import argparse

# ─── Parse argumentos ─────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(
    description="Migrar Portal STAE SQLite → Neon PostgreSQL"
)
parser.add_argument(
    "--connection",
    type=str,
    help='Connection string Neon. Ex: "postgresql://user:pass@host/portal_stae?sslmode=require"',
    default=None
)
parser.add_argument(
    "--step",
    type=int,
    help="Executar apenas um passo específico (1-5). Default: todos",
    default=0
)
args = parser.parse_args()

# ─── Configuração ─────────────────────────────────────────────────────────────
DB_NAME        = "portal_stae"
SETTINGS_NEON  = "portalstae/settings_neon.py"
FIXTURE_FILE   = "fixtures_backup_completo.json"
DJANGO_SETTINGS_SQLITE = "portalstae.settings"
DJANGO_SETTINGS_NEON   = "portalstae.settings_neon"

NEON_CONNECTION = args.connection or os.environ.get("NEON_DATABASE_URL", "")

BANNER = """
================================================================
          PORTAL STAE - Migracao SQLite -> Neon PostgreSQL
                    Base de dados: portalstae
================================================================
"""
print(BANNER)

# ─── Utilitários ──────────────────────────────────────────────────────────────
def run(cmd, env=None, capture=False):
    """Executa um comando no shell e mostra output em tempo real."""
    print(f"\n  > {cmd}")
    result = subprocess.run(
        cmd, shell=True,
        env={**os.environ, **(env or {})},
        capture_output=capture, text=True
    )
    if result.returncode != 0:
        print(f"  [ERRO] codigo de saida: {result.returncode}")
        if capture:
            print(result.stderr)
        return False
    return True

def header(step, title):
    print(f"\n{'='*64}")
    print(f"  PASSO {step}: {title}")
    print(f"{'='*64}")


# ══════════════════════════════════════════════════════════════════════════════
# PASSO 1 — Criar settings_neon.py
# ══════════════════════════════════════════════════════════════════════════════
def passo1_criar_settings():
    header(1, "Criar settings_neon.py")

    if not NEON_CONNECTION:
        print("""
  [AVISO] Nenhuma connection string fornecida.
  Cria a base de dados no Neon.tech:
    1. Acede a https://neon.tech e cria uma conta gratuita
    2. Cria um novo projecto chamado  'portal-stae'
    3. Cria uma base de dados chamada 'portal_stae'
    4. Copia a 'Connection String' (começa com postgresql://...)
    5. Executa novamente:
       python MIGRAR_PARA_NEON.py --connection "postgresql://..."
        """)
        # Criar settings_neon.py com placeholder para o utilizador preencher
        connection_placeholder = "postgresql://USER:PASSWORD@HOST.neon.tech/portal_stae?sslmode=require"
    else:
        connection_placeholder = NEON_CONNECTION
        print(f"  [OK] Connection string recebida.")

    settings_content = f'''"""
settings_neon.py — Configuracoes de producao para Neon PostgreSQL
Herda todas as configuracoes do settings.py base e substitui apenas a DB.

COMO USAR:
  set DJANGO_SETTINGS_MODULE=portalstae.settings_neon
  python manage.py migrate
  python manage.py loaddata fixtures_backup_completo.json
"""
from .settings import *  # Herda tudo do settings base

# ── Base de dados: Neon PostgreSQL ────────────────────────────────────────────
DATABASES = {{
    "default": {{
        "ENGINE":   "django.db.backends.postgresql",
        "OPTIONS":  {{
            "service": "portal_stae",
        }},
    }}
}}

# Connection string Neon (recomendado usar variavel de ambiente em producao)
import dj_database_url
DATABASES["default"] = dj_database_url.parse(
    "{connection_placeholder}",
    conn_max_age=600,
    conn_health_checks=True,
)

# ── Segurança em producao ─────────────────────────────────────────────────────
DEBUG = False
ALLOWED_HOSTS = ["localhost", "127.0.0.1", ".neon.tech", ".railway.app", ".vercel.app"]

# SSL obrigatório para Neon
DATABASES["default"]["OPTIONS"] = {{"sslmode": "require"}}

# ── Static files em producao ──────────────────────────────────────────────────
STATIC_ROOT = BASE_DIR / "staticfiles"
'''

    with open(SETTINGS_NEON, "w", encoding="utf-8") as f:
        f.write(settings_content)

    print(f"  [OK] Criado: {SETTINGS_NEON}")
    if not NEON_CONNECTION:
        print(f"  [!]  Edita {SETTINGS_NEON} e substitui a connection string antes de continuar.")

# ══════════════════════════════════════════════════════════════════════════════
# PASSO 2 — Exportar dados actuais (SQLite → JSON Fixtures)
# ══════════════════════════════════════════════════════════════════════════════
def passo2_exportar_fixtures():
    header(2, "Exportar dados do SQLite para JSON (fixtures)")

    # Apps a exportar (por ordem para respeitar FKs)
    APPS_ORDER = [
        "auth",
        "recursoshumanos",
        "gestaoequipamentos",
        "credenciais",
        "eleicao",
        "partidos",
        "circuloseleitorais",
        "candidaturas",
        "ugea",
        "dfec",
        "rs",
        "gestaocombustivel",
        "apuramento",
        "chatbot",
        "pagina_stae",
        "admin_portal",
    ]

    env = {"DJANGO_SETTINGS_MODULE": DJANGO_SETTINGS_SQLITE, "PYTHONUTF8": "1"}

    print(f"\n  A exportar todos os dados para: {FIXTURE_FILE} (excluindo resultados eleitorais...)")
    ok = run(
        f"python manage.py dumpdata --natural-foreign --natural-primary "
        f"--indent 2 -e dfec.resultadoeleitoral -o {FIXTURE_FILE}",
        env=env
    )
    if ok:
        size = os.path.getsize(FIXTURE_FILE) / 1024
        print(f"  [OK] Fixtures exportados: {FIXTURE_FILE} ({size:.1f} KB)")
    else:
        print("  [ERRO] Falha ao exportar fixtures. A tentar app por app...")
        # Fallback: exportar app por app e concatenar
        fixtures = []
        for app in APPS_ORDER:
            tmp = f"tmp_{app}.json"
            if run(f"python manage.py dumpdata {app} --indent 2 -o {tmp}", env=env, capture=True):
                fixtures.append(tmp)
                print(f"    [OK] {app}")

        print(f"\n  Criado {len(fixtures)} ficheiros de fixtures individuais.")

# ══════════════════════════════════════════════════════════════════════════════
# PASSO 3 — Instalar dependências PostgreSQL
# ══════════════════════════════════════════════════════════════════════════════
def passo3_instalar_deps():
    header(3, "Instalar dependencias PostgreSQL")

    pkgs = ["psycopg2-binary", "dj-database-url"]
    for pkg in pkgs:
        ok = run(f"pip install {pkg}", capture=True)
        if ok:
            print(f"  [OK] {pkg} instalado")
        else:
            print(f"  [AVISO] Falha ao instalar {pkg}")

# ══════════════════════════════════════════════════════════════════════════════
# PASSO 4 — Executar Migrations no Neon
# ══════════════════════════════════════════════════════════════════════════════
def passo4_migrations_neon():
    header(4, "Executar migrations Django no Neon PostgreSQL")

    if not NEON_CONNECTION:
        print("  [SKIP] Sem connection string. Configura o Neon primeiro (Passo 1).")
        return

    env = {"DJANGO_SETTINGS_MODULE": DJANGO_SETTINGS_NEON}

    print("  A criar todas as tabelas no Neon...")
    ok = run("python manage.py migrate", env=env)
    if ok:
        print("  [OK] Todas as tabelas criadas no Neon!")
    else:
        print("  [ERRO] Verifica a connection string e a ligacao ao Neon.")

# ══════════════════════════════════════════════════════════════════════════════
# PASSO 5 — Importar Dados (Fixtures) para o Neon
# ══════════════════════════════════════════════════════════════════════════════
def passo5_importar_dados():
    header(5, "Importar dados para o Neon")

    if not NEON_CONNECTION:
        print("  [SKIP] Sem connection string.")
        return

    if not os.path.exists(FIXTURE_FILE):
        print(f"  [ERRO] Ficheiro de fixtures nao encontrado: {FIXTURE_FILE}")
        print("         Executa o Passo 2 primeiro.")
        return

    env = {"DJANGO_SETTINGS_MODULE": DJANGO_SETTINGS_NEON, "PYTHONUTF8": "1"}

    print(f"  A importar dados de: {FIXTURE_FILE}")
    ok = run(f"python manage.py loaddata {FIXTURE_FILE}", env=env)
    if ok:
        print("  [OK] Dados importados com sucesso para o Neon!")
    else:
        print("  [ERRO] Falha ao importar. Verifica os logs acima.")

# ══════════════════════════════════════════════════════════════════════════════
# SQL Script directo para criar a base de dados (se tiveres acesso directo)
# ══════════════════════════════════════════════════════════════════════════════
def gerar_sql_de_criacao():
    sql = """-- ================================================================
-- PORTAL STAE — Script SQL de criacao da base de dados Neon
-- Base de dados: portal_stae
-- Motor: PostgreSQL (via Neon.tech)
-- ================================================================

-- Nota: No Neon.tech a base de dados e criada pela interface web.
-- Este script verifica e configura configuracoes de producao.

-- Configurar encoding
SET client_encoding = 'UTF8';

-- Criar schema padrao (ja existe no Neon, mas por garantia)
CREATE SCHEMA IF NOT EXISTS public;

-- Extensoes uteis para Django
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";     -- UUIDs
CREATE EXTENSION IF NOT EXISTS "pg_trgm";       -- Full-text search trigrams
CREATE EXTENSION IF NOT EXISTS "unaccent";      -- Pesquisa sem acentos (util para pt)

-- Configurar timezone de Mocambique
SET timezone = 'Africa/Maputo';

-- ================================================================
-- CHECKLIST NEON.TECH:
-- ================================================================
-- 1. Aceder a https://neon.tech/
-- 2. Criar conta (gratuita)
-- 3. Criar novo projecto: "portal-stae"
-- 4. Criar base de dados: "portal_stae"
-- 5. Copiar a Connection String
-- 6. Executar: python MIGRAR_PARA_NEON.py --connection "postgresql://..."
-- ================================================================
"""
    with open("NEON_SETUP.sql", "w", encoding="utf-8") as f:
        f.write(sql)
    print(f"\n  [OK] Script SQL criado: NEON_SETUP.sql")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
gerar_sql_de_criacao()

passos = {
    1: passo1_criar_settings,
    2: passo2_exportar_fixtures,
    3: passo3_instalar_deps,
    4: passo4_migrations_neon,
    5: passo5_importar_dados,
}

if args.step > 0:
    # Executar apenas um passo
    if args.step in passos:
        passos[args.step]()
    else:
        print(f"[ERRO] Passo {args.step} invalido. Escolhe entre 1 e 5.")
else:
    # Executar todos os passos
    for n, fn in passos.items():
        fn()

print(f"""
{'='*64}
  CONCLUIDO!

  Proximos passos:
  1. Acede a https://neon.tech e cria o projecto 'portal-stae'
  2. Cria a base de dados 'portal_stae'
  3. Copia a Connection String do Neon
  4. Executa:
     python MIGRAR_PARA_NEON.py --connection "postgresql://..."

  Ou executa passo a passo:
     python MIGRAR_PARA_NEON.py --step 1 --connection "..."
     python MIGRAR_PARA_NEON.py --step 2
     python MIGRAR_PARA_NEON.py --step 3
     python MIGRAR_PARA_NEON.py --step 4 --connection "..."
     python MIGRAR_PARA_NEON.py --step 5 --connection "..."
{'='*64}
""")
