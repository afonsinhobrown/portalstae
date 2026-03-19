from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, Count
from datetime import date, timedelta
import json
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from io import BytesIO
import zipfile
from datetime import datetime

from reportlab.lib.styles import ParagraphStyle

# AGORA TODAS AS IMPORTACOES DEVEM FUNCIONAR
from .models import (
    Solicitante, PedidoCredencial, CredencialEmitida,
    Evento, TipoCredencial, CredencialFuncionario,
    AuditoriaCredencial, ConfiguracaoEmergencia, ModeloCredencial
)
from .forms import (
    SolicitanteForm, TipoCredencialForm, PedidoCredencialForm, PedidoRemotoForm,
    AnalisePedidoForm, EmitirCredencialForm, CredencialFuncionarioForm,
    VerificacaoOfflineForm, EmergenciaBloqueioForm,
    BeneficiarioFormSet, EventoForm
)
from .utils_pdf import gerar_pdf_cartao_credencial, gerar_pdf_credencial, gerar_imagem_cartao


def is_admin_credenciais(user):
    return user.is_authenticated and user.is_staff


def garantir_dados_base():
    """Garante que existam tipos de credencial e modelos base no sistema"""
    # 1. Tipos de Credencial
    if not TipoCredencial.objects.exists():
        tipos = [
            {'nome': 'Acesso Geral', 'cor': '#6c757d', 'ordem': 10},
            {'nome': 'Imprensa', 'cor': '#17a2b8', 'ordem': 1},
            {'nome': 'Observador Nacional', 'cor': '#28a745', 'ordem': 2},
            {'nome': 'Observador Internacional', 'cor': '#fd7e14', 'ordem': 3},
            {'nome': 'Delegado de Candidatura', 'cor': '#007bff', 'ordem': 4},
            {'nome': 'VIP / Convidado', 'cor': '#6f42c1', 'ordem': 5},
            {'nome': 'Staff / Técnico', 'cor': '#343a40', 'ordem': 6},
        ]
        for t in tipos:
            TipoCredencial.objects.get_or_create(
                nome=t['nome'], 
                defaults={'cor': t['cor'], 'ordem': t['ordem'], 'ativo': True}
            )

    # 2. Modelo de Credencial Padrão
    if not ModeloCredencial.objects.exists():
        ModeloCredencial.objects.create(
            nome="Modelo STAE Padrão",
            descricao="Design oficial básico para todas as credenciais",
            cor_fundo="#ffffff",
            cor_texto="#000000",
            ativo=True
        )


@login_required
def dashboard_credenciais(request):
    """Dashboard principal de Credenciais"""
    garantir_dados_base()

    # Estatísticas
    total_solicitantes = Solicitante.objects.filter(ativo=True).count()  # ← CORRIGIDO
    pedidos_pendentes = PedidoCredencial.objects.filter(status='pendente').count()
    credenciais_activas = CredencialEmitida.objects.filter(status='emitida').count()
    eventos_activos = Evento.objects.filter(ativo=True, data_fim__gte=date.today()).count()
    credenciais_funcionarios = CredencialFuncionario.objects.filter(ativa=True).count()

    # Estatísticas de auditoria recente
    auditoria_recente = AuditoriaCredencial.objects.select_related('usuario', 'credencial')[:10]

    # Bloqueios de emergência ativos
    bloqueios_ativos = ConfiguracaoEmergencia.objects.filter(ativo=True)

    # Pedidos recentes
    pedidos_recentes = PedidoCredencial.objects.all().order_by('-data_pedido')[:10]

    # Estatísticas por tipo
    pedidos_por_tipo = PedidoCredencial.objects.values('tipo_credencial__nome').annotate(
        total=Count('id')
    ).order_by('-total')

    context = {
        'total_solicitantes': total_solicitantes,
        'pedidos_pendentes': pedidos_pendentes,
        'credenciais_activas': credenciais_activas,
        'eventos_activos': eventos_activos,
        'credenciais_funcionarios': credenciais_funcionarios,
        'pedidos_recentes': pedidos_recentes,
        'pedidos_por_tipo': pedidos_por_tipo,
        'auditoria_recente': auditoria_recente,
        'bloqueios_ativos': bloqueios_ativos,
    }
    return render(request, 'credenciais/dashboard.html', context)


@login_required
def lista_solicitantes(request):
    """Lista todos os solicitantes"""
    query = request.GET.get('q', '')
    tipo_filter = request.GET.get('tipo', '')

    solicitantes = Solicitante.objects.filter(ativo=True)

    if query:
        solicitantes = solicitantes.filter(
            Q(nome_completo__icontains=query) |
            Q(email__icontains=query) |
            Q(numero_bi__icontains=query) |
            Q(nif__icontains=query)
        )

    if tipo_filter:
        solicitantes = solicitantes.filter(tipo=tipo_filter)

    return render(request, 'credenciais/solicitantes_list.html', {
        'solicitantes': solicitantes,
        'query': query,
        'tipo_filter': tipo_filter,
    })


@login_required
def adicionar_solicitante(request):
    """Adicionar novo solicitante"""
    if request.method == 'POST':
        form = SolicitanteForm(request.POST, request.FILES)
        if form.is_valid():
            solicitante = form.save()

            AuditoriaCredencial.registrar(
                acao='criacao',
                usuario=request.user,
                solicitante=solicitante,
                detalhes={'via': 'formulario'},
                request=request
            )

            messages.success(request, 'Solicitante adicionado com sucesso!')
            return redirect('credenciais:lista_solicitantes')
    else:
        form = SolicitanteForm()

    return render(request, 'credenciais/solicitante_form.html', {
        'form': form,
        'titulo': 'Adicionar Solicitante'
    })


@login_required
def pedir_credencial(request):
    """Solicitar credencial (interno) - Suporta múltiplos beneficiários"""
    garantir_dados_base()
    
    if request.method == 'POST':
        form = PedidoCredencialForm(request.POST, request.FILES)
        formset = BeneficiarioFormSet(request.POST, request.FILES)
        
        if form.is_valid():
            pedido = form.save(commit=False)
            pedido.criado_por = request.user
            pedido.status = 'pendente'
            pedido.save()
            
            # Se for organização, processar beneficiários
            if pedido.solicitante.tipo != 'singular':
                formset = BeneficiarioFormSet(request.POST, request.FILES, instance=pedido)
                if formset.is_valid():
                    formset.save()
            
            AuditoriaCredencial.registrar(
                acao='criacao_pedido',
                usuario=request.user,
                pedido=pedido,
                detalhes={'via': 'formulario_interno', 'numero': pedido.numero_pedido},
                request=request
            )

            messages.success(request, f'Pedido {pedido.numero_pedido} submetido com sucesso!')
            return redirect('credenciais:lista_pedidos')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = PedidoCredencialForm(initial={'criado_por': request.user})
        formset = BeneficiarioFormSet()

    return render(request, 'credenciais/pedir_credencial.html', {
        'form': form,
        'formset': formset
    })



def pedir_credencial_remoto(request):
    """Solicitar credencial (remoto - público)"""
    garantir_dados_base()
    if request.method == 'POST':
        form = PedidoRemotoForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Criar ou encontrar solicitante
                    solicitante, created = Solicitante.objects.get_or_create(
                        email=form.cleaned_data['email'],
                        defaults={
                            'nome_completo': form.cleaned_data['nome_completo'],
                            'telefone': form.cleaned_data['telefone'],
                            'nacionalidade': form.cleaned_data['nacionalidade'],
                            'numero_bi': form.cleaned_data['numero_bi'],
                            'tipo': 'singular',
                            'numero_identificacao': f"REM-{int(timezone.now().timestamp())}"
                        }
                    )

                    # Criar pedido
                    pedido = form.save(commit=False)
                    pedido.solicitante = solicitante
                    pedido.status = 'pendente'
                    pedido.pedido_remoto = True
                    pedido.save()

                    AuditoriaCredencial.registrar(
                        acao='criacao',
                        solicitante=solicitante,
                        pedido=pedido,
                        detalhes={'via': 'remoto'},
                        request=request
                    )

                    messages.success(request, 'Pedido remoto submetido com sucesso! Aguarde contacto.')
                    return redirect('credenciais:pedido_sucesso')

            except Exception as e:
                messages.error(request, f'Erro ao processar pedido: {str(e)}')
    else:
        form = PedidoRemotoForm()

    return render(request, 'credenciais/pedido_remoto.html', {
        'form': form
    })


