import os
import django
import sys
from decimal import Decimal

# Setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "portalstae.settings")
django.setup()

from gestaocombustivel.models import PedidoCombustivel, ContratoCombustivel
from ugea.models import Contrato, PedidoConsumo, Fornecedor

def run():
    print("=== Sincronizando Pedidos de Combustível com Aprovação UGEA ===")
    
    pedidos_origem = PedidoCombustivel.objects.all()
    count = 0
    
    for p in pedidos_origem:
        # Encontrar contrato UGEA correspondente
        # Assumindo que o contrato de combustível tem o mesmo número na UGEA (garantido pelo script anterior)
        # O PedidoCombustivel original pode não ter link direto para Contrato, então inferimos pelo fornecedor/tipo
        # MAS, na nossa migração anterior, assumimos que criamos Contratos com o 'numero_contrato' original.
        
        # Estratégia: Tentar achar um contrato ativo de Combustível na UGEA para este tipo
        # Como o PedidoCombustivel pode não ter contrato vinculado explicitamente no modelo antigo,
        # vamos usar o primeiro contrato ativo do tipo de combustível correspondente.
        
        tipo = p.viatura.tipo_combustivel if p.viatura else 'diesel' # Fallback
        
        contrato_ugea = Contrato.objects.filter(
            tipo_servico__icontains=tipo,
            ativo=True
        ).first()
        
        if not contrato_ugea:
            print(f" -> AVISO: Nenhum contrato UGEA encontrado para {tipo}. Pulando pedido {p.id}.")
            continue
            
        # Verificar duplicados (simples, por descrição + data aprox)
        # Ajuste: Campo motivo não existe no PedidoCombustivel, remover uso.
        descricao_match = f"Abastecimento Viatura {p.viatura.matricula} (Sincronizado)"
        existe = PedidoConsumo.objects.filter(
            descricao=descricao_match,
            quantidade=p.quantidade_litros
        ).exists()
        
        if existe:
            continue
            
        print(f" -> Criando Pedido de Aprovação UGEA para: {p.viatura}")
        
        # Calcular valor estimado
        valor = Decimal(p.quantidade_litros) * contrato_ugea.preco_unitario
        
        PedidoConsumo.objects.create(
            contrato=contrato_ugea,
            solicitante=f"Viatura {p.viatura.matricula}",
            descricao=descricao_match,
            quantidade=p.quantidade_litros,
            valor_estimado=valor,
            status='pendente' if p.status == 'pendente' else 'aprovado'
        )
        count += 1

    print(f"\n=== Sincronização Concluída. {count} pedidos enviados para UGEA. ===")

if __name__ == "__main__":
    run()
