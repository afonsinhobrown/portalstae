import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

from rs.models import ModeloVisualArtefacto
from eleicao.models import Eleicao
from django.core.files import File

def seed_primeiro_modelo():
    eleicao = Eleicao.objects.filter(ativo=True).first()
    if not eleicao:
        print("SAD: Nenhuma eleição ativa encontrada.")
        return

    print(f"DEBUG: Encontrada eleição: {eleicao.nome}")
    img_path = 'c:/Users/Acer/Documents/tecnologias/portalstae/static/img/stae_mecanismo_soberania_urnas_cabines.png'
    
    if not os.path.exists(img_path):
        print(f"ERROR: Imagem não encontrada em {img_path}")
        return

    # Proposta de Urna
    with open(img_path, 'rb') as f:
        obj, created = ModeloVisualArtefacto.objects.get_or_create(
            eleicao=eleicao,
            tipo='urna',
            versao=1,
            defaults={
                'descricao_tecnica': "Urna oficial STAE v1. Polímero reforçado, visor de transparência frontal para auditoria visual instantânea.",
                'status': 'pendente'
            }
        )
        if created:
            obj.imagem.save('modelo_urna_v1.png', File(f))
            print("OK: Urna V1 criada.")
        else:
            print("INFO: Urna V1 já existe.")

    # Proposta de Cabine
    with open(img_path, 'rb') as f:
        obj, created = ModeloVisualArtefacto.objects.get_or_create(
            eleicao=eleicao,
            tipo='cabine',
            versao=1,
            defaults={
                'descricao_tecnica': "Cabine de votação rápida. Estrutura de alumínio aeroespacial leve, cortinas blackout com cores nacionais.",
                'status': 'pendente'
            }
        )
        if created:
            obj.imagem.save('modelo_cabine_v1.png', File(f))
            print("OK: Cabine V1 criada.")
        else:
            print("INFO: Cabine V1 já existe.")

if __name__ == "__main__":
    seed_primeiro_modelo()
