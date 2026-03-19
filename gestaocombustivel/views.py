from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Sum
from django.http import HttpResponse
from datetime import date, timedelta, datetime
import csv

from django.utils import timezone

from .models import (
    Viatura, PedidoCombustivel, ManutencaoViatura, RotaTransporte,
    FornecedorCombustivel, ContratoCombustivel, FornecedorManutencao, ContratoManutencao,
    SeguroViatura, RegistroDiarioRota, RegistroUtilizacao, PagamentoContrato, PontoRota, FuncionarioRota,
    PrecoServicoContrato, TIPO_MANUTENCAO_CHOICES
)
from .forms import (PedidoCombustivelForm, ManutencaoViaturaForm, SeguroViaturaForm,
                    RotaTransporteForm, RegistroDiarioRotaForm, ViaturaForm, PontoRotaForm,
                    FornecedorCombustivelForm)
from recursoshumanos.models import Funcionario
from ugea.models import Contrato, PedidoConsumo, ItemContrato


def is_admin_combustivel(user):
    return user.is_authenticated and user.is_staff


@login_required
def dashboard_combustivel(request):
    """Dashboard principal de Gestão de Combustível"""
    viaturas = Viatura.objects.filter(activa=True)
    pedidos_pendentes = PedidoCombustivel.objects.filter(status='pendente')
    manutencoes_activas = ManutencaoViatura.objects.filter(status='em_curso')
    seguros_a_vencer = SeguroViatura.objects.filter(
        data_fim__lte=date.today() + timedelta(days=30),
        activo=True
    )
    rotas_activas = RotaTransporte.objects.filter(activa=True)
    
    # USANDO DADOS CENTRALIZADOS DA UGEA
    # Contratos de combustível ativos na UGEA
    contratos_ugea = Contrato.objects.filter(
        tipo_servico__icontains='combustível', 
        ativo=True
    ).order_by('data_fim')

    # Estatísticas
    total_gasto_mes = PedidoCombustivel.objects.filter(
        data_abastecimento__month=date.today().month,
        data_abastecimento__year=date.today().year,
        status='abastecido'
    ).aggregate(Sum('custo_total'))['custo_total__sum'] or 0
    
    # Totais e Detalhes por Contrato
    total_valor_contratos = 0
    total_gasto_contratos = 0
    total_remanescente_valor = 0
    total_divida = 0
    
    contratos_stats = []

    for c in contratos_ugea:
        # Calcular dívida (Executado vs Pago)
        # Assumindo que valor_executado é atualizado pelos Pagamentos e Pedidos Aprovados
        # Na UGEA: 
        #   valor_executado = soma dos pagamentos? NAO.
        #   valor_executado = geralmente é o valor GASTO (consumido) do contrato.
        #   valor_pago = o que tesouraria ja pagou.
        
        # Vamos assumir:
        # valor_executado = Total de Pedidos de Consumo Aprovados/Abastecidos
        # valor_pago = Soma de Pagamentos Reais
        
        # O modelo atual da UGEA tem: 
        #   .valor_executado (definido no Pagamento.save, o que está errado logicamente se for consumo, mas vamos ajustar)
        
        # Correção Lógica Rápida para Visualização:
        # Vamos calcular o consumido real via Pedidos
        consumido = c.pedidos_consumo.filter(status='aprovado').aggregate(Sum('valor_estimado'))['valor_estimado__sum'] or 0
        # Se usarmos PedidoCombustivel legado vinculado (ainda não está 100%), fallback para valor_executado do modelo
        if consumido == 0:
            consumido = c.valor_executado # Fallback

        pago = c.pagamentos.aggregate(Sum('valor'))['valor__sum'] or 0
        
        saldo = c.valor_total - consumido
        divida = consumido - pago
        if divida < 0: divida = 0

        total_valor_contratos += c.valor_total
        total_gasto_contratos += consumido
        
        if saldo > 0:
            total_remanescente_valor += saldo
            
        if divida > 0:
            total_divida += divida

        contratos_stats.append({
            'numero': c.numero_contrato,
            'fornecedor': c.proposta_vencedora.fornecedor, # CharField
            'valor_total': c.valor_total,
            'consumido': consumido,
            'saldo': saldo,
            'divida': divida,
            'percentual': (consumido / c.valor_total * 100) if c.valor_total > 0 else 0
        })
    
    percentual_consumido = 0
    if total_valor_contratos > 0:
        percentual_consumido = (total_gasto_contratos / total_valor_contratos) * 100

    
    # Lógica para mostrar info do contrato nos Cards
    contrato_info_display = ""
    count_contratos = contratos_ugea.count()
    if count_contratos == 1:
        c = contratos_ugea.first()
        contrato_info_display = f"Ref: Contrato {c.numero_contrato} - {c.proposta_vencedora.fornecedor}"
    elif count_contratos > 1:
        contrato_info_display = f"Ref: {count_contratos} Contratos Ativos (Ver detalhes abaixo)"
    else:
        contrato_info_display = "Nenhum contrato ativo vinculado"

    context = {
        'total_viaturas': viaturas.count(),
        'pedidos_pendentes': pedidos_pendentes.count(),
        'manutencoes_activas': manutencoes_activas.count(),
        'seguros_a_vencer': seguros_a_vencer.count(),
        'contratos_ativos_count': contratos_ugea.count(),
        'total_gasto_mes': total_gasto_mes,
        'total_valor_contratos': total_valor_contratos,
        'total_gasto_contratos': total_gasto_contratos,
        'percentual_consumido': percentual_consumido,
        # Novos KPIs
        'total_remanescente_valor': total_remanescente_valor,
        'total_divida': total_divida,
        'contratos_stats': contratos_stats,
        'contrato_info_display': contrato_info_display, # INFO PARA O USER
    }

    # Adicionar listas recentes ao contexto e contadores para sidebar
    context.update({
        'viaturas_recentes': viaturas.order_by('-data_criacao')[:5],
        'pedidos_recentes': pedidos_pendentes[:5],
        'rotas_recentes': rotas_activas.order_by('-data_criacao')[:4],
        'viaturas_count': viaturas.count(),
        'rotas_count': rotas_activas.count(),
        'manutencoes_activas_count': manutencoes_activas.count(),
    })
    
    return render(request, 'gestaocombustivel/dashboard.html', context)


# gestaocombustivel/views.py - função lista_viaturas()

@login_required
def lista_viaturas(request):
    """Lista todas as viaturas"""
    tipo_filter = request.GET.get('tipo', '')
    estado_filter = request.GET.get('estado', '')

    # MUDAR ISTO: Remover o filtro activa=True (ou usar .all())
    viaturas = Viatura.objects.all()  # ← Mostra TODAS as viaturas

    # viaturas = Viatura.objects.filter(activa=True)  # ← Isso filtra apenas ativas

    if tipo_filter:
        viaturas = viaturas.filter(tipo_viatura=tipo_filter)

    if estado_filter:
        viaturas = viaturas.filter(estado=estado_filter)

    return render(request, 'gestaocombustivel/viaturas_list.html', {
        'viaturas': viaturas,
        'tipo_filter': tipo_filter,
        'estado_filter': estado_filter,
    })


