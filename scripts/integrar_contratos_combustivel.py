import os
import django
import sys
from decimal import Decimal
from datetime import date

# Setup do ambiente Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "portalstae.settings")
django.setup()

from gestaocombustivel.models import ContratoCombustivel
from ugea.models import Concurso, CadernoEncargos, Proposta, Contrato

def run():
    print("=== Iniciando Integração de Contratos de Combustível para UGEA ===")
    
    contratos_combustivel = ContratoCombustivel.objects.all()
    
    if not contratos_combustivel.exists():
        print("Nenhum contrato de combustível encontrado.")
        return

    count = 0
    for cc in contratos_combustivel:
        print(f"Processando contrato: {cc.numero_contrato} ({cc.fornecedor.nome})")
        
        # 1. Verificar se já existe Contrato UGEA com este número
        if Contrato.objects.filter(numero_contrato=cc.numero_contrato).exists():
            print(f" -> Contrato {cc.numero_contrato} já existe. Atualizando detalhes...")
            c = Contrato.objects.get(numero_contrato=cc.numero_contrato)
            c.tipo_servico = f"Combustível {cc.tipo_combustivel.capitalize()}"
            c.preco_unitario = cc.preco_unitario
            c.sector_id = 6
            c.valor_executado = cc.valor_consumido_total
            c.save()
            continue

        # 2. Criar Concurso Mock
        titulo_concurso = f"Fornecimento de Combustível ({cc.tipo_combustivel}) - {cc.numero_contrato}"
        concurso = Concurso.objects.create(
            titulo=titulo_concurso,
            tipo="Concurso Público",
            descricao=f"Regularização de contrato existente de {cc.tipo_combustivel}.",
            data_abertura=cc.data_inicio,
            data_encerramento=cc.data_inicio, # Simbólico
            valor_estimado=cc.valor_total_contrato,
            status='encerrado' # Já está activo
        )
        print(f" -> Concurso criado: {concurso.numero}")

        # 3. Criar Caderno de Encargos Mock
        CadernoEncargos.objects.create(
            concurso=concurso,
            objeto_concurso=f"Fornecimento de {cc.tipo_combustivel} para frota.",
            especificacoes_tecnicas=f"Combustível {cc.tipo_combustivel} conforme padrões nacionais.",
            condicoes_administrativas="Conforme contrato vigente.",
            clausulas_contratuais="Contrato já assinado.",
            prazo_execucao_dias=365,
            garantia_exigida=0
        )

        # 4. Criar Proposta Vencedora Mock
        proposta = Proposta.objects.create(
            concurso=concurso,
            fornecedor=cc.fornecedor.nome,
            nuit=cc.fornecedor.nuit,
            valor_proposto=cc.valor_total_contrato,
            prazo_entrega_dias=1,
            validade_proposta_dias=90,
            pontuacao_tecnica=100.0,
            pontuacao_financeira=100.0,
            pontuacao_final=100.0,
            classificacao=1  # Indica vencedora
        )

        # 5. Criar Contrato UGEA (Com Detalhes)
        Contrato.objects.create(
            concurso=concurso,
            proposta_vencedora=proposta,
            numero_contrato=cc.numero_contrato,
            data_inicio=cc.data_inicio,
            data_fim=cc.data_fim,
            valor_total=cc.valor_total_contrato,
            valor_executado=cc.valor_consumido_total,
            # Novos Campos Detalhados
            tipo_servico=f"Combustível {cc.tipo_combustivel.capitalize()}",
            preco_unitario=cc.preco_unitario,
            sector_id=6 # ID 6: Dept. Transportes e Logística (Fixo conforme pedido)
        )
        
        count += 1
        print(" -> Contrato UGEA criado com sucesso.")

    print(f"\n=== Integração Concluída. {count} contratos migrados. ===")

if __name__ == "__main__":
    run()
