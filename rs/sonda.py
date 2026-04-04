from django.http import JsonResponse
from django.apps import apps
from django.contrib.auth.decorators import login_required

def sondar_factos_reais(request):
    """Sonda técnica para listar o que de facto existe na Neon"""
    inventario = {}
    for model in apps.get_models():
        try:
            count = model.objects.count()
            if count > 0:
                key = f"{model._meta.app_label}.{model.__name__}"
                detalhes = []
                if any(k in model.__name__.lower() for k in ['eleicao', 'plano']):
                    for obj in model.objects.all():
                        detalhes.append({
                            'id': obj.id,
                            'info': getattr(obj, 'nome', getattr(obj, 'titulo', str(obj)))
                        })
                inventario[key] = {
                    'total': count,
                    'detalhes': detalhes
                }
        except:
            continue
    return JsonResponse({'status': 'soberano', 'base': 'Neon PostgreSQL', 'data': inventario}, json_dumps_params={'indent': 2})