@login_required
def detalhe_viatura(request, viatura_id):
    """Detalhes de uma viatura específica"""
    viatura = get_object_or_404(Viatura, id=viatura_id)
    pedidos = PedidoCombustivel.objects.filter(viatura=viatura).order_by('-data_pedido')[:10]
    manutencoes = ManutencaoViatura.objects.filter(viatura=viatura).order_by('-data_solicitacao')[:5]
    seguros = SeguroViatura.objects.filter(viatura=viatura, ativo=True)

    return render(request, 'gestaocombustivel/viatura_detail.html', {
        'viatura': viatura,
        'pedidos': pedidos,
        'manutencoes': manutencoes,
        'seguros': seguros,
    })


# gestaocombustivel/views.py - função pedir_combustivel()

@login_required
def pedir_combustivel(request):
    """Solicitar combustível"""
    if request.method == 'POST':
        # Manipular POST para injetar compatibilidade com sistema legado
        data = request.POST.copy()
        
        contrato_id = data.get('contrato_id')
        item_id = data.get('item_id')
        
        contrato_ugea = None
        item_ugea = None
        
        if contrato_id:
            try:
                contrato_ugea = Contrato.objects.get(id=contrato_id)
                if item_id:
                    item_ugea = ItemContrato.objects.get(id=item_id)
                
                # Sincronizar Fornecedor Legado
                # Tenta achar pelo NUIT ou Nome
                nuit_fornecedor = contrato_ugea.proposta_vencedora.nuit
                nome_fornecedor = contrato_ugea.proposta_vencedora.fornecedor
                
                # Importar FornecedorCombustivel localmente
                from .models import FornecedorCombustivel
                
                fornecedor_legado = FornecedorCombustivel.objects.filter(nuit=nuit_fornecedor).first()
                if not fornecedor_legado:
                    fornecedor_legado = FornecedorCombustivel.objects.filter(nome__iexact=nome_fornecedor).first()
                
                if not fornecedor_legado:
                    # Criar um fornecedor espelho se não existir
                    fornecedor_legado = FornecedorCombustivel.objects.create(
                        nome=nome_fornecedor,
                        nuit=nuit_fornecedor,
                        activo=True,
                        observacoes="Gerado automaticamente via UGEA"
                    )
                
                data['fornecedor'] = fornecedor_legado.id
                
                # INJETAR PREÇO NO DATA PARA VALIDAR FORM
                if item_ugea:
                    data['preco_por_litro'] = item_ugea.preco_unitario
                elif contrato_ugea:
                    data['preco_por_litro'] = contrato_ugea.preco_unitario
                
            except Exception as e:
                pass # Deixa o form validar e falhar se necessário

        form = PedidoCombustivelForm(data)
        if form.is_valid():
            pedido = form.save(commit=False)

            # Se tivermos dados da UGEA, atualizar preço e totais
            if item_ugea:
                pedido.preco_por_litro = item_ugea.preco_unitario
                pedido.custo_total = pedido.quantidade_litros * pedido.preco_por_litro
            elif contrato_ugea:
                pedido.preco_por_litro = contrato_ugea.preco_unitario
                pedido.custo_total = pedido.quantidade_litros * pedido.preco_por_litro

            # Gerar número de senha único
            import random
            import time
            pedido.numero_senha = f"SENHA{int(time.time()) % 10000:04d}"

            # Salvar o pedido (o solicitante já vem do formulário)
            pedido.save()
            form.save_m2m()  # Para campos ManyToMany

            # CRIAR PEDIDO NA UGEA (Centralização)
            if contrato_ugea:
                try:
                    PedidoConsumo.objects.create(
                        contrato=contrato_ugea,
                        item_contrato=item_ugea,
                        solicitante=pedido.solicitante.nome_completo,
                        data_pedido=pedido.data_abastecimento,
                        quantidade=pedido.quantidade_litros,
                        valor_estimado=pedido.custo_total,
                        status='pendente',
                        descricao=f"Abastecimento Viatura {pedido.viatura.matricula} (Ref: #{pedido.id})",
                        modulo_origem='gestaocombustivel',
                        ref_id=pedido.id
                    )
                except Exception as e:
                    print(f"Erro ao criar PedidoConsumo UGEA: {e}")

            # Enviar mensagem de sucesso
            messages.success(request,
                             f'✅ Pedido de combustível submetido com sucesso!<br>'
                             f'<strong>Senha:</strong> {pedido.numero_senha}<br>'
                             f'<strong>Solicitante:</strong> {pedido.solicitante.nome_completo}<br>'
                             f'<strong>Viatura:</strong> {pedido.viatura.matricula}<br>'
                             f'<strong>Quantidade:</strong> {pedido.quantidade_litros}L'
                             )

            return redirect('gestaocombustivel:lista_pedidos')
        else:
            # Mostrar erros do formulário
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        # GET request - criar formulário
        form = PedidoCombustivelForm()

        # Pré-selecionar viatura se veio da lista de viaturas
        viatura_id = request.GET.get('viatura')
        if viatura_id:
            try:
                viatura = Viatura.objects.get(id=viatura_id)
                form.fields['viatura'].initial = viatura
                # Pré-preencher kilometragem da viatura
                if viatura.kilometragem_actual:
                    form.fields['kilometragem_actual'].initial = viatura.kilometragem_actual
            except Viatura.DoesNotExist:
                pass

    # BUSCAR DADOS DA UGEA PARA O FORMULÁRIO
    # Contratos de combustível ativos
    contratos_ugea = Contrato.objects.filter(
        tipo_servico__icontains='combustível',
        ativo=True
    ).prefetch_related('itens')

    # Serializar dados para usar no JS (Contrato -> Itens -> Preço)
    import json
    contratos_data = []
    for c in contratos_ugea:
        itens = []
        for i in c.itens.all():
            itens.append({
                'id': i.id,
                'descricao': i.descricao,
                'preco': float(i.preco_unitario)
            })
        
        # Se não tiver itens, cria um dummy baseado no preço geral (fallback)
        if not itens:
            itens.append({
                'id': f"default_{c.id}",
                'descricao': "Combustível Geral",
                'preco': float(c.preco_unitario)
            })

        contratos_data.append({
            'id': c.id,
            'numero': c.numero_contrato,
            'fornecedor': c.proposta_vencedora.fornecedor,
            'itens': itens
        })


    # Mapeamento Viatura -> Tipo de Combustível para Auto-Seleção
    viaturas_info = {}
    from .models import Viatura
    for v in Viatura.objects.filter(activa=True):
        viaturas_info[v.id] = v.tipo_combustivel  # Ex: 'gasolina', 'diesel'

    return render(request, 'gestaocombustivel/pedir_combustivel.html', {
        'form': form,
        'contratos_json': json.dumps(contratos_data),
        'contratos_ugea': contratos_ugea,
        'viaturas_info_json': json.dumps(viaturas_info)
    })


@login_required
def lista_pedidos_combustivel(request):
    """Lista todos os pedidos de combustível"""
    status_filter = request.GET.get('status', '')
    tipo_filter = request.GET.get('tipo', '')

    pedidos = PedidoCombustivel.objects.all().order_by('-data_pedido')

    if status_filter:
        pedidos = pedidos.filter(status=status_filter)

    if tipo_filter:
        pedidos = pedidos.filter(tipo_pedido=tipo_filter)

    return render(request, 'gestaocombustivel/pedidos_list.html', {
        'pedidos': pedidos,
        'status_filter': status_filter,
        'tipo_filter': tipo_filter,
    })


