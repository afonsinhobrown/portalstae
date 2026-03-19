#!/usr/bin/env python
"""
Script de teste para verificar configuração do Portal STAE
Execute: python test_setup.py
"""

import os
import sys
import django
from pathlib import Path


def test_django_setup():
    """Testar configuração do Django"""
    try:
        # Adicionar o diretório do projeto ao path
        project_root = Path(__file__).parent
        sys.path.append(str(project_root))

        # Configurar settings do Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
        django.setup()

        print("✅ Django configurado com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro na configuração do Django: {e}")
        return False


def test_apps_import():
    """Testar importação das apps"""
    try:
        from admin_portal import models as admin_models
        from recursoshumanos import models as rh_models
        from gestaoequipamentos import models as equip_models
        from gestaocombustivel import models as comb_models
        from credenciais import models as cred_models

        print("✅ Todas as apps importadas com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro na importação das apps: {e}")
        return False


def test_directories():
    """Verificar estrutura de diretórios"""
    required_dirs = [
        'portalstae',
        'admin_portal',
        'recursoshumanos',
        'gestaoequipamentos',
        'gestaocombustivel',
        'credenciais',
        'templates',
        'static/css',
        'static/js',
        'static/images',
        'media'
    ]

    missing_dirs = []
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            missing_dirs.append(dir_path)

    if missing_dirs:
        print(f"❌ Diretórios em falta: {missing_dirs}")
        return False
    else:
        print("✅ Estrutura de diretórios completa!")
        return True


def test_required_files():
    """Verificar ficheiros essenciais"""
    required_files = [
        'manage.py',
        'portalstae/settings.py',
        'portalstae/urls.py',
        'admin_portal/models.py',
        'recursoshumanos/models.py',
        'gestaoequipamentos/models.py',
        'gestaocombustivel/models.py',
        'credenciais/models.py'
    ]

    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)

    if missing_files:
        print(f"❌ Ficheiros em falta: {missing_files}")
        return False
    else:
        print("✅ Ficheiros essenciais presentes!")
        return True


def main():
    """Executar todos os testes"""
    print("🧪 INICIANDO TESTES DO PORTAL STAE")
    print("=" * 50)

    tests = [
        test_directories,
        test_required_files,
        test_django_setup,
        test_apps_import
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Erro no teste {test.__name__}: {e}")
            results.append(False)

    print("=" * 50)
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"🎉 TODOS OS {total} TESTES PASSARAM!")
        print("🚀 O projeto está pronto para uso!")
    else:
        print(f"⚠ {passed}/{total} testes passaram")
        print("❌ Verifique os erros acima")


if __name__ == "__main__":
    main()