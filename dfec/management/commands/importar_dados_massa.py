from django.core.management.base import BaseCommand
import os
import unicodedata
from django.conf import settings
from dfec.services import ImportacaoService

class Command(BaseCommand):
    help = 'Carrega dados eleitorais em massa das pastas padronizadas'

    def handle(self, *args, **options):
        base_path = os.path.join(settings.BASE_DIR, 'eleicoes')
        
        if not os.path.exists(base_path):
            self.stdout.write(self.style.ERROR(f'Diretório não encontrado: {base_path}'))
            return

        # Mapeamento automático de pastas
        target_dirs = {}
        self.stdout.write(f"Procurando pastas em: {base_path}")
        
        for item in os.listdir(base_path):
            # Normalizar nome para comparação segura
            norm = unicodedata.normalize('NFC', item)
            full_path = os.path.join(base_path, item)
            
            if os.path.isdir(full_path):
                if '2018' in norm:
                    target_dirs[item] = 2018
                elif 'MesaAMesa' in norm:
                    # Assumindo 2023 para a pasta genérica conforme solicitado
                    target_dirs[item] = 2023 

        if not target_dirs:
            self.stdout.write(self.style.WARNING("Nenhuma pasta de eleições compatível encontrada."))
            return

        for folder_name, ano in target_dirs.items():
            folder_path = os.path.join(base_path, folder_name)
            self.stdout.write(self.style.HTTP_INFO(f'\n>>> Processando {folder_name} (Ano {ano})...'))
            
            total_sucesso = 0
            total_falha = 0
            
            for root, dirs, files in os.walk(folder_path):
                self.stdout.write(f'Scanning: {root} ({len(files)} files)')
                for file in files:
                    if file.lower().endswith('.csv'):
                        full_path = os.path.join(root, file)
                        self.stdout.write(f'Found CSV: {full_path}')
                        try:
                            with open(full_path, 'rb') as f:
                                # Chama o serviço com o ano correto
                                ok, msg = ImportacaoService.processar_arquivo_imemory(f, file, ano=ano, tipo_manual='AUTO')
                                
                                if ok:
                                    # self.stdout.write(f'  [OK] {file}') # Verbose demais
                                    total_sucesso += 1
                                    # Mostra progresso simples
                                    if total_sucesso % 10 == 0:
                                        self.stdout.write(f'    Processados: {total_sucesso}...')
                                else:
                                    self.stdout.write(self.style.WARNING(f'  [FALHA] {file}: {msg}'))
                                    total_falha += 1
                                    
                        except Exception as e:
                             self.stdout.write(self.style.ERROR(f'  [ERRO] {full_path}: {e}'))
            
            self.stdout.write(self.style.SUCCESS(f'Concluído {ano}: {total_sucesso} sucessos, {total_falha} falhas.'))
            
        self.stdout.write(self.style.SUCCESS('\nProcesso de carga massiva finalizado.'))