def pedido_sucesso(request):
    """Página de sucesso para pedidos remotos"""
    return render(request, 'credenciais/pedido_sucesso.html')


@login_required
def lista_pedidos(request):
    """Lista inteligente de pedidos com filtros e ações contextuais"""

    # Filtros
    status_filter = request.GET.get('status', '')
    tipo_filter = request.GET.get('tipo', '')
    search_query = request.GET.get('q', '')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')

    # Query base
    pedidos = PedidoCredencial.objects.all().select_related(
        'solicitante', 'tipo_credencial', 'evento'
    ).prefetch_related('credencial').order_by('-data_pedido')

    # Aplicar filtros
    if status_filter:
        pedidos = pedidos.filter(status=status_filter)

    if tipo_filter:
        pedidos = pedidos.filter(tipo_credencial_id=tipo_filter)

    if search_query:
        pedidos = pedidos.filter(
            Q(numero_pedido__icontains=search_query) |
            Q(solicitante__nome_completo__icontains=search_query) |
            Q(solicitante__email__icontains=search_query) |
            Q(solicitante__numero_bi__icontains=search_query) |
            Q(motivo__icontains=search_query)
        )

    if data_inicio:
        pedidos = pedidos.filter(data_pedido__gte=data_inicio)

    if data_fim:
        pedidos = pedidos.filter(data_pedido__lte=data_fim)

    # Estatísticas
    total_pedidos = pedidos.count()
    pedidos_aprovados = pedidos.filter(status='aprovado').count()
    pedidos_emitidos = pedidos.filter(status='emitido').count()
    pedidos_pendentes = pedidos.filter(status__in=['pendente', 'em_analise']).count()

    # Tipos de credencial para filtro
    tipos_credencial = TipoCredencial.objects.filter(ativo=True)

    # Status disponíveis
    status_choices = PedidoCredencial.STATUS_CHOICES

    # Paginação
    paginator = Paginator(pedidos, 25)  # 25 por página
    page = request.GET.get('page')

    try:
        pedidos_paginados = paginator.page(page)
    except PageNotAnInteger:
        pedidos_paginados = paginator.page(1)
    except EmptyPage:
        pedidos_paginados = paginator.page(paginator.num_pages)

    context = {
        'pedidos': pedidos_paginados,
        'tipos_credencial': tipos_credencial,
        'status_choices': status_choices,
        'status_filter': status_filter,
        'tipo_filter': tipo_filter,
        'search_query': search_query,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'total_pedidos': total_pedidos,
        'pedidos_aprovados': pedidos_aprovados,
        'pedidos_emitidos': pedidos_emitidos,
        'pedidos_pendentes': pedidos_pendentes,
    }

    return render(request, 'credenciais/pedidos_list.html', context)


@login_required
@user_passes_test(is_admin_credenciais)
def analisar_pedido(request, pedido_id):
    """Analisar e aprovar/rejeitar pedido"""
    pedido = get_object_or_404(PedidoCredencial, id=pedido_id)

    # Verificar se já foi analisado
    if pedido.status not in ['pendente', 'em_analise']:
        messages.warning(request, f'Este pedido já foi {pedido.get_status_display().lower()}.')
        return redirect('credenciais:lista_pedidos')

    if request.method == 'POST':
        acao = request.POST.get('acao')  # 'aprovar' ou 'reprovar'
        observacoes = request.POST.get('observacoes_analise', '')

        try:
            with transaction.atomic():
                if acao == 'aprovar':
                    pedido.status = 'aprovado'
                    mensagem = f'Pedido #{pedido.numero_pedido} APROVADO!'
                    classe = 'success'
                elif acao == 'reprovar':
                    pedido.status = 'reprovado'
                    mensagem = f'Pedido #{pedido.numero_pedido} REPROVADO.'
                    classe = 'warning'
                else:
                    messages.error(request, 'Ação inválida.')
                    return redirect('credenciais:analisar_pedido', pedido_id=pedido_id)

                pedido.observacoes_analise = observacoes
                pedido.analisado_por = request.user
                pedido.data_analise = timezone.now()
                pedido.save()

                # Registrar auditoria
                AuditoriaCredencial.registrar(
                    acao='analise' if acao == 'aprovar' else 'rejeicao',
                    usuario=request.user,
                    pedido=pedido,
                    detalhes={
                        'acao': acao,
                        'observacoes': observacoes,
                        'pedido_numero': pedido.numero_pedido
                    },
                    request=request
                )

                messages.add_message(request, messages.SUCCESS if acao == 'aprovar' else messages.WARNING, mensagem)
                return redirect('credenciais:lista_pedidos')

        except Exception as e:
            messages.error(request, f'Erro ao processar análise: {str(e)}')

    # GET request - mostrar formulário
    form = AnalisePedidoForm(instance=pedido) if hasattr(pedido, 'AnalisePedidoForm') else None

    return render(request, 'credenciais/analisar_pedido.html', {
        'pedido': pedido,
        'form': form
    })


