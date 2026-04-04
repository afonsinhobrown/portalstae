import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

from rs.models import PlanoLogistico, MaterialEleitoral, CategoriaMaterial, TipoMaterial
from eleicao.models import Eleicao
from django.db import transaction

def importar_requisitos_materiais():
    print("--- IMPORTAÇÃO TÉCNICA DE REQUISITOS (STAE) ---")
    
    # 1. Identificar o Plano para a Eleição ID 3
    # Se não houver um plano, criamos um Plano de Soberania Padrão
    plano = PlanoLogistico.objects.filter(eleicao_id=3).order_by('-id').first()
    if not plano:
        from django.utils.timezone import now
        from datetime import timedelta
        eleicao = Eleicao.objects.get(id=3)
        plano = PlanoLogistico.objects.create(
            nome=f"Plano Integrado - {eleicao.nome}",
            eleicao=eleicao,
            data_inicio=now().date(),
            data_fim=now().date() + timedelta(days=180), # Horizonte de 6 meses
            esta_ativo=True
        )
        print(f"Set-up: Criado Plano Logístico para {eleicao.nome}")

    with transaction.atomic():
        # 2. Criar ou Obter Categorias de Portugal/Moçambique
        cat_ti, _ = CategoriaMaterial.objects.get_or_create(nome="Informática e Infraestrutura")
        cat_cons, _ = CategoriaMaterial.objects.get_or_create(nome="Consumíveis de Registo")
        cat_sens, _ = CategoriaMaterial.objects.get_or_create(nome="Material Sensível")
        cat_kits, _ = CategoriaMaterial.objects.get_or_create(nome="Kits de Votação")

        # 3. Lista de Itens a Importar
        requisitos = [
            {
                'item': "Discos de Upgrade para Servidores Centrais",
                'cat': cat_ti,
                'op': 'VOTACAO',
                'p_unit': 45000.00, # Valor Estimativo em MZN
                'qtd': 20,
                'distr': False # Mantém-se no Nível Central
            },
            {
                'item': "Toner para Impressoras de Cartões",
                'cat': cat_cons,
                'op': 'RECENSEAMENTO',
                'p_unit': 8500.00,
                'qtd': 500,
                'distr': True
            },
            {
                'item': "Cartões de Eleitor (PVC com Microchip)",
                'cat': cat_cons,
                'op': 'RECENSEAMENTO',
                'p_unit': 120.00,
                'qtd': 1000000,
                'distr': True
            },
            {
                'item': "Boletins de Inscrição de Recenseamento",
                'cat': cat_sens,
                'op': 'RECENSEAMENTO',
                'p_unit': 15.50,
                'qtd': 2000000,
                'distr': True
            },
            {
                'item': "Kits de Votação Completos (Urnas, Cabines, Selos)",
                'cat': cat_kits,
                'op': 'VOTACAO',
                'p_unit': 125000.00,
                'qtd': 150, # Exemplo de Kits Master
                'distr': True
            }
        ]

        print("A processar requisitos orçamentais...")
        for req in requisitos:
            tipo_din, _ = TipoMaterial.objects.get_or_create(
                nome=req['item'],
                categoria=req['cat']
            )

            material, created = MaterialEleitoral.objects.update_or_create(
                plano=plano,
                item=req['item'],
                defaults={
                    'tipo_dinamico': tipo_din,
                    'tipo_operacao': req['op'],
                    'quantidade_planeada': req['qtd'],
                    'preco_unitario': Decimal(str(req['p_unit'])),
                    'por_distrito': req['distr']
                }
            )
            status = "Criado" if created else "Atualizado"
            print(f" > {status}: {req['item']} | Operação: {req['op']}")

    print(f"\n[SUCESSO] Importação concluída no Plano: {plano.nome}")

if __name__ == "__main__":
    importar_requisitos_materiais()
