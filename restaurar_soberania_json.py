import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

from circuloseleitorais.models import DivisaoAdministrativa, DivisaoEleicao
from eleicao.models import Eleicao
from django.db import transaction

# Dados fornecidos pelo utilizador (Soberania Geográfica)
DADOS_JSON = [
    {"id":920,"nome":"Cidade de Maputo","codigo":"01","nivel":"provincia","divisao_base_id":562,"eleicao_id":3,"parent_id":None},
    {"id":921,"nome":"MAPUTO","codigo":"02","nivel":"provincia","divisao_base_id":524,"eleicao_id":3,"parent_id":None},
    {"id":922,"nome":"GAZA","codigo":"03","nivel":"provincia","divisao_base_id":468,"eleicao_id":3,"parent_id":None},
    {"id":923,"nome":"INHAMBANE","codigo":"04","nivel":"provincia","divisao_base_id":427,"eleicao_id":3,"parent_id":None},
    {"id":924,"nome":"SOFALA","codigo":"05","nivel":"provincia","divisao_base_id":378,"eleicao_id":3,"parent_id":None},
    {"id":925,"nome":"MANICA","codigo":"06","nivel":"provincia","divisao_base_id":332,"eleicao_id":3,"parent_id":None},
    {"id":926,"nome":"TETE","codigo":"07","nivel":"provincia","divisao_base_id":284,"eleicao_id":3,"parent_id":None},
    {"id":927,"nome":"ZAMB ZIA","codigo":"08","nivel":"provincia","divisao_base_id":221,"eleicao_id":3,"parent_id":None},
    {"id":928,"nome":"NAMPULA","codigo":"09","nivel":"provincia","divisao_base_id":130,"eleicao_id":3,"parent_id":None},
    {"id":929,"nome":"C.DELGADO","codigo":"10","nivel":"provincia","divisao_base_id":56,"eleicao_id":3,"parent_id":None},
    {"id":930,"nome":"NIASSA","codigo":"11","nivel":"provincia","divisao_base_id":1,"eleicao_id":3,"parent_id":None},
    {"id":931,"nome":"DISTRITO URBANO  N 1","codigo":"0101","nivel":"distrito","divisao_base_id":563,"eleicao_id":3,"parent_id":920},
    {"id":932,"nome":"DISTRITO URBANO N  2","codigo":"0102","nivel":"distrito","divisao_base_id":564,"eleicao_id":3,"parent_id":920},
    {"id":933,"nome":"DISTRITO URBANO N  3","codigo":"0103","nivel":"distrito","divisao_base_id":565,"eleicao_id":3,"parent_id":920},
    {"id":934,"nome":"DISTRITO URBANO N  4","codigo":"0104","nivel":"distrito","divisao_base_id":566,"eleicao_id":3,"parent_id":920},
    {"id":935,"nome":"DISTRITO URBANO N  5","codigo":"0105","nivel":"distrito","divisao_base_id":567,"eleicao_id":3,"parent_id":920},
    {"id":936,"nome":"CIDADE DA MATOLA","codigo":"0201","nivel":"distrito","divisao_base_id":525,"eleicao_id":3,"parent_id":921},
    {"id":937,"nome":"BOANE","codigo":"0202","nivel":"distrito","divisao_base_id":529,"eleicao_id":3,"parent_id":921},
    {"id":938,"nome":"MANHI A","codigo":"0204","nivel":"distrito","divisao_base_id":538,"eleicao_id":3,"parent_id":921},
    {"id":939,"nome":"MARRACUENE","codigo":"0205","nivel":"distrito","divisao_base_id":545,"eleicao_id":3,"parent_id":921},
    {"id":940,"nome":"NAMAACHA","codigo":"0208","nivel":"distrito","divisao_base_id":559,"eleicao_id":3,"parent_id":921},
    {"id":941,"nome":"CIDADE DE XAI-XAI","codigo":"0301","nivel":"distrito","divisao_base_id":469,"eleicao_id":3,"parent_id":922},
    {"id":942,"nome":"BILENE - MACIA","codigo":"0302","nivel":"distrito","divisao_base_id":470,"eleicao_id":3,"parent_id":922},
    {"id":943,"nome":"CHIBUTO","codigo":"0303","nivel":"distrito","divisao_base_id":477,"eleicao_id":3,"parent_id":922},
    {"id":944,"nome":"CHOKWE","codigo":"0306","nivel":"distrito","divisao_base_id":491,"eleicao_id":3,"parent_id":922},
    {"id":945,"nome":"GUIJA","codigo":"0307","nivel":"distrito","divisao_base_id":496,"eleicao_id":3,"parent_id":922},
    {"id":946,"nome":"MANJACAZE","codigo":"0309","nivel":"distrito","divisao_base_id":505,"eleicao_id":3,"parent_id":922},
    {"id":947,"nome":"CIDADE DE  INHAMBANE","codigo":"0401","nivel":"distrito","divisao_base_id":428,"eleicao_id":3,"parent_id":923},
    {"id":948,"nome":"HOMOINE","codigo":"0404","nivel":"distrito","divisao_base_id":435,"eleicao_id":3,"parent_id":923},
    {"id":949,"nome":"INHARRIME","codigo":"0405","nivel":"distrito","divisao_base_id":438,"eleicao_id":3,"parent_id":923},
    {"id":950,"nome":"MASSINGA","codigo":"0409","nivel":"distrito","divisao_base_id":451,"eleicao_id":3,"parent_id":923},
    {"id":951,"nome":"CIDADE DE MAXIXE","codigo":"0410","nivel":"distrito","divisao_base_id":454,"eleicao_id":3,"parent_id":923},
    {"id":952,"nome":"VILANKULO","codigo":"0413","nivel":"distrito","divisao_base_id":462,"eleicao_id":3,"parent_id":923},
    {"id":953,"nome":"ZAVALA","codigo":"0414","nivel":"distrito","divisao_base_id":465,"eleicao_id":3,"parent_id":923},
    {"id":954,"nome":"CIDADE DE  BEIRA","codigo":"0501","nivel":"distrito","divisao_base_id":379,"eleicao_id":3,"parent_id":924},
    {"id":955,"nome":"BUZI","codigo":"0502","nivel":"distrito","divisao_base_id":385,"eleicao_id":3,"parent_id":924},
    {"id":956,"nome":"CAIA","codigo":"0503","nivel":"distrito","divisao_base_id":389,"eleicao_id":3,"parent_id":924},
    {"id":957,"nome":"DONDO","codigo":"0507","nivel":"distrito","divisao_base_id":404,"eleicao_id":3,"parent_id":924},
    {"id":958,"nome":"CORONGOSA","codigo":"0508","nivel":"distrito","divisao_base_id":407,"eleicao_id":3,"parent_id":924},
    {"id":959,"nome":"NHAMATANDA","codigo":"0513","nivel":"distrito","divisao_base_id":424,"eleicao_id":3,"parent_id":924},
    {"id":960,"nome":"CIDADE DE  CHIMOIO","codigo":"0601","nivel":"distrito","divisao_base_id":337,"eleicao_id":3,"parent_id":925},
    {"id":961,"nome":"BARUE","codigo":"0602","nivel":"distrito","divisao_base_id":333,"eleicao_id":3,"parent_id":925},
    {"id":962,"nome":"GONDOLA","codigo":"0603","nivel":"distrito","divisao_base_id":338,"eleicao_id":3,"parent_id":925},
    {"id":963,"nome":"MACOSSA","codigo":"0606","nivel":"distrito","divisao_base_id":355,"eleicao_id":3,"parent_id":925},
    {"id":964,"nome":"MANICA","codigo":"0607","nivel":"distrito","divisao_base_id":359,"eleicao_id":3,"parent_id":925},
    {"id":965,"nome":"SUSSUNDENGA","codigo":"0609","nivel":"distrito","divisao_base_id":369,"eleicao_id":3,"parent_id":925},
    {"id":966,"nome":"CIDADE DE TETE","codigo":"0701","nivel":"distrito","divisao_base_id":285,"eleicao_id":3,"parent_id":926},
    {"id":967,"nome":"ANGONIA","codigo":"0702","nivel":"distrito","divisao_base_id":286,"eleicao_id":3,"parent_id":926},
    {"id":968,"nome":"CAHORA-BASSA","codigo":"0703","nivel":"distrito","divisao_base_id":289,"eleicao_id":3,"parent_id":926},
    {"id":969,"nome":"MOATIZE","codigo":"0710","nivel":"distrito","divisao_base_id":316,"eleicao_id":3,"parent_id":926}
]

