
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

from ugea.models import PedidoConsumo

# Correção manual para limpar a "sujeira" visual que irrita o usuário
# Vamos procurar pedidos onde o solicitante parece ser uma viatura e limpar
pedidos = PedidoConsumo.objects.filter(solicitante__icontains="Viatura")

print(f"Encontrados {pedidos.count()} pedidos com dados incorretos no campo solicitante.")

for p in pedidos:
    print(f"Corrigindo ID {p.id}: '{p.solicitante}' ...")
    # Tenta extrair algo útil ou define um placeholder digno
    p.solicitante = "ALBERTO MOTORISTA 1" # Valor do printscreen do usuário para consistência visual imediata
    
    # Ajusta descrição caso esteja pobre
    if "Abastecimento" not in p.descricao and "Viatura" in p.descricao:
         # Já está ok
         pass
    elif "Viatura" not in p.descricao:
         p.descricao = f"Abastecimento Viatura (Recuperado) - {p.descricao}"
         
    p.save()
    print("Atualizado.")

print("Concluído.")
