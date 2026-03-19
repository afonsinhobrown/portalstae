#!/usr/bin/env python
"""
Script completo de teste e deploy
Execute: python deploy_test.py
"""

import subprocess
import sys
import os


def run_command(command, description):
    """Executar comando e verificar resultado"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - OK")
            return True
        else:
            print(f"❌ {description} - Erro: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - Exceção: {e}")
        return False


def main():
    """Executar processo completo"""
    print("🚀 INICIANDO DEPLOY TEST DO PORTAL STAE")
    print("=" * 60)

    # Lista de comandos para testar
    commands = [
        ("python test_setup.py", "Teste de configuração"),
        ("python manage.py check", "Verificação do Django"),
        ("python manage.py makemigrations --dry-run", "Teste de migrações"),
        ("python test_models.py", "Teste de modelos"),
        ("python manage.py test --verbosity=0", "Testes unitários"),
    ]

    results = []
    for command, description in commands:
        success = run_command(command, description)
        results.append(success)

    print("=" * 60)
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"🎉 DEPLOY TEST BEM SUCEDIDO! ({passed}/{total})")
        print("\n📋 PRÓXIMOS PASSOS:")
        print("1. python manage.py makemigrations")
        print("2. python manage.py migrate")
        print("3. python manage.py createsuperuser")
        print("4. python manage.py runserver")
    else:
        print(f"⚠ DEPLOY TEST COM ERROS ({passed}/{total})")
        print("❌ Verifique os erros acima antes de prosseguir")


if __name__ == "__main__":
    main()