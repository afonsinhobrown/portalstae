import os
import csv
import glob
from django.core.management.base import BaseCommand
from django.db import transaction
from dfec.models import ResultadoEleitoral

class Command(BaseCommand):
    help = 'Importa os resultados das Eleições Autárquicas de 2018 (Mesa a Mesa)'

    def add_arguments(self, parser):
        parser.add_argument('path', type=str, help='Caminho para a pasta eleicoes')

    def handle(self, *args, **options):
        base_path = options['path']
        self.stdout.write(f"Iniciando importação de: {base_path}")

        pattern = os.path.join(base_path, "**", "*.csv")
        files = glob.glob(pattern, recursive=True)

        self.stdout.write(f"Encontrados {len(files)} arquivos CSV.")

        total_imported = 0
        
        with transaction.atomic():
            # Limpar dados existentes? Opcional.
            # ResultadoEleitoral.objects.all().delete()
            
            for file_path in files:
                filename = os.path.basename(file_path)
                
                # Identificar tipo de eleição pelo nome do arquivo
                tipo = 'AM' if ' - AM' in filename else ('PCM' if ' - PCM' in filename else 'OUTRO')
                if tipo == 'OUTRO':
                    continue

                self.stdout.write(f"Processando: {filename} ({tipo})")
                
                try:
                    self.process_file(file_path, tipo)
                    total_imported += 1
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"Erro ao processar {filename}: {str(e)}"))

        self.stdout.write(self.style.SUCCESS(f"Importação concluída! {total_imported} arquivos processados."))

    def process_file(self, file_path, tipo):
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            # Ler primeiras linhas para detectar formato
            first_line = f.readline().strip()
            
            # Alguns arquivos começam com "sep=,"
            if 'sep=' in first_line:
                # Pular essa linha e ler o cabeçalho real
                pass
            else:
                # Voltar ao início se não for sep=
                f.seek(0)

            reader = csv.DictReader(f)
            
            # Normalizar nomes de colunas (strip spaces)
            reader.fieldnames = [name.strip() for name in reader.fieldnames] if reader.fieldnames else []

            for row in reader:
                # Pular linhas vazias
                if not row.get('Província'):
                    continue

                codigo = row.get('Código da Assembleia de Voto', '').strip()
                # Remover o "." no final do código se existir (ex: "1101401 .")
                if codigo.endswith(' .'):
                    codigo = codigo[:-2]
                
                if not codigo:
                    continue

                # Criar ou atualizar
                ResultadoEleitoral.objects.update_or_create(
                    codigo_assembleia=codigo,
                    tipo_eleicao=tipo,
                    defaults={
                        'provincia_original': row.get('Província'),
                        'distrito_original': row.get('Distrito'),
                        'posto_administrativo': row.get('Posto Administrativo'),
                        'localidade': row.get('Localidade'),
                        'local_votacao': row.get('Local'),
                        'eleitores_inscritos': self.clean_int(row.get('Número de Eleitores Inscritos')),
                        'total_votantes': self.clean_int(row.get('Total de Votantes')),
                        'votos_validos': self.clean_int(row.get('Votos Válidos')),
                        'votos_nulos': self.clean_int(row.get('Votos Nulos')),
                        'votos_branco': self.clean_int(row.get('Votos em Branco')),
                        'abstencoes': self.clean_int(row.get('Abstenções')),
                        'ano': 2018
                    }
                )

    def clean_int(self, value):
        if not value:
            return 0
        try:
            return int(str(value).replace('.', '').replace(',', '').strip())
        except ValueError:
            return 0
