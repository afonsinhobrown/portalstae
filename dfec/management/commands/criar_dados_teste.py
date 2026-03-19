# dfec/management/commands/criar_dados_teste.py
from django.core.management.base import BaseCommand
from dfec.models import *
from django.contrib.auth.models import User
import random
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Cria dados de teste para o sistema Dfec'

    def handle(self, *args, **kwargs):
        # Criar usuário admin se não existir
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin123')

        self.stdout.write('Dados de teste criados com sucesso!')