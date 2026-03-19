#!/usr/bin/env python
import os
import sys
import django
from pathlib import Path


def setup_django():
    project_root = Path(__file__).parent
    sys.path.append(str(project_root))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
    django.setup()


def check_apps():
    from django.apps import apps

    print("🔍 VERIFICAÇÃO FINAL DE APPS")
    print("=" * 50)

    apps_to_check = [
        'admin_portal',
        'recursoshumanos',
        'gestaoequipamentos',
        'gestaocombustivel',
        'credenciais'
    ]

    for app in apps_to_check:
        try:
            app_config = apps.get_app_config(app)
            # Converter generator para lista para contar
            models = list(app_config.get_models())
            print(f"✅ {app}: {len(models)} modelos | {app_config.verbose_name}")

            # Listar os modelos
            for model in models:
                print(f"   - {model.__name__}")

        except Exception as e:
            print(f"❌ {app}: {e}")


def check_migrations():
    """Verificar status das migrações"""
    print("\n📊 STATUS DAS MIGRAÇÕES:")
    print("=" * 30)

    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT app, name FROM django_migrations ORDER BY app, applied")
        migrations = cursor.fetchall()

        current_app = None
        for app, migration in migrations:
            if app != current_app:
                print(f"\n📦 {app}:")
                current_app = app
            print(f"   ✅ {migration}")


if __name__ == "__main__":
    setup_django()
    check_apps()
    check_migrations()