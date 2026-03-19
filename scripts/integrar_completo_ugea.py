import os
import django
import sys
import datetime
from decimal import Decimal
from django.db.models import Sum
from django.utils import timezone

# Setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "portalstae.settings")
django.setup()

from gestaocombustivel.models import (
    FornecedorCombustivel, FornecedorManutencao,
    ContratoCombustivel, ContratoManutencao, SeguroViatura,
    PagamentoContrato, ManutencaoViatura
)
from ugea.models import Contrato, Fornecedor, Pagamento, Concurso, Proposta, PedidoConsumo, ItemContrato
from recursoshumanos.models import Sector

def get_or_create_setor(codigo="6"):
    # ID 6 é logística, fallback seguro
    s = Sector.objects.filter(id=codigo).first()
    return s

def migrar_fornecedores():
    print("--- 1. Migrando Fornecedores ---")
    
    # Combustível
    for f in FornecedorCombustivel.objects.all():
        Fornecedor.objects.update_or_create(
            nuit=f.nuit,
            defaults={
                'nome': f.nome,
                'telefone': f.contacto,
                'endereco': f.endereco,
                'email': f.email,
                'categoria': 'combustivel',
                'ativo': f.activo
            }
        )
        
    # Manutenção
    for f in FornecedorManutencao.objects.all():
        Fornecedor.objects.update_or_create(
            nuit=f.nuit,
            defaults={
                'nome': f.nome,
                'telefone': f.contacto,
                'endereco': f.endereco,
                'email': f.email,
                'categoria': 'servicos', # Manutenção é serviço
                'ativo': f.activo
            }
        )
    print("Fornecedores migrados.")

def criar_concurso_ficticio(nome, tipo):
    c, created = Concurso.objects.get_or_create(
        titulo=f"Concurso {nome} (Migrado)",
        defaults={
            'tipo': tipo,
            'status': 'adjudicado',
            'descricao': "Concurso migrado automaticamente do sistema legado.",
            'valor_estimado': 0,
            'data_abertura': timezone.now(),
            'data_encerramento': timezone.now() + datetime.timedelta(days=30)
        }
    )
    return c

