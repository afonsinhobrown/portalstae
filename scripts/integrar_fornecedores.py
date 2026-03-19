import os
import django
import sys

# Setup do ambiente
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "portalstae.settings")
django.setup()

from gestaocombustivel.models import FornecedorCombustivel
from ugea.models import Fornecedor

def run():
    print("=== Migrando Fornecedores de Combustível para Base UGEA Central ===")
    
    fornecedores_origem = FornecedorCombustivel.objects.all()
    
    if not fornecedores_origem.exists():
        print("Nenhum fornecedor encontrado na app Gestão Combustível.")
        return

    count = 0
    updated = 0
    
    for f in fornecedores_origem:
        # Verificar duplicados pelo NUIT
        existe = Fornecedor.objects.filter(nuit=f.nuit).first()
        
        if existe:
            print(f" -> Atualizando Fornecedor existente: {f.nome}")
            existe.nome = f.nome # Atualiza nome se mudou
            existe.telefone = f.contacto
            existe.endereco = f.endereco
            existe.email = f.email
            if existe.categoria != 'combustivel':
                existe.categoria = 'combustivel' # ou manter misto
            existe.save()
            updated += 1
        else:
            print(f" -> Criando Novo Fornecedor UGEA: {f.nome}")
            Fornecedor.objects.create(
                nome=f.nome,
                nuit=f.nuit,
                endereco=f.endereco,
                email=f.email,
                telefone=f.contacto,
                categoria='combustivel',
                ativo=f.ativo
            )
            count += 1
            
    print(f"\n=== Migração Concluída ===")
    print(f"Novos: {count}")
    print(f"Atualizados: {updated}")

if __name__ == "__main__":
    run()