@login_required
@user_passes_test(is_admin_combustivel)
def aprovar_pedido_combustivel(request, pedido_id):
    """Aprovar ou rejeitar pedido de combustível"""
    pedido = get_object_or_404(PedidoCombustivel, id=pedido_id)

    if request.method == 'POST':
        acao = request.POST.get('acao')

        if acao == 'aprovar':
            pedido.status = 'aprovado'
            pedido.aprovado_por = request.user
            pedido.data_aprovacao = timezone.now()
            messages.success(request, 'Pedido de combustível aprovado!')
        elif acao == 'rejeitar':
            pedido.status = 'rejeitado'
            messages.success(request, 'Pedido de combustível rejeitado!')
        elif acao == 'abastecer':
            senha_confirmacao = request.POST.get('senha_confirmacao')
            # Se a senha estiver vazia ou incorreta
            if not senha_confirmacao or senha_confirmacao.strip() != pedido.numero_senha:
                messages.error(request, 'Senha de confirmação incorreta! O abastecimento não foi confirmado.')
                return redirect('gestaocombustivel:aprovar_pedido', pedido_id=pedido.id)
            
            pedido.status = 'abastecido'
            messages.success(request, 'Combustível abastecido e confirmado com sucesso!')

        pedido.save()
        return redirect('gestaocombustivel:lista_pedidos')

    return render(request, 'gestaocombustivel/aprovar_pedido.html', {
        'pedido': pedido
    })


@login_required
def solicitar_manutencao(request):
    """Solicitar manutenção de viatura"""
    if request.method == 'POST':
        form = ManutencaoViaturaForm(request.POST)
        if form.is_valid():
            manutencao = form.save(commit=False)
            
            # PROCESSAR CONTRATO UGEA
            contrato_ugea = form.cleaned_data.get('contrato_ugea')
            if contrato_ugea:
                # Usamos o nome do fornecedor da UGEA e salvamos no campo texto 'oficina'
                # Pois o modelo ainda espera um FornecedorManutencao legado (FK)
                nome_fornecedor = "Desconhecido"
                if contrato_ugea.proposta_vencedora and contrato_ugea.proposta_vencedora.fornecedor:
                    nome_fornecedor = contrato_ugea.proposta_vencedora.fornecedor.nome
                
                manutencao.oficina = nome_fornecedor
                manutencao.observacoes = f"Contrato UGEA: {contrato_ugea.numero_contrato}\n" + manutencao.observacoes
            
            manutencao.registado_por = request.user
            
            # Se houver um funcionário associado ao usuário, salva como solicitante
            if hasattr(request.user, 'funcionario'):
                manutencao.solicitante = request.user.funcionario
            
            # Garante que kilometragem_actual tenha um valor
            if not manutencao.kilometragem_actual and manutencao.viatura:
                manutencao.kilometragem_actual = manutencao.viatura.kilometragem_actual or 0

            manutencao.save()
            messages.success(request, 'Solicitação de manutenção submetida com sucesso!')
            return redirect('gestaocombustivel:lista_manutencoes')
        else:
            # Mostrar erros do formulário
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = ManutencaoViaturaForm()

    return render(request, 'gestaocombustivel/solicitar_manutencao.html', {
        'form': form
    })


@login_required
def lista_manutencoes(request):
    """Lista todas as manutenções"""
    status_filter = request.GET.get('status', '')

    manutencoes = ManutencaoViatura.objects.all().order_by('-data_solicitacao')

    if status_filter:
        manutencoes = manutencoes.filter(status=status_filter)

    return render(request, 'gestaocombustivel/manutencoes_list.html', {
        'manutencoes': manutencoes,
        'status_filter': status_filter,
    })


@login_required
def lista_rotas(request):
    """Lista todas as rotas de transporte"""
    rotas = RotaTransporte.objects.filter(activa=True)
    return render(request, 'gestaocombustivel/rotas_list.html', {
        'rotas': rotas
    })


@login_required
def registro_diario_rota(request):
    """Registo diário de rota"""
    if request.method == 'POST':
        form = RegistroDiarioRotaForm(request.POST)
        if form.is_valid():
            registro = form.save(commit=False)
            registro.confirmado_por_motorista = True
            registro.data_confirmacao = timezone.now()
            registro.save()

            messages.success(request, 'Registro diário de rota salvo!')
            return redirect('gestaocombustivel:dashboard_combustivel')
    else:
        form = RegistroDiarioRotaForm()

    return render(request, 'gestaocombustivel/registro_diario.html', {
        'form': form
    })


@login_required
@user_passes_test(is_admin_combustivel)
def relatorios_combustivel(request):
    """Relatórios de consumo e custos"""
    mes = request.GET.get('mes', date.today().month)
    ano = request.GET.get('ano', date.today().year)

    # Dados para relatórios
    pedidos_mes = PedidoCombustivel.objects.filter(
        data_pedido__year=ano,
        data_pedido__month=mes,
        status='abastecido'
    )

    total_consumo = pedidos_mes.aggregate(
        total_litros=Sum('quantidade_litros'),
        total_custo=Sum('custo_total')
    )

    # Consumo por viatura
    consumo_por_viatura = pedidos_mes.values(
        'viatura__matricula', 'viatura__marca', 'viatura__modelo'
    ).annotate(
        total_litros=Sum('quantidade_litros'),
        total_custo=Sum('custo_total')
    ).order_by('-total_custo')

    context = {
        'pedidos_mes': pedidos_mes,
        'total_consumo': total_consumo,
        'consumo_por_viatura': consumo_por_viatura,
        'mes': mes,
        'ano': ano,
    }

    return render(request, 'gestaocombustivel/relatorios.html', context)


# gestaocombustivel/views.py - ADIÇÕES

from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


# ========== VIATURAS (CRUD Completo) ==========

class ViaturaCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Viatura
    form_class = ViaturaForm
    template_name = 'gestaocombustivel/viatura_form.html'
    success_url = reverse_lazy('gestaocombustivel:lista_viaturas')

    def test_func(self):
        return is_admin_combustivel(self.request.user)

    def form_valid(self, form):
        form.instance.criado_por = self.request.user
        form.instance.actualizado_por = self.request.user

        # CORREÇÃO: Garantir que campos numéricos não sejam None
        instance = form.save(commit=False)

        if instance.kilometragem_actual is None:
            instance.kilometragem_actual = 0

        if instance.capacidade_tanque is None:
            instance.capacidade_tanque = 0

        if instance.proxima_manutencao_km is None:
            instance.proxima_manutencao_km = 10000

        if instance.custo_aquisicao is None:
            instance.custo_aquisicao = 0

        instance.save()
        form.save_m2m()  # Para campos ManyToMany

        messages.success(self.request, 'Viatura criada com sucesso!')
        return super().form_valid(form)

    def form_invalid(self, form):
        # Mostrar erros do formulário
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)


class ViaturaUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Viatura
    form_class = ViaturaForm
    template_name = 'gestaocombustivel/viatura_form.html'
    success_url = reverse_lazy('gestaocombustivel:lista_viaturas')

    def test_func(self):
        return is_admin_combustivel(self.request.user)

    def form_valid(self, form):
        form.instance.actualizado_por = self.request.user

        # CORREÇÃO: Garantir que campos numéricos não sejam None
        instance = form.save(commit=False)

        if instance.kilometragem_actual is None:
            instance.kilometragem_actual = 0

        if instance.capacidade_tanque is None:
            instance.capacidade_tanque = 0

        if instance.proxima_manutencao_km is None:
            instance.proxima_manutencao_km = 10000

        instance.save()
        form.save_m2m()  # Para campos ManyToMany

        messages.success(self.request, 'Viatura atualizada com sucesso!')
        return super().form_valid(form)

    def form_invalid(self, form):
        # Mostrar erros do formulário
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)


@login_required
@user_passes_test(is_admin_combustivel)
def desactivar_viatura(request, viatura_id):
    """Desactivar viatura (soft delete)"""
    viatura = get_object_or_404(Viatura, id=viatura_id)
    viatura.activa = False
    viatura.estado = 'inativo'
    viatura.save()
    messages.success(request, f'Viatura {viatura.matricula} desactivada!')
    return redirect('gestaocombustivel:lista_viaturas')


# ========== FORNECEDORES DE COMBUSTÍVEL ==========

@login_required
@user_passes_test(is_admin_combustivel)
@login_required
@user_passes_test(is_admin_combustivel)
def lista_fornecedores(request):
    """Lista todos os fornecedores com filtros"""
    # Filtros
    q = request.GET.get('q')
    nuit = request.GET.get('nuit')
    activo = request.GET.get('activo')
    
    fornecedores = FornecedorCombustivel.objects.all()
    
    if q:
        fornecedores = fornecedores.filter(
            Q(nome__icontains=q) | Q(contacto__icontains=q)
        )
    if nuit:
        fornecedores = fornecedores.filter(nuit__icontains=nuit)
    
    # Filtro de status simplificado para o template
    is_ativos = False
    is_inativos = False
    
    if activo == 'true':
        fornecedores = fornecedores.filter(activo=True)
        is_ativos = True
    elif activo == 'false':
        fornecedores = fornecedores.filter(activo=False)
        is_inativos = True
    else:
        # Padrão: mostra todos (ou ativos se preferir, mas vamos manter todos)
        pass

    # Estatísticas simples
    total_ativos = FornecedorCombustivel.objects.filter(activo=True).count()
    total_inativos = FornecedorCombustivel.objects.filter(activo=False).count()
    total_pedidos = PedidoCombustivel.objects.count()

    # Paginação
    paginator = Paginator(fornecedores, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'gestaocombustivel/fornecedores_list.html', {
        'fornecedores': page_obj,
        'fornecedores_ativos': total_ativos, # Para os cards de estatística
        'fornecedores_inativos': total_inativos,
        'total_pedidos': total_pedidos,
        'is_ativos': is_ativos,   # Variáveis booleanas simples para o template
        'is_inativos': is_inativos
    })


# gestaocombustivel/views.py

@login_required
@user_passes_test(is_admin_combustivel)
def criar_fornecedor(request):
    """Criar novo fornecedor"""
    # Opções de tipos de combustível do modelo Viatura
    tipos_combustivel = Viatura.TIPO_COMBUSTIVEL_CHOICES

    if request.method == 'POST':
        nome = request.POST.get('nome')
        nuit = request.POST.get('nuit')
        contacto = request.POST.get('contacto')

        if not nome or not nuit or not contacto:
            messages.error(request, 'Nome, NUIT e Contacto são obrigatórios.')
            return render(request, 'gestaocombustivel/fornecedor_form.html', {
                'tipos_combustivel': tipos_combustivel,
                'tipos_selecionados': request.POST.getlist('tipos_combustivel', [])
            })

        # Verificar se NUIT já existe
        if FornecedorCombustivel.objects.filter(nuit=nuit).exists():
            messages.error(request, 'Já existe um fornecedor com este NUIT.')
            return render(request, 'gestaocombustivel/fornecedor_form.html', {
                'tipos_combustivel': tipos_combustivel,
                'tipos_selecionados': request.POST.getlist('tipos_combustivel', [])
            })

        # Processar tipos de combustível selecionados
        tipos_selecionados = request.POST.getlist('tipos_combustivel', [])
        tipos_str = ', '.join([dict(tipos_combustivel).get(tipo, tipo) for tipo in tipos_selecionados])

        fornecedor = FornecedorCombustivel.objects.create(
            nome=nome,
            nuit=nuit,
            contacto=contacto,
            email=request.POST.get('email', ''),
            endereco=request.POST.get('endereco', ''),
            tipos_combustivel=tipos_str,
            observacoes=request.POST.get('observacoes', '')
        )

        # Verificar se deve desativar (para edição)
        if 'activo' not in request.POST and 'activo' in request.POST:
            fornecedor.activo = False
            fornecedor.save()

        messages.success(request, f'Fornecedor {fornecedor.nome} criado!')
        return redirect('gestaocombustivel:lista_fornecedores')

    # GET request - mostrar formulário vazio
    return render(request, 'gestaocombustivel/fornecedor_form.html', {
        'tipos_combustivel': tipos_combustivel,
        'tipos_selecionados': []  # Lista vazia para novo fornecedor
    })


@login_required
@user_passes_test(is_admin_combustivel)
@login_required
@user_passes_test(is_admin_combustivel)
def editar_fornecedor(request, fornecedor_id):
    """Editar fornecedor existente"""
    fornecedor = get_object_or_404(FornecedorCombustivel, id=fornecedor_id)
    tipos_combustivel = Viatura.TIPO_COMBUSTIVEL_CHOICES

    # Converter string de tipos para lista
    tipos_selecionados = []
    if fornecedor.tipos_combustivel:
        # Converte os nomes dos tipos para os valores
        tipos_dict = dict(tipos_combustivel)
        for key, value in tipos_dict.items():
            if value in fornecedor.tipos_combustivel:
                tipos_selecionados.append(key)

    if request.method == 'POST':
        form = FornecedorCombustivelForm(request.POST, instance=fornecedor)
        if form.is_valid():
            fornecedor = form.save(commit=False)
            
            # Processar tipos selecionados (manual)
            novos_tipos_selecionados = request.POST.getlist('tipos_combustivel', [])
            tipos_str = ', '.join([dict(tipos_combustivel).get(tipo, tipo) for tipo in novos_tipos_selecionados])
            fornecedor.tipos_combustivel = tipos_str
            
            fornecedor.save()
            messages.success(request, 'Fornecedor atualizado!')
            return redirect('gestaocombustivel:lista_fornecedores')
        else:
            messages.error(request, 'Por favor, corrija os erros no formulário.')
    else:
        form = FornecedorCombustivelForm(instance=fornecedor)

    # Preparar lista de tipos para o template (para exibir checkboxes corretamente)
    tipos_combustivel_display = []
    # Se for POST com erro, usar os dados do POST para manter checkboxes marcados
    current_selected = request.POST.getlist('tipos_combustivel') if request.method == 'POST' else tipos_selecionados
    
    for key, value in tipos_combustivel:
        tipos_combustivel_display.append({
            'codigo': key,
            'nome': value,
            'checked': key in current_selected
        })

    return render(request, 'gestaocombustivel/fornecedor_form.html', {
        'form': form,  # Passando o form para o template renderizar os campos
        'object': fornecedor,
        'tipos_combustivel_display': tipos_combustivel_display,
        'tipos_combustivel': tipos_combustivel,
        'tipos_selecionados': tipos_selecionados
    })






