from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Partido, LiderancaPartido
from .forms import PartidoForm, LiderancaForm

@login_required
def dashboard(request):
    # Estatísticas
    total_partidos = Partido.objects.count()
    partidos_ativos = Partido.objects.filter(ativo=True).count()
    
    # Listagem recente
    partidos = Partido.objects.all().order_by('-criado_em')[:10]
    
    context = {
        'total_partidos': total_partidos,
        'partidos_ativos': partidos_ativos,
        'partidos': partidos
    }
    return render(request, 'partidos/dashboard.html', context)

@login_required
def criar_partido(request):
    if request.method == 'POST':
        form = PartidoForm(request.POST, request.FILES)
        if form.is_valid():
            partido = form.save()
            messages.success(request, f'Partido {partido.sigla} registado com sucesso!')
            return redirect('partidos:detalhe_partido', partido_id=partido.id)
    else:
        form = PartidoForm()
    
    return render(request, 'partidos/form_partido.html', {'form': form, 'titulo': 'Novo Partido'})

@login_required
def detalhe_partido(request, partido_id):
    partido = get_object_or_404(Partido, id=partido_id)
    liderancas = partido.historico_lideranca.all().order_by('-ativo', '-data_inicio')
    
    return render(request, 'partidos/detalhe_partido.html', {
        'partido': partido,
        'liderancas': liderancas
    })

@login_required
def editar_partido(request, partido_id):
    partido = get_object_or_404(Partido, id=partido_id)
    if request.method == 'POST':
        form = PartidoForm(request.POST, request.FILES, instance=partido)
        if form.is_valid():
            form.save()
            messages.success(request, 'Dados do partido atualizados!')
            return redirect('partidos:detalhe_partido', partido_id=partido.id)
    else:
        form = PartidoForm(instance=partido)
    
    return render(request, 'partidos/form_partido.html', {'form': form, 'titulo': f'Editar {partido.sigla}'})

@login_required
def lista_partidos(request):
    query = request.GET.get('q', '')
    if query:
        partidos = Partido.objects.filter(
            models.Q(sigla__icontains=query) | 
            models.Q(nome_completo__icontains=query)
        ).order_by('sigla')
    else:
        partidos = Partido.objects.all().order_by('sigla')
    
    return render(request, 'partidos/lista_partidos.html', {
        'partidos': partidos,
        'query': query
    })

@login_required
def lista_liderancas(request):
    liderancas = LiderancaPartido.objects.all().select_related('partido').order_by('-ativo', 'nome')
    return render(request, 'partidos/lista_liderancas.html', {
        'liderancas': liderancas
    })

@login_required
def lista_documentos(request):
    partidos = Partido.objects.all().order_by('sigla')
    return render(request, 'partidos/lista_documentos.html', {
        'partidos': partidos
    })
