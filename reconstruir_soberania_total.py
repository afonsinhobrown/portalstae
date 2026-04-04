import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

from circuloseleitorais.models import DivisaoAdministrativa, DivisaoEleicao
from eleicao.models import Eleicao
from django.db import transaction

# DADOS GEOGRÁFICOS BASE (NIASSA...)
BASE_GEO = [
    {"id":1,"nome":"NIASSA","codigo":"11","nivel":"provincia","parent_id":None},
    {"id":2,"nome":"CIDADE DE LICHINGA","codigo":"1101","nivel":"distrito","parent_id":1},
    {"id":3,"nome":"CUAMBA","codigo":"1102","nivel":"distrito","parent_id":1},
    {"id":4,"nome":"CIDADE DE CUAMBA","codigo":"110201","nivel":"posto","parent_id":3},
    {"id":5,"nome":"ETATARA","codigo":"110202","nivel":"posto","parent_id":3},
    {"id":6,"nome":"LURIO","codigo":"110203","nivel":"posto","parent_id":3},
    {"id":7,"nome":"LAGO","codigo":"1103","nivel":"distrito","parent_id":1},
    {"id":8,"nome":"METANGULA","codigo":"110301","nivel":"posto","parent_id":7},
    {"id":9,"nome":"COBUE","codigo":"110302","nivel":"posto","parent_id":7},
    {"id":10,"nome":"LUNHO","codigo":"110303","nivel":"posto","parent_id":7},
    {"id":11,"nome":"MANIAMBA","codigo":"110304","nivel":"posto","parent_id":7},
    {"id":12,"nome":"LICHINGA","codigo":"1104","nivel":"distrito","parent_id":1},
    {"id":13,"nome":"CHIMBONILA","codigo":"110401","nivel":"posto","parent_id":12},
    {"id":14,"nome":"LIONE","codigo":"110402","nivel":"posto","parent_id":12},
    {"id":15,"nome":"MEPONDA","codigo":"110403","nivel":"posto","parent_id":12},
    # ... seguem outros distritos e postos do Niassa
]

# ASSOCIACÕES ELEITORAIS (ELEICAO ID 3)
ASSOC_ELEICAO = [
    {"id":920,"nome":"Cidade de Maputo","codigo":"01","nivel":"provincia","divisao_base_id":562,"eleicao_id":3,"parent_id":None},
    {"id":922,"nome":"GAZA","codigo":"03","nivel":"provincia","divisao_base_id":468,"eleicao_id":3,"parent_id":None},
    {"id":930,"nome":"NIASSA","codigo":"11","nivel":"provincia","divisao_base_id":1,"eleicao_id":3,"parent_id":None},
    {"id":936,"nome":"CIDADE DA MATOLA","codigo":"0201","nivel":"distrito","divisao_base_id":525,"eleicao_id":3,"parent_id":921},
    # ... seguem outros distritos da eleicao
]

def reconstruir_tudo():
    print("--- RECONSTRUÇÃO DE SOBERANIA NACIONAL (STAE) ---")
    eleicao, _ = Eleicao.objects.get_or_create(id=3, defaults={'nome': 'Ciclo Eleitoral Atual', 'ano': 2024, 'tipo': 'geral'})

    with transaction.atomic():
        # 1. Reconstruir Base
        print("Injetando Geografia Base...")
        for b in BASE_GEO:
            parent = DivisaoAdministrativa.objects.filter(id=b['parent_id']).first() if b['parent_id'] else None
            DivisaoAdministrativa.objects.update_or_create(
                id=b['id'],
                defaults={'nome': b['nome'], 'codigo': b['codigo'], 'nivel': b['nivel'], 'parent': parent}
            )

        # 2. Reconstruir Associações
        print("Injetando Associações da Eleição 3...")
        for a in ASSOC_ELEICAO:
            base = DivisaoAdministrativa.objects.filter(id=a['divisao_base_id']).first()
            parent = DivisaoEleicao.objects.filter(id=a['parent_id']).first() if a['parent_id'] else None
            
            # Garantir que se a base nao existir (por exemplo Maputo nao foi enviada no 2o JSON), criamos uma dummy
            if not base:
                base, _ = DivisaoAdministrativa.objects.get_or_create(
                    id=a['divisao_base_id'],
                    defaults={'nome': a['nome'] + " (Base)", 'codigo': a['codigo'], 'nivel': a['nivel']}
                )

            DivisaoEleicao.objects.update_or_create(
                id=a['id'],
                defaults={
                    'eleicao': eleicao,
                    'nome': a['nome'],
                    'codigo': a['codigo'],
                    'nivel': a['nivel'],
                    'divisao_base': base,
                    'parent': parent
                }
            )

    print("\n[OK] Soberania Geográfica e Eleitoral Restaurada com Sucesso!")

if __name__ == "__main__":
    reconstruir_tudo()
