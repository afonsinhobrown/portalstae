import pandas as pd
import os
from django.core.files import File
from .models import FAQEntry, DocumentoLegal


class DataImporter:
    def import_from_excel(self, file_path):
        """Importa FAQs de ficheiro Excel"""
        try:
            df = pd.read_excel(file_path)
            created_count = 0

            for index, row in df.iterrows():
                obj, created = FAQEntry.objects.get_or_create(
                    pergunta=row['pergunta'],
                    defaults={
                        'resposta': row['resposta'],
                        'tags': row.get('tags', '').split(','),
                        'fonte': row.get('fonte', 'Excel Import')
                    }
                )
                if created:
                    created_count += 1

            return f"Importadas {created_count} novas FAQs de {len(df)} linhas"

        except Exception as e:
            return f"Erro na importação: {str(e)}"

    def import_from_csv(self, file_path):
        """Importa de CSV"""
        try:
            df = pd.read_csv(file_path)
            created_count = 0

            for index, row in df.iterrows():
                obj, created = FAQEntry.objects.get_or_create(
                    pergunta=row['pergunta'],
                    defaults={
                        'resposta': row['resposta'],
                        'tags': row.get('tags', '').split(','),
                        'fonte': row.get('fonte', 'CSV Import')
                    }
                )
                if created:
                    created_count += 1

            return f"Importadas {created_count} novas FAQs de {len(df)} linhas"

        except Exception as e:
            return f"Erro na importação CSV: {str(e)}"