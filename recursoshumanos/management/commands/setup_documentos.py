# management/commands/setup_documentos.py
from django.core.management.base import BaseCommand
from recursoshumanos.models import TipoDocumento


class Command(BaseCommand):
    help = 'Configura tipos de documentos padrão'

    def handle(self, *args, **kwargs):
        tipos = [
            {
                'codigo': 'REL-ANUAL',
                'nome': 'Relatório Anual de Atividades',
                'descricao': 'Relatório anual das atividades realizadas',
                'template_html': '''
                    <div class="documento">
                        <h1>{{ titulo }}</h1>
                        <div class="meta">
                            <strong>Nº:</strong> {{ numero_oficio }}<br>
                            <strong>Data:</strong> {{ data_documento }}<br>
                            <strong>Setor:</strong> {{ setor_elaborador }}
                        </div>

                        <h2>1. INTRODUÇÃO</h2>
                        <p>{{ introducao }}</p>

                        <h2>2. OBJETIVOS</h2>
                        <p>{{ objetivos }}</p>

                        <h2>3. ATIVIDADES REALIZADAS</h2>
                        <p>{{ atividades }}</p>

                        <h2>4. RESULTADOS</h2>
                        <p>{{ resultados }}</p>

                        <h2>5. CONCLUSÕES E RECOMENDAÇÕES</h2>
                        <p>{{ conclusoes }}</p>
                    </div>
                ''',
                'campos_obrigatorios': ['titulo', 'introducao', 'objetivos', 'atividades', 'resultados'],
                'campos_opcionais': ['conclusoes', 'recomendacoes', 'anexos'],
                'estrutura': ['introducao', 'objetivos', 'atividades', 'resultados', 'conclusoes']
            },
            # ... mais tipos
        ]

        for tipo_data in tipos:
            tipo, created = TipoDocumento.objects.update_or_create(
                codigo=tipo_data['codigo'],
                defaults=tipo_data
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'Tipo criado: {tipo.nome}'))
            else:
                self.stdout.write(self.style.WARNING(f'Tipo atualizado: {tipo.nome}'))