@login_required
@user_passes_test(is_admin_credenciais)
def emitir_credencial(request, pedido_id):
    """Emitir credencial para pedido - versão FLEXÍVEL"""

    # 1. PRIMEIRO: Encontre o pedido SEM filtrar por status
    try:
        pedido = PedidoCredencial.objects.get(id=pedido_id)
    except PedidoCredencial.DoesNotExist:
        messages.error(request, f'❌ Pedido #{pedido_id} não encontrado.')
        return redirect('credenciais:lista_pedidos')

    # 2. VERIFIQUE o status atual e aja conforme
    if pedido.status == 'emitido':
        # Se já tem credencial, redireciona para reimpressão
        if hasattr(pedido, 'credencial') and pedido.credencial:
            messages.info(request,
                          f'✅ Credencial {pedido.credencial.numero_credencial} já foi emitida. '
                          f'Redirecionando para reimpressão...'
                          )
            return redirect('credenciais:reimprimir_credencial', credencial_id=pedido.credencial.id)
        else:
            # Status está como 'emitido' mas não tem credencial → corrigir
            pedido.status = 'aprovado'
            pedido.save()
            messages.warning(request, '⚠️ Status corrigido: de "emitido" para "aprovado".')

    elif pedido.status == 'reprovado':
        messages.error(request, '❌ Este pedido foi REPROVADO. Não pode ser emitido.')
        return redirect('credenciais:lista_pedidos')

    elif pedido.status == 'cancelado':
        messages.warning(request, '⚠️ Este pedido foi CANCELADO.')
        return redirect('credenciais:lista_pedidos')

    elif pedido.status in ['pendente', 'em_analise']:
        messages.warning(request,
                         f'⚠️ Este pedido está {pedido.get_status_display().upper()}. '
                         f'<a href="/credenciais/analisar-pedido/{pedido.id}/" class="alert-link">Clique aqui para aprová-lo</a>.'
                         )
        return redirect('credenciais:analisar_pedido', pedido_id=pedido.id)

    elif pedido.status != 'aprovado':
        # Qualquer outro status → forçar para 'aprovado'
        messages.warning(request, f'⚠️ Status "{pedido.get_status_display()}" alterado para "APROVADO".')
        pedido.status = 'aprovado'
        pedido.save()

    # 3. SE CHEGOU AQUI → PEDIDO ESTÁ PRONTO PARA EMISSÃO
    # Verificar se ModeloCredencial existe
    try:
        from .models import ModeloCredencial
        modelos_existem = True
        modelos_disponiveis = ModeloCredencial.objects.filter(ativo=True)
    except:
        modelos_existem = False
        modelos_disponiveis = []

    if request.method == 'POST':
        # Obter dados do formulário
        modelo_id = request.POST.get('modelo', '')
        acao_pdf = request.POST.get('acao_pdf', 'salvar')
        observacoes = request.POST.get('observacoes', '')

        try:
            with transaction.atomic():
                # Verificar se já não foi criada durante o processo
                if hasattr(pedido, 'credencial') and pedido.credencial:
                    messages.warning(request, '⚠️ Credencial já foi emitida durante este processo.')
                    return redirect('credenciais:detalhe_credencial', credencial_id=pedido.credencial.id)

                # Encontrar próximo número de credencial
                ultima_credencial = CredencialEmitida.objects.order_by('-id').first()

                if ultima_credencial:
                    # Tenta extrair número do formato STAE000001
                    import re
                    numero_match = re.search(r'STAE(\d+)', ultima_credencial.numero_credencial)

                    if numero_match:
                        ultimo_num = int(numero_match.group(1))
                        proximo_num = ultimo_num + 1
                    else:
                        # Fallback: contar total + 1
                        proximo_num = CredencialEmitida.objects.count() + 1
                else:
                    # Primeira credencial
                    proximo_num = 1

                numero_credencial = f"STAE{proximo_num:06d}"

                # Determinar data de validade
                from datetime import date, timedelta
                hoje = date.today()

                if pedido.evento and pedido.evento.data_fim:
                    data_validade = pedido.evento.data_fim
                elif pedido.data_fim:
                    data_validade = pedido.data_fim
                else:
                    data_validade = hoje + timedelta(days=365)  # 1 ano por padrão

                # OBTER MODELO (obrigatório)
                modelo = None
                if modelo_id and modelos_existem:
                    try:
                        modelo = ModeloCredencial.objects.get(id=modelo_id, ativo=True)
                    except ModeloCredencial.DoesNotExist:
                        pass
                
                # Se não foi selecionado ou não existe, usar o primeiro disponível ou criar padrão
                if not modelo:
                    modelo = ModeloCredencial.objects.filter(ativo=True).first()
                    if not modelo:
                        # Criar modelo padrão se não existir
                        modelo = ModeloCredencial.objects.create(
                            nome="Modelo STAE Padrão",
                            descricao="Design oficial básico para todas as credenciais",
                            cor_fundo="#ffffff",
                            cor_texto="#000000",
                            ativo=True
                        )

                # CRIAR A CREDENCIAL com modelo obrigatório
                credencial = CredencialEmitida.objects.create(
                    pedido=pedido,
                    modelo=modelo,
                    numero_credencial=numero_credencial,
                    data_validade=data_validade,
                    emitida_por=request.user
                )

                # Gerar códigos de segurança
                credencial.gerar_qr_code()
                credencial.gerar_codigo_offline()

                # Adicionar observações se houver
                if observacoes:
                    credencial.observacoes = observacoes

                credencial.save()

                # Atualizar status do pedido
                pedido.status = 'emitido'
                pedido.save()

                # Registrar auditoria
                AuditoriaCredencial.registrar(
                    acao='emissao',
                    usuario=request.user,
                    credencial=credencial,
                    pedido=pedido,
                    detalhes={
                        'numero_credencial': credencial.numero_credencial,
                        'data_validade': credencial.data_validade.strftime('%d/%m/%Y'),
                        'observacoes': observacoes
                    },
                    request=request
                )

                # Mensagem de sucesso
                messages.success(request,
                                 f'✅ Credencial <strong>{credencial.numero_credencial}</strong> emitida com sucesso!<br>'
                                 f'<small>Validade: {credencial.data_validade.strftime("%d/%m/%Y")}</small>'
                                 )

                # Sempre redirecionar para a página de reimprimir que tem o layout correto do cartão
                return redirect('credenciais:reimprimir_credencial', credencial_id=credencial.id)

        except Exception as e:
            messages.error(request, f'❌ Erro ao emitir credencial: {str(e)}')
            # Log do erro para debugging
            import traceback
            print(f"ERRO NA EMISSÃO: {traceback.format_exc()}")

    # 4. PREPARAR CONTEXTO PARA O TEMPLATE
    context = {
        'pedido': pedido,
        'modelos_existem': modelos_existem,
        'modelos_disponiveis': modelos_disponiveis,
        'titulo': f'Emitir Credencial - {pedido.numero_pedido}'
    }

    return render(request, 'credenciais/emitir_credencial.html', context)




@login_required
def detalhe_credencial(request, credencial_id):
    """Detalhes de uma credencial emitida"""
    credencial = get_object_or_404(CredencialEmitida, id=credencial_id)

    # Histórico de auditoria desta credencial
    historico = AuditoriaCredencial.objects.filter(
        credencial=credencial
    ).order_by('-data_hora')[:10]

    return render(request, 'credenciais/detalhe_credencial.html', {
        'credencial': credencial,
        'historico': historico
    })


@login_required
def lista_credenciais_funcionarios(request):
    """Lista credenciais de funcionários"""
    credenciais = CredencialFuncionario.objects.filter(ativa=True).select_related(
        'funcionario', 'tipo_credencial', 'modelo'
    )
    return render(request, 'credenciais/credenciais_funcionarios.html', {
        'credenciais': credenciais
    })


@login_required
@user_passes_test(is_admin_credenciais)
def emitir_credencial_funcionario(request):
    """Emitir credencial para funcionário"""
    if request.method == 'POST':
        form = CredencialFuncionarioForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    credencial = form.save(commit=False)

                    # Gerar número de credencial
                    ultima = CredencialFuncionario.objects.order_by('-id').first()
                    ultimo_num = int(ultima.numero_credencial[4:]) if ultima else 0
                    credencial.numero_credencial = f"FUNC{(ultimo_num + 1):06d}"

                    credencial.save()

                    # Gerar QR Code e código offline
                    credencial.gerar_qr_code()
                    credencial.gerar_codigo_offline()
                    credencial.save()

                    AuditoriaCredencial.registrar(
                        acao='emissao',
                        usuario=request.user,
                        detalhes={
                            'tipo': 'funcionario',
                            'numero_credencial': credencial.numero_credencial,
                            'funcionario': str(credencial.funcionario)
                        },
                        request=request
                    )

                messages.success(request, f'Credencial {credencial.numero_credencial} emitida para funcionário!')
                return redirect('credenciais:lista_credenciais_funcionarios')

            except Exception as e:
                messages.error(request, f'Erro ao emitir credencial: {str(e)}')
    else:
        form = CredencialFuncionarioForm()

    return render(request, 'credenciais/emitir_credencial_funcionario.html', {
        'form': form
    })


@login_required
def relatorios_credenciais(request):
    """Relatórios e estatísticas de credenciais"""
    # Estatísticas básicas
    total_solicitantes = Solicitante.objects.filter(ativo=True).count()
    total_pedidos = PedidoCredencial.objects.count()
    total_credenciais = CredencialEmitida.objects.count()
    total_funcionarios = CredencialFuncionario.objects.filter(ativa=True).count()

    # Estatísticas por género
    stats_genero = Solicitante.objects.filter(ativo=True).values('genero').annotate(
        total=Count('id')
    )

    # Estatísticas por nacionalidade
    stats_nacionalidade = Solicitante.objects.filter(ativo=True).values('nacionalidade').annotate(
        total=Count('id')
    ).order_by('-total')[:10]

    # Eventos mais populares
    eventos_populares = Evento.objects.annotate(
        total_pedidos=Count('pedidocredencial')
    ).order_by('-total_pedidos')[:10]

    # Credenciais por status
    stats_status = CredencialEmitida.objects.values('status').annotate(
        total=Count('id')
    )

    # Estatísticas por tipo de organização
    stats_tipo_solicitante = Solicitante.objects.filter(ativo=True).values('tipo').annotate(
        total=Count('id')
    ).order_by('-total')

    context = {
        'total_solicitantes': total_solicitantes,
        'total_pedidos': total_pedidos,
        'total_credenciais': total_credenciais,
        'total_funcionarios': total_funcionarios,
        'stats_genero': stats_genero,
        'stats_nacionalidade': stats_nacionalidade,
        'eventos_populares': eventos_populares,
        'stats_status': stats_status,
    }

    return render(request, 'credenciais/relatorios.html', context)


