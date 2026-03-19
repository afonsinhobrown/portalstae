from django.core.management.base import BaseCommand
from chatbot.mozambique_sources import MozambiqueDataSources


class Command(BaseCommand):
    help = 'Carrega dados iniciais do STAE para o chatbot'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Apaga dados existentes antes de carregar',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('A apagar FAQs existentes...')
            from chatbot.models import FAQEntry
            FAQEntry.objects.all().delete()

        data_loader = MozambiqueDataSources()
        created_count = data_loader.load_initial_knowledge()

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Carregadas {created_count} FAQs iniciais do STAE Moçambique'
            )
        )

        # Estatísticas
        from chatbot.models import FAQEntry
        total_faqs = FAQEntry.objects.count()
        self.stdout.write(f'📊 Total de FAQs na base: {total_faqs}')