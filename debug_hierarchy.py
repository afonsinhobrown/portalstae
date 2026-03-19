import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

from recursoshumanos.models import Funcionario, Sector, Licenca
from django.db.models import Q




def check_hierarchy():
    try:
        director = Funcionario.objects.get(user__username='usuarioaaa0')
        direcao_alvo = director.sector
        print(f"Director Sector: {direcao_alvo.id} - {direcao_alvo.nome}")
        
        # Exact query from views.py
        licencas = Licenca.objects.filter(
            Q(funcionario__sector=direcao_alvo) |
            Q(funcionario__sector__direcao=direcao_alvo) |
            Q(funcionario__sector__direcao__direcao=direcao_alvo)
        )
        
        print(f"Query Count: {licencas.count()}")
        print("Query SQL equivalent logic check:")
        
        all_lics = Licenca.objects.all()
        for l in all_lics:
            s = l.funcionario.sector
            p = s.direcao
            gp = p.direcao if p else None
            
            match_s = (s == direcao_alvo)
            match_p = (p == direcao_alvo)
            match_gp = (gp == direcao_alvo)
            
            if match_s or match_p or match_gp:
                 print(f" [MATCH] Lic {l.id} | Sec: {s.id} | Parent: {p.id if p else 'None'} | Top: {gp.id if gp else 'None'}")
            else:
                 # Debug why it missed if we expected it
                 if l.funcionario.nome_completo.upper().find("ANA MARIA") != -1:
                     print(f" [FAIL] Lic {l.id} | Sec: {s.id} | Parent: {p.id if p else 'None'} | Target was: {direcao_alvo.id}")

    except Exception as e:
        print(f"ERR: {e}")

if __name__ == "__main__":
    check_hierarchy()