@login_required
def verificar_credencial(request):
    """Verificar validade de uma credencial via QR Code"""
    codigo = request.GET.get('codigo', '')

    if codigo:
        try:
            credencial = CredencialEmitida.objects.get(codigo_verificacao=codigo)

            # Registrar verificação
            AuditoriaCredencial.registrar(
                acao='verificacao',
                usuario=request.user if request.user.is_authenticated else None,
                credencial=credencial,
                detalhes={'via': 'qr_code'},
                request=request
            )

            return JsonResponse({
                'valida': credencial.esta_valida(),
                'numero': credencial.numero_credencial,
                'solicitante': str(credencial.pedido.solicitante),
                'validade': credencial.data_validade.isoformat(),
                'status': credencial.status,
                'bloqueio_emergencia': credencial.bloqueio_emergencia
            })
        except CredencialEmitida.DoesNotExist:
            return JsonResponse({'valida': False, 'erro': 'Credencial não encontrada'})

    return render(request, 'credenciais/verificar_credencial.html')


@login_required
def verificar_credencial_offline(request):
    """Verificação offline de credencial (para agentes no campo)"""
    if request.method == 'POST':
        form = VerificacaoOfflineForm(request.POST)
        if form.is_valid():
            codigo_offline = form.cleaned_data['codigo_offline'].strip().upper()
            latitude = form.cleaned_data.get('latitude')
            longitude = form.cleaned_data.get('longitude')

            if not codigo_offline:
                messages.error(request, 'Digite um código de verificação')
                return render(request, 'credenciais/verificar_offline.html', {'form': form})

            try:
                # Extrair número da credencial do código
                if '-' in codigo_offline:
                    numero_credencial = codigo_offline.split('-')[0]
                else:
                    numero_credencial = codigo_offline[:6]

                # Buscar credencial
                credencial = CredencialEmitida.objects.get(
                    numero_credencial__startswith=numero_credencial
                )

                # Verificar
                valida = credencial.verificar_offline(codigo_offline)

                if valida:
                    # Registrar uso
                    credencial.registrar_uso(latitude, longitude)

                    # Auditoria
                    AuditoriaCredencial.registrar(
                        acao='uso_offline',
                        usuario=request.user if request.user.is_authenticated else None,
                        credencial=credencial,
                        detalhes={
                            'codigo_offline': codigo_offline,
                            'latitude': latitude,
                            'longitude': longitude,
                            'valida': True
                        },
                        request=request
                    )

                    messages.success(request,
                                     f'Credencial VÁLIDA: {credencial.numero_credencial} - {credencial.pedido.solicitante.nome_completo}'
                                     )
                else:
                    messages.error(request, 'Código inválido ou credencial expirada!')

                return render(request, 'credenciais/verificar_offline.html', {
                    'form': form,
                    'resultado': {
                        'valida': valida,
                        'credencial': credencial if valida else None
                    }
                })

            except CredencialEmitida.DoesNotExist:
                messages.error(request, 'Credencial não encontrada!')
            except Exception as e:
                messages.error(request, f'Erro na verificação: {str(e)}')
    else:
        form = VerificacaoOfflineForm()

    return render(request, 'credenciais/verificar_offline.html', {'form': form})


@login_required
@user_passes_test(is_admin_credenciais)
def emergencia_bloqueio(request):
    """Painel de controle para bloqueios de emergência"""
    configuracoes = ConfiguracaoEmergencia.objects.all().order_by('-id')

    if request.method == 'POST':
        form = EmergenciaBloqueioForm(request.POST)
        if form.is_valid():
            try:
                config = form.save(commit=False)
                config.save()

                # Ativar imediatamente
                afetadas = config.ativar(request.user)

                messages.success(request,
                                 f'Bloqueio de emergência ativado! {afetadas} credenciais afetadas.'
                                 )

                return redirect('credenciais:emergencia_bloqueio')

            except Exception as e:
                messages.error(request, f'Erro ao ativar bloqueio: {str(e)}')
    else:
        form = EmergenciaBloqueioForm()

    eventos = Evento.objects.filter(ativo=True, data_fim__gte=date.today())
    tipos_credencial = TipoCredencial.objects.filter(ativo=True)

    return render(request, 'credenciais/emergencia_bloqueio.html', {
        'configuracoes': configuracoes,
        'form': form,
        'eventos': eventos,
        'tipos_credencial': tipos_credencial,
    })


def auditoria_view(request):
    """Página de auditoria de credenciais"""
    # Implementação básica
    return render(request, 'credenciais/auditoria.html')

@login_required
@user_passes_test(is_admin_credenciais)
def desativar_bloqueio_emergencia(request, config_id):
    """Desativar bloqueio de emergência"""
    config = get_object_or_404(ConfiguracaoEmergencia, id=config_id)

    if config.ativo:
        config.desativar(request.user)
        messages.success(request, f'Bloqueio "{config.nome}" desativado!')
    else:
        messages.warning(request, 'Este bloqueio já está desativado.')

    return redirect('credenciais:emergencia_bloqueio')


@login_required
def auditoria_credenciais(request):
    """Visualizar auditoria do sistema"""
    acao_filter = request.GET.get('acao', '')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    usuario_filter = request.GET.get('usuario', '')

    auditoria = AuditoriaCredencial.objects.all().select_related(
        'usuario', 'credencial', 'solicitante'
    )

    if acao_filter:
        auditoria = auditoria.filter(acao=acao_filter)

    if usuario_filter:
        auditoria = auditoria.filter(usuario__username__icontains=usuario_filter)

    if data_inicio:
        auditoria = auditoria.filter(data_hora__gte=data_inicio)

    if data_fim:
        auditoria = auditoria.filter(data_hora__lte=data_fim)

    paginator = Paginator(auditoria, 50)
    page = request.GET.get('page')

    try:
        registros = paginator.page(page)
    except PageNotAnInteger:
        registros = paginator.page(1)
    except EmptyPage:
        registros = paginator.page(paginator.num_pages)

    return render(request, 'credenciais/auditoria.html', {
        'registros': registros,
        'acoes': AuditoriaCredencial.TIPO_ACAO,
        'filtros': {
            'acao': acao_filter,
            'usuario': usuario_filter,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
        }
    })