def restaurar_soberania():
    print("--- INICIANDO RESTAURAÇÃO DE SOBERANIA GEOGRÁFICA ---")
    
    # Garantir que a Eleição ID 3 existe (ou criar uma dummy se necessário para o teste)
    eleicao, _ = Eleicao.objects.get_or_create(id=3, defaults={'nome': 'Eleição de Soberania (Recuperada)', 'ano': 2024, 'tipo': 'geral'})

    with transaction.atomic():
        id_map_base = {} # {original_id: new_base_obj}
        id_map_eleicao = {} # {original_id: new_eleicao_obj}

        # Separar Províncias e Distritos para manter a hierarquia
        provincias_data = [d for d in DADOS_JSON if d['nivel'] == 'provincia']
        distritos_data = [d for d in DADOS_JSON if d['nivel'] == 'distrito']

        print(f"Processando {len(provincias_data)} Províncias...")
        for p in provincias_data:
            # 1. Criar na Base (DivisaoAdministrativa)
            base_p, _ = DivisaoAdministrativa.objects.get_or_create(
                id=p['divisao_base_id'],
                defaults={'nome': p['nome'], 'codigo': p['codigo'], 'nivel': 'provincia'}
            )
            id_map_base[p['id']] = base_p

            # 2. Criar na Eleição (DivisaoEleicao)
            eleicao_p, _ = DivisaoEleicao.objects.update_or_create(
                id=p['id'],
                defaults={
                    'eleicao': eleicao,
                    'nome': p['nome'],
                    'codigo': p['codigo'],
                    'nivel': 'provincia',
                    'divisao_base': base_p,
                    'parent': None
                }
            )
            id_map_eleicao[p['id']] = eleicao_p

        print(f"Processando {len(distritos_data)} Distritos...")
        for d in distritos_data:
            # 1. Criar na Base
            base_d, _ = DivisaoAdministrativa.objects.get_or_create(
                id=d['divisao_base_id'],
                defaults={
                    'nome': d['nome'], 
                    'codigo': d['codigo'], 
                    'nivel': 'distrito',
                    'parent': id_map_base.get(d['parent_id'])
                }
            )
            
            # 2. Criar na Eleição
            DivisaoEleicao.objects.update_or_create(
                id=d['id'],
                defaults={
                    'eleicao': eleicao,
                    'nome': d['nome'],
                    'codigo': d['codigo'],
                    'nivel': 'distrito',
                    'divisao_base': base_d,
                    'parent': id_map_eleicao.get(d['parent_id'])
                }
            )

    print("\n[SUCESSO] Soberania Geográfica Restaurada para a Eleição ID 3!")

if __name__ == "__main__":
    restaurar_soberania()
