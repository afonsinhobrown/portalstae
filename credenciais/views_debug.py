# credenciais/views_debug.py
from django.shortcuts import render
from django.http import HttpResponse
from .models import Evento
from .forms import PedidoCredencialForm
import json


def debug_eventos_view(request):
    """View para debug dos eventos"""

    # 1. Verificar eventos diretamente do modelo
    eventos = Evento.objects.all()
    eventos_ativos = Evento.objects.filter(ativo=True)

    # 2. Criar formulário
    form = PedidoCredencialForm()

    # 3. Verificar o queryset do campo evento
    evento_field = form.fields['evento']
    evento_queryset = evento_field.queryset

    # 4. Preparar dados para mostrar
    data = {
        'total_eventos': eventos.count(),
        'eventos_ativos': eventos_ativos.count(),
        'eventos_list': list(eventos.values('id', 'nome', 'activo', 'data_inicio')),
        'eventos_ativos_list': list(eventos_ativos.values('id', 'nome', 'activo', 'data_inicio')),
        'form_evento_queryset_count': evento_queryset.count(),
        'form_evento_queryset_items': list(evento_queryset.values('id', 'nome', 'activo')),
    }

    return HttpResponse(json.dumps(data, indent=2, default=str), content_type='application/json')
