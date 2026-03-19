
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

from ugea.models import Contrato, ItemContrato

def sync_items():
    contratos = Contrato.objects.all()
    count = 0
    for c in contratos:
        if not c.itens.exists():
            caderno = getattr(c.concurso, 'cadernoencargos', None)
            if caderno:
                print(f"Sincronizando contrato {c.numero_contrato}...")
                for item_c in caderno.itens.all():
                    ItemContrato.objects.get_or_create(
                        contrato=c,
                        descricao=item_c.descricao,
                        defaults={'preco_unitario': 0}
                    )
                    count += 1
    print(f"Sincronização concluída. {count} itens criados.")

if __name__ == "__main__":
    sync_items()