# API para verificação offline (para apps móveis)
@csrf_exempt
def api_verificar_offline(request):
    """API para verificação offline (sem autenticação necessária)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            codigo_offline = data.get('codigo', '').strip().upper()

            if not codigo_offline:
                return JsonResponse({'error': 'Código obrigatório'}, status=400)

            # Buscar credencial
            if '-' in codigo_offline:
                numero_credencial = codigo_offline.split('-')[0]
            else:
                numero_credencial = codigo_offline[:6]

            credencial = CredencialEmitida.objects.get(
                numero_credencial__startswith=numero_credencial
            )

            # Verificar
            valida = credencial.verificar_offline(codigo_offline)

            if valida:
                # Registrar uso com geolocalização se disponível
                lat = data.get('latitude')
                long = data.get('longitude')
                credencial.registrar_uso(lat, long)

                # Auditoria
                AuditoriaCredencial.registrar(
                    acao='uso_offline',
                    credencial=credencial,
                    detalhes={
                        'codigo': codigo_offline,
                        'latitude': lat,
                        'longitude': long,
                        'via_api': True
                    },
                    request=request
                )

            return JsonResponse({
                'valida': valida,
                'credencial': {
                    'numero': credencial.numero_credencial,
                    'solicitante': str(credencial.pedido.solicitante),
                    'validade': credencial.data_validade.isoformat(),
                    'status': credencial.status,
                    'bloqueio_emergencia': credencial.bloqueio_emergencia,
                    'codigo_offline': credencial.codigo_offline
                } if valida else None
            })

        except CredencialEmitida.DoesNotExist:
            return JsonResponse({'valida': False, 'error': 'Credencial não encontrada'}, status=404)
        except Exception as e:
            return JsonResponse({'valida': False, 'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método não permitido'}, status=405)


@login_required
@user_passes_test(is_admin_credenciais)
def emitir_em_lote(request):
    """Emitir múltiplas credenciais de uma vez"""
    if request.method == 'POST':
        pedidos_ids = request.POST.getlist('pedidos')
        modelo_id = request.POST.get('modelo')
        acao_pdf = request.POST.get('acao_pdf', 'salvar')

        if not pedidos_ids or not modelo_id:
            messages.error(request, 'Selecione pedidos e um modelo')
            return redirect('credenciais:lista_pedidos')

        try:
            modelo = ModeloCredencial.objects.get(id=modelo_id, ativo=True)
            pedidos = PedidoCredencial.objects.filter(
                id__in=pedidos_ids,
                status='aprovado'
            ).select_related('solicitante', 'tipo_credencial')

            credenciais_emitidas = []

            with transaction.atomic():
                # Encontrar último número
                ultima = CredencialEmitida.objects.order_by('-id').first()
                ultimo_num = int(ultima.numero_credencial[4:]) if ultima else 0

                for i, pedido in enumerate(pedidos):
                    # Verificar se já não tem credencial
                    if hasattr(pedido, 'credencialemitida'):
                        continue

                    credencial = CredencialEmitida.objects.create(
                        pedido=pedido,
                        modelo=modelo,
                        numero_credencial=f"STAE{(ultimo_num + i + 1):06d}",
                    )

                    # Gerar códigos
                    credencial.gerar_qr_code()
                    credencial.gerar_codigo_offline()
                    credencial.save()

                    pedido.status = 'emitido'
                    pedido.save()

                    credenciais_emitidas.append(credencial)

                    AuditoriaCredencial.registrar(
                        acao='emissao',
                        usuario=request.user,
                        credencial=credencial,
                        pedido=pedido,
                        detalhes={'em_lote': True},
                        request=request
                    )

            if acao_pdf == 'download_zip' and credenciais_emitidas:
                # Criar string com IDs para o download ZIP
                ids_str = ','.join([str(c.id) for c in credenciais_emitidas])
                messages.success(
                    request,
                    f'{len(credenciais_emitidas)} credenciais emitidas em lote! '
                    f'<a href="/credenciais/download-zip/?ids={ids_str}">Baixar PDFs em ZIP</a>'
                )
            else:
                messages.success(
                    request,
                    f'{len(credenciais_emitidas)} credenciais emitidas em lote!'
                )

            return redirect('credenciais:lista_pedidos')

        except Exception as e:
            messages.error(request, f'Erro ao emitir em lote: {str(e)}')

    return redirect('credenciais:lista_pedidos')


@login_required
def visualizar_pdf_credencial(request, credencial_id):
    """Visualizar PDF da credencial no navegador"""
    credencial = get_object_or_404(CredencialEmitida, id=credencial_id)

    # Verificar permissões
    if not request.user.is_staff and credencial.pedido.criado_por != request.user:
        messages.error(request, 'Não tem permissão para visualizar esta credencial.')
        return redirect('credenciais:dashboard_credenciais')

    # Gerar PDF
    pdf_content = gerar_pdf_credencial(credencial)

    # Configurar resposta
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="credencial_{credencial.numero_credencial}.pdf"'
    return response


@login_required
def download_pdf_credencial(request, credencial_id):
    """Download do PDF da credencial"""
    credencial = get_object_or_404(CredencialEmitida, id=credencial_id)

    # Verificar permissões
    if not request.user.is_staff and credencial.pedido.criado_por != request.user:
        messages.error(request, 'Não tem permissão para baixar esta credencial.')
        return redirect('credenciais:dashboard_credenciais')

    # Gerar PDF
    pdf_content = gerar_pdf_credencial(credencial)

    # Configurar resposta para download
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="credencial_{credencial.numero_credencial}.pdf"'
    return response


@login_required
def pdf_credencial_funcionario(request, credencial_id):
    """Gerar PDF para credencial de funcionário"""
    credencial = get_object_or_404(CredencialFuncionario, id=credencial_id)

    # Verificar permissões
    if not request.user.is_staff:
        messages.error(request, 'Não tem permissão para visualizar esta credencial.')
        return redirect('credenciais:dashboard_credenciais')

    # Gerar PDF
    pdf_content = gerar_pdf_credencial_funcionario(credencial)

    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="credencial_func_{credencial.numero_credencial}.pdf"'
    return response


@login_required
def download_credenciais_zip(request):
    """Download de múltiplas credenciais em arquivo ZIP"""
    credencial_ids = request.GET.get('ids', '').split(',')

    if not credencial_ids or credencial_ids[0] == '':
        messages.error(request, 'Nenhuma credencial selecionada.')
        return redirect('credenciais:lista_pedidos')

    try:
        # Criar arquivo ZIP em memória
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for credencial_id in credencial_ids:
                if credencial_id:
                    credencial = CredencialEmitida.objects.get(id=int(credencial_id))
                    pdf_content = gerar_pdf_credencial(credencial)

                    # Adicionar ao ZIP
                    filename = f"credencial_{credencial.numero_credencial}.pdf"
                    zip_file.writestr(filename, pdf_content)

        # Configurar resposta
        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="credenciais_stae.zip"'

        # Registrar auditoria
        AuditoriaCredencial.registrar(
            acao='download_zip',
            usuario=request.user,
            detalhes={
                'num_credenciais': len([c for c in credencial_ids if c]),
                'credenciais': credencial_ids
            },
            request=request
        )

        return response

    except Exception as e:
        messages.error(request, f'Erro ao criar arquivo ZIP: {str(e)}')
        return redirect('credenciais:lista_pedidos')


@login_required
def imprimir_credencial(request, credencial_id):
    """Página de impressão otimizada para credencial"""
    credencial = get_object_or_404(CredencialEmitida, id=credencial_id)

    # Verificar permissões
    if not request.user.is_staff and credencial.pedido.criado_por != request.user:
        messages.error(request, 'Não tem permissão para imprimir esta credencial.')
        return redirect('credenciais:dashboard_credenciais')

    return render(request, 'credenciais/imprimir_credencial.html', {
        'credencial': credencial
    })


# ===== FUNÇÕES AUXILIARES PARA GERAÇÃO DE PDF =====

def gerar_pdf_credencial(credencial):
    """Gerar PDF para credencial emitida"""
    from reportlab.lib.pagesizes import A4, mm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.graphics.barcode import qr
    from reportlab.graphics.shapes import Drawing
    import os
    from django.conf import settings

    # Criar buffer
    buffer = BytesIO()

    # Configurar tamanho do cartão (85x54mm padrão ISO ID-1)
    width = 85 * mm
    height = 54 * mm

    # Criar documento
    doc = SimpleDocTemplate(
        buffer,
        pagesize=(width, height),
        rightMargin=5 * mm,
        leftMargin=5 * mm,
        topMargin=5 * mm,
        bottomMargin=5 * mm
    )

    # Estilos
    styles = getSampleStyleSheet()

    # Estilo personalizado para título
    estilo_titulo = ParagraphStyle(
        'TituloCredencial',
        parent=styles['Heading2'],
        fontSize=12,
        alignment=1,  # Center
        textColor=colors.HexColor('#1a237e'),
        spaceAfter=10,
        fontName='Helvetica-Bold'
    )

    # Estilo para dados
    estilo_dados = ParagraphStyle(
        'DadosCredencial',
        parent=styles['Normal'],
        fontSize=8,
        alignment=0,  # Left
        spaceAfter=4,
        fontName='Helvetica'
    )

    # Estilo para labels
    estilo_label = ParagraphStyle(
        'LabelCredencial',
        parent=styles['Normal'],
        fontSize=7,
        alignment=0,
        spaceAfter=2,
        textColor=colors.gray,
        fontName='Helvetica-Oblique'
    )

    # Elementos do documento
    elements = []

    # Logo
    try:
        logo_path = os.path.join(settings.STATIC_ROOT, 'img', 'stae_logo.png')
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=35 * mm, height=12 * mm)
            logo.hAlign = 'CENTER'
            elements.append(logo)
            elements.append(Spacer(1, 3 * mm))
    except:
        pass

    # Título
    elements.append(Paragraph("CREDENCIAL OFICIAL", estilo_titulo))
    elements.append(Spacer(1, 6 * mm))

    # Tabela com dados
    dados = [
        [Paragraph("<b>Nº:</b>", estilo_label),
         Paragraph(credencial.numero_credencial, estilo_dados)],
        [Paragraph("<b>Nome:</b>", estilo_label),
         Paragraph(credencial.pedido.solicitante.nome_completo, estilo_dados)],
        [Paragraph("<b>Tipo:</b>", estilo_label),
         Paragraph(str(credencial.pedido.tipo_credencial), estilo_dados)],
    ]

    if credencial.pedido.evento:
        dados.append([
            Paragraph("<b>Evento:</b>", estilo_label),
            Paragraph(str(credencial.pedido.evento.nome), estilo_dados)
        ])

    if credencial.pedido.solicitante.numero_bi:
        dados.append([
            Paragraph("<b>BI:</b>", estilo_label),
            Paragraph(credencial.pedido.solicitante.numero_bi, estilo_dados)
        ])

    dados.append([
        Paragraph("<b>Validade:</b>", estilo_label),
        Paragraph(credencial.data_validade.strftime("%d/%m/%Y"), estilo_dados)
    ])

    dados.append([
        Paragraph("<b>Status:</b>", estilo_label),
        Paragraph(credencial.get_status_display(), estilo_dados)
    ])

    # Criar tabela
    table = Table(dados, colWidths=[20 * mm, 55 * mm])
    table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 8 * mm))

    # QR Code
    qr_code = qr.QrCodeWidget(credencial.codigo_verificacao)
    bounds = qr_code.getBounds()
    width_qr = bounds[2] - bounds[0]
    height_qr = bounds[3] - bounds[1]
    drawing = Drawing(20 * mm, 20 * mm, transform=[20 * mm / width_qr, 0, 0, 20 * mm / height_qr, 0, 0])
    drawing.add(qr_code)
    drawing.hAlign = 'CENTER'
    elements.append(drawing)

    # Rodapé
    elements.append(Spacer(1, 3 * mm))
    elements.append(Paragraph(
        f"Verificar: {credencial.codigo_offline}",
        ParagraphStyle(
            'Rodape',
            parent=styles['Normal'],
            fontSize=6,
            alignment=1,
            textColor=colors.gray
        )
    ))

    elements.append(Paragraph(
        f"Emitido: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        ParagraphStyle(
            'DataEmissao',
            parent=styles['Normal'],
            fontSize=5,
            alignment=1,
            textColor=colors.gray
        )
    ))

    # Gerar PDF
    doc.build(elements)

    # Obter conteúdo
    pdf = buffer.getvalue()
    buffer.close()

    return pdf


def gerar_pdf_credencial_funcionario(credencial):
    """Gerar PDF para credencial de funcionário"""
    from reportlab.lib.pagesizes import A4, mm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.graphics.barcode import qr
    from reportlab.graphics.shapes import Drawing
    import os
    from django.conf import settings

    # Criar buffer
    buffer = BytesIO()

    # Configurar tamanho
    width = 85 * mm
    height = 54 * mm

    # Criar documento
    doc = SimpleDocTemplate(
        buffer,
        pagesize=(width, height),
        rightMargin=5 * mm,
        leftMargin=5 * mm,
        topMargin=5 * mm,
        bottomMargin=5 * mm
    )

    # Estilos
    styles = getSampleStyleSheet()

    # Estilo personalizado
    estilo_titulo = ParagraphStyle(
        'TituloFuncionario',
        parent=styles['Heading2'],
        fontSize=12,
        alignment=1,
        textColor=colors.HexColor('#0d47a1'),
        spaceAfter=10,
        fontName='Helvetica-Bold'
    )

    estilo_dados = ParagraphStyle(
        'DadosFuncionario',
        parent=styles['Normal'],
        fontSize=8,
        alignment=0,
        spaceAfter=4,
        fontName='Helvetica'
    )

    estilo_label = ParagraphStyle(
        'LabelFuncionario',
        parent=styles['Normal'],
        fontSize=7,
        alignment=0,
        spaceAfter=2,
        textColor=colors.gray,
        fontName='Helvetica-Oblique'
    )

    # Elementos do documento
    elements = []

    # Logo
    try:
        logo_path = os.path.join(settings.STATIC_ROOT, 'img', 'stae_logo.png')
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=35 * mm, height=12 * mm)
            logo.hAlign = 'CENTER'
            elements.append(logo)
            elements.append(Spacer(1, 3 * mm))
    except:
        pass

    # Título
    elements.append(Paragraph("CREDENCIAL FUNCIONÁRIO", estilo_titulo))
    elements.append(Spacer(1, 6 * mm))

    # Tabela com dados
    dados = [
        [Paragraph("<b>Nº:</b>", estilo_label),
         Paragraph(credencial.numero_credencial, estilo_dados)],
        [Paragraph("<b>Nome:</b>", estilo_label),
         Paragraph(credencial.funcionario.nome_completo, estilo_dados)],
        [Paragraph("<b>Cargo:</b>", estilo_label),
         Paragraph(credencial.funcionario.cargo, estilo_dados)],
        [Paragraph("<b>Depto:</b>", estilo_label),
         Paragraph(credencial.funcionario.departamento, estilo_dados)],
        [Paragraph("<b>Tipo:</b>", estilo_label),
         Paragraph(str(credencial.tipo_credencial), estilo_dados)],
        [Paragraph("<b>Validade:</b>", estilo_label),
         Paragraph(credencial.data_validade.strftime("%d/%m/%Y"), estilo_dados)],
    ]

    # Criar tabela
    table = Table(dados, colWidths=[20 * mm, 55 * mm])
    table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 8 * mm))

    # QR Code
    qr_code = qr.QrCodeWidget(credencial.codigo_verificacao)
    bounds = qr_code.getBounds()
    width_qr = bounds[2] - bounds[0]
    height_qr = bounds[3] - bounds[1]
    drawing = Drawing(20 * mm, 20 * mm, transform=[20 * mm / width_qr, 0, 0, 20 * mm / height_qr, 0, 0])
    drawing.add(qr_code)
    drawing.hAlign = 'CENTER'
    elements.append(drawing)

    # Rodapé
    elements.append(Spacer(1, 3 * mm))
    elements.append(Paragraph(
        f"Verificar: {credencial.codigo_offline}",
        ParagraphStyle(
            'Rodape',
            parent=styles['Normal'],
            fontSize=6,
            alignment=1,
            textColor=colors.gray
        )
    ))

    elements.append(Paragraph(
        f"Emitido: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        ParagraphStyle(
            'DataEmissao',
            parent=styles['Normal'],
            fontSize=5,
            alignment=1,
            textColor=colors.gray
        )
    ))

    # Gerar PDF
    doc.build(elements)

    # Obter conteúdo
    pdf = buffer.getvalue()
    buffer.close()

    return pdf


# ===== VIEWS ADICIONAIS =====

@login_required
def reimprimir_credencial(request, credencial_id):
    """Reimprimir uma credencial já emitida - COM OPÇÃO DE MODELO E PDF"""
    try:
        credencial = CredencialEmitida.objects.select_related(
            'pedido__solicitante',
            'pedido__tipo_credencial', 
            'pedido__evento',
            'emitida_por'
        ).get(id=credencial_id)
    except CredencialEmitida.DoesNotExist:
        messages.error(request, '❌ Credencial não encontrada.')
        return redirect('credenciais:lista_pedidos')

    # Verificar permissões
    if not request.user.is_staff:
        messages.error(request, '❌ Não tem permissão para gerir credenciais.')
        return redirect('credenciais:dashboard_credenciais')

    # Carregar Modelos Disponíveis (Feature Resgatada)
    modelos_disponiveis = ModeloCredencial.objects.filter(ativo=True)
    if not modelos_disponiveis.exists():
        ModeloCredencial.objects.create(
            nome="Modelo STAE Padrão",
            descricao="Design oficial básico",
            cor_fundo="#ffffff",
            ativo=True
        )
        modelos_disponiveis = ModeloCredencial.objects.filter(ativo=True)

    if request.method == 'POST':
        # CENÁRIO A: Troca de Modelo
        if 'modelo_id' in request.POST:
            modelo_id = request.POST.get('modelo_id')
            try:
                modelo = ModeloCredencial.objects.get(id=modelo_id, ativo=True)
                credencial.modelo = modelo
                credencial.save()
                messages.success(request, f'Modelo alterado para "{modelo.nome}"!')
            except ModeloCredencial.DoesNotExist:
                messages.error(request, 'Modelo inválido.')
            return redirect('credenciais:reimprimir_credencial', credencial_id=credencial.id)

        # CENÁRIO B: Reimpressão / Download
        acao_pdf = request.POST.get('acao_pdf', 'visualizar_cartao')
        motivo = request.POST.get('motivo_reimpressao', 'Reimpressão solicitada')
        quantidade = int(request.POST.get('quantidade_copias', 1))

        # Registrar auditoria
        AuditoriaCredencial.registrar(
            acao='reimpressao',
            usuario=request.user,
            credencial=credencial,
            detalhes={'motivo': motivo, 'quantidade': quantidade, 'acao': acao_pdf},
            request=request
        )

        messages.success(request, f'✅ Processando: {acao_pdf}')

        # Rotear para a função correta no Utils
        if acao_pdf == 'download_cartao':
            pdf = gerar_pdf_cartao_credencial(credencial)
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="cartao_{credencial.numero_credencial}.pdf"'
            return response
            
        elif acao_pdf == 'visualizar_cartao':
            pdf = gerar_pdf_cartao_credencial(credencial)
            return HttpResponse(pdf, content_type='application/pdf')
            
        elif acao_pdf == 'download': # Formal
            pdf = gerar_pdf_credencial(credencial)
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="credencial_formal_{credencial.numero_credencial}.pdf"'
            return response

        # Se nada der certo, volta para o form
        return redirect('credenciais:reimprimir_credencial', credencial_id=credencial.id)

    # Lógica Adicional de Visualização
    if not hasattr(credencial, 'dias_para_expirar'):
        from datetime import date
        hoje = date.today()
        if credencial.data_validade:
            credencial.dias_para_expirar = (credencial.data_validade - hoje).days
        else:
            credencial.dias_para_expirar = 0

    return render(request, 'credenciais/reimprimir_credencial.html', {
        'credencial': credencial,
        'modelos_disponiveis': modelos_disponiveis,
        'titulo': f'Gerir Credencial - {credencial.numero_credencial}'
    })


@login_required
@user_passes_test(is_admin_credenciais)
def relatorio_credenciais_pdf(request):
    """Gerar relatório de credenciais em PDF"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch

    # Filtros
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    status = request.GET.get('status')
    tipo = request.GET.get('tipo')

    # Consultar credenciais
    credenciais = CredencialEmitida.objects.all().select_related(
        'pedido__solicitante', 'pedido__tipo_credencial', 'pedido__evento'
    ).order_by('-data_emissao')

    if data_inicio:
        credenciais = credenciais.filter(data_emissao__gte=data_inicio)
    if data_fim:
        credenciais = credenciais.filter(data_emissao__lte=data_fim)
    if status:
        credenciais = credenciais.filter(status=status)
    if tipo:
        credenciais = credenciais.filter(pedido__tipo_credencial_id=tipo)

    # Criar buffer
    buffer = BytesIO()

    # Criar documento
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    # Elementos do documento
    elements = []

    # Título
    elements.append(Paragraph("RELATÓRIO DE CREDENCIAIS - STAE", styles['Title']))
    elements.append(Spacer(1, 0.25 * inch))

    # Informações do relatório
    elements.append(Paragraph(
        f"Período: {data_inicio or 'Início'} a {data_fim or 'Hoje'}",
        styles['Normal']
    ))
    elements.append(Paragraph(
        f"Total de credenciais: {credenciais.count()}",
        styles['Normal']
    ))
    elements.append(Spacer(1, 0.25 * inch))

    # Tabela de credenciais
    if credenciais.exists():
        data = [["Nº Credencial", "Nome", "Tipo", "Evento", "Emissão", "Validade", "Status"]]

        for credencial in credenciais[:100]:  # Limitar a 100 registros
            data.append([
                credencial.numero_credencial,
                credencial.pedido.solicitante.nome_completo[:30],
                str(credencial.pedido.tipo_credencial)[:20],
                str(credencial.pedido.evento)[:20] if credencial.pedido.evento else "-",
                credencial.data_emissao.strftime("%d/%m/%Y"),
                credencial.data_validade.strftime("%d/%m/%Y"),
                credencial.get_status_display()
            ])

        table = Table(data, colWidths=[1 * inch, 1.5 * inch, 1 * inch, 1.2 * inch, 0.8 * inch, 0.8 * inch, 0.7 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 0.25 * inch))

        # Estatísticas
        elements.append(Paragraph("Estatísticas:", styles['Heading2']))
        stats = credenciais.values('status').annotate(total=Count('id'))
        for stat in stats:
            elements.append(Paragraph(
                f"{stat['status'].capitalize()}: {stat['total']}",
                styles['Normal']
            ))
    else:
        elements.append(Paragraph("Nenhuma credencial encontrada com os filtros aplicados.", styles['Normal']))

    # Rodapé
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph(
        f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')} por {request.user.get_full_name() or request.user.username}",
        ParagraphStyle(
            'Rodape',
            parent=styles['Normal'],
            fontSize=8,
            alignment=2,  # Right
            textColor=colors.gray
        )
    ))

    # Gerar PDF
    doc.build(elements)

    # Configurar resposta
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="relatorio_credenciais.pdf"'
    return response





