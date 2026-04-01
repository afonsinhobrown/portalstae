from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Eleicao, EventoEleitoral
from .forms import EleicaoForm, EventoForm

def dashboard(request):
    eleicoes = Eleicao.objects.all().order_by('-ano')
    proxima_eleicao = Eleicao.objects.filter(ativo=True).first()
    
    return render(request, 'eleicao/dashboard.html', {
        'eleicoes': eleicoes,
        'proxima_eleicao': proxima_eleicao
    })

def criar_eleicao(request):
    if request.method == 'POST':
        form = EleicaoForm(request.POST)
        if form.is_valid():
            eleicao = form.save()
            messages.success(request, 'Eleição criada com sucesso!')
            return redirect('eleicao:detalhe_eleicao', eleicao_id=eleicao.id)
    else:
        form = EleicaoForm()
    return render(request, 'eleicao/form_eleicao.html', {'form': form, 'titulo': 'Nova Eleição'})

def detalhe_eleicao(request, eleicao_id):
    eleicao = get_object_or_404(Eleicao, id=eleicao_id)
    eventos = eleicao.eventos.all().order_by('data_inicio')
    
    if request.method == 'POST':
        form_evento = EventoForm(request.POST)
        if form_evento.is_valid():
            evento = form_evento.save(commit=False)
            evento.eleicao = eleicao
            evento.save()
            messages.success(request, 'Evento adicionado ao calendário!')
            return redirect('eleicao:detalhe_eleicao', eleicao_id=eleicao.id)
    else:
        form_evento = EventoForm()
        
    return render(request, 'eleicao/detalhe_eleicao.html', {
        'eleicao': eleicao,
        'eventos': eventos,
        'form_evento': form_evento
    })

def editar_eleicao(request, eleicao_id):
    eleicao = get_object_or_404(Eleicao, id=eleicao_id)
    if request.method == 'POST':
        form = EleicaoForm(request.POST, instance=eleicao)
        if form.is_valid():
            form.save()
            return redirect('eleicao:detalhe_eleicao', eleicao_id=eleicao.id)
    else:
        form = EleicaoForm(instance=eleicao)
    return render(request, 'eleicao/form_eleicao.html', {'form': form, 'titulo': f'Editar {eleicao.nome}'})

def calendario_geral(request):
    """Visualização global de todos os marcos eleitorais"""
    eleicoes = Eleicao.objects.filter(ativo=True)
    eventos = EventoEleitoral.objects.all().order_by('data_inicio')
    return render(request, 'eleicao/calendario.html', {
        'eleicoes': eleicoes,
        'eventos': eventos
    })

def gestao_materiais(request):
    """Controle de logística e materiais (Urnas, etc)"""
    from rs.models import MaterialEleitoral
    eleicao_ativa = Eleicao.objects.filter(ativo=True).first()
    try:
        materiais = list(MaterialEleitoral.objects.filter(eleicao=eleicao_ativa)) if eleicao_ativa else []
    except Exception:
        materiais = []
    
    return render(request, 'eleicao/materiais.html', {
        'eleicao': eleicao_ativa,
        'materiais': materiais
    })

def configuracoes_eleicao(request):
    """Configurações técnicas do sistema eleitoral"""
    eleicao_ativa = Eleicao.objects.filter(ativo=True).first()
    return render(request, 'eleicao/configuracoes.html', {
        'eleicao': eleicao_ativa
    })
