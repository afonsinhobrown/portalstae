# gestaoequipamentos/views.py - CORREÇÃO COMPLETA
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone

from .models import Equipamento, MovimentacaoEquipamento, CategoriaEquipamento, TipoEquipamento, Armazem
from .forms import EquipamentoForm, MovimentacaoEquipamentoForm, CategoriaEquipamentoForm, ArmazemForm
from recursoshumanos.models import Sector, Funcionario


# ===== DASHBOARD =====
@login_required(login_url='/accounts/login/')  # ← ADICIONE AQUI
def dashboard_equipamentos(request):
    equipamentos = Equipamento.objects.filter(em_uso=True)
    movimentacoes_pendentes = MovimentacaoEquipamento.objects.filter(status='pendente')

    equipamentos_operacionais = equipamentos.filter(
        Q(estado='excelente') | Q(estado='bom') | Q(estado='regular')
    ).count()

    equipamentos_manutencao = equipamentos.filter(estado='precisa_manutencao').count()

    context = {
        'total_equipamentos': equipamentos.count(),
        'movimentacoes_pendentes': movimentacoes_pendentes.count(),
        'equipamentos_operacionais': equipamentos_operacionais,
        'equipamentos_manutencao': equipamentos_manutencao,
        'equipamentos_recentes': equipamentos.order_by('-data_criacao')[:5],
        'movimentacoes_recentes': movimentacoes_pendentes[:5],
    }
    return render(request, 'gestaoequipamentos/dashboard.html', context)


# ===== EQUIPAMENTOS =====
@login_required(login_url='/accounts/login/')  # ← ADICIONE AQUI
def lista_equipamentos(request):
    categoria_filter = request.GET.get('categoria', '')
    sector_filter = request.GET.get('sector', '')
    estado_filter = request.GET.get('estado', '')

    equipamentos = Equipamento.objects.filter(em_uso=True)

    if categoria_filter:
        equipamentos = equipamentos.filter(tipo__categoria_id=categoria_filter)
    if sector_filter:
        equipamentos = equipamentos.filter(sector_atual_id=sector_filter)
    if estado_filter:
        equipamentos = equipamentos.filter(estado=estado_filter)

    categorias = CategoriaEquipamento.objects.all()
    sectores = Sector.objects.all()

    return render(request, 'gestaoequipamentos/equipamento_list.html', {
        'equipamentos': equipamentos,
        'categorias': categorias,
        'sectores': sectores,
        'categoria_filter': categoria_filter,
        'sector_filter': sector_filter,
        'estado_filter': estado_filter,
    })


@login_required(login_url='/accounts/login/')  # ← ADICIONE AQUI
def novo_equipamento(request):
    if request.method == 'POST':
        form = EquipamentoForm(request.POST)
        if form.is_valid():
            equipamento = form.save(commit=False)
            equipamento.criado_por = request.user
            equipamento.save()
            messages.success(request, 'Equipamento adicionado com sucesso!')
            return redirect('gestaoequipamentos:detalhe_equipamento', equipamento_id=equipamento.id)
    else:
        form = EquipamentoForm()

    # DADOS PARA OS SELECTS
    tipos = TipoEquipamento.objects.select_related('categoria').all()
    sectores = Sector.objects.all()
    funcionarios = Funcionario.objects.filter(ativo=True)

    return render(request, 'gestaoequipamentos/equipamento_form.html', {
        'form': form,
        'titulo': 'Adicionar Novo Equipamento',
        'tipos': tipos,
        'sectores': sectores,
        'funcionarios': funcionarios
    })


@login_required(login_url='/accounts/login/')  # ← ADICIONE AQUI
def detalhe_equipamento(request, equipamento_id):
    equipamento = get_object_or_404(Equipamento, id=equipamento_id)
    movimentacoes = MovimentacaoEquipamento.objects.filter(equipamento=equipamento).order_by('-data_solicitacao')

    return render(request, 'gestaoequipamentos/equipamento_detail.html', {
        'equipamento': equipamento,
        'movimentacoes': movimentacoes,
    })


@login_required(login_url='/accounts/login/')  # ← ADICIONE AQUI
def editar_equipamento(request, equipamento_id):
    equipamento = get_object_or_404(Equipamento, id=equipamento_id)

    if request.method == 'POST':
        form = EquipamentoForm(request.POST, instance=equipamento)
        if form.is_valid():
            form.save()
            messages.success(request, 'Equipamento atualizado com sucesso!')
            return redirect('gestaoequipamentos:detalhe_equipamento', equipamento_id=equipamento.id)
    else:
        form = EquipamentoForm(instance=equipamento)

    return render(request, 'gestaoequipamentos/equipamento_form.html', {
        'form': form,
        'titulo': f'Editar {equipamento.tipo.nome}',
        'equipamento': equipamento
    })


@login_required(login_url='/accounts/login/')  # ← ADICIONE AQUI
def excluir_equipamento(request, equipamento_id):
    equipamento = get_object_or_404(Equipamento, id=equipamento_id)

    if request.method == 'POST':
        equipamento.em_uso = False
        equipamento.save()
        messages.success(request, 'Equipamento marcado como inativo!')
        return redirect('gestaoequipamentos:lista_equipamentos')

    return render(request, 'gestaoequipamentos/equipamento_confirm_delete.html', {
        'equipamento': equipamento
    })