# ADICIONAR APÓS AS OUTRAS FUNÇÕES, ANTES DO FIM DO FICHEIRO


# ================================================
# QR CODE FUNCTIONS
# ================================================

@login_required
def gerar_qrcode(request, pk):
    """Gerar/regenerar QR Code para uma credencial"""
    try:
        credencial = get_object_or_404(CredencialEmitida, id=pk)

        # Verificar permissões
        if not request.user.is_staff:
            messages.error(request, '❌ Não tem permissão para gerar QR Codes.')
            return redirect('credenciais:dashboard_credenciais')

        # Gerar código único de verificação se não existir
        if not credencial.codigo_verificacao:
            import uuid
            credencial.codigo_verificacao = str(uuid.uuid4())[:8].upper()
            credencial.save()

        # Criar QR Code
        import qrcode
        from io import BytesIO
        from django.core.files.base import ContentFile

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        # Conteúdo do QR Code (URL de verificação)
        qr_data = f"http://localhost:8000/credenciais/verificar/{credencial.codigo_verificacao}"
        qr.add_data(qr_data)
        qr.make(fit=True)

        # Gerar imagem
        img = qr.make_image(fill_color="black", back_color="white")

        # Salvar no modelo
        buffer = BytesIO()
        img.save(buffer, format='PNG')

        # Salvar como ImageField
        if credencial.qr_code:
            # Atualizar imagem existente
            credencial.qr_code.save(
                f'qrcode_{credencial.numero_credencial}.png',
                ContentFile(buffer.getvalue()),
                save=True
            )
        else:
            # Criar nova imagem
            credencial.qr_code.save(
                f'qrcode_{credencial.numero_credencial}.png',
                ContentFile(buffer.getvalue())
            )

        messages.success(request, f'✅ QR Code gerado com sucesso para credencial {credencial.numero_credencial}!')

        # Registrar auditoria
        AuditoriaCredencial.registrar(
            acao='gerar_qrcode',
            usuario=request.user,
            credencial=credencial,
            detalhes={
                'codigo_verificacao': credencial.codigo_verificacao,
                'qr_data': qr_data
            },
            request=request
        )

        return redirect('credenciais:reimprimir_credencial', credencial_id=credencial.id)

    except Exception as e:
        messages.error(request, f'❌ Erro ao gerar QR Code: {str(e)}')
        return redirect('credenciais:reimprimir_credencial', credencial_id=pk)

