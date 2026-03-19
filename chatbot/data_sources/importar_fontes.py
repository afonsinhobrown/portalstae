# chatbot/management/commands/importar_fontes.py
from django.core.management.base import BaseCommand
from chatbot.data_sources import DataSourceManager


class Command(BaseCommand):
    help = 'Importa dados de todas as fontes externas'

    def handle(self, *args, **options):
        manager = DataSourceManager()

        # Exemplo: importar calendário eleitoral
        calendario = manager.moz_apis.get_election_data('calendario_eleitoral')

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Dados importados: {len(calendario)} itens do calendário eleitoral'
            )
        )