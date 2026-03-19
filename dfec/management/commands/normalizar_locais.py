from django.core.management.base import BaseCommand
from dfec.models import ResultadoEleitoral, Provincia, Distrito
from django.db import transaction
import unicodedata

class Command(BaseCommand):
    help = 'Normaliza os dados eleitorais criando registros canônicos de Províncias e Distritos'

    def handle(self, *args, **options):
        self.stdout.write("Iniciando normalização de dados...")

        # Mapa de Correções Conhecidas (De -> Para)
        # Adicione aqui correções manuais conforme necessário
        CORRECOES = {
            'Maputo City': 'Maputo Cidade',
            'Maputo': 'Maputo Província', # Se distinguir da cidade
            'Provincia de Gaza': 'Gaza',
            'D. Chibuto': 'Chibuto',
            # ...
        }

        with transaction.atomic():
            resultados = ResultadoEleitoral.objects.filter(provincia_ref__isnull=True)
            self.stdout.write(f"Processando {resultados.count()} registros pendentes...")

            for res in resultados:
                # 1. Normalizar Província
                nome_prov = self.normalizar_texto(res.provincia_original)
                nome_prov = CORRECOES.get(nome_prov, nome_prov)
                
                # Tratamento especial para Maputo
                if 'maputo' in nome_prov.lower():
                   if 'cidade' in nome_prov.lower() or 'city' in nome_prov.lower() or res.distrito_original.lower().startswith('kam'):
                       nome_prov = 'Maputo Cidade'
                   else:
                       nome_prov = 'Maputo Província'

                provincia, _ = Provincia.objects.get_or_create(nome=nome_prov)
                res.provincia_ref = provincia

                # 2. Normalizar Distrito
                nome_dist = self.normalizar_texto(res.distrito_original)
                nome_dist = CORRECOES.get(nome_dist, nome_dist)
                
                # Remover prefixos comuns erros de input (ex: "D. ")
                if nome_dist.startswith("d. "):
                    nome_dist = nome_dist[3:]

                # Se for Maputo Cidade, o distrito muitas vezes é o Ka...
                if provincia.nome == 'Maputo Cidade' and 'municipal' in nome_dist.lower():
                    # Normaliza: MUNICIPAL KAMAVOTA -> Kamavota
                    nome_dist = nome_dist.replace('municipal', '').strip().title()

                distrito, _ = Distrito.objects.get_or_create(provincia=provincia, nome=nome_dist)
                res.distrito_ref = distrito
                
                res.save()

        self.stdout.write(self.style.SUCCESS('Normalização concluída com sucesso!'))

    def normalizar_texto(self, texto):
        if not texto:
            return "Desconhecido"
        # Remove acentos e força Title Case
        nfkd = unicodedata.normalize('NFKD', texto)
        sem_acento = u"".join([c for c in nfkd if not unicodedata.combining(c)])
        return sem_acento.strip().title()