@login_required
def exportar_cartao_png(request, credencial_id):
    """Exportar cartão como imagem PNG"""
    credencial = get_object_or_404(CredencialEmitida, id=credencial_id)

    # Verificar permissões
    if not request.user.is_staff:
        from django.contrib import messages
        messages.error(request, 'Não tem permissão para exportar esta credencial.')
        return redirect('credenciais:dashboard_credenciais')

    try:
        # TENTAR USAR imgkit (wkhtmltoimage)
        import imgkit

        # Renderizar HTML do cartão
        from django.template.loader import render_to_string
        html_content = render_to_string('credenciais/cartao_pvc.html', {
            'credencial': credencial,
            'config': {'entidade': 'stae'}  # Padrão STAE
        })


        # Configurações para imagem
        options = {
            'format': 'png',
            'width': 340,  # Largura do cartão
            'height': 540,  # Altura do cartão
            'quality': 100,
            'disable-smart-width': '',
        }

        # Converter HTML para PNG
        png_data = imgkit.from_string(html_content, False, options=options)

        # Retornar como download
        response = HttpResponse(png_data, content_type='image/png')
        response['Content-Disposition'] = f'attachment; filename="credencial_{credencial.numero_credencial}.png"'
        return response

    except ImportError:
        # Se imgkit não estiver instalado
        from django.contrib import messages
        messages.error(request, 'Biblioteca imgkit não instalada. Execute: pip install imgkit')
        return redirect('credenciais:reimprimir_credencial', credencial_id=credencial_id)
    except Exception as e:
        from django.contrib import messages
        messages.error(request, f'Erro ao gerar PNG: {str(e)}')
        return redirect('credenciais:reimprimir_credencial', credencial_id=credencial_id)