def migrar_contratos():
    print("--- 2. Migrando Contratos ---")
    setor_logistica = get_or_create_setor()

    # Contratos Combustível
    for cc in ContratoCombustivel.objects.all():
        concurso = criar_concurso_ficticio("Combustível", "Fornecimento")
        
        # Proposta Mock
        proposta, _ = Proposta.objects.get_or_create(
            concurso=concurso,
            nuit=cc.fornecedor.nuit,
            defaults={
                'fornecedor': cc.fornecedor.nome,
                'valor_proposto': cc.valor_total_contrato,
                'classificacao': 1,
            }
        )

        Contrato.objects.update_or_create(
            numero_contrato=cc.numero_contrato,
            defaults={
                'concurso': concurso,
                'proposta_vencedora': proposta,
                'data_inicio': cc.data_inicio,
                'data_fim': cc.data_fim,
                'valor_total': cc.valor_total_contrato,
                'valor_executado': cc.valor_consumido_total,
                'tipo_servico': f"Combustível {cc.tipo_combustivel}",
                'sector': setor_logistica,
                'ativo': cc.activo
            }
        )
        
        # Criar Item de Contrato (Combustível)
        ItemContrato.objects.get_or_create(
            contrato=contrato,
            descricao=f"Fornecimento de {cc.tipo_combustivel.capitalize()}",
            defaults={'preco_unitario': cc.preco_unitario}
        )

    # Contratos Manutenção
    for cm in ContratoManutencao.objects.all():
        concurso = criar_concurso_ficticio("Manutenção Frota", "Serviços")
        
        proposta, _ = Proposta.objects.get_or_create(
            concurso=concurso,
            nuit=cm.fornecedor.nuit,
            defaults={
                'fornecedor': cm.fornecedor.nome,
                'valor_proposto': cm.valor_total,
                'classificacao': 1,
            }
        )

        Contrato.objects.update_or_create(
            numero_contrato=cm.numero_contrato,
            defaults={
                'concurso': concurso,
                'proposta_vencedora': proposta,
                'data_inicio': cm.data_inicio,
                'data_fim': cm.data_fim,
                'valor_total': cm.valor_total,
                'valor_executado': cm.valor_gasto,
                'tipo_servico': cm.descricao or "Manutenção Geral",
                'sector': setor_logistica,
                'ativo': cm.activo
            }
        )
        
        # Criar Item Genérico para Manutenção
        ItemContrato.objects.get_or_create(
            contrato=contrato,
            descricao=cm.descricao or "Serviço de Manutenção Geral",
            defaults={'preco_unitario': 0} # Manutenção varia, 0 como base
        )

    # Seguros (Tratados como Contratos)
    for sv in SeguroViatura.objects.all():
        # Seguros muitas vezes não têm contrato guarda-chuva, mas cada apólice é um contrato
        concurso = criar_concurso_ficticio("Seguros", "Serviços")
        
        # Nome da companhia como 'contrato' se não tiver NUIT
        proposta, _ = Proposta.objects.get_or_create(
            concurso=concurso,
            fornecedor=sv.companhia_seguros, # Usando nome como chave se nuit faltar
            defaults={
                'nuit': '999999999', # Placeholder
                'valor_proposto': sv.premio_seguro,
                'classificacao': 1,
            }
        )

        contrato, _ = Contrato.objects.update_or_create(
            numero_contrato=sv.numero_apolice,
            defaults={
                'concurso': concurso,
                'proposta_vencedora': proposta,
                'data_inicio': sv.data_inicio,
                'data_fim': sv.data_fim,
                'valor_total': sv.premio_seguro, # Valor do contrato é o prémio
                'valor_executado': sv.premio_seguro, # Seguro paga-se à cabeça geralmente
                'tipo_servico': f"Seguro {sv.get_tipo_seguro_display()} - {sv.viatura.matricula}",
                'sector': setor_logistica,
                'ativo': sv.activo
            }
        )
        
        # Item de Seguro
        ItemContrato.objects.get_or_create(
            contrato=contrato,
            descricao=f"Prémio de Seguro - {sv.get_tipo_seguro_display()}",
            defaults={'preco_unitario': sv.premio_seguro}
        )
    print("Contratos migrados.")

def migrar_pagamentos():
    print("--- 3. Migrando Pagamentos Reais ---")
    
    # Pagamentos de Combustível
    for pc in PagamentoContrato.objects.all():
        contrato_ugea = Contrato.objects.filter(numero_contrato=pc.contrato.numero_contrato).first()
        if not contrato_ugea: continue
        
        Pagamento.objects.update_or_create(
            referencia=pc.referencia_documento or f"PAG-{pc.id}",
            contrato=contrato_ugea,
            defaults={
                'data_pagamento': pc.data_pagamento,
                'valor': pc.valor,
                'descricao': pc.observacoes or "Pagamento de Combustível Importado"
            }
        )

    # Manutenções (Se houver custo real, conta como execução/pagamento)
    for mv in ManutencaoViatura.objects.exclude(custo_real__isnull=True):
        if not mv.contrato: continue
        contrato_ugea = Contrato.objects.filter(numero_contrato=mv.contrato.numero_contrato).first()
        if not contrato_ugea: continue
        
        Pagamento.objects.update_or_create(
            referencia=f"MANUT-{mv.id}",
            contrato=contrato_ugea,
            defaults={
                'data_pagamento': mv.data_agendada, # Aprox
                'valor': mv.custo_real,
                'descricao': f"Manutenção {mv.viatura.matricula} - {mv.tipo_manutencao}"
            }
        )
    print("Pagamentos migrados.")

def run():
    print("=== INICIANDO INTEGRAÇÃO SUPREMA UGEA ===")
    migrar_fornecedores()
    migrar_contratos()
    migrar_pagamentos()
    print("=== INTEGRAÇÃO CONCLUÍDA ===")

if __name__ == "__main__":
    run()