@login_required
@user_passes_test(is_admin_combustivel)
def desactivar_fornecedor(request, fornecedor_id):
    """Desactivar fornecedor"""
    fornecedor = get_object_or_404(FornecedorCombustivel, id=fornecedor_id)
    fornecedor.activo = False
    fornecedor.save()
    messages.success(request, f'Fornecedor {fornecedor.nome} desactivado!')
    return redirect('gestaocombustivel:lista_fornecedores')



# ========== CONTRATOS DE COMBUSTÍVEL ==========

@login_required
@user_passes_test(is_admin_combustivel)
def lista_contratos(request):
    """Lista todos os contratos"""
    ativo_filter = request.GET.get('ativo', 'todos')
    
    contratos = ContratoCombustivel.objects.all().order_by('-data_inicio')
    
    # Flags booleanas para o template (evita erros de formatação no HTML)
    is_todos = False
    is_ativos = False
    is_inativos = False

    if ativo_filter == 'sim':
        contratos = contratos.filter(activo=True)
        is_ativos = True
    elif ativo_filter == 'nao':
        contratos = contratos.filter(activo=False)
        is_inativos = True
    else:
        is_todos = True
        
    return render(request, 'gestaocombustivel/contratos_list.html', {
        'contratos': contratos,
        'ativo_filter': ativo_filter,
        'is_todos': is_todos,
        'is_ativos': is_ativos,
        'is_inativos': is_inativos
    })

@login_required
@user_passes_test(is_admin_combustivel)
def criar_contrato(request):
    """Criar novo contrato"""
    fornecedores = FornecedorCombustivel.objects.filter(activo=True)
    tipos_combustivel = Viatura.TIPO_COMBUSTIVEL_CHOICES

    if request.method == 'POST':
        try:
            fornecedor_id = request.POST.get('fornecedor')
            numero_contrato = request.POST.get('numero_contrato')
            # tipo_combustivel não é mais relevante, fixar valor ou pegar se vier
            tipo_combustivel = request.POST.get('tipo_combustivel', 'gasolina')
            
            preco_gasolina = request.POST.get('preco_unitario')
            preco_diesel = request.POST.get('preco_diesel')
            litros = request.POST.get('litros_contratados')
            valor_total = request.POST.get('valor_total_contrato')
            data_inicio = request.POST.get('data_inicio')
            data_fim = request.POST.get('data_fim')

            if not all([fornecedor_id, numero_contrato, preco_gasolina, litros, data_inicio, data_fim]):
                messages.error(request, 'Todos os campos obrigatórios devem ser preenchidos.')
                raise ValueError("Campos em falta")

            # Garantir valor total
            if not valor_total and preco_gasolina and litros:
                valor_total = float(preco_gasolina) * float(litros)

            # Validações
            if ContratoCombustivel.objects.filter(numero_contrato=numero_contrato).exists():
                messages.error(request, 'Já existe um contrato com este número.')
                raise ValueError("Duplicado")

            # Converter datas de string para objeto date
            if isinstance(data_inicio, str):
                data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            if isinstance(data_fim, str):
                data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()

            contrato = ContratoCombustivel.objects.create(
                fornecedor_id=fornecedor_id,
                numero_contrato=numero_contrato,
                tipo_combustivel=tipo_combustivel, # Campo legado
                preco_unitario=float(preco_gasolina),
                preco_diesel=float(preco_diesel) if preco_diesel else 0,
                litros_contratados=float(litros),
                valor_total_contrato=float(valor_total),
                data_inicio=data_inicio,
                data_fim=data_fim,
                observacoes=request.POST.get('observacoes', '')
            )
            
            messages.success(request, f'Contrato {contrato.numero_contrato} criado com sucesso!')
            return redirect('gestaocombustivel:lista_contratos')
            
        except ValueError as e:
            # Mantém os dados no formulário em caso de erro (simplificado)
            print(f"Erro ao criar contrato: {e}")
            pass
            
    return render(request, 'gestaocombustivel/contrato_form.html', {
        'fornecedores': fornecedores,
        'tipos_combustivel': tipos_combustivel
    })


@login_required
@user_passes_test(is_admin_combustivel)
def editar_contrato(request, contrato_id):
    """Editar contrato"""
    contrato = get_object_or_404(ContratoCombustivel, id=contrato_id)
    fornecedores = FornecedorCombustivel.objects.filter(activo=True)
    tipos_combustivel = Viatura.TIPO_COMBUSTIVEL_CHOICES

    if request.method == 'POST':
        try:
            contrato.numero_contrato = request.POST.get('numero_contrato')
            # tipo_combustivel ignorado na edição
            
            contrato.preco_unitario = float(request.POST.get('preco_unitario'))
            
            preco_diesel = request.POST.get('preco_diesel')
            if preco_diesel:
                contrato.preco_diesel = float(preco_diesel)
                
            contrato.litros_contratados = float(request.POST.get('litros_contratados'))
            
            valor_total = request.POST.get('valor_total_contrato')
            if valor_total:
                contrato.valor_total_contrato = float(valor_total)
            
            data_inicio = request.POST.get('data_inicio')
            data_fim = request.POST.get('data_fim')

            # Converter strings para data
            if isinstance(data_inicio, str):
                contrato.data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            if isinstance(data_fim, str):
                contrato.data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()

            contrato.observacoes = request.POST.get('observacoes', '')
            contrato.activo = 'activo' in request.POST
            
            contrato.save()
            messages.success(request, 'Contrato atualizado!')
            return redirect('gestaocombustivel:lista_contratos')
        except ValueError:
            messages.error(request, 'Erro nos valores numéricos.')

    return render(request, 'gestaocombustivel/contrato_form.html', {
        'object': contrato,
        'fornecedores': fornecedores,
        'tipos_combustivel': tipos_combustivel
    })

@login_required
def detalhe_contrato(request, contrato_id):
    """Detalhes do contrato"""
    contrato = get_object_or_404(ContratoCombustivel, id=contrato_id)
    # Pedidos associados a este contrato
    pedidos = contrato.abastecimentos.all().order_by('-data_abastecimento')
    # Pagamentos realizados
    pagamentos = contrato.pagamentos.all().order_by('-data_pagamento')
    
    return render(request, 'gestaocombustivel/contrato_detail.html', {
        'contrato': contrato,
        'pedidos': pedidos,
        'pagamentos': pagamentos
    })


# ========== SEGUROS (CRUD Completo) ==========

class SeguroCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = SeguroViatura
    form_class = SeguroViaturaForm
    template_name = 'gestaocombustivel/seguro_form.html'
    success_url = reverse_lazy('gestaocombustivel:lista_seguros')

    def test_func(self):
        return is_admin_combustivel(self.request.user)

    def form_valid(self, form):
        # CORREÇÃO: Garantir que campos numéricos não sejam None
        instance = form.save(commit=False)

        if instance.premio_seguro is None:
            instance.premio_seguro = 0

        if instance.franquia is None:
            instance.franquia = 0

        if instance.valor_segurado is None:
            instance.valor_segurado = 0

        instance.registado_por = self.request.user
        instance.save()

        messages.success(self.request, 'Seguro criado com sucesso!')
        return super().form_valid(form)

    def form_invalid(self, form):
        # Mostrar erros do formulário
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)


