
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

from ugea.models import Contrato, ItemContrato

print("--- DIAGNÓSTICO DE ITENS DE CONTRATO ---")

try:
    contrato = Contrato.objects.get(id=1) # Assumindo ID 1 como o principal que estamos mexendo
    print(f"Contrato #{contrato.id}: {contrato.numero_contrato}")
    
    print(f"Itens (Total: {contrato.itens.count()}):")
    for item in contrato.itens.all():
        print(f" - ID {item.id} | Desc: '{item.descricao}' | Preço: {item.preco_unitario}")
        
except Contrato.DoesNotExist:
    print("Contrato ID 1 não encontrado.")
    # Listar último contrato modificado
    last = Contrato.objects.order_by('-data_atualizacao').first()
    if last:
        print(f"Último contrato modificado ID: {last.id}")
        for item in last.itens.all():
            print(f" - ID {item.id} | Desc: '{item.descricao}' | Preço: {item.preco_unitario}")

print("--- FIM ---")
