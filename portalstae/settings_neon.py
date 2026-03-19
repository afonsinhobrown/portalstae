"""
settings_neon.py — Configuracoes de producao para Neon PostgreSQL
Herda todas as configuracoes do settings.py base e substitui apenas a DB.

COMO USAR:
  set DJANGO_SETTINGS_MODULE=portalstae.settings_neon
  python manage.py migrate
  python manage.py loaddata fixtures_backup_completo.json
"""
from .settings import *  # Herda tudo do settings base

# ── Base de dados: Neon PostgreSQL ────────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE":   "django.db.backends.postgresql",
        "OPTIONS":  {
            "service": "portal_stae",
        },
    }
}

# Connection string Neon (recomendado usar variavel de ambiente em producao)
import dj_database_url
DATABASES["default"] = dj_database_url.parse(
    "postgresql://neondb_owner:npg_xP2dwTc1kLqn@ep-long-king-agnipa9p-pooler.c-2.eu-central-1.aws.neon.tech/portalstae?sslmode=require&channel_binding=require",
    conn_max_age=600,
    conn_health_checks=True,
)

# ── Segurança em producao ─────────────────────────────────────────────────────
DEBUG = False
ALLOWED_HOSTS = ["localhost", "127.0.0.1", ".neon.tech", ".railway.app", ".vercel.app"]

# SSL obrigatório para Neon
DATABASES["default"]["OPTIONS"] = {"sslmode": "require"}

# ── Static files em producao ──────────────────────────────────────────────────
STATIC_ROOT = BASE_DIR / "staticfiles"
