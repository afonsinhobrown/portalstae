from django.db.models import Sum
from .models import MaterialEleitoral
from eleicao.models import Eleicao
from circuloseleitorais.models import CirculoEleitoral

def sync_plano_logistico(eleicao):
    """
    Motor de Sincronização Dinâmica (PRAM) de Alta Fidelidade (35+ ITENS).
    Gera as necessidades para o Armazém Central e Distribuição Territorial (Provincial ou Autárquica).
    """
    if not eleicao: return

    total_eleitores = eleicao.circulos.aggregate(total=Sum('num_eleitores'))['total'] or 0
    total_mesas = eleicao.circulos.aggregate(total=Sum('num_mesas'))['total'] or 0
    
    if total_mesas == 0: return

    # 1. ESTOQUE NACIONAL (Armazém Central - Reservas de Soberania)
    # Estes itens são geridos a nível global para toda a eleição
    estoque_central = [
        ('boletim', 'Boletins de Voto Oficial (Stock Central +10%)', int(total_eleitores * 1.1)),
        ('colete_m', 'Coletes Oficiais MMV (Reserva Nacional)', total_mesas * 2),
        ('tinta_f', 'Tinta Indelével (Stock de Contingência)', int(total_eleitores / 500) + 100),
        ('envelope_s', 'Envelopes de Segurança Invioláveis (Total Nacional)', total_mesas * 15),
        ('selo_p', 'Selos de Urna Numerados (Stock Central)', total_mesas * 20),
        ('megafone', 'Megafones p/ Coordenação Nacional', 100),
    ]

    for tipo, nome, qtd in estoque_central:
        MaterialEleitoral.objects.update_or_create(
            eleicao=eleicao, tipo=tipo, localizacao_destino='Armazém Central',
            defaults={'item': nome, 'quantidade_planeada': qtd}
        )

    # 2. DISTRIBUIÇÃO TÁTICA (Provincial para Legislativas/Presidenciais, Autárquica para Autárquicas)
    if eleicao.tipo == 'autarquica':
        # Nas Autárquicas, a unidade de planeamento é a própria Autarquia (Circulo)
        destinos = eleicao.circulos.all()
    else:
        # Nas outras, agrupamos por Província
        destinos_nomes = eleicao.circulos.values_list('provincia', flat=True).distinct()
        class DestinoMock:
            def __init__(self, nome, qs, eleicao):
                self.nome = nome
                self.num_mesas = qs.filter(provincia=nome).aggregate(t=Sum('num_mesas'))['t'] or 0
                self.num_eleitores = qs.filter(provincia=nome).aggregate(t=Sum('num_eleitores'))['t'] or 0
        destinos = [DestinoMock(n, eleicao.circulos.all(), eleicao) for n in destinos_nomes]

    for dest in destinos:
        m_local = dest.num_mesas if hasattr(dest, 'num_mesas') else dest.num_mesas
        e_local = dest.num_eleitores if hasattr(dest, 'num_eleitores') else dest.num_eleitores
        nome_destino = dest.nome
        
        if m_local == 0: continue

        # Matriz Tática por Unidade Operacional
        matriz = [
            ('urna_v', f'Urnas de Votação - {nome_destino}', m_local + (m_local // 10)),
            ('cabine', f'Cabines de Voto - {nome_destino}', m_local * 2),
            ('boletim', f'Boletins de Voto Destinados - {nome_destino}', int(e_local * 1.05)),
            ('carimbo_v', f'Carimbos "VOTOU" - {nome_destino}', m_local),
            ('carimbo_s', f'Carimbos Oficiais STAE - {nome_destino}', m_local),
            ('acta_v', f'Cadernos de Actas de Votação - {nome_destino}', m_local * 2),
            ('acta_a', f'Cadernos de Actas de Apuramento - {nome_destino}', m_local),
            ('edital', f'Editais de Resultados - {nome_destino}', m_local * 5),
            ('caneta', f'Canetas Esferográficas - {nome_destino}', m_local * 10),
            ('lanterna', f'Lanternas LED Frontais - {nome_destino}', m_local * 3),
            ('envelope_s', f'Sacos de Inviolabilidade (Actas) - {nome_destino}', m_local * 4),
            ('selo_p', f'Selos de Urna (Plástico Rígido) - {nome_destino}', m_local * 10),
            ('colete_m', f'Coletes Oficiais MMV - {nome_destino}', m_local * 7),
            ('credencial', f'Crachás Oficiais - {nome_destino}', m_local * 10),
            ('almofada', f'Almofadas de Tinta - {nome_destino}', m_local * 2),
            ('kit', f'Maletas de Transporte de Kit - {nome_destino}', m_local),
            ('infra', f'Mobiliário de Campanha - {nome_destino}', m_local),
        ]
        
        for tipo, nome, qtd in matriz:
            MaterialEleitoral.objects.update_or_create(
                eleicao=eleicao, tipo=tipo, localizacao_destino=nome_destino,
                defaults={'item': nome, 'quantidade_planeada': qtd}
            )
