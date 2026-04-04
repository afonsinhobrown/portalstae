import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

from eleicao.models import Eleicao
from rs.models import PlanoLogistico

def mapear():
    output_file = "MAPA_SISTEMA_STAE.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("=== DICIONÁRIO DE SOBERANIA - ELEIÇÕES ===\n")
        eleicoes = Eleicao.objects.all().order_by('id')
        for e in eleicoes:
            status = "[ATIVO]" if e.ativo else "[INATIVO]"
            f.write(f"ID: {e.id} | {e.nome} | Ano: {e.ano} | Tipo: {e.tipo} {status}\n")
        
        f.write("\n=== DICIONÁRIO DE SOBERANIA - PLANOS LOGÍSTICOS ===\n")
        planos = PlanoLogistico.objects.all().order_by('id')
        for p in planos:
            status = "[ATIVO]" if p.esta_ativo else "[INATIVO]"
            eleicao_nome = p.eleicao.nome if p.eleicao else "SEM ELEIÇÃO"
            ref_nome = p.eleicao_referencia.nome if p.eleicao_referencia else "SEM REFERÊNCIA"
            f.write(f"ID: {p.id} | Nome: {p.nome} | {status}\n")
            f.write(f"      -> Eleição Operativa: {eleicao_nome} (ID: {p.eleicao_id})\n")
            f.write(f"      -> Eleição Referência: {ref_nome} (ID: {p.eleicao_referencia_id})\n")
            f.write("-" * 50 + "\n")

    print(f"Mapeamento concluído. Verifique o ficheiro: {output_file}")

if __name__ == "__main__":
    mapear()
