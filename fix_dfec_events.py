import os
import sys
import django
from datetime import date

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "portalstae.settings")
django.setup()

from credenciais.models import Evento

def run():
    print("--- DIAGNÓSTICO DE EVENTOS ---")
    eventos = Evento.objects.all().order_by('-id')
    
    if not eventos.exists():
        print("NENHUM evento encontrado! Criando um de teste...")
        Evento.objects.create(
            nome="Curso de Formação DFEC (Teste)",
            categoria='formacao',
            data_inicio=date(2025, 1, 1),
            data_fim=date(2025, 12, 31),
            ativo=True,
            descricao='Evento criado automaticamente para teste.'
        )
        print("Evento de teste criado com sucesso.")
    else:
        for e in eventos:
            status = "ATIVO" if e.ativo else "INATIVO"
            print(f"[{e.id}] {e.nome}")
            print(f"    Categoria: {e.categoria}")
            print(f"    Status: {status}")
            print(f"    Datas: {e.data_inicio} a {e.data_fim}")
            
            # Se for DFEC e estiver inativo, ativar
            if 'formacao' in e.categoria and not e.ativo:
                print(f"   -> ATIVANDO evento DFEC automaticamente...")
                e.ativo = True
                e.save()
            
            # Se for teste antigo, manter
            print("-" * 30)

    print("Verifique se o evento desejado está listado acima como ATIVO.")

if __name__ == "__main__":
    run()
