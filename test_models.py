#!/usr/bin/env python
"""
Testar criação de modelos
Execute: python test_models.py
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()


def test_rh_models():
    """Testar modelos de Recursos Humanos"""
    from recursoshumanos.models import Sector, CategoriaFuncionario, Funcionario

    try:
        # Testar criação de objetos
        sector = Sector(
            nome="Direção Geral",
            codigo="DG",
            tipo="geral"
        )

        categoria = CategoriaFuncionario(
            nome="Técnico Superior",
            escala="A",
            categoria="tecnico_superior"
        )

        print("✅ Modelos de RH testados com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro nos modelos de RH: {e}")
        return False


def test_credenciais_models():
    """Testar modelos de Credenciais"""
    from credenciais.models import Solicitante, TipoCredencial, Evento

    try:
        solicitante = Solicitante(
            nome_completo="João Teste",
            tipo="singular",
            genero="masculino",
            email="joao@teste.com",
            telefone="+258841234567"
        )

        tipo_credencial = TipoCredencial(
            nome="Observador",
            categoria="externo",
            abrangencia="nacional"
        )

        evento = Evento(
            nome="Eleições 2024",
            tipo_evento="votacao",
            data_inicio="2024-10-15",
            data_fim="2024-10-15",
            localizacao="Maputo"
        )

        print("✅ Modelos de Credenciais testados com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro nos modelos de Credenciais: {e}")
        return False


def test_all_models():
    """Testar todos os modelos"""
    print("🧪 TESTANDO MODELOS DO SISTEMA")
    print("=" * 40)

    tests = [test_rh_models, test_credenciais_models]

    for test in tests:
        test()

    print("=" * 40)
    print("✅ Testes de modelos concluídos!")


if __name__ == "__main__":
    test_all_models()