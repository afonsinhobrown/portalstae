import csv
import io
import os
from django.db import transaction
from dfec.models import ResultadoEleitoral, Provincia, Distrito
import unicodedata

class ImportacaoService:
    @staticmethod
    def processar_arquivo_imemory(file_obj, filename, ano=2018, tipo_manual='AUTO'):
        """
        Processa um arquivo CSV carregado na memória.
        Retorna (sucesso: bool, mensagem: str)
        """
        try:
            # Detectar tipo de eleição
            if tipo_manual and tipo_manual != 'AUTO':
                tipo = tipo_manual
            else:
                tipo = 'AM' if ' - AM' in filename else ('PCM' if ' - PCM' in filename else 'OUTRO')
            
            if tipo == 'OUTRO':
                return False, f"Tipo de eleição não identificado no arquivo {filename}. Selecione manualmente."

            decoded_file = file_obj.read().decode('utf-8', errors='replace')
            io_string = io.StringIO(decoded_file)
            
            # Lógica de Pular cabeçalhos estranhos (sep=)
            first_line = io_string.readline().strip()
            if 'sep=' not in first_line:
                io_string.seek(0)
            
            reader = csv.DictReader(io_string)
            # Garante que fieldnames seja uma lista strings
            fnames = reader.fieldnames
            if fnames is not None:
                reader.fieldnames = [str(name).strip() for name in fnames]
            else:
                reader.fieldnames = []
            
            registros_criados = 0
            
            with transaction.atomic():
                for row in reader:
                    if not row or not row.get('Província'):
                        continue

                    # Obter código de forma segura
                    codigo_raw = row.get('Código da Assembleia de Voto')
                    codigo = str(codigo_raw).strip() if codigo_raw else ""
                    
                    if codigo.endswith(' .'):
                        codigo = codigo[:-2]
                    
                    if not codigo:
                        continue

                    res, created = ResultadoEleitoral.objects.update_or_create(
                        codigo_assembleia=codigo,
                        tipo_eleicao=tipo,
                        ano=ano,
                        defaults={
                            'provincia_original': str(row.get('Província') or ""),
                            'distrito_original': str(row.get('Distrito') or ""),
                            'posto_administrativo': str(row.get('Posto Administrativo') or ""),
                            'localidade': str(row.get('Localidade') or ""),
                            'local_votacao': str(row.get('Local') or ""),
                            'eleitores_inscritos': ImportacaoService._clean_int(row.get('Número de Eleitores Inscritos')),
                            'total_votantes': ImportacaoService._clean_int(row.get('Total de Votantes')),
                            'votos_validos': ImportacaoService._clean_int(row.get('Votos Válidos')),
                            'votos_nulos': ImportacaoService._clean_int(row.get('Votos Nulos')),
                            'votos_branco': ImportacaoService._clean_int(row.get('Votos em Branco')),
                            'abstencoes': ImportacaoService._clean_int(row.get('Abstenções')),
                        }
                    )
                    
                    # Tentar Normalizar Instantaneamente
                    ImportacaoService._normalizar_registro(res)
                    
                    registros_criados += 1
            
            return True, f"{registros_criados} registros processados."

        except Exception as e:
            return False, str(e)

    @staticmethod
    def _clean_int(value):
        if value is None:
            return 0
        try:
            return int(str(value).replace('.', '').replace(',', '').strip())
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def _normalizar_registro(res):
        """
        Aplica a lógica de normalização (linkagem) para um único registro.
        """
        # 1. Normalizar Província
        prov_orig = str(res.provincia_original or "")
        nome_prov = ImportacaoService._normalizar_texto(prov_orig)
        nome_prov = ImportacaoService._aplicar_correcoes(nome_prov)
        
        # Tratamento Maputo
        distrito_orig = str(res.distrito_original or "").lower()
        prov_lower = nome_prov.lower()
        if 'maputo' in prov_lower:
               if 'cidade' in prov_lower or 'city' in prov_lower or distrito_orig.startswith('kam'):
                   nome_prov = 'Maputo Cidade'
               else:
                   nome_prov = 'Maputo Província'

        # Lista Branca de Províncias
        VALIDAS = [
            'Cabo Delgado', 'Gaza', 'Inhambane', 'Manica', 
            'Maputo Cidade', 'Maputo Província', 'Nampula', 
            'Niassa', 'Sofala', 'Tete', 'Zambezia', 'Zambézia' # Aceitar ambas grafias por enquanto
        ]

        if nome_prov not in VALIDAS:
            print(f"Aviso: Província ignorada -> {nome_prov}")
            return # Não vincula nem cria lixo

        provincia, _ = Provincia.objects.get_or_create(nome=nome_prov)
        res.provincia_ref = provincia

        # 2. Normalizar Distrito
        dist_orig_raw = str(res.distrito_original or "")
        nome_dist = ImportacaoService._normalizar_texto(dist_orig_raw)
        nome_dist = ImportacaoService._aplicar_correcoes(nome_dist)
        
        if nome_dist.startswith("d. "):
            nome_dist = nome_dist[3:]
        
        dist_lower = nome_dist.lower()
        if provincia is not None and getattr(provincia, 'nome', '') == 'Maputo Cidade' and 'municipal' in dist_lower:
             nome_dist = nome_dist.replace('municipal', '').replace('Municipal', '').strip().title()

        distrito_obj, _ = Distrito.objects.get_or_create(provincia=provincia, nome=nome_dist)
        res.distrito_ref = distrito_obj
        res.save()

    @staticmethod
    def _normalizar_texto(texto):
        if not texto:
            return "Desconhecido"
        nfkd = unicodedata.normalize('NFKD', texto)
        sem_acento = u"".join([c for c in nfkd if not unicodedata.combining(c)])
        return sem_acento.strip().title()

    @staticmethod
    def _aplicar_correcoes(texto):
        CORRECOES = {
            'Maputo City': 'Maputo Cidade',
            'Provincia de Gaza': 'Gaza',
            'D. Chibuto': 'Chibuto',
        }
        return CORRECOES.get(texto, texto)
