from django.core.management.base import BaseCommand
from credenciais.models import ModeloCredencial


class Command(BaseCommand):
    help = 'Cria modelos de credencial com diferentes tamanhos'

    def handle(self, *args, **kwargs):
        tamanhos = [
            {
                'nome': 'Modelo STAE Padrão (ID-1)',
                'descricao': 'Tamanho padrão internacional ID-1 (cartão de crédito)',
                'tamanho': '85x54',
            },
            {
                'nome': 'Modelo STAE Compacto (ID-000)',
                'descricao': 'Tamanho compacto ID-000',
                'tamanho': '66x45',
            },
            {
                'nome': 'Modelo STAE Grande (ID-2)',
                'descricao': 'Tamanho grande ID-2',
                'tamanho': '105x74',
            },
            {
                'nome': 'Modelo STAE Extra Grande (ID-3)',
                'descricao': 'Tamanho extra grande ID-3',
                'tamanho': '125x88',
            },
            {
                'nome': 'Modelo STAE Crachá Vertical',
                'descricao': 'Crachá vertical para eventos',
                'tamanho': '54x85',
            },
            {
                'nome': 'Modelo STAE Crachá Horizontal',
                'descricao': 'Crachá horizontal para eventos',
                'tamanho': '100x70',
            }
        ]

        self.stdout.write("Criando modelos de credencial...")
        for modelo_data in tamanhos:
            modelo, created = ModeloCredencial.objects.get_or_create(
                nome=modelo_data['nome'],
                defaults={
                    'descricao': modelo_data['descricao'],
                    'tamanho': modelo_data['tamanho'],
                    'cor_fundo': '#ffffff',
                    'cor_texto': '#000000',
                    'ativo': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Criado: {modelo.nome} ({modelo.tamanho}mm)'))
            else:
                self.stdout.write(f'- Já existe: {modelo.nome} ({modelo.tamanho}mm)')

        total = ModeloCredencial.objects.filter(ativo=True).count()
        self.stdout.write(self.style.SUCCESS(f'\nTotal de modelos ativos: {total}'))