@login_required
def lista_seguros(request):
    """Lista todos os seguros"""
    viatura_filter = request.GET.get('viatura', '')

    seguros = SeguroViatura.objects.all().order_by('-data_inicio')

    if viatura_filter:
        seguros = seguros.filter(viatura_id=viatura_filter)

    viaturas = Viatura.objects.filter(activa=True)

    return render(request, 'gestaocombustivel/seguros_list.html', {
        'seguros': seguros,
        'viaturas': viaturas,
        'viatura_filter': viatura_filter
    })


@login_required
@user_passes_test(is_admin_combustivel)
def renovar_seguro(request, seguro_id):
    """Renovar seguro automaticamente"""
    seguro = get_object_or_404(SeguroViatura, id=seguro_id)

    # Calcula novas datas (1 ano)
    nova_data_inicio = seguro.data_fim + timedelta(days=1)
    nova_data_fim = nova_data_inicio + timedelta(days=365)

    # CORREÇÃO: Garantir que campos numéricos não sejam None
    premio_seguro = seguro.premio_seguro if seguro.premio_seguro is not None else 0
    franquia = seguro.franquia if seguro.franquia is not None else 0

    novo_seguro = SeguroViatura.objects.create(
        viatura=seguro.viatura,
        tipo_seguro=seguro.tipo_seguro,
        companhia_seguros=seguro.companhia_seguros,
        numero_apolice=f"REN-{seguro.numero_apolice}-{date.today().year}",
        data_inicio=nova_data_inicio,
        data_fim=nova_data_fim,
        premio_seguro=premio_seguro,
        franquia=franquia,
        valor_segurado=seguro.valor_segurado,
        coberturas=seguro.coberturas,
        restricoes=seguro.restricoes,
        condicoes_especiais=seguro.condicoes_especiais,
        contacto_seguros=seguro.contacto_seguros,
        renovacao_automatica=seguro.renovacao_automatica,
        registado_por=request.user
    )

    # Desactiva seguro antigo
    seguro.activo = False
    seguro.save()

    messages.success(request, f'Seguro renovado! Nova apólice: {novo_seguro.numero_apolice}')
    return redirect('gestaocombustivel:lista_seguros')


# ========== MANUTENÇÃO (Workflow Completo) ==========

@login_required
@user_passes_test(is_admin_combustivel)
def concluir_manutencao(request, manutencao_id):
    """Concluir manutenção e actualizar viatura"""
    manutencao = get_object_or_404(ManutencaoViatura, id=manutencao_id)

    if request.method == 'POST':
        custo_real = request.POST.get('custo_real')
        relatorio = request.POST.get('relatorio_manutencao', '')

        manutencao.status = 'concluida'
        manutencao.data_conclusao = date.today()
        manutencao.relatorio_manutencao = relatorio
        manutencao.concluido_por = request.user

        # CORREÇÃO: Converter custo_real para Decimal
        try:
            if custo_real:
                manutencao.custo_real = float(custo_real)
        except (ValueError, TypeError):
            manutencao.custo_real = 0

        manutencao.save()

        # Actualizar viatura
        viatura = manutencao.viatura
        viatura.data_ultima_manutencao = date.today()

        # Se foi manutenção preventiva, recalcular próxima manutenção
        if manutencao.tipo_manutencao == 'preventiva' and manutencao.kilometragem_actual:
            viatura.proxima_manutencao_km = float(manutencao.kilometragem_actual) + 10000

        # Mudar estado se estava em manutenção
        if viatura.estado == 'manutencao':
            viatura.estado = 'bom'

        viatura.save()

        messages.success(request, 'Manutenção concluída!')
        return redirect('gestaocombustivel:lista_manutencoes')

    return render(request, 'gestaocombustivel/concluir_manutencao.html', {
        'manutencao': manutencao
    })


# ========== ROTAS (Gestão Completa) ==========

@login_required
@user_passes_test(is_admin_combustivel)
def criar_rota(request):
    """Criar nova rota"""
    if request.method == 'POST':
        form = RotaTransporteForm(request.POST)
        if form.is_valid():
            rota = form.save(commit=False)
            rota.criado_por = request.user

            # CORREÇÃO: Garantir que campos numéricos não sejam None
            if rota.distancia_total is None:
                rota.distancia_total = 0

            if rota.combustivel_estimado is None:
                rota.combustivel_estimado = 0

            rota.save()

            messages.success(request, f'Rota {rota.nome_rota} criada!')
            return redirect('gestaocombustivel:detalhe_rota', rota_id=rota.id)
        else:
            # Mostrar erros do formulário
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = RotaTransporteForm()

    return render(request, 'gestaocombustivel/rota_form.html', {'form': form})


@login_required
def detalhe_rota(request, rota_id):
    """Detalhes da rota com pontos e funcionários"""
    rota = get_object_or_404(RotaTransporte, id=rota_id)
    pontos = rota.pontos.all().order_by('ordem')
    funcionarios = FuncionarioRota.objects.filter(rota=rota)

    return render(request, 'gestaocombustivel/rota_detail.html', {
        'rota': rota,
        'pontos': pontos,
        'funcionarios': funcionarios
    })