@login_required(login_url='/accounts/login/')  # ← ADICIONE AQUI
def movimentar_equipamento(request, equipamento_id):
    equipamento = get_object_or_404(Equipamento, id=equipamento_id)

    if request.method == 'POST':
        form = MovimentacaoEquipamentoForm(request.POST)
        if form.is_valid():
            movimentacao = form.save(commit=False)
            movimentacao.equipamento = equipamento
            movimentacao.sector_origem = equipamento.sector_atual
            movimentacao.solicitado_por = request.user
            movimentacao.save()

            messages.success(request, 'Pedido de movimentação submetido com sucesso!')
            return redirect('gestaoequipamentos:detalhe_equipamento', equipamento_id=equipamento.id)
    else:
        form = MovimentacaoEquipamentoForm()

    return render(request, 'gestaoequipamentos/movimentar_equipamento.html', {
        'equipamento': equipamento,
        'form': form,
    })


# ===== MOVIMENTAÇÕES =====
@login_required(login_url='/accounts/login/')  # ← ADICIONE AQUI
def lista_movimentacoes(request):
    status_filter = request.GET.get('status', '')
    movimentacoes = MovimentacaoEquipamento.objects.all().order_by('-data_solicitacao')

    if status_filter:
        movimentacoes = movimentacoes.filter(status=status_filter)

    return render(request, 'gestaoequipamentos/movimentacoes_list.html', {
        'movimentacoes': movimentacoes,
        'status_filter': status_filter,
    })


@login_required(login_url='/accounts/login/')  # ← ADICIONE AQUI
def aprovar_movimentacao(request, movimentacao_id):
    movimentacao = get_object_or_404(MovimentacaoEquipamento, id=movimentacao_id)

    if request.method == 'POST':
        acao = request.POST.get('acao')

        if acao == 'aprovar' and request.user.is_staff:
            movimentacao.status = 'aprovada'
            movimentacao.aprovado_por = request.user
            movimentacao.data_aprovacao = timezone.now()
            messages.success(request, 'Movimentação aprovada!')
        elif acao == 'rejeitar' and request.user.is_staff:
            movimentacao.status = 'rejeitada'
            messages.success(request, 'Movimentação rejeitada!')

        movimentacao.save()
        return redirect('gestaoequipamentos:lista_movimentacoes')

    return render(request, 'gestaoequipamentos/aprovar_movimentacao.html', {
        'movimentacao': movimentacao
    })


@login_required(login_url='/accounts/login/')  # ← ADICIONE AQUI
def concluir_movimentacao(request, movimentacao_id):
    movimentacao = get_object_or_404(MovimentacaoEquipamento, id=movimentacao_id, status='aprovada')

    if request.method == 'POST':
        # Atualizar localização do equipamento
        movimentacao.equipamento.sector_atual = movimentacao.sector_destino
        movimentacao.equipamento.save()

        movimentacao.status = 'concluida'
        movimentacao.data_conclusao = timezone.now()
        movimentacao.save()

        messages.success(request, 'Movimentação concluída!')
        return redirect('gestaoequipamentos:lista_movimentacoes')

    return render(request, 'gestaoequipamentos/concluir_movimentacao.html', {
        'movimentacao': movimentacao
    })


# ===== CATEGORIAS =====
@login_required(login_url='/accounts/login/')  # ← ADICIONE AQUI
def lista_categorias(request):
    categorias = CategoriaEquipamento.objects.all()
    return render(request, 'gestaoequipamentos/categorias_list.html', {
        'categorias': categorias
    })


@login_required(login_url='/accounts/login/')  # ← ADICIONE AQUI
def nova_categoria(request):
    if request.method == 'POST':
        form = CategoriaEquipamentoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoria criada com sucesso!')
            return redirect('gestaoequipamentos:lista_categorias')
    else:
        form = CategoriaEquipamentoForm()

    return render(request, 'gestaoequipamentos/categoria_form.html', {
        'form': form,
        'titulo': 'Nova Categoria'
    })


# ===== ARMAZÉNS =====
@login_required(login_url='/accounts/login/')  # ← ADICIONE AQUI
def lista_armazens(request):
    armazens = Armazem.objects.all()
    return render(request, 'gestaoequipamentos/armazens_list.html', {
        'armazens': armazens
    })


@login_required(login_url='/accounts/login/')  # ← ADICIONE AQUI
def novo_armazem(request):
    if request.method == 'POST':
        form = ArmazemForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Armazém criado com sucesso!')
            return redirect('gestaoequipamentos:lista_armazens')
    else:
        form = ArmazemForm()

    return render(request, 'gestaoequipamentos/armazem_form.html', {
        'form': form,
        'titulo': 'Novo Armazém'
    })

# ===== PATRIMÓNIO GLOBAL (INTEGRAÇÃO RS E DFEC) =====
@login_required(login_url='/accounts/login/')
def patrimonio_global(request):
    """Vista agregadora de todos os activos do STAE geridos em diferentes módulos"""
    from rs.models import MaterialEleitoral
    from dfec.models.completo import LogisticaMaterialDFEC
    
    # 1. Equipamentos Gerais (Sede/Geral)
    equipamentos = Equipamento.objects.filter(em_uso=True)
    
    # 2. Logística Eleitoral (Módulo RS)
    materiais_eleitorais = MaterialEleitoral.objects.all()
    
    # 3. Materiais de Formação (Módulo DFEC)
    materiais_formacao = LogisticaMaterialDFEC.objects.all()
    
    context = {
        'equipamentos': equipamentos,
        'materiais_eleitorais': materiais_eleitorais,
        'materiais_formacao': materiais_formacao,
        'total_activos': equipamentos.count() + materiais_eleitorais.count() + materiais_formacao.count()
    }
    
    return render(request, 'gestaoequipamentos/patrimonio_global.html', context)
