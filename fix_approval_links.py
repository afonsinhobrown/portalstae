import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

from ugea.models import PedidoConsumo
from gestaocombustivel.models import PedidoCombustivel

def fix_links():
    print("Fixing links between PedidoConsumo and PedidoCombustivel...")
    pedidos_combustivel = PedidoCombustivel.objects.all()
    
    for p_fuel in pedidos_combustivel:
        # Tenta encontrar o PedidoConsumo pela descrição ou solicitante/data
        # Descrição formato: "Abastecimento Viatura AB-111-CD (Ref: #123)"
        ref_text = f"(Ref: #{p_fuel.id})"
        p_ugea = PedidoConsumo.objects.filter(descricao__contains=ref_text).first()
        
        if p_ugea:
            if not p_ugea.ref_id or not p_ugea.modulo_origem:
                p_ugea.modulo_origem = 'gestaocombustivel'
                p_ugea.ref_id = p_fuel.id
                p_ugea.save()
                print(f"Linked UGEA #{p_ugea.id} to Fuel #{p_fuel.id}")
        else:
            print(f"No UGEA found for Fuel #{p_fuel.id}")

if __name__ == "__main__":
    fix_links()