@login_required
@user_passes_test(is_admin_combustivel)
def editar_rota(request, rota_id):
    """Editar rota existente"""
    rota = get_object_or_404(RotaTransporte, id=rota_id)
    
    if request.method == 'POST':
        form = RotaTransporteForm(request.POST, instance=rota)
        if form.is_valid():
            form.save()
            messages.success(request, f'Rota {rota.nome_rota} actualizada!')
            return redirect('gestaocombustivel:detalhe_rota', rota_id=rota.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = RotaTransporteForm(instance=rota)

    return render(request, 'gestaocombustivel/rota_form.html', {
        'form': form,
        'rota': rota,
        'object': rota,
        'edit_mode': True
    })

@login_required
def imprimir_rota(request, rota_id):
    """Gerar visualização de impressão da rota"""
    rota = get_object_or_404(RotaTransporte, id=rota_id)
    pontos = rota.pontos.all().order_by('ordem')
    passageiros = FuncionarioRota.objects.filter(rota=rota)
    from django.utils import timezone
    
    # Organizar passageiros por ponto para facilitar no template
    passageiros_por_ponto = {}
    for p in pontos:
        passageiros_por_ponto[p.id] = passageiros.filter(ponto_embarque=p)
        
    return render(request, 'gestaocombustivel/rota_print.html', {
        'rota': rota,
        'pontos': pontos,
        'passageiros_por_ponto': passageiros_por_ponto,
        'now': timezone.now()
    })

@login_required
def imprimir_lista_rotas(request):
    """Gerar visualização de impressão de todas as rotas activas"""
    rotas = RotaTransporte.objects.filter(activa=True)
    from django.utils import timezone
    
    dados_rotas = []
    for rota in rotas:
        pontos = rota.pontos.all().order_by('ordem')
        passageiros = FuncionarioRota.objects.filter(rota=rota)
        passageiros_por_ponto = {p.id: passageiros.filter(ponto_embarque=p) for p in pontos}
        
        dados_rotas.append({
            'rota': rota,
            'pontos': pontos,
            'passageiros_por_ponto': passageiros_por_ponto
        })
        
    return render(request, 'gestaocombustivel/rotas_print_list.html', {
        'dados_rotas': dados_rotas,
        'now': timezone.now()
    })


@login_required
@user_passes_test(is_admin_combustivel)
def adicionar_ponto_rota(request, rota_id):
    """Adicionar ponto a uma rota"""
    rota = get_object_or_404(RotaTransporte, id=rota_id)

    if request.method == 'POST':
        form = PontoRotaForm(request.POST)
        if form.is_valid():
            ponto = form.save(commit=False)
            ponto.rota = rota
            ponto.save()
            messages.success(request, f'Ponto {ponto.nome_ponto} adicionado!')
            return redirect('gestaocombustivel:detalhe_rota', rota_id=rota.id)
        else:
            # Mostrar erros do formulário
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = PontoRotaForm(initial={'rota': rota})

    return render(request, 'gestaocombustivel/ponto_form.html', {
        'form': form,
        'rota': rota
    })


@login_required
@user_passes_test(is_admin_combustivel)
def adicionar_funcionario_rota(request, rota_id):
    """Adicionar funcionário a uma rota"""
    rota = get_object_or_404(RotaTransporte, id=rota_id)

    if request.method == 'POST':
        funcionario_id = request.POST.get('funcionario')
        ponto_id = request.POST.get('ponto_embarque')

        if not funcionario_id or not ponto_id:
            messages.error(request, 'Funcionário e ponto de embarque são obrigatórios.')
            return redirect('gestaocombustivel:adicionar_funcionario_rota', rota_id=rota.id)

        funcionario = get_object_or_404(Funcionario, id=funcionario_id)
        ponto = get_object_or_404(PontoRota, id=ponto_id)

        # Verificar se já está na rota
        if FuncionarioRota.objects.filter(rota=rota, funcionario=funcionario).exists():
            messages.warning(request, f'Funcionário {funcionario.nome_completo} já está nesta rota.')
        else:
            FuncionarioRota.objects.create(
                rota=rota,
                funcionario=funcionario,
                ponto_embarque=ponto
            )
            messages.success(request, f'Funcionário {funcionario.nome_completo} adicionado à rota!')

        return redirect('gestaocombustivel:detalhe_rota', rota_id=rota.id)

    funcionarios = Funcionario.objects.filter(ativo=True).exclude(
        id__in=FuncionarioRota.objects.filter(rota=rota).values('funcionario_id')
    )
    pontos = rota.pontos.all()
    ponto_id = request.GET.get('ponto_id')

    return render(request, 'gestaocombustivel/add_funcionario_rota.html', {
        'rota': rota,
        'funcionarios': funcionarios,
        'pontos': pontos,
        'ponto_id': ponto_id
    })


# ========== VALIDAÇÕES ADICIONAIS ==========

def validar_datas_manutencao(self):
    """Validação adicional para manutenção"""
    from django.core.exceptions import ValidationError
    from datetime import date

    if self.data_agendada and self.data_agendada < date.today():
        raise ValidationError("Data agendada não pode ser no passado")

    if self.data_conclusao and self.data_conclusao < self.data_agendada:
        raise ValidationError("Data de conclusão não pode ser anterior à data agendada")


def validar_kilometragem_viatura(self):
    """Valida que kilometragem não diminui"""
    from django.core.exceptions import ValidationError

    if (self.kilometragem_actual and self.viatura.kilometragem_actual and
            float(self.kilometragem_actual) < float(self.viatura.kilometragem_actual)):
        raise ValidationError("Kilometragem atual não pode ser menor que a anterior")


# Adicionar validações aos models
def add_validation_to_manutencao():
    """Adiciona validação ao modelo ManutencaoViatura"""
    from django.core.exceptions import ValidationError
    from datetime import date

    def clean_manutencao(self):
        errors = {}

        if self.data_agendada and self.data_agendada < date.today():
            errors['data_agendada'] = "Data agendada não pode ser no passado"

        if self.data_conclusao and self.data_agendada:
            if self.data_conclusao < self.data_agendada:
                errors['data_conclusao'] = "Data de conclusão não pode ser anterior à data agendada"

        if errors:
            raise ValidationError(errors)

    return clean_manutencao


# Adicionar ao model ManutencaoViatura se necessário
# ManutencaoViatura.add_to_class('clean', add_validation_to_manutencao())


# ========== EXPORTAÇÃO DE RELATÓRIOS ==========

@login_required
@user_passes_test(is_admin_combustivel)
def exportar_relatorio_csv(request):
    """Exportar relatório para CSV"""
    mes = request.GET.get('mes', date.today().month)
    ano = request.GET.get('ano', date.today().year)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="relatorio_combustivel_{mes}_{ano}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Data', 'Viatura', 'Tipo', 'Litros', 'Preço/Litro', 'Custo Total', 'Fornecedor'])

    pedidos = PedidoCombustivel.objects.filter(
        data_pedido__year=ano,
        data_pedido__month=mes,
        status='abastecido'
    )

    for pedido in pedidos:
        writer.writerow([
            pedido.data_abastecimento,
            pedido.viatura.matricula,
            pedido.get_tipo_pedido_display(),
            pedido.quantidade_litros or 0,
            pedido.preco_por_litro or 0,
            pedido.custo_total or 0,
            pedido.fornecedor.nome if pedido.fornecedor else 'N/A'
        ])

    return response


# ========== FUNÇÕES ADICIONAIS ==========

@login_required
@user_passes_test(is_admin_combustivel)
def activar_viatura(request, viatura_id):
    """Activar viatura previamente desactivada"""
    viatura = get_object_or_404(Viatura, id=viatura_id)
    viatura.activa = True
    viatura.estado = 'bom'
    viatura.save()
    messages.success(request, f'Viatura {viatura.matricula} activada!')
    return redirect('gestaocombustivel:lista_viaturas')


@login_required
@user_passes_test(is_admin_combustivel)
def activar_fornecedor(request, fornecedor_id):
    """Activar fornecedor previamente desactivado"""
    fornecedor = get_object_or_404(FornecedorCombustivel, id=fornecedor_id)
    fornecedor.activo = True
    fornecedor.save()
    messages.success(request, f'Fornecedor {fornecedor.nome} activado!')
    return redirect('gestaocombustivel:lista_fornecedores')


@login_required
def historico_viatura(request, viatura_id):
    """Histórico completo de uma viatura"""
    viatura = get_object_or_404(Viatura, id=viatura_id)

    # Obter todos os dados históricos
    pedidos = PedidoCombustivel.objects.filter(viatura=viatura).order_by('-data_pedido')
    manutencoes = ManutencaoViatura.objects.filter(viatura=viatura).order_by('-data_solicitacao')
    seguros = SeguroViatura.objects.filter(viatura=viatura).order_by('-data_inicio')

    return render(request, 'gestaocombustivel/historico_viatura.html', {
        'viatura': viatura,
        'pedidos': pedidos,
        'manutencoes': manutencoes,
        'seguros': seguros,
    })


@login_required
@user_passes_test(is_admin_combustivel)
@login_required
@user_passes_test(is_admin_combustivel)
def registrar_pagamento_contrato(request, contrato_id):
    contrato = get_object_or_404(ContratoCombustivel, id=contrato_id)
    if request.method == 'POST':
        valor = request.POST.get('valor')
        referencia = request.POST.get('referencia')
        data_pagamento = request.POST.get('data_pagamento')
        observacoes = request.POST.get('observacoes')
        
        PagamentoContrato.objects.create(
            contrato=contrato,
            valor=valor,
            referencia_documento=referencia,
            data_pagamento=data_pagamento,
            observacoes=observacoes,
            registado_por=request.user
        )
        messages.success(request, 'Pagamento registrado com sucesso!')
        return redirect('gestaocombustivel:lista_contratos') # Ou detalhe do contrato se existir
    
    return render(request, 'gestaocombustivel/pagamento_form.html', {'contrato': contrato})


import qrcode
from io import BytesIO
import base64

@login_required
def imprimir_requisicao(request, pedido_id):
    pedido = get_object_or_404(PedidoCombustivel, id=pedido_id)
    
    # Dados para o QR Code (JSON ou Texto Formatado)
    qr_data = f"PEDIDO:{pedido.id}|SENHA:{pedido.numero_senha}|VIATURA:{pedido.viatura.matricula}|LITROS:{pedido.quantidade_litros}"
    
    # Gerar QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    # Converter para Base64
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_image_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return render(request, 'gestaocombustivel/requisicao_print.html', {
        'pedido': pedido,
        'qr_code': qr_image_base64
    })

@login_required
@user_passes_test(is_admin_combustivel)
def configuracao_sistema(request):
    """Configurações do sistema"""
    if request.method == 'POST':
        # Placeholder para futura implementação de salvamento
        messages.success(request, 'Configurações actualizadas!')
        return redirect('gestaocombustivel:configuracao_sistema')

    return render(request, 'gestaocombustivel/configuracao.html')

@login_required
@user_passes_test(is_admin_combustivel)
def eliminar_pagamento(request, pagamento_id):
    """Elimina um registro de pagamento"""
    pagamento = get_object_or_404(PagamentoContrato, id=pagamento_id)
    contrato_id = pagamento.contrato.id
    
    if request.method == 'POST':
        pagamento.delete()
        messages.success(request, 'Pagamento eliminado com sucesso.')
    
    return redirect('gestaocombustivel:detalhe_contrato', contrato_id=contrato_id)


# --- GESTÃO DE OFICINAS E CONTRATOS DE MANUTENÇÃO ---

@login_required
@user_passes_test(is_admin_combustivel)
def lista_oficinas(request):
    oficinas = FornecedorManutencao.objects.filter(activo=True)
    paginator = Paginator(oficinas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'gestaocombustivel/oficinas_list.html', {'page_obj': page_obj})

@login_required
@user_passes_test(is_admin_combustivel)
def nova_oficina(request):
    if request.method == 'POST':
        # Processamento manual simplificado
        nome = request.POST.get('nome')
        nuit = request.POST.get('nuit')
        contacto = request.POST.get('contacto')
        endereco = request.POST.get('endereco')
        
        try:
            FornecedorManutencao.objects.create(
                nome=nome, 
                nuit=nuit, 
                contacto=contacto,
                endereco=endereco,
                activo=True
            )
            messages.success(request, 'Oficina cadastrada com sucesso!')
            return redirect('gestaocombustivel:lista_oficinas')
        except Exception as e:
            messages.error(request, f'Erro ao cadastrar: {e}')
            
    return render(request, 'gestaocombustivel/oficina_form.html')

@login_required
@user_passes_test(is_admin_combustivel)
def lista_contratos_manutencao(request):
    contratos = ContratoManutencao.objects.filter(activo=True)
    return render(request, 'gestaocombustivel/contratos_manutencao_list.html', {'contratos': contratos})

@login_required
@user_passes_test(is_admin_combustivel)
def novo_contrato_manutencao(request):
    from .models import TIPO_MANUTENCAO_CHOICES
    oficinas = FornecedorManutencao.objects.filter(activo=True)
    
    if request.method == 'POST':
        fornecedor_id = request.POST.get('fornecedor')
        numero = request.POST.get('numero_contrato')
        descricao = request.POST.get('descricao')
        valor = request.POST.get('valor_total')
        inicio = request.POST.get('data_inicio')
        fim = request.POST.get('data_fim')
        
        try:
            fornecedor = FornecedorManutencao.objects.get(id=fornecedor_id)
            contrato = ContratoManutencao.objects.create(
                fornecedor=fornecedor,
                numero_contrato=numero,
                descricao=descricao,
                valor_total=valor,
                data_inicio=inicio,
                data_fim=fim,
                activo=True
            )
            
            # Salvar preços por tipo de serviço
            for service_code, _ in TIPO_MANUTENCAO_CHOICES:
                price_val = request.POST.get(f'price_{service_code}')
                if price_val and price_val.strip():
                    PrecoServicoContrato.objects.create(
                        contrato=contrato,
                        tipo_servico=service_code,
                        preco=price_val
                    )

            messages.success(request, 'Contrato registado com sucesso!')
            return redirect('gestaocombustivel:lista_contratos_manutencao')
        except Exception as e:
            messages.error(request, f'Erro ao criar contrato: {e}')

    return render(request, 'gestaocombustivel/contrato_manutencao_form.html', {
        'oficinas': oficinas,
        'servicos': TIPO_MANUTENCAO_CHOICES
    })

@login_required
@user_passes_test(is_admin_combustivel)
def detalhe_contrato_manutencao(request, contrato_id):
    contrato = get_object_or_404(ContratoManutencao, id=contrato_id)
    return render(request, 'gestaocombustivel/contrato_manutencao_detail.html', {'contrato': contrato})

@login_required
@user_passes_test(is_admin_combustivel)
def editar_contrato_manutencao(request, contrato_id):
    contrato = get_object_or_404(ContratoManutencao, id=contrato_id)
    from .models import TIPO_MANUTENCAO_CHOICES
    oficinas = FornecedorManutencao.objects.filter(activo=True)
    
    if request.method == 'POST':
        contrato.numero_contrato = request.POST.get('numero_contrato')
        contrato.descricao = request.POST.get('descricao')
        contrato.valor_total = request.POST.get('valor_total')
        contrato.data_inicio = request.POST.get('data_inicio')
        contrato.data_fim = request.POST.get('data_fim')
        contrato.save()
        
        # Atualizar preços
        PrecoServicoContrato.objects.filter(contrato=contrato).delete()
        for service_code, _ in TIPO_MANUTENCAO_CHOICES:
            price_val = request.POST.get(f'price_{service_code}')
            if price_val and price_val.strip():
                PrecoServicoContrato.objects.create(
                    contrato=contrato,
                    tipo_servico=service_code,
                    preco=price_val
                )
        
        messages.success(request, 'Contrato atualizado com sucesso!')
        return redirect('gestaocombustivel:lista_contratos_manutencao')
        
    # Buscar preços existentes para preencher o form
    precos_existentes = {p.tipo_servico: p.preco for p in PrecoServicoContrato.objects.filter(contrato=contrato)}
    
    return render(request, 'gestaocombustivel/contrato_manutencao_form.html', {
        'contrato': contrato,
        'oficinas': oficinas,
        'servicos': TIPO_MANUTENCAO_CHOICES,
        'precos_existentes': precos_existentes
    })

@login_required
def imprimir_ordem_manutencao(request, manutencao_id):
    manutencao = get_object_or_404(ManutencaoViatura, id=manutencao_id)
    return render(request, 'gestaocombustivel/ordem_manutencao_print.html', {'manutencao': manutencao})
