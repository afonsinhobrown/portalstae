# create_groups.py (executar uma vez)
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

from django.contrib.auth.models import Group
from django.conf import settings


def criar_grupos_iniciais():
    grupos = getattr(settings, 'GRUPOS_PADRAO', [
        'STAE',
        'ADMINISTRADORES',
        'TECNICOS',
        'GESTORES_COMBUSTIVEL',
        'PUBLICO',
    ])

    for grupo_nome in grupos:
        Group.objects.get_or_create(name=grupo_nome)
        print(f"Grupo criado: {grupo_nome}")

    print("Grupos criados com sucesso!")


if __name__ == '__main__':
    criar_grupos_iniciais()