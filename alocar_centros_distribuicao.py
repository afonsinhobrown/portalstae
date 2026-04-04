import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

from rs.models import PlanoLogistico, MaterialEleitoral, AlocacaoLogistica
from django.db import transaction

def alocar_materiais_provinciais():
    print("--- CONFIGURAÇÃO DE CENTROS DE DISTRIBUIÇÃO (11 PROVÍNCIAS) ---")
    
    # Obter o plano recém-criado
    plano = PlanoLogistico.objects.filter(eleicao_id=3).order_by('-id').first()
    if not plano:
        print("[ERRO] Por favor, corra primeiro o script: importar_kits_logistica.py")
        return

    materiais = MaterialEleitoral.objects.filter(plano=plano)
    
    # Unidades de Destino (Centros de Soberania)
    unidades = [
        'MAPUTO_C', 'MAPUTO_P', 'GAZA', 'INHAMBANE', 'SOFALA', 
        'MANICA', 'TETE', 'ZAMBEZIA', 'NAMPULA', 'CABO_D', 'NIASSA'
    ]

    with transaction.atomic():
        for m in materiais:
            if not m.por_distrito:
                # Alocação Central para IT / Upgrade de Servidores
                AlocacaoLogistica.objects.get_or_create(
                    material_nacional=m,
                    unidade='CENTRAL',
                    defaults={'quantidade_necessaria': m.quantidade_planeada}
                )
                print(f" > Centralizado: {m.item} alocado ao STAE CENTRAL.")
            else:
                # Distribuição Proporcional Geográfica
                qtd_por_prov = m.quantidade_planeada // len(unidades)
                for u in unidades:
                    AlocacaoLogistica.objects.get_or_create(
                        material_nacional=m,
                        unidade=u,
                        defaults={'quantidade_necessaria': qtd_por_prov}
                    )
                print(f" > Distribuído: {m.item} dividido pelas 11 Províncias.")

    print("\n[SUCESSO] Centros de Distribuição operacionais para todo Moçambique!")

if __name__ == "__main__":
    alocar_materiais_provinciais()
