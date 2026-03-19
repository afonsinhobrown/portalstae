
import os
import django
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

from ugea.models import PedidoConsumo
from gestaocombustivel.models import PedidoCombustivel

print("--- INICIANDO CORREÇÃO DE DADOS (SYNC) ---")

# Regex para extrair o ID do pedido original da descrição
# Padrão antigo: "Pedido via Gestão Combustível #123 ..."
# Padrão novo: "Abastecimento Viatura ... (Ref: #123)"

count = 0
pedidos_ugea = PedidoConsumo.objects.all()

for p_ugea in pedidos_ugea:
    desc = p_ugea.descricao or ""
    fuel_id = None
    
    # Tenta encontrar o ID
    match = re.search(r'#(\d+)', desc)
    if match:
        fuel_id = match.group(1)
        
    if fuel_id:
        try:
            pedido_original = PedidoCombustivel.objects.get(id=fuel_id)
            
            # Fonte da verdade: O PedidoCombustivel
            nome_real = pedido_original.solicitante.nome_completo
            viatura_real = pedido_original.viatura.matricula
            
            # Atualizar UGEA
            changed = False
            
            # Se o solicitante estiver vazio ou parecer errado, corrige
            if not p_ugea.solicitante or "Viatura" in p_ugea.solicitante or p_ugea.solicitante == "N/A":
                print(f"[FIX] Pedido UGEA {p_ugea.id}: Solicitante '{p_ugea.solicitante}' -> '{nome_real}'")
                p_ugea.solicitante = nome_real
                changed = True
                
            # Garante que a descrição tenha a info da viatura se não tiver
            if "Viatura" not in p_ugea.descricao:
                 p_ugea.descricao = f"Abastecimento Viatura {viatura_real} (Ref: #{fuel_id})"
                 changed = True
            
            if changed:
                p_ugea.save()
                count += 1
                
        except PedidoCombustivel.DoesNotExist:
            print(f"[WARN] Pedido original #{fuel_id} não encontrado para UGEA {p_ugea.id}")
    else:
        print(f"[SKIP] Não foi possível extrair ID de origem de: '{desc}'")

print(f"--- FIM. Total corrigidos: {count} ---")