@login_required
def visualizar_para_impressao(request, credencial_id):
    """Visualizar cartão otimizado para impressão"""
    credencial = get_object_or_404(CredencialEmitida, id=credencial_id)

    # Verificar permissões
    if not request.user.is_staff:
        from django.contrib import messages
        messages.error(request, 'Não tem permissão para imprimir esta credencial.')
        return redirect('credenciais:dashboard_credenciais')

    # Renderizar template de impressão
    # Renderizar template de impressão
    return render(request, 'credenciais/imprimir_cartao.html', {
        'credencial': credencial,
        'somente_cartao': True  # Flag para mostrar apenas o cartão
    })

# --- EVENT MANAGEMENT VIEWS ---

@login_required
def lista_eventos(request):
    """Lista todos os eventos cadastrados"""
    query = request.GET.get('q', '')
    eventos = Evento.objects.all().order_by('-data_inicio')
    if query:
        eventos = eventos.filter(Q(nome__icontains=query) | Q(local__icontains=query))
    
    return render(request, 'credenciais/eventos_list.html', {'eventos': eventos, 'query': query})

@login_required
@user_passes_test(is_admin_credenciais)
def adicionar_evento(request):
    """Adicionar novo evento"""
    if request.method == 'POST':
        form = EventoForm(request.POST, request.FILES)
        if form.is_valid():
            evento = form.save(commit=False)
            evento.criado_por = request.user
            evento.save()
            messages.success(request, 'Evento criado com sucesso!')
            return redirect('credenciais:lista_eventos')
    else:
        form = EventoForm()
    return render(request, 'credenciais/evento_form.html', {'form': form, 'titulo': 'Novo Evento'})

@login_required
@user_passes_test(is_admin_credenciais)
def editar_evento(request, evento_id):
    """Editar evento existente"""
    evento = get_object_or_404(Evento, id=evento_id)
    if request.method == 'POST':
        form = EventoForm(request.POST, request.FILES, instance=evento)
        if form.is_valid():
            form.save()
            messages.success(request, 'Evento atualizado!')
            return redirect('credenciais:lista_eventos')
    else:
        form = EventoForm(instance=evento)
    return render(request, 'credenciais/evento_form.html', {'form': form, 'evento': evento, 'titulo': 'Editar Evento'})

@login_required
def detalhe_evento(request, evento_id):
    """Detalhes de um evento e seus pedidos"""
    evento = get_object_or_404(Evento, id=evento_id)
    pedidos = PedidoCredencial.objects.filter(evento=evento).order_by('-data_pedido')
    return render(request, 'credenciais/evento_detail.html', {'evento': evento, 'pedidos': pedidos})

@login_required
def api_get_evento_detalhes(request, evento_id):
    """Retorna detalhes do evento para o formulário de pedido via AJAX"""
    evento = get_object_or_404(Evento, id=evento_id)
    return JsonResponse({
        'id': evento.id,
        'nome': evento.nome,
        'abrangencia': evento.abrangencia,
        'provincia': evento.provincia,
        'data_inicio': evento.data_inicio.strftime('%Y-%m-%d'),
        'data_fim': evento.data_fim.strftime('%Y-%m-%d'),
    })

# --- TRACKING VIEW ---

def rastrear_pedido(request):
    """Página pública/interna para rastrear estado do pedido"""
    codigo = request.GET.get('codigo', '').strip()
    pedido = None
    if codigo:
        pedido = PedidoCredencial.objects.filter(
            Q(numero_pedido=codigo) | Q(codigo_confirmacao=codigo) | Q(solicitante__numero_bi=codigo)
        ).first()
        if not pedido:
            messages.error(request, 'Nenhum pedido encontrado com este código.')
            
    return render(request, 'credenciais/rastreio.html', {'pedido': pedido, 'codigo': codigo})


# --- GESTÃO DE TIPOS DE CREDENCIAL ---

@login_required
@user_passes_test(is_admin_credenciais)
def lista_tipos_credencial(request):
    """Listar todos os tipos de credencial"""
    tipos = TipoCredencial.objects.all().order_by('ordem', 'nome')
    return render(request, 'credenciais/tipos_list.html', {'tipos': tipos})

@login_required
@user_passes_test(is_admin_credenciais)
def adicionar_tipo_credencial(request):
    """Adicionar novo tipo de credencial"""
    if request.method == 'POST':
        form = TipoCredencialForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de credencial criado com sucesso!')
            return redirect('credenciais:lista_tipos_credencial')
    else:
        form = TipoCredencialForm()
    return render(request, 'credenciais/tipo_form.html', {'form': form, 'titulo': 'Novo Tipo de Credencial'})

@login_required
@user_passes_test(is_admin_credenciais)
def editar_tipo_credencial(request, tipo_id):
    """Editar tipo de credencial existente"""
    tipo = get_object_or_404(TipoCredencial, id=tipo_id)
    if request.method == 'POST':
        form = TipoCredencialForm(request.POST, instance=tipo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de credencial atualizado!')
            return redirect('credenciais:lista_tipos_credencial')
    else:
        form = TipoCredencialForm(instance=tipo)
    return render(request, 'credenciais/tipo_form.html', {'form': form, 'tipo': tipo, 'titulo': 'Editar Tipo de Credencial'})






@login_required
def visualizar_pdf_cartao_credencial(request, credencial_id):
    """Visualiza o PDF do cartão no navegador"""
    credencial = get_object_or_404(CredencialEmitida, id=credencial_id)
    pdf = gerar_pdf_cartao_credencial(credencial)
    return HttpResponse(pdf, content_type='application/pdf')

@login_required
def download_pdf_cartao_credencial(request, credencial_id):
    """Baixa o PDF do cartão"""
    credencial = get_object_or_404(CredencialEmitida, id=credencial_id)
    pdf = gerar_pdf_cartao_credencial(credencial)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="cartao_{credencial.numero_credencial}.pdf"'
    return response

@login_required
def visualizar_para_impressao(request, credencial_id):
    """Página limpa (HTML) para impressão direta do cartão pelo navegador"""
    credencial = get_object_or_404(CredencialEmitida, id=credencial_id)
    return render(request, 'credenciais/imprimir_cartao.html', {'credencial': credencial})

@login_required
def exportar_cartao_png(request, credencial_id):
    """Exportar cartão como imagem PNG (via imgkit/utils)"""
    credencial = get_object_or_404(CredencialEmitida, id=credencial_id)
    
    png_data = gerar_imagem_cartao(credencial)
    if png_data:
        response = HttpResponse(png_data, content_type='image/png')
        response['Content-Disposition'] = f'attachment; filename="credencial_{credencial.numero_credencial}.png"'
        return response
    else:
        messages.error(request, 'Erro ao gerar imagem. Verifique se o wkhtmltopdf está instalado no servidor.')
        return redirect('credenciais:reimprimir_credencial', credencial_id=credencial_id)


def api_buscar_solicitante(request):
    """API para buscar solicitante por nome (para autocomplete)"""
    termo = request.GET.get('q', '').strip()
    
    if len(termo) < 3:
        return JsonResponse({'results': []})
    
    solicitantes = Solicitante.objects.filter(
        Q(nome_completo__icontains=termo) | Q(email__icontains=termo),
        ativo=True
    )[:10]
    
    results = [{
        'id': s.id,
        'nome_completo': s.nome_completo,
        'email': s.email,
        'telefone': s.telefone,
        'numero_bi': s.numero_bi or '',
        'nacionalidade': s.nacionalidade or 'Moçambicana'
    } for s in solicitantes]
    
    return JsonResponse({'results': results})
