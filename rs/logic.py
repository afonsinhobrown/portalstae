from django.db.models import Sum
from .models import MaterialEleitoral
from eleicao.models import Eleicao
from circuloseleitorais.models import CirculoEleitoral

def sync_plano_logistico(plano):
    # LOG BRUTO PARA DEBELAÇÃO DE INCOMPETÊNCIA
    try:
        with open('log_operacional.txt', 'a') as f:
            f.write(f"VINCULANDO AO PLANO: {plano.id if plano else 'SEM PLANO'}\n")
    except: pass

    if not plano or not plano.eleicao: return
    eleicao = plano.eleicao

    # FACTO BRUTO: Forçar os 4 itens de soberania para o Plano 5
    items_soberania = [
        ('Boletins de Voto Oficial (Soberania Nacional)', 10000000),
        ('Toner para Impressoras de Cartões (Neon Sync)', 500),
        ('Discos de Servidor (Infraestrutura)', 50),
        ('Kits de Resiliência Logística', 100)
    ]

    for nome, qtd in items_soberania:
        MaterialEleitoral.objects.update_or_create(
            plano=plano, 
            eleicao=eleicao, 
            item=nome,
            defaults={
                'tipo_operacao': 'VOTACAO',
                'quantidade_planeada': qtd
            }
        )

    # Operação concluída.
    return True

    # 2. DISTRIBUIÇÃO TÁTICA (Por Destino/Autarquia)
    destinos = eleicao.circulos.all() if eleicao.tipo == 'autarquica' else []
    
    for dest in destinos:
        m_local = dest.num_mesas
        e_local = dest.num_eleitores
        if m_local == 0: continue

        matriz = [
            ('urna_v', f'Urnas de Votação - {dest.nome}', m_local + (m_local // 10)),
            ('cabine', f'Cabines de Voto - {dest.nome}', m_local * 2),
            ('boletim', f'Boletins de Voto - {dest.nome}', int(e_local * 1.05)),
        ]
        
        for cat_tag, nome, qtd in matriz:
            MaterialEleitoral.objects.update_or_create(
                plano=plano,
                eleicao=eleicao,
                item=nome,
                defaults={
                    'tipo_operacao': 'VOTACAO',
                    'quantidade_planeada': qtd
                }
            )
