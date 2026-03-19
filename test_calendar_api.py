
import os
import django
import json
from django.conf import settings
from django.urls import reverse

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "portalstae.settings")
django.setup()

from dfec.models.completo import PlanoAtividade
from django.urls import set_script_prefix

# Mock request context for reverse to work (though reverse usually works without request if not building absolute URIs)
# We just want to see the JSON structure.

def test_api(plano_id):
    planos = PlanoAtividade.objects.filter(id=plano_id)
    eventos = []
    
    for plano in planos:
        if plano.data_inicio_planeada:
             eventos.append({
                'title': f"Plano: {plano.nome}",
                'start': plano.data_inicio_planeada.isoformat(),
                'end': plano.data_fim_planeada.isoformat() if plano.data_fim_planeada else None,
                'color': '#4e73df', 
                'allDay': True,
                # 'url': reverse('dfec:plano_detalhe', args=[plano.id]) # reverse needs configured urlconf, might fail in raw script if not careful
            })
        
        for atividade in plano.atividades.all():
            if not atividade.data_inicio:
                continue

            cor = '#1cc88a'
            if atividade.status == 'NAO_INICIADO': cor = '#858796'
            
            eventos.append({
                'title': atividade.nome,
                'start': atividade.data_inicio.isoformat(),
                'end': atividade.data_fim.isoformat() if atividade.data_fim else None,
                'client': 'dfec',
                'allDay': True,
                'color': cor,
                'description': atividade.descricao or "",
            })
            
    print(json.dumps(eventos, indent=2))

test_api(2)
