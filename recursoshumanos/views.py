# recursoshumanos/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden, FileResponse
from django.db.models import Q, Count, Avg, Sum, Max
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from django.utils import timezone
from datetime import date, datetime, timedelta
import calendar
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from .decorators import rh_required, chefe_required, director_required
from .models import *
from .forms import *
from .utils.notificacoes import Notificador
from .utils.helpers import calcular_dias_uteis, gerar_relatorio_presencas_mensal, verificar_conflito_ferias





# ========== DASHBOARD PRINCIPAL ==========

@login_required
@rh_required
def dashboard_rh(request):
    """Dashboard específico para RH/Administração"""
    user = request.user
    context = {}

    # Verificar se é RH - redirecionar se não for
    if not (user.is_staff or user.groups.filter(name='rh_staff').exists()):
        messages.error(request, "Acesso restrito ao Departamento de Recursos Humanos.")
        return redirect('recursoshumanos:dashboard')

    # Estatísticas gerais
    context['total_funcionarios'] = Funcionario.objects.filter(ativo=True).count()
    context['funcionarios_novos'] = Funcionario.objects.filter(
        data_admissao__month=date.today().month,
        data_admissao__year=date.today().year
    ).count()

    # Licenças pendentes
    context['licencas_pendentes_rh'] = Licenca.objects.filter(
        status='pendente'
    ).select_related('funcionario').order_by('data_criacao')[:10]

    context['total_licencas_pendentes'] = Licenca.objects.filter(status='pendente').count()

    # Licenças aguardando chefes
    context['licencas_aguardando_chefe'] = Licenca.objects.filter(
        status='aguardando_chefe'
    ).select_related('funcionario').order_by('-data_analise_rh')[:5]

    # Licenças aguardando diretores
    context['licencas_aguardando_diretor'] = Licenca.objects.filter(
        status='aguardando_diretor'
    ).select_related('funcionario').order_by('-data_parecer_chefe')[:5]

    # Licenças aprovadas recentemente
    context['licencas_aprovadas_recentes'] = Licenca.objects.filter(
        status='aprovado',
        data_parecer_diretor__date=date.today()
    ).select_related('funcionario').order_by('-data_parecer_diretor')[:5]

    # Saldos de férias críticos (menos de 5 dias)
    try:
        context['saldos_criticos'] = SaldoFerias.objects.filter(
            dias_saldo__lt=5,
            ano=date.today().year
        ).select_related('funcionario')[:5]
    except:
        context['saldos_criticos'] = []

    # Avaliações pendentes
    context['avaliacoes_pendentes'] = AvaliacaoDesempenho.objects.filter(
        status='pendente'
    ).select_related('funcionario').order_by('-data_avaliacao')[:5]

    # Contratos próximos do vencimento (próximos 30 dias)
    hoje = date.today()
    trinta_dias = hoje + timedelta(days=30)

    # Linhas 99-105 devem ficar assim:
    context['contratos_vencendo'] = Funcionario.objects.filter(
        data_saida__gte=hoje,  # ← ALTERADO
        data_saida__lte=trinta_dias,  # ← ALTERADO
        ativo=True
    ).order_by('data_saida')[:5]  # ← ALTERADO

    # Notificações
    notificacoes_recentes = NotificacaoSistema.objects.filter(
        usuario=user
    ).order_by('-data_criacao')[:5]

    notificacoes_nao_lidas = NotificacaoSistema.objects.filter(
        usuario=user,
        lida=False
    ).count()

    context['notificacoes_recentes'] = notificacoes_recentes
    context['notificacoes_nao_lidas'] = notificacoes_nao_lidas

    context['hoje'] = date.today()
    context['hora_atual'] = timezone.now()

    return render(request, 'recursoshumanos/dashboard_rh.html', context)


@login_required(login_url='/rh/login/')
def dashboard_completo(request):
    """Dashboard único adaptado ao perfil do usuário"""
    user = request.user

    # REDIRECIONAR RH PARA DASHBOARD ESPECÍFICO
    if user.is_staff or user.groups.filter(name='rh_staff').exists():
        return redirect('recursoshumanos:dashboard_rh')

    context = {}

    try:
        funcionario = Funcionario.objects.get(user=user)
        context['funcionario'] = funcionario

        # Determinar perfil
        context['is_chefe'] = funcionario.funcao in ['chefe', 'coordenador', 'director']
        context['is_director'] = funcionario.funcao == 'director'

        # Informações pessoais
        context['minhas_licencas'] = Licenca.objects.filter(
            funcionario=funcionario
        ).order_by('-data_inicio')[:5]

        context['minhas_avaliacoes'] = AvaliacaoDesempenho.objects.filter(
            funcionario=funcionario
        ).order_by('-data_avaliacao')[:3]

        context['meus_registros_hoje'] = RegistroPresenca.objects.filter(
            funcionario=funcionario,
            data_hora__date=date.today()
        ).order_by('data_hora')

        # Se for chefe

        if context['is_chefe']:
            # UM CHEFE SÓ DEVE VER FUNCIONÁRIOS DO SEU SETOR
            # Alterado para pegar TODOS do setor e excluir apenas a si mesmo e diretores (caso existam no setor)
            # Isso garante que 'Técnico Superior', 'Motorista', etc. apareçam
            subordinados = Funcionario.objects.filter(
                sector=funcionario.sector,
                ativo=True
            ).exclude(
                id=funcionario.id
            ).exclude(
                funcao='director'  # Garante que não liste um diretor se houver
            )

            # Se o usuário for Coordenador, talvez não deva ver o Chefe de Departamento
            if funcionario.funcao == 'coordenador':
                 subordinados = subordinados.exclude(funcao='chefe')

            context['subordinados_diretos'] = subordinados
            context['subordinados_count'] = subordinados.count()

            context['licencas_equipa_pendentes'] = Licenca.objects.filter(
                funcionario__in=subordinados,
                status='aguardando_chefe'
            ).select_related('funcionario')[:5]

            context['avaliacoes_equipa_pendentes'] = AvaliacaoDesempenho.objects.filter(
                funcionario__in=subordinados,
                status='pendente'
            ).select_related('funcionario')[:5]

        # Se for director
        if context['is_director']:
            # DIRETORES AVALIAM: CHEFES DE DEPARTAMENTO e COORDENADORES da sua DIREÇÃO (que não sejam eles mesmos)
            chefes_e_coordenadores = Funcionario.objects.filter(
                sector__direcao=funcionario.sector.direcao, # Mesma Direção
                funcao__in=['chefe', 'coordenador'], # Apenas chefias
                ativo=True # Apenas ativos
            ).exclude(id=funcionario.id)

            context['chefes_sob_direcao'] = chefes_e_coordenadores
            context['chefes_sob_direcao_count'] = chefes_e_coordenadores.count()

            # Licenças aguardando diretor (já existia)
            context['licencas_aguardando_diretor'] = Licenca.objects.filter(
                funcionario__sector__direcao=funcionario.sector.direcao,
                status='aguardando_diretor'
            ).select_related('funcionario')[:5]
            
            # Avaliações: Diretor vê chefes que PRECISAM ser avaliados
            # Aqui listamos os Chefes para Avaliação (mesmo que não haja "pendência" formal, ele pode iniciar)
            context['avaliacoes_direcao_pendentes'] = AvaliacaoDesempenho.objects.filter(
                funcionario__in=chefes_e_coordenadores,
                status='pendente'
            ).select_related('funcionario')[:5]

    except Funcionario.DoesNotExist:
        pass

    # Notificações
    notificacoes_recentes = NotificacaoSistema.objects.filter(
        usuario=user
    ).order_by('-data_criacao')[:5]

    notificacoes_nao_lidas = NotificacaoSistema.objects.filter(
        usuario=user,
        lida=False
    ).count()

    context['notificacoes_recentes'] = notificacoes_recentes
    context['notificacoes_nao_lidas'] = notificacoes_nao_lidas

    # Canal do setor
    try:
        funcionario = Funcionario.objects.get(user=user)
        canal_setor = CanalComunicacao.objects.filter(
            setor=funcionario.sector,
            tipo='departamento'
        ).first()
        context['canal_setor'] = canal_setor
    except:
        pass

    context['hoje'] = date.today()

    return render(request, 'recursoshumanos/dashboard_completo.html', context)



# ========== FUNCIONÁRIOS ==========

@login_required
@rh_required
def lista_funcionarios(request):
    """Lista todos os funcionários (apenas RH)"""
    funcionarios = Funcionario.objects.select_related('sector', 'user').order_by('nome_completo')

    # Filtros
    setor_filter = request.GET.get('setor')
    status_filter = request.GET.get('status')

    if setor_filter:
        funcionarios = funcionarios.filter(sector_id=setor_filter)

    if status_filter == 'ativos':
        funcionarios = funcionarios.filter(ativo=True)
    elif status_filter == 'inativos':
        funcionarios = funcionarios.filter(ativo=False)

    context = {
        'funcionarios': funcionarios,
        'sectores': Sector.objects.all(),
        'setor_filter': setor_filter,
        'status_filter': status_filter,
    }
    return render(request, 'recursoshumanos/funcionarios/lista.html', context)


@login_required
@rh_required
def detalhes_funcionario(request, funcionario_id):
    """Detalhes completos de um funcionário"""
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)

    # Dados relacionados
    licencas = Licenca.objects.filter(funcionario=funcionario).order_by('-data_inicio')
    avaliacoes = AvaliacaoDesempenho.objects.filter(funcionario=funcionario).order_by('-data_avaliacao')
    promocoes = Promocao.objects.filter(funcionario=funcionario).order_by('-data_promocao')
    registros_recentes = RegistroPresenca.objects.filter(
        funcionario=funcionario
    ).order_by('-data_hora')[:10]

    context = {
        'funcionario': funcionario,
        'licencas': licencas,
        'avaliacoes': avaliacoes,
        'promocoes': promocoes,
        'registros_recentes': registros_recentes,
    }
    return render(request, 'recursoshumanos/funcionarios/detalhes.html', context)


import random
from datetime import datetime


@login_required
@rh_required
def criar_funcionario(request):
    """Criar novo funcionário com número automático"""
    if request.method == 'POST':
        form = FuncionarioForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                funcionario = form.save(commit=False)

                # GERAR NÚMERO AUTOMÁTICO
                import random
                from datetime import datetime
                ano_atual = datetime.now().year
                sequencia = random.randint(1000, 9999)
                numero_gerado = f"STAE-{ano_atual}-{sequencia}"

                # Verificar se número já existe
                while Funcionario.objects.filter(numero_identificacao=numero_gerado).exists():
                    sequencia = random.randint(1000, 9999)
                    numero_gerado = f"STAE-{ano_atual}-{sequencia}"

                funcionario.numero_identificacao = numero_gerado
                funcionario.save()
                form.save_m2m()

                # Gerar QR Code
                funcionario.gerar_qr_code()

                messages.success(request, '✅ Funcionário criado com sucesso!')
                messages.info(request, f'📋 Nome: {funcionario.nome_completo}')
                messages.info(request, f'🔢 Número: {funcionario.numero_identificacao}')
                messages.info(request, f'📱 QR Code gerado automaticamente')

                return redirect('detalhes_funcionario', funcionario_id=funcionario.id)

            except Exception as e:
                messages.error(request, f'❌ Erro ao criar funcionário: {str(e)}')
    else:
        form = FuncionarioForm()

    # Gerar número para preview
    import random
    from datetime import datetime
    ano_atual = datetime.now().year
    sequencia = random.randint(1000, 9999)
    numero_preview = f"STAE-{ano_atual}-{sequencia}"

    context = {
        'form': form,
        'numero_preview': numero_preview,
        'hoje': date.today().strftime('%Y-%m-%d'),
    }
    return render(request, 'recursoshumanos/funcionarios/criar.html', context)  # ← CAMINHO CORRETO



# ========== LICENÇAS ==========



@login_required
@rh_required
def analisar_licenca_rh(request, licenca_id):
    """RH analisa licença antes de enviar para o chefe"""
    licenca = get_object_or_404(Licenca, id=licenca_id)

    # Verificar se é RH
    if not (request.user.is_staff or request.user.groups.filter(name='rh_staff').exists()):
        messages.error(request, "Apenas RH pode analisar licenças.")
        return redirect('dashboard')

    # Verificar se licença está no status correto
    if licenca.status != 'pendente':
        messages.warning(request, f"Esta licença já foi processada. Status atual: {licenca.get_status_display()}")
        return redirect('/rh/licencas/pendentes-rh/')


    # Obter saldo de férias do funcionário (se for férias)
    saldo_ferias = None
    licencas_ano = []
    dias_ja_gozados = 0
    ano_atual = date.today().year

    if licenca.tipo == 'ferias':
        # Obter ou criar saldo para o ano
        saldo_ferias = SaldoFerias.objects.filter(
            funcionario=licenca.funcionario,
            ano=ano_atual
        ).first()

        if not saldo_ferias:
            saldo_ferias = SaldoFerias.objects.create(
                funcionario=licenca.funcionario,
                ano=ano_atual,
                dias_disponiveis=22,
                dias_gozados=0,
                dias_saldo=22
            )

        # Calcular saldo atual
        saldo_ferias.calcular_saldo()

        # Obter histórico de licenças do ano
        licencas_ano = Licenca.objects.filter(
            funcionario=licenca.funcionario,
            data_inicio__year=ano_atual,
            tipo='ferias',
            status='aprovado'
        )

        dias_ja_gozados = licencas_ano.aggregate(
            total=Sum('dias_utilizados')
        )['total'] or 0

    if request.method == 'POST':
        decisao = request.POST.get('decisao')
        observacoes_rh = request.POST.get('observacoes_rh', '').strip()
        dias_autorizados = request.POST.get('dias_autorizados')

        if not observacoes_rh:
            messages.error(request, "Observações são obrigatórias.")
            return redirect('analisar_licenca_rh', licenca_id=licenca_id)

        if decisao == 'aprovar':
            # Verificar se tem saldo suficiente (para férias)
            if licenca.tipo == 'ferias' and saldo_ferias and saldo_ferias.dias_saldo < licenca.dias_utilizados:
                messages.error(request,
                               f"Saldo insuficiente! Disponível: {saldo_ferias.dias_saldo} dias, Solicitado: {licenca.dias_utilizados} dias")
                return redirect('analisar_licenca_rh', licenca_id=licenca_id)

            # Atualizar licença
            licenca.status = 'aguardando_chefe'
            licenca.observacoes_rh = observacoes_rh
            licenca.rh_aprovador = request.user
            licenca.data_analise_rh = timezone.now()

            # Se RH pode ajustar dias
            if dias_autorizados and dias_autorizados.isdigit():
                dias_int = int(dias_autorizados)
                if dias_int > 0:
                    licenca.dias_autorizados_rh = dias_int
                    # Atualizar dias utilizados se diferente
                    if dias_int != licenca.dias_utilizados:
                        licenca.dias_utilizados = dias_int
                        messages.info(request, f"Dias ajustados para {dias_int}")

            licenca.save()

            # Notificar chefe
            Notificador.licenca_analisada_rh(licenca)

            messages.success(request, "✅ Licença aprovada pelo RH e enviada para o chefe.")
            return redirect('lista_licencas_pendentes_rh')

        elif decisao == 'rejeitar':
            licenca.status = 'rejeitado'
            licenca.observacoes_rh = observacoes_rh
            licenca.rh_aprovador = request.user
            licenca.data_analise_rh = timezone.now()
            licenca.save()

            # Notificar funcionário
            Notificador.licenca_analisada_rh(licenca)

            messages.warning(request, "❌ Licença rejeitada pelo RH.")
            return redirect('lista_licencas_pendentes_rh')

    context = {
        'licenca': licenca,
        'saldo_ferias': saldo_ferias,
        'licencas_ano': licencas_ano,
        'dias_ja_gozados': dias_ja_gozados,
        'ano_atual': ano_atual,
    }

    return render(request, 'recursoshumanos/licencas/analisar_rh.html', context)


# ========== FÉRIAS ==========

@login_required
@rh_required
def lista_pedidos_ferias(request):
    """Lista todos os pedidos de férias"""
    pedidos = PedidoFerias.objects.select_related(
        'funcionario',
        'funcionario__sector'
    ).order_by('-data_solicitacao')

    # Filtros
    status_filter = request.GET.get('status')
    setor_filter = request.GET.get('setor')

    if status_filter:
        pedidos = pedidos.filter(status=status_filter)

    if setor_filter:
        pedidos = pedidos.filter(funcionario__sector_id=setor_filter)

    # Paginação
    paginator = Paginator(pedidos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'pedidos': page_obj,
        'page_obj': page_obj,
        'status_filter': status_filter,
        'setor_filter': setor_filter,
        'sectores': Sector.objects.all(),
        'status_choices': PedidoFerias.STATUS_CHOICES,
    }
    return render(request, 'recursoshumanos/ferias/lista_pedidos.html', context)


@login_required
@rh_required
def aprovar_pedido_ferias(request, pedido_id):
    """Aprovar ou rejeitar pedido de férias"""
    pedido = get_object_or_404(PedidoFerias, id=pedido_id)

    # Verificar se é RH
    if not (request.user.is_staff or request.user.groups.filter(name='rh_staff').exists()):
        messages.error(request, "Apenas RH pode aprovar pedidos de férias.")
        return redirect('dashboard')

    if request.method == 'POST':
        acao = request.POST.get('acao')
        observacoes = request.POST.get('observacoes', '').strip()

        if acao == 'aprovar':
            # Verificar saldo de férias
            ano = pedido.data_inicio.year
            saldo, created = SaldoFerias.objects.get_or_create(
                funcionario=pedido.funcionario,
                ano=ano,
                defaults={'dias_disponiveis': 22, 'dias_gozados': 0, 'dias_saldo': 22}
            )

            if saldo.dias_saldo < pedido.dias_solicitados:
                messages.error(request,
                               f"Saldo insuficiente! Disponível: {saldo.dias_saldo} dias, "
                               f"Solicitado: {pedido.dias_solicitados} dias")
                return redirect('aprovar_pedido_ferias', pedido_id=pedido_id)

            # Atualizar pedido
            pedido.status = 'aprovado'
            pedido.aprovado_por = request.user
            pedido.data_aprovacao = timezone.now()
            pedido.observacoes_rh = observacoes
            pedido.save()

            # Atualizar saldo de férias
            saldo.dias_gozados += pedido.dias_solicitados
            saldo.calcular_saldo()
            saldo.save()

            # Criar licença automática
            licenca = Licenca.objects.create(
                funcionario=pedido.funcionario,
                tipo='ferias',
                data_inicio=pedido.data_inicio,
                data_fim=pedido.data_fim,
                dias_utilizados=pedido.dias_solicitados,
                status='aprovado',
                observacoes_rh=observacoes,
                rh_aprovador=request.user,
                data_analise_rh=timezone.now()
            )

            # Gerar documento
            gerar_documento_ferias(licenca)

            # Notificar funcionário
            Notificador.licenca_autorizada(licenca)

            messages.success(request, '✅ Férias aprovadas com sucesso!')

        elif acao == 'rejeitar':
            pedido.status = 'rejeitado'
            pedido.aprovado_por = request.user
            pedido.data_aprovacao = timezone.now()
            pedido.observacoes_rh = observacoes
            pedido.save()

            # Notificar funcionário
            NotificacaoSistema.objects.create(
                usuario=pedido.funcionario.user,
                tipo='ferias',
                titulo='❌ Pedido de Férias Rejeitado',
                mensagem=f'Seu pedido de férias foi rejeitado. Motivo: {observacoes[:100]}...',
                link_url='/rh/licencas/minhas/'
            )

            messages.warning(request, '❌ Pedido de férias rejeitado.')

        return redirect('lista_pedidos_ferias')

    context = {
        'pedido': pedido,
    }
    return render(request, 'recursoshumanos/ferias/aprovar.html', context)


@login_required
def solicitar_ferias(request):
    """Solicitar férias"""
    funcionario = get_object_or_404(Funcionario, user=request.user)

    # Verificar saldo atual
    ano_atual = date.today().year
    saldo_atual = SaldoFerias.objects.filter(
        funcionario=funcionario,
        ano=ano_atual
    ).first()

    if not saldo_atual:
        saldo_atual = SaldoFerias.objects.create(
            funcionario=funcionario,
            ano=ano_atual,
            dias_disponiveis=22,
            dias_gozados=0,
            dias_saldo=22
        )

    if request.method == 'POST':
        form = PedidoFeriasForm(request.POST)
        if form.is_valid():
            try:
                pedido = form.save(commit=False)
                pedido.funcionario = funcionario
                pedido.status = 'pendente'
                pedido.save()

                # Notificar RH
                Notificador.licenca_submetida(pedido)

                messages.success(request, '✅ Pedido de férias enviado com sucesso!')
                return redirect('recursoshumanos:minhas_licencas')

            except Exception as e:
                messages.error(request, f'❌ Erro ao solicitar férias: {str(e)}')
    else:
        # Calcular data padrão (30 dias a partir de hoje)
        data_inicio_padrao = date.today() + timedelta(days=30)
        data_fim_padrao = data_inicio_padrao + timedelta(days=21)  # 3 semanas

        form = PedidoFeriasForm(initial={
            'data_inicio': data_inicio_padrao,
            'data_fim': data_fim_padrao,
        })

    context = {
        'form': form,
        'funcionario': funcionario,
        'saldo_atual': saldo_atual,
        'hoje': date.today(),
    }
    return render(request, 'recursoshumanos/ferias/solicitar.html', context)


@login_required
def minhas_ferias(request):
    """Histórico de férias do funcionário"""
    funcionario = get_object_or_404(Funcionario, user=request.user)

    # Pedidos de férias
    pedidos = PedidoFerias.objects.filter(
        funcionario=funcionario
    ).order_by('-data_solicitacao')

    # Saldos de férias por ano
    saldos = SaldoFerias.objects.filter(
        funcionario=funcionario
    ).order_by('-ano')

    context = {
        'pedidos': pedidos,
        'saldos': saldos,
        'funcionario': funcionario,
    }
    return render(request, 'recursoshumanos/ferias/minhas.html', context)


@login_required
@rh_required
def relatorio_ferias(request):
    """Relatório de férias"""
    ano = request.GET.get('ano', date.today().year)

    # Saldos de férias do ano
    saldos = SaldoFerias.objects.filter(
        ano=ano
    ).select_related('funcionario').order_by('funcionario__nome_completo')

    # Pedidos de férias do ano
    pedidos = PedidoFerias.objects.filter(
        data_solicitacao__year=ano
    ).select_related('funcionario').order_by('-data_solicitacao')

    # Estatísticas
    total_funcionarios = saldos.count()
    total_dias_disponiveis = saldos.aggregate(Sum('dias_disponiveis'))['dias_disponiveis__sum'] or 0
    total_dias_gozados = saldos.aggregate(Sum('dias_gozados'))['dias_gozados__sum'] or 0
    total_dias_saldo = saldos.aggregate(Sum('dias_saldo'))['dias_saldo__sum'] or 0

    # Anos disponíveis
    anos = SaldoFerias.objects.dates('ano', 'year')
    anos_disponiveis = sorted(set([ano.year for ano in anos]), reverse=True)

    context = {
        'saldos': saldos,
        'pedidos': pedidos,
        'ano': int(ano),
        'anos_disponiveis': anos_disponiveis,
        'total_funcionarios': total_funcionarios,
        'total_dias_disponiveis': total_dias_disponiveis,
        'total_dias_gozados': total_dias_gozados,
        'total_dias_saldo': total_dias_saldo,
    }
    return render(request, 'recursoshumanos/relatorios/ferias.html', context)


@login_required
@rh_required
def lista_licencas_pendentes_rh(request):
    """Lista todas as licenças pendentes para análise do RH"""
    licencas = Licenca.objects.filter(
        status='pendente'
    ).select_related(
        'funcionario',
        'funcionario__sector'
    ).order_by('-data_criacao')

    # Paginação
    paginator = Paginator(licencas, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Estatísticas
    total_pendentes = licencas.count()
    total_ferias = licencas.filter(tipo='ferias').count()
    total_outros = licencas.exclude(tipo='ferias').count()

    context = {
        'licencas': page_obj,
        'page_obj': page_obj,
        'total_pendentes': total_pendentes,
        'total_ferias': total_ferias,
        'total_outros': total_outros,
    }

    return render(request, 'recursoshumanos/licencas/lista_pendentes_rh.html', context)


@login_required
@chefe_required
def licencas_do_setor(request):
    """Lista todas as licenças do setor do chefe"""
    chefe = get_object_or_404(Funcionario, user=request.user)

    # Obter funcionários do mesmo setor (excluindo o chefe)
    funcionarios_setor = Funcionario.objects.filter(
        sector=chefe.sector,
        ativo=True
    ).exclude(id=chefe.id)

    # Obter todas as licenças dos funcionários do setor
    licencas = Licenca.objects.filter(
        funcionario__in=funcionarios_setor
    ).select_related(
        'funcionario',
        'funcionario__sector',
        'chefe_aprovador',
        'diretor_aprovador'

    ).order_by('-data_inicio')

    # Filtros
    status_filter = request.GET.get('status')
    tipo_filter = request.GET.get('tipo')
    funcionario_filter = request.GET.get('funcionario')

    if status_filter:
        licencas = licencas.filter(status=status_filter)

    if tipo_filter:
        licencas = licencas.filter(tipo=tipo_filter)

    if funcionario_filter:
        licencas = licencas.filter(funcionario_id=funcionario_filter)

    # Estatísticas
    total_licencas = licencas.count()
    aguardando_chefe = licencas.filter(status='aguardando_chefe').count()
    aguardando_diretor = licencas.filter(status='aguardando_diretor').count()
    aprovadas = licencas.filter(status='aprovado').count()

    context = {
        'chefe': chefe,
        'licencas': licencas,
        'funcionarios_setor': funcionarios_setor,
        'status_filter': status_filter,
        'tipo_filter': tipo_filter,
        'funcionario_filter': funcionario_filter,
        'total_licencas': total_licencas,
        'aguardando_chefe': aguardando_chefe,
        'aguardando_diretor': aguardando_diretor,
        'aprovadas': aprovadas,
    }

    return render(request, 'recursoshumanos/licencas/licencas_setor.html', context)


@login_required
@director_required
def licencas_da_direcao(request):
    """Lista todas as licenças da direção do diretor"""
    director = get_object_or_404(Funcionario, user=request.user)

    # Verificar se é diretor
    if director.funcao != 'director':
        messages.error(request, "Apenas diretores podem acessar esta página.")
        return redirect('dashboard')

    # Obter o setor do diretor (assumindo que ele chefia este setor)
    direcao_alvo = director.sector

    # Definir setores da direção para uso nos filtros e resumo
    setores_direcao = Sector.objects.filter(
        Q(id=direcao_alvo.id) |
        Q(direcao=direcao_alvo) |
        Q(direcao__direcao=direcao_alvo)
    )

    # Buscar licenças do próprio setor, dos filhos e dos netos
    # Isso cobre:
    # 1. Diretor Geral (Sec 8) -> Vê Sec 2 (Filho) -> Vê Sec 9 (Neto)
    # 2. Diretor RH (Sec 2) -> Vê Sec 9 (Filho)
    # 3. Diretor Dept (Sec 9) -> Vê Sec 9 (Se houver diretores aqui)
    licencas = Licenca.objects.filter(
        Q(funcionario__sector=direcao_alvo) |
        Q(funcionario__sector__direcao=direcao_alvo) |
        Q(funcionario__sector__direcao__direcao=direcao_alvo)
    )

    # Apply common select_related and ordering
    licencas = licencas.select_related(
        'funcionario',
        'funcionario__sector',
        'chefe_aprovador',
        'diretor_aprovador'
    ).order_by('-data_inicio')

    # Filtros
    status_filter = request.GET.get('status')
    setor_filter = request.GET.get('setor')
    tipo_filter = request.GET.get('tipo')

    if status_filter:
        licencas = licencas.filter(status=status_filter)

    if setor_filter:
        licencas = licencas.filter(funcionario__sector_id=setor_filter)

    if tipo_filter:
        licencas = licencas.filter(tipo=tipo_filter)

    # Estatísticas
    total_licencas = licencas.count()
    aguardando_diretor = licencas.filter(status='aguardando_diretor').count()
    aprovadas_mes = licencas.filter(
        status='aprovado',
        data_parecer_diretor__month=date.today().month,
        data_parecer_diretor__year=date.today().year
    ).count()

    # Resumo por setor
    resumo_setores = []
    for setor in setores_direcao:
        licencas_setor = licencas.filter(funcionario__sector=setor)
        resumo_setores.append({
            'id': setor.id,
            'codigo': setor.codigo,
            'nome': setor.nome,
            'total': licencas_setor.count(),
            'aguardando': licencas_setor.filter(status='aguardando_diretor').count(),
        })

    context = {
        'director': director,
        'licencas': licencas,
        'setores_direcao': setores_direcao,
        'status_filter': status_filter,
        'setor_filter': setor_filter,
        'tipo_filter': tipo_filter,
        'total_licencas': total_licencas,
        'aguardando_diretor': aguardando_diretor,
        'aprovadas_mes': aprovadas_mes,
        'total_setores': setores_direcao.count(),
        'resumo_setores': resumo_setores,
    }

    return render(request, 'recursoshumanos/licencas/licencas_direcao.html', context)


@login_required
def minhas_licencas(request):
    """Licenças do funcionário logado com histórico completo"""
    # Admin pode ver todas as licenças, funcionário vê apenas as suas
    try:
        funcionario = Funcionario.objects.get(user=request.user)
        is_admin_view = False
    except Funcionario.DoesNotExist:
        if request.user.is_staff or request.user.is_superuser:
            funcionario = None
            is_admin_view = True
        else:
            from django.contrib import messages
            from django.shortcuts import redirect
            messages.error(request, "Você precisa de um perfil de funcionário para acessar esta página.")
            return redirect('recursoshumanos:dashboard')

    # Obter licenças (todas para admin, apenas do funcionário para usuário normal)
    if is_admin_view:
        licencas = Licenca.objects.all()
    else:
        licencas = Licenca.objects.filter(funcionario=funcionario)
    
    licencas = licencas.select_related(
        'chefe_aprovador',
        'diretor_aprovador',
        'funcionario__sector'
    ).order_by('-data_inicio')

    # Para cada licença, construir histórico completo
    for licenca in licencas:
        licenca.historico_completo = []

        # 1. Criação da licença
        licenca.historico_completo.append({
            'data': licenca.data_criacao or timezone.now(),
            'evento': 'Licença criada',
            'status': 'submetida',
            'detalhes': f'Solicitação de {licenca.get_tipo_display()} submetida',
            'responsavel': licenca.funcionario.nome_completo,
            'icon': 'fas fa-paper-plane'
        })

        # 2. Parecer do chefe (se existir)
        if licenca.parecer_chefe and licenca.data_parecer_chefe:
            licenca.historico_completo.append({
                'data': licenca.data_parecer_chefe,
                'evento': 'Parecer do Chefe',
                'status': licenca.status_chefia,
                'detalhes': f'{licenca.get_status_chefia_display()}' + (
                    f' - {licenca.parecer_chefe[:100]}...' if licenca.parecer_chefe else ''),
                'responsavel': licenca.chefe_aprovador.get_full_name() if licenca.chefe_aprovador else 'Chefe do Setor',
                'icon': 'fas fa-user-tie'
            })

        # 3. Parecer do diretor (se existir)
        if licenca.parecer_diretor and licenca.data_parecer_diretor:
            licenca.historico_completo.append({
                'data': licenca.data_parecer_diretor,
                'evento': 'Parecer do Diretor',
                'status': licenca.status,
                'detalhes': f'Status final: {licenca.get_status_display()}' + (
                    f' - {licenca.parecer_diretor[:100]}...' if licenca.parecer_diretor else ''),
                'responsavel': licenca.diretor_aprovador.get_full_name() if licenca.diretor_aprovador else 'Diretor',
                'icon': 'fas fa-user-tie'
            })

        # 4. Documento (Disponível sempre que aprovado)
        if licenca.status == 'aprovado' or licenca.documento_ferias:
            licenca.historico_completo.append({
                'data': licenca.data_parecer_diretor if licenca.data_parecer_diretor else licenca.data_atualizacao,
                'evento': 'Documento Oficial',
                'status': 'documento',
                'detalhes': 'Documento de férias disponível para download',
                'responsavel': 'Sistema',
                'icon': 'fas fa-file-pdf'
            })

        # Ordenar histórico por data (garantindo que data não seja None)
        licenca.historico_completo.sort(key=lambda x: x['data'] or timezone.now())

        # Calcular status atual para exibição
        if licenca.status == 'aguardando_chefe':
            licenca.status_atual = 'Aguardando parecer do chefe'
            licenca.status_cor = 'warning'
        elif licenca.status == 'aguardando_diretor':
            licenca.status_atual = 'Aguardando autorização do diretor'
            licenca.status_cor = 'info'
        elif licenca.status == 'aprovado':
            licenca.status_atual = 'Aprovada e autorizada'
            licenca.status_cor = 'success'
        elif licenca.status == 'rejeitado':
            licenca.status_atual = 'Rejeitada'
            licenca.status_cor = 'danger'
        else:
            licenca.status_atual = licenca.get_status_display()
            licenca.status_cor = 'secondary'

    # Filtros
    ano_filter = request.GET.get('ano')
    tipo_filter = request.GET.get('tipo')
    status_filter = request.GET.get('status')

    if ano_filter:
        licencas = licencas.filter(data_inicio__year=ano_filter)

    if tipo_filter:
        licencas = licencas.filter(tipo=tipo_filter)

    if status_filter:
        licencas = licencas.filter(status=status_filter)

    # Anos disponíveis para filtro
    if is_admin_view:
        anos = Licenca.objects.all().dates('data_inicio', 'year')
    else:
        anos = Licenca.objects.filter(funcionario=funcionario).dates('data_inicio', 'year')
    anos_disponiveis = [ano.year for ano in anos]

    context = {
        'licencas': licencas,
        'anos_disponiveis': sorted(set(anos_disponiveis), reverse=True),
        'ano_filter': ano_filter,
        'tipo_filter': tipo_filter,
        'status_filter': status_filter,
        'funcionario': funcionario,
        'is_admin_view': is_admin_view,
        'hoje': date.today(),
    }
    return render(request, 'recursoshumanos/licencas/minhas.html', context)


@login_required
def solicitar_licenca(request):
    """Solicitar nova licença"""
    funcionario = get_object_or_404(Funcionario, user=request.user)

    # Verificar saldo atual de férias se for férias
    saldo_atual = None
    if request.GET.get('tipo') == 'ferias' or request.method == 'GET':
        try:
            saldo_atual = SaldoFerias.objects.filter(
                funcionario=funcionario,
                ano=date.today().year
            ).first()

            # Se não existir saldo, criar com valores padrão
            if not saldo_atual:
                saldo_atual = SaldoFerias.objects.create(
                    funcionario=funcionario,
                    ano=date.today().year,
                    dias_disponiveis=22,
                    dias_gozados=0,
                    dias_saldo=22
                )
        except:
            saldo_atual = None

    if request.method == 'POST':
        form = LicencaForm(request.POST)
        if form.is_valid():
            try:
                licenca = form.save(commit=False)
                licenca.funcionario = funcionario
                licenca.status = 'pendente'  # Vai para análise do RH primeiro
                licenca.save()

                # Notificação automática para RH
                Notificador.licenca_submetida(licenca)

                messages.success(request, '✅ Licença solicitada com sucesso!')
                messages.info(request, '📋 Sua licença foi submetida para análise do Departamento de Recursos Humanos.')
                messages.info(request, '⏳ Você será notificado sobre o andamento do processo.')

                return redirect('recursoshumanos:minhas_licencas')

            except Exception as e:
                messages.error(request, f'❌ Erro ao criar licença: {str(e)}')
        else:
            messages.error(request, '❌ Por favor, corrija os erros no formulário.')
    else:
        # Formulário inicial com data padrão
        initial_data = {
            'data_inicio': date.today() + timedelta(days=7),
            'data_fim': date.today() + timedelta(days=21),
        }

        # Se veio com tipo específico
        tipo_licenca = request.GET.get('tipo')
        if tipo_licenca:
            initial_data['tipo'] = tipo_licenca

        form = LicencaForm(initial=initial_data)

    context = {
        'form': form,
        'funcionario': funcionario,
        'saldo_atual': saldo_atual,
        'hoje': date.today(),
        'tipos_licenca': Licenca.TIPO_CHOICES,
    }

    return render(request, 'recursoshumanos/licencas/solicitar.html', context)


@login_required
@chefe_required
def dar_parecer_licenca(request, licenca_id):
    """Chefe dá parecer sobre licença (após RH ter aprovado)"""
    licenca = get_object_or_404(Licenca, id=licenca_id)
    chefe = get_object_or_404(Funcionario, user=request.user)

    # Verificar se é chefe do funcionário
    if licenca.funcionario.sector != chefe.sector:
        messages.error(request, "Não tem permissão para dar parecer sobre este funcionário.")
        return redirect('recursoshumanos:dashboard')

    # Verificar se licença está no status correto (após RH)
    if licenca.status != 'aguardando_chefe':
        messages.warning(request,
                         f"Esta licença não está aguardando seu parecer. Status atual: {licenca.get_status_display()}")
        return redirect('recursoshumanos:dashboard')

    if request.method == 'POST':
        parecer = request.POST.get('parecer', '').strip()
        status_decisao = request.POST.get('status')  # 'favoravel' ou 'desfavoravel'

        if not parecer:
            messages.error(request, "O parecer não pode estar vazio.")
            return redirect('recursoshumanos:dar_parecer_licenca', licenca_id=licenca_id)

        # Atualizar licença
        licenca.parecer_chefe = parecer
        licenca.chefe_aprovador = request.user
        licenca.data_parecer_chefe = timezone.now()
        licenca.status_chefia = status_decisao

        if status_decisao == 'favoravel':
            licenca.status = 'aguardando_diretor'
            mensagem_status = 'aprovada pelo chefe, aguardando diretor'
        else:
            licenca.status = 'rejeitado'
            mensagem_status = 'rejeitada pelo chefe'

        licenca.save()

        # Notificação automática
        Notificador.licenca_parecer_chefe(licenca)

        messages.success(request, f'Parecer registrado! Licença {mensagem_status}.')
        return redirect('recursoshumanos:dashboard')

    # Mostrar análise do RH ao chefe
    context = {
        'licenca': licenca,
        'chefe': chefe,
        'mostrar_analise_rh': True,
    }
    return render(request, 'recursoshumanos/licencas/dar_parecer.html', context)


@login_required
@director_required
def autorizar_licenca(request, licenca_id):
    """Diretor autoriza ou reprova licença (após chefe)"""
    licenca = get_object_or_404(Licenca, id=licenca_id)
    director = get_object_or_404(Funcionario, user=request.user)

    # Verificar se o diretor tem jurisdição
    # Para Diretor Geral, ignoramos essa verificação estrita ou adaptamos
    if licenca.funcionario.sector.direcao != director.sector.direcao and not director.sector.direcao is None:
         # Se diretor tem pai (não é Geral) e direção não bate -> Erro
         # Mas se director.sector.direcao is None (Geral), ele pode autorizar tudo.
         pass
         # messages.error(request, "Não tem jurisdição sobre este setor.")
         # return redirect('recursoshumanos:dashboard')

    # Verificar se é diretor superior (se aplicável)
    if director.funcao != 'director':
        messages.error(request, "Apenas diretores podem autorizar licenças.")
        return redirect('recursoshumanos:dashboard')

    # Verificar se licença está no status correto (após chefe)
    if licenca.status != 'aguardando_diretor':
        messages.warning(request,
                         f"Esta licença não está aguardando autorização. Status atual: {licenca.get_status_display()}")
        return redirect('recursoshumanos:dashboard')

    if request.method == 'POST':
        parecer = request.POST.get('parecer', '').strip()
        acao = request.POST.get('acao')  # 'autorizar' ou 'reprovar'

        if not parecer and acao == 'autorizar':
            messages.error(request, "É necessário incluir um parecer para autorizar.")
            return redirect('recursoshumanos:autorizar_licenca', licenca_id=licenca_id)

        licenca.parecer_diretor = parecer
        licenca.diretor_aprovador = request.user
        licenca.data_parecer_diretor = timezone.now()

        if acao == 'autorizar':
            licenca.status = 'aprovado'

            # Atualizar saldo de férias se for férias
            if licenca.tipo == 'ferias':
                ano = licenca.data_inicio.year
                saldo, created = SaldoFerias.objects.get_or_create(
                    funcionario=licenca.funcionario,
                    ano=ano,
                    defaults={'dias_disponiveis': 22, 'dias_gozados': 0, 'dias_saldo': 22}
                )
                saldo.dias_gozados += licenca.dias_utilizados
                saldo.calcular_saldo()
                saldo.save()

            # Gerar documento de férias (opcional nesta fase, o modelo pede geração manual/link)
            # documento = gerar_documento_ferias(licenca)
            # if documento:
            #    licenca.documento_ferias = documento
            
            # --- GERAÇÃO AUTOMÁTICA DO PDF ---
            try:
                from .utils.pdf_generator import render_pdf_file
                
                # Nome do arquivo único
                filename = f"licenca_{licenca.id}_{timezone.now().strftime('%Y%m%d%H%M%S')}.pdf"
                
                # Contexto para o template
                pdf_context = {'licenca': licenca}
                
                # Gerar o arquivo PDF (bytes)
                pdf_content = render_pdf_file('recursoshumanos/documentos/ferias_anuais_pdf.html', pdf_context)
                
                if pdf_content:
                    from django.core.files.base import ContentFile
                    licenca.documento_ferias.save(filename, ContentFile(pdf_content), save=False)
            except Exception as e:
                print(f"Erro ao gerar PDF: {e}")
                # Não interromper o fluxo se falhar o PDF
            # ---------------------------------

            # Notificação automática
            Notificador.licenca_autorizada(licenca)
            messages.success(request, 'Licença autorizada com sucesso!')

        elif acao == 'reprovar':
            licenca.status = 'rejeitado'
            messages.warning(request, 'Licença reprovada!')

        licenca.save()
        return redirect('recursoshumanos:dashboard')

    # Mostrar histórico completo ao diretor
    context = {
        'licenca': licenca,
        'director': director,
        'mostrar_analise_rh': True,
        'mostrar_parecer_chefe': True,
    }
    return render(request, 'recursoshumanos/licencas/autorizar.html', context)




@login_required
@rh_required
def relatorio_licencas(request):
    """Relatório de licenças (apenas RH)"""
    licencas = Licenca.objects.select_related('funcionario').order_by('-data_inicio')

    # Filtros
    ano = request.GET.get('ano', date.today().year)
    setor_filter = request.GET.get('setor')
    tipo_filter = request.GET.get('tipo')
    status_filter = request.GET.get('status')

    if ano:
        licencas = licencas.filter(data_inicio__year=ano)

    if setor_filter:
        licencas = licencas.filter(funcionario__sector_id=setor_filter)

    if tipo_filter:
        licencas = licencas.filter(tipo=tipo_filter)

    if status_filter:
        licencas = licencas.filter(status=status_filter)

    # Estatísticas
    total_licencas = licencas.count()
    total_dias = licencas.aggregate(total=Sum('dias_utilizados'))['total'] or 0
    licencas_aprovadas = licencas.filter(status='aprovado').count()

    # Anos disponíveis
    anos = Licenca.objects.dates('data_inicio', 'year')
    anos_disponiveis = sorted(set([ano.year for ano in anos]), reverse=True)

    context = {
        'licencas': licencas,
        'ano': int(ano) if ano else date.today().year,
        'anos_disponiveis': anos_disponiveis,
        'setor_filter': setor_filter,
        'tipo_filter': tipo_filter,
        'status_filter': status_filter,
        'sectores': Sector.objects.all(),
        'total_licencas': total_licencas,
        'total_dias': total_dias,
        'licencas_aprovadas': licencas_aprovadas,
    }
    return render(request, 'recursoshumanos/relatorios/licencas.html', context)


def gerar_documento_ferias(licenca):
    """Gera documento de férias em PDF"""
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from io import BytesIO
    from django.core.files import File

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Estilo personalizado
    estilo_titulo = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=1,
        spaceAfter=30
    )

    # Título
    elements.append(Paragraph('AUTORIZAÇÃO DE GOZO DE FÉRIAS', estilo_titulo))
    elements.append(Spacer(1, 20))

    # Dados do funcionário
    dados_funcionario = [
        ['Nome:', licenca.funcionario.nome_completo],
        ['Número de Identificação:', licenca.funcionario.numero_identificacao],
        ['Setor:', f"{licenca.funcionario.sector.codigo}"],
        ['Função:', licenca.funcionario.get_funcao_display()],
        ['Período:', f"{licenca.data_inicio.strftime('%d/%m/%Y')} a {licenca.data_fim.strftime('%d/%m/%Y')}"],
        ['Dias:', str(licenca.dias_utilizados)],
    ]

    tabela_dados = Table(dados_funcionario, colWidths=[150, 300])
    tabela_dados.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(tabela_dados)
    elements.append(Spacer(1, 30))

    # Pareceres
    if licenca.parecer_chefe:
        elements.append(Paragraph('<b>PARECER DO CHEFE IMEDIATO:</b>', styles['Heading3']))
        elements.append(Paragraph(licenca.parecer_chefe, styles['Normal']))
        elements.append(Spacer(1, 10))

    if licenca.parecer_diretor:
        elements.append(Paragraph('<b>PARECER DO DIRETOR:</b>', styles['Heading3']))
        elements.append(Paragraph(licenca.parecer_diretor, styles['Normal']))
        elements.append(Spacer(1, 20))

    # Assinaturas
    elementos_assinatura = [
        ['', ''],
        ['___________________________________', '___________________________________'],
        ['Assinatura do Funcionário', 'Assinatura do Diretor'],
        ['', ''],
        [f"Data: {date.today().strftime('%d/%m/%Y')}", f"Carimbo e Assinatura"]
    ]

    tabela_assinatura = Table(elementos_assinatura, colWidths=[250, 250])
    tabela_assinatura.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    elements.append(tabela_assinatura)

    # Gerar PDF
    doc.build(elements)

    # Salvar arquivo
    from django.core.files.base import ContentFile
    filename = f"ferias_{licenca.funcionario.numero_identificacao}_{date.today().strftime('%Y%m%d')}.pdf"

    licenca.documento_ferias.save(filename, ContentFile(buffer.getvalue()))
    return licenca.documento_ferias


# ========== AVALIAÇÕES ==========

@login_required
def minhas_avaliacoes(request):
    """Avaliações do funcionário"""
    try:
        funcionario = Funcionario.objects.get(user=request.user)
    except Funcionario.DoesNotExist:
        messages.error(request, "Seu usuário não está vinculado a um perfil de Funcionário. Entre em contato com o RH.")
        return redirect('recursoshumanos:dashboard')

    avaliacoes = AvaliacaoDesempenho.objects.filter(
        funcionario=funcionario
    ).order_by('-data_avaliacao')

    # Estatísticas
    if avaliacoes:
        ultima_avaliacao = avaliacoes.first()
        media_historica = avaliacoes.aggregate(avg=Avg('nota_final_geral'))['avg'] or 0
    else:
        ultima_avaliacao = None
        media_historica = 0

    context = {
        'funcionario': funcionario,
        'avaliacoes': avaliacoes,
        'ultima_avaliacao': ultima_avaliacao,
        'media_historica': round(media_historica, 2),
        'total_avaliacoes': avaliacoes.count(),
    }
    return render(request, 'recursoshumanos/avaliacoes/minhas.html', context)


@login_required
def avaliacoes_realizadas(request):
    """Lista avaliações feitas pelo usuário logado (Chefe/Director)"""
    avaliacoes = request.user.avaliacoes_realizadas.select_related('funcionario').order_by('-data_avaliacao')
    
    context = {
        'avaliacoes': avaliacoes
    }
    return render(request, 'recursoshumanos/avaliacoes/realizadas.html', context)


@login_required
@require_POST
def apagar_avaliacao(request, avaliacao_id):
    """Apagar uma avaliação realizada pelo usuário"""
    avaliacao = get_object_or_404(AvaliacaoDesempenho, id=avaliacao_id)
    
    # Verificar permissão (apenas o autor pode apagar)
    if avaliacao.avaliado_por != request.user and not request.user.is_superuser:
        messages.error(request, "Você não tem permissão para apagar esta avaliação.")
    else:
        avaliacao.delete()
        messages.success(request, "Avaliação removida com sucesso.")
        
    return redirect('recursoshumanos:avaliacoes_realizadas')


@login_required
def avaliar_funcionario(request, funcionario_id):
    """Avaliar funcionário"""
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
    avaliador = Funcionario.objects.filter(user=request.user).first()

    # Verificar permissões
    pode_avaliar = False

    if request.user.is_staff or request.user.groups.filter(name='rh_staff').exists():
        pode_avaliar = True

    elif avaliador and avaliador.funcao == 'director':
        if funcionario.sector.direcao == avaliador.sector.direcao:
            pode_avaliar = True

    elif avaliador and avaliador.funcao in ['chefe', 'coordenador']:
        if funcionario.sector == avaliador.sector and funcionario.id != avaliador.id:
            pode_avaliar = True

    if not pode_avaliar:
        messages.error(request, "Não tem permissão para avaliar este funcionário.")
        return redirect('dashboard')

    competencias = Competencia.objects.filter(ativo=True)

    if request.method == 'POST':
        try:
            total_pontos = 0
            competencias_avaliadas = []

            for competencia in competencias:
                campo_nome = f'competencia_{competencia.id}'
                pontuacao = int(request.POST.get(campo_nome, 0))

                if pontuacao < 0 or pontuacao > 5:
                    messages.error(request, f"Pontuação inválida para {competencia.nome}.")
                    return redirect('recursoshumanos:avaliar_funcionario', funcionario_id=funcionario_id)

                total_pontos += pontuacao
                competencias_avaliadas.append({
                    'competencia': competencia,
                    'pontuacao': pontuacao
                })

            # Calcular nota final
            nota_final = total_pontos / len(competencias) if competencias else 0

            # Determinar classificação
            if nota_final >= 4.5:
                classificacao = 'Excelente'
            elif nota_final >= 3.5:
                classificacao = 'Bom'
            elif nota_final >= 2.5:
                classificacao = 'Satisfatório'
            elif nota_final >= 1.5:
                classificacao = 'Regular'
            else:
                classificacao = 'Insuficiente'

            # Criar avaliação
            avaliacao = AvaliacaoDesempenho.objects.create(
                funcionario=funcionario,
                avaliado_por=request.user,
                periodo=request.POST.get('periodo', str(date.today().year)),
                observacoes=request.POST.get('observacoes', ''),
                nota_final_geral=round(nota_final, 2),
                classificacao_final=classificacao,
                status='concluido'
            )

            # Salvar competências
            for item in competencias_avaliadas:
                CompetenciaAvaliada.objects.create(
                    avaliacao=avaliacao,
                    competencia=item['competencia'],
                    pontuacao=item['pontuacao']
                )

            # Notificação automática
            Notificador.avaliacao_realizada(avaliacao)

            messages.success(request, f'Avaliação registrada com sucesso!')
            return redirect('recursoshumanos:dashboard')

        except Exception as e:
            messages.error(request, f'Erro ao processar avaliação: {str(e)}')
            return redirect('recursoshumanos:avaliar_funcionario', funcionario_id=funcionario_id)

    context = {
        'funcionario': funcionario,
        'competencias': competencias,
        'competencias_ids': list(competencias.values_list('id', flat=True)),
        'avaliador': avaliador,
    }
    return render(request, 'recursoshumanos/avaliacoes/avaliar.html', context)


@login_required
@rh_required
def relatorio_avaliacoes(request):
    """Relatório de avaliações"""
    avaliacoes = AvaliacaoDesempenho.objects.select_related('funcionario').order_by('-data_avaliacao')

    # Filtros
    ano = request.GET.get('ano', date.today().year)
    setor_filter = request.GET.get('setor')
    classificacao_filter = request.GET.get('classificacao')

    if ano:
        avaliacoes = avaliacoes.filter(data_avaliacao__year=ano)

    if setor_filter:
        avaliacoes = avaliacoes.filter(funcionario__sector_id=setor_filter)

    if classificacao_filter:
        avaliacoes = avaliacoes.filter(classificacao_final=classificacao_filter)

    # Estatísticas
    total_avaliacoes = avaliacoes.count()
    media_geral = avaliacoes.aggregate(avg=Avg('nota_final_geral'))['avg'] or 0
    melhor_nota = avaliacoes.aggregate(max=Max('nota_final_geral'))['max'] or 0

    # Anos disponíveis
    anos = AvaliacaoDesempenho.objects.dates('data_avaliacao', 'year')
    anos_disponiveis = sorted(set([ano.year for ano in anos]), reverse=True)

    context = {
        'avaliacoes': avaliacoes,
        'ano': int(ano) if ano else date.today().year,
        'anos_disponiveis': anos_disponiveis,
        'setor_filter': setor_filter,
        'classificacao_filter': classificacao_filter,
        'sectores': Sector.objects.all(),
        'total_avaliacoes': total_avaliacoes,
        'media_geral': round(media_geral, 2),
        'melhor_nota': round(melhor_nota, 2),
    }
    return render(request, 'recursoshumanos/relatorios/avaliacoes.html', context)


# ========== SISTEMA DE PRESENÇA ==========

@login_required
def scanner_presenca(request):
    """Interface para scanner de QR Code"""
    if request.method == 'POST':
        qr_data = request.POST.get('qr_data')
        tipo = request.POST.get('tipo', 'entrada')

        try:
            partes = qr_data.split('|')
            if len(partes) >= 3 and partes[0] == 'STAE':
                funcionario_id = partes[1]
                funcionario = Funcionario.objects.get(id=funcionario_id)

                # Registrar presença
                RegistroPresenca.objects.create(
                    funcionario=funcionario,
                    tipo=tipo,
                    metodo='qr_code',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    observacoes=f"Registro via QR code - {tipo}"
                )

                return JsonResponse({
                    'success': True,
                    'funcionario': funcionario.nome_completo,
                    'hora': timezone.now().strftime('%H:%M')
                })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return render(request, 'recursoshumanos/presenca/scanner.html')


@login_required
@rh_required
def gerar_cartao_funcionario(request, funcionario_id):
    """Gerar cartão PVC em PDF com o mesmo layout do preview"""
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)

    # Gerar QR code se não existir
    if not funcionario.qr_code:
        funcionario.gerar_qr_code()

    # Configurar resposta PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="cartao_{funcionario.numero_identificacao}.pdf"'

    # Tamanho do cartão (CR-80 padrão)
    width = 85.6 * mm
    height = 54 * mm

    # Criar PDF
    p = canvas.Canvas(response, pagesize=(width, height))

    # ========== FUNDO COM GRADIENTE ==========
    # Gradiente azul (igual ao CSS)
    p.setFillColor(colors.HexColor('#1a4a72'))  # Cor principal
    p.rect(0, 0, width, height, fill=True)

    # ========== LOGO STAE (canto superior direito) ==========
    p.setFont("Helvetica-Bold", 8)
    p.setFillColor(colors.white)
    p.drawRightString(width - 5 * mm, height - 5 * mm, "STAE")

    # ========== FOTO DO FUNCIONÁRIO ==========
    foto_x = 5 * mm
    foto_y = 15 * mm
    foto_width = 25 * mm
    foto_height = 35 * mm

    if funcionario.foto:
        try:
            # Desenhar moldura branca
            p.setStrokeColor(colors.white)
            p.setLineWidth(0.5)
            p.rect(foto_x, foto_y, foto_width, foto_height, fill=False, stroke=True)

            # Foto
            p.drawImage(
                funcionario.foto.path,
                foto_x + 1 * mm,  # Margem interna
                foto_y + 1 * mm,  # Margem interna
                width=foto_width - 2 * mm,
                height=foto_height - 2 * mm,
                preserveAspectRatio=True,
                mask='auto'
            )
        except:
            # Placeholder se foto não carregar
            p.setFillColor(colors.HexColor('#2c3e50'))
            p.rect(foto_x + 1 * mm, foto_y + 1 * mm, foto_width - 2 * mm, foto_height - 2 * mm, fill=True)

            p.setFont("Helvetica", 6)
            p.setFillColor(colors.white)
            p.drawCentredString(
                foto_x + foto_width / 2,
                foto_y + foto_height / 2,
                "SEM FOTO"
            )
    else:
        # Placeholder se não tiver foto
        p.setFillColor(colors.HexColor('#2c3e50'))
        p.rect(foto_x + 1 * mm, foto_y + 1 * mm, foto_width - 2 * mm, foto_height - 2 * mm, fill=True)

        p.setFont("Helvetica", 6)
        p.setFillColor(colors.white)
        p.drawCentredString(
            foto_x + foto_width / 2,
            foto_y + foto_height / 2,
            "SEM FOTO"
        )

    # ========== QR CODE ==========
    qr_x = width - 30 * mm
    qr_y = 15 * mm
    qr_size = 25 * mm

    if funcionario.qr_code:
        try:
            # Moldura branca
            p.setStrokeColor(colors.white)
            p.setLineWidth(0.5)
            p.rect(qr_x, qr_y, qr_size, qr_size, fill=False, stroke=True)

            # QR Code
            p.drawImage(
                funcionario.qr_code.path,
                qr_x + 1 * mm,
                qr_y + 1 * mm,
                width=qr_size - 2 * mm,
                height=qr_size - 2 * mm,
                preserveAspectRatio=True,
                mask='auto'
            )
        except:
            # Placeholder para QR
            p.setFillColor(colors.white)
            p.rect(qr_x + 1 * mm, qr_y + 1 * mm, qr_size - 2 * mm, qr_size - 2 * mm, fill=True)

            p.setFont("Helvetica-Bold", 10)
            p.setFillColor(colors.HexColor('#1a4a72'))
            p.drawCentredString(
                qr_x + qr_size / 2,
                qr_y + qr_size / 2 + 2 * mm,
                "QR"
            )
            p.drawCentredString(
                qr_x + qr_size / 2,
                qr_y + qr_size / 2 - 2 * mm,
                "CODE"
            )

    # ========== INFORMAÇÕES DO FUNCIONÁRIO ==========
    info_x = foto_x + foto_width + 3 * mm
    info_y = height - 15 * mm
    linha_altura = 4 * mm

    # Nome
    p.setFont("Helvetica-Bold", 7)
    p.setFillColor(colors.white)
    p.drawString(info_x, info_y, "NOME:")
    p.setFont("Helvetica-Bold", 8)
    nome = funcionario.nome_completo
    if len(nome) > 25:
        nome = nome[:25] + "..."
    p.drawString(info_x + 12 * mm, info_y, nome)

    # Número de Funcionário
    info_y -= linha_altura
    p.setFont("Helvetica-Bold", 7)
    p.setFillColor(colors.white)
    p.drawString(info_x, info_y, "Nº FUNC.:")
    p.setFont("Helvetica", 7)
    p.drawString(info_x + 12 * mm, info_y, funcionario.numero_identificacao)

    # NUIT
    info_y -= linha_altura
    p.setFont("Helvetica-Bold", 7)
    p.drawString(info_x, info_y, "NUIT:")
    p.setFont("Helvetica", 7)
    nuit = funcionario.nuit or "N/D"
    p.drawString(info_x + 12 * mm, info_y, nuit)

    # Setor
    info_y -= linha_altura
    p.setFont("Helvetica-Bold", 7)
    p.drawString(info_x, info_y, "SETOR:")
    p.setFont("Helvetica", 7)
    setor = str(funcionario.sector.codigo) if funcionario.sector else "N/D"
    p.drawString(info_x + 12 * mm, info_y, setor)

    # Função
    info_y -= linha_altura
    p.setFont("Helvetica-Bold", 7)
    p.drawString(info_x, info_y, "FUNÇÃO:")
    p.setFont("Helvetica", 7)
    funcao = funcionario.get_funcao_display() or "N/D"
    if len(funcao) > 15:
        funcao = funcao[:15] + "..."
    p.drawString(info_x + 12 * mm, info_y, funcao)

    # Data de Admissão
    info_y -= linha_altura
    p.setFont("Helvetica-Bold", 7)
    p.drawString(info_x, info_y, "ADMISSÃO:")
    p.setFont("Helvetica", 7)
    if funcionario.data_admissao:
        data_str = funcionario.data_admissao.strftime("%d/%m/%Y")
    else:
        data_str = "N/D"
    p.drawString(info_x + 12 * mm, info_y, data_str)

    # ========== RODAPÉ ==========
    rodape_y = 5 * mm

    # Linha separadora
    p.setStrokeColor(colors.HexColor('#FFFFFF'))
    p.setLineWidth(0.3)
    p.line(10 * mm, rodape_y + 3 * mm, width - 10 * mm, rodape_y + 3 * mm)

    # Texto do rodapé
    p.setFont("Helvetica", 5)
    p.setFillColor(colors.HexColor('#CCCCCC'))
    p.drawCentredString(width / 2, rodape_y + 1 * mm, "CARTÃO DE IDENTIFICAÇÃO STAE")

    # Validade (2 anos a partir de hoje)
    hoje = timezone.now().date()
    validade = hoje.replace(year=hoje.year + 2)
    p.setFont("Helvetica", 4)
    p.drawCentredString(width / 2, rodape_y - 1 * mm, f"Válido até: {validade.strftime('%d/%m/%Y')}")

    # ========== BORDA DE SEGURANÇA ==========
    p.setStrokeColor(colors.HexColor('#FFFFFF'))
    p.setLineWidth(0.2)
    p.rect(1 * mm, 1 * mm, width - 2 * mm, height - 2 * mm, fill=False, stroke=True)

    # ========== FINALIZAR PDF ==========
    p.showPage()
    p.save()

    return response


from django.template.loader import render_to_string
from xhtml2pdf import pisa
from io import BytesIO


@login_required
@rh_required
def gerar_cartao_html_pdf(request, funcionario_id):
    """Gerar cartão PVC em PDF - VERSÃO SIMPLIFICADA"""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm

    funcionario = get_object_or_404(Funcionario, id=funcionario_id)

    if not funcionario.qr_code:
        funcionario.gerar_qr_code()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="cartao_{funcionario.numero_identificacao}.pdf"'

    # Tamanho do cartão CR-80
    width = 85.6 * mm
    height = 54 * mm

    p = canvas.Canvas(response, pagesize=(width, height))

    # FUNDO AZUL
    p.setFillColor(colors.HexColor('#1a4a72'))
    p.rect(0, 0, width, height, fill=True)

    # CABEÇALHO
    p.setFont("Helvetica-Bold", 6.5)  # Reduzido para caber
    p.setFillColor(colors.white)
    p.drawCentredString(width / 2, height - 4 * mm,
                        "STAE - SECRETARIADO TÉCNICO DE ADMINISTRAÇÃO ELEITORAL")

    # FOTO (CENTRALIZADA VERTICALMENTE)
    foto_w = 25 * mm
    foto_h = 35 * mm
    foto_x = 5 * mm
    foto_y = (height - foto_h) / 2  # Centralizada

    if funcionario.foto:
        try:
            # Moldura branca
            p.setStrokeColor(colors.white)
            p.setLineWidth(0.5)
            p.rect(foto_x, foto_y, foto_w, foto_h, fill=False, stroke=True)

            # Foto com margem interna
            p.drawImage(funcionario.foto.path,
                        foto_x + 1 * mm,
                        foto_y + 1 * mm,
                        width=foto_w - 2 * mm,
                        height=foto_h - 2 * mm,
                        preserveAspectRatio=True,
                        mask='auto')
        except:
            # Placeholder se falhar
            p.setFillColor(colors.HexColor('#2c3e50'))
            p.rect(foto_x + 1 * mm, foto_y + 1 * mm, foto_w - 2 * mm, foto_h - 2 * mm, fill=True)
            p.setFillColor(colors.white)
            p.setFont("Helvetica", 6)
            p.drawCentredString(foto_x + foto_w / 2, foto_y + foto_h / 2, "SEM FOTO")
    else:
        # Placeholder se não tiver foto
        p.setFillColor(colors.HexColor('#2c3e50'))
        p.rect(foto_x + 1 * mm, foto_y + 1 * mm, foto_w - 2 * mm, foto_h - 2 * mm, fill=True)
        p.setFillColor(colors.white)
        p.setFont("Helvetica", 6)
        p.drawCentredString(foto_x + foto_w / 2, foto_y + foto_h / 2, "SEM FOTO")

    # QR CODE PEQUENO (inferior direito)
    qr_size = 15 * mm
    qr_x = width - qr_size - 5 * mm  # 5mm da borda direita
    qr_y = 5 * mm  # 5mm da borda inferior

    if funcionario.qr_code:
        try:
            # Moldura branca
            p.setStrokeColor(colors.white)
            p.setLineWidth(0.3)
            p.rect(qr_x, qr_y, qr_size, qr_size, fill=False, stroke=True)

            # QR Code
            p.drawImage(funcionario.qr_code.path,
                        qr_x + 0.5 * mm,
                        qr_y + 0.5 * mm,
                        width=qr_size - 1 * mm,
                        height=qr_size - 1 * mm,
                        preserveAspectRatio=True)
        except:
            # Placeholder QR
            p.setFillColor(colors.white)
            p.rect(qr_x + 0.5 * mm, qr_y + 0.5 * mm, qr_size - 1 * mm, qr_size - 1 * mm, fill=True)
            p.setFillColor(colors.HexColor('#1a4a72'))
            p.setFont("Helvetica-Bold", 5)
            p.drawCentredString(qr_x + qr_size / 2, qr_y + qr_size / 2 + 1 * mm, "QR")
            p.drawCentredString(qr_x + qr_size / 2, qr_y + qr_size / 2 - 1 * mm, "CODE")

    # INFORMAÇÕES (alinhadas com a foto)
    info_x = foto_x + foto_w + 3 * mm
    info_y = foto_y + foto_h - 4 * mm  # Começa no topo da foto
    linha_altura = 4 * mm

    # NOME
    p.setFont("Helvetica-Bold", 8)
    p.setFillColor(colors.white)
    p.drawString(info_x, info_y, "NOME:")
    p.setFont("Helvetica", 8)
    nome = funcionario.nome_completo
    if len(nome) > 25: nome = nome[:25] + "..."
    p.drawString(info_x + 12 * mm, info_y, nome)

    # Número
    info_y -= linha_altura
    p.setFont("Helvetica-Bold", 7)
    p.drawString(info_x, info_y, "Nº FUNC.:")
    p.setFont("Helvetica", 7)
    p.drawString(info_x + 12 * mm, info_y, funcionario.numero_identificacao)

    # NUIT
    info_y -= linha_altura
    p.setFont("Helvetica-Bold", 7)
    p.drawString(info_x, info_y, "NUIT:")
    p.setFont("Helvetica", 7)
    nuit = funcionario.nuit or "N/D"
    p.drawString(info_x + 12 * mm, info_y, nuit)

    # SECTOR
    info_y -= linha_altura
    p.setFont("Helvetica-Bold", 7)
    p.drawString(info_x, info_y, "SECTOR:")
    p.setFont("Helvetica", 7)
    setor_nome = funcionario.sector.nome if funcionario.sector else "N/D"
    if len(setor_nome) > 20: setor_nome = setor_nome[:20] + "..."
    p.drawString(info_x + 12 * mm, info_y, setor_nome)

    # FUNÇÃO
    info_y -= linha_altura
    p.setFont("Helvetica-Bold", 7)
    p.drawString(info_x, info_y, "FUNÇÃO:")
    p.setFont("Helvetica", 7)
    funcao = funcionario.get_funcao_display() or "N/D"
    if len(funcao) > 18: funcao = funcao[:18] + "..."
    p.drawString(info_x + 12 * mm, info_y, funcao)

    # ADMISSÃO
    info_y -= linha_altura
    p.setFont("Helvetica-Bold", 7)
    p.drawString(info_x, info_y, "ADMISSÃO:")
    p.setFont("Helvetica", 7)
    data = funcionario.data_admissao.strftime("%d/%m/%Y") if funcionario.data_admissao else "N/D"
    p.drawString(info_x + 12 * mm, info_y, data)

    # RODAPÉ
    rodape_y = 3 * mm
    p.setStrokeColor(colors.HexColor('#FFFFFF'))
    p.setLineWidth(0.2)
    p.line(10 * mm, rodape_y + 2 * mm, width - 10 * mm, rodape_y + 2 * mm)

    p.setFont("Helvetica", 4.5)
    p.setFillColor(colors.HexColor('#CCCCCC'))
    p.drawCentredString(width / 2, rodape_y + 0.5 * mm, "CARTÃO DE IDENTIFICAÇÃO")

    validade = timezone.now().date() + timedelta(days=365 * 2)
    p.setFont("Helvetica", 4)
    p.drawCentredString(width / 2, rodape_y - 1.5 * mm, f"Válido até: {validade.strftime('%d/%m/%Y')}")

    # BORDA DE SEGURANÇA
    p.setStrokeColor(colors.HexColor('#FFFFFF'))
    p.setLineWidth(0.2)
    p.rect(1 * mm, 1 * mm, width - 2 * mm, height - 2 * mm, fill=False, stroke=True)

    p.showPage()
    p.save()

    return response



@login_required
@rh_required
def relatorio_presencas(request):
    """Relatório de presenças"""
    registros = RegistroPresenca.objects.select_related('funcionario')

    # Filtros
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    setor_filter = request.GET.get('setor')

    if data_inicio:
        registros = registros.filter(data_hora__date__gte=data_inicio)
    if data_fim:
        registros = registros.filter(data_hora__date__lte=data_fim)
    if setor_filter:
        registros = registros.filter(funcionario__sector_id=setor_filter)

    # Agrupar por funcionário
    funcionarios_data = {}
    for registro in registros:
        func_id = registro.funcionario.id
        if func_id not in funcionarios_data:
            funcionarios_data[func_id] = {
                'funcionario': registro.funcionario,
                'registros': [],
                'total_dias': 0
            }
        funcionarios_data[func_id]['registros'].append(registro)

    context = {
        'funcionarios_data': funcionarios_data.values(),
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'sectores': Sector.objects.all(),
    }
    return render(request, 'recursoshumanos/relatorios/presencas.html', context)


@login_required
@rh_required
def folha_efetividade(request):
    """Gerar folha de efetividade em PDF"""
    if request.method == 'POST':
        setor_id = request.POST.get('setor')
        mes = int(request.POST.get('mes', date.today().month))
        ano = int(request.POST.get('ano', date.today().year))

        setor = get_object_or_404(Sector, id=setor_id) if setor_id else None
        funcionarios = Funcionario.objects.filter(ativo=True)

        if setor:
            funcionarios = funcionarios.filter(sector=setor)

        # Calcular dias do mês
        ultimo_dia = calendar.monthrange(ano, mes)[1]
        dias_mes = range(1, ultimo_dia + 1)

        # Obter licenças do mês
        licencas_mes = Licenca.objects.filter(
            data_inicio__month=mes,
            data_inicio__year=ano,
            status='aprovado'
        ).select_related('funcionario')

        # Mapear dias de licença
        dias_licenca = {}
        for licenca in licencas_mes:
            dias = [(licenca.data_inicio + timedelta(days=x)).day
                    for x in range((licenca.data_fim - licenca.data_inicio).days + 1)
                    if (licenca.data_inicio + timedelta(days=x)).month == mes]

            if licenca.funcionario.id not in dias_licenca:
                dias_licenca[licenca.funcionario.id] = []
            dias_licenca[licenca.funcionario.id].extend(dias)

        # Gerar PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="folha_efetividade_{mes}_{ano}.pdf"'

        p = canvas.Canvas(response, pagesize=A4)
        width, height = A4

        # Cabeçalho
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, height - 50, f"FOLHA DE EFETIVIDADE - {mes}/{ano}")
        if setor:
            p.setFont("Helvetica", 12)
            p.drawString(50, height - 70, f"Setor: {setor.codigo} - {setor.nome}")

        # Tabela
        y_pos = height - 100
        linha_altura = 20
        coluna_largura = (width - 100) / (len(dias_mes) + 2)

        # Cabeçalhos
        p.setFont("Helvetica-Bold", 8)
        p.drawString(50, y_pos, "FUNCIONÁRIO")
        for i, dia in enumerate(dias_mes):
            x_pos = 50 + coluna_largura * (i + 1)
            p.drawString(x_pos + 5, y_pos, str(dia))
        p.drawString(50 + coluna_largura * (len(dias_mes) + 1), y_pos, "ASS.")

        y_pos -= linha_altura

        # Linhas para cada funcionário
        p.setFont("Helvetica", 8)
        for funcionario in funcionarios:
            if y_pos < 100:
                p.showPage()
                y_pos = height - 50
                p.setFont("Helvetica", 8)

            p.drawString(50, y_pos, funcionario.nome_completo[:20])

            for i, dia in enumerate(dias_mes):
                x_pos = 50 + coluna_largura * (i + 1)

                if funcionario.id in dias_licenca and dia in dias_licenca[funcionario.id]:
                    p.setFillColor(colors.black)
                    p.rect(x_pos, y_pos - 15, coluna_largura - 2, linha_altura - 5, fill=True)
                else:
                    p.setFillColor(colors.white)
                    p.rect(x_pos, y_pos - 15, coluna_largura - 2, linha_altura - 5, fill=True, stroke=True)

            x_pos = 50 + coluna_largura * (len(dias_mes) + 1)
            p.rect(x_pos, y_pos - 15, coluna_largura - 2, linha_altura - 5, fill=False, stroke=True)

            y_pos -= linha_altura

        p.showPage()
        p.save()

        return response

    sectores = Sector.objects.all()
    return render(request, 'recursoshumanos/relatorios/folha_efetividade.html', {'sectores': sectores})


# ========== SISTEMA DE COMUNICAÇÃO INTERNA ==========

# recursoshumanos/views.py - adicione esta função
@login_required
def criar_canal(request):
    """Criar novo canal de comunicação"""
    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        tipo = request.POST.get('tipo', 'grupo')
        enviar_para_todos = request.POST.get('enviar_para_todos') == 'on'

        if not nome:
            messages.error(request, "O nome do canal é obrigatório.")
            return redirect('criar_canal')

        # Criar canal
        canal = CanalComunicacao.objects.create(
            nome=nome,
            descricao=descricao,
            tipo=tipo,
            criado_por=request.user,
            enviar_para_todos=enviar_para_todos
        )

        # Adicionar membros
        membros_ids = request.POST.getlist('membros')
        if membros_ids:
            usuarios = User.objects.filter(id__in=membros_ids)
            canal.membros.set(usuarios)

        # Adicionar criador como membro
        canal.membros.add(request.user)

        messages.success(request, f'Canal "{nome}" criado com sucesso!')
        return redirect('canal_chat', canal_id=canal.id)

    # Listar usuários disponíveis
    usuarios = User.objects.filter(is_active=True).exclude(id=request.user.id)

    context = {
        'usuarios': usuarios,
        'tipos_canal': CanalComunicacao.TIPO_CHOICES,
    }
    return render(request, 'recursoshumanos/comunicacao/criar_canal.html', context)


# recursoshumanos/views.py - adicione esta função
# recursoshumanos/views.py - atualize a função
@login_required
def lista_usuarios_chat(request):
    """Lista todos os usuários para conversas diretas"""
    usuario_atual = request.user

    # Buscar usuários ativos exceto o atual
    usuarios = User.objects.filter(is_active=True).exclude(id=usuario_atual.id)

    # Carregar conversas diretas existentes
    conversas_diretas = CanalComunicacao.objects.filter(
        tipo='direto',  # ← FILTRE POR 'tipo' EM VEZ DE 'eh_conversa_direta'
        membros=usuario_atual
    ).prefetch_related('membros')

    # Contar conversas diretas para estatísticas
    conversas_diretas_count = conversas_diretas.count()

    # Canais de grupo (não diretos)
    canais_grupo_count = usuario_atual.canais_participantes.exclude(tipo='direto').count()

    # Mapear conversas por usuário
    conversas_por_usuario = {}
    for conversa in conversas_diretas:
        outro_usuario = conversa.membros.exclude(id=usuario_atual.id).first()
        if outro_usuario:
            conversas_por_usuario[outro_usuario.id] = conversa

    # Adicionar informações de funcionário
    usuarios_com_info = []
    for usuario in usuarios:
        # Buscar funcionário relacionado
        try:
            funcionario = usuario.funcionario
            nome_completo = funcionario.nome_completo
            setor = funcionario.sector.nome if funcionario.sector else "Sem setor"
            foto = funcionario.foto.url if funcionario.foto else None
        except:
            nome_completo = usuario.get_full_name() or usuario.username
            setor = "Sem informações"
            foto = None

        # Verificar se já tem conversa
        tem_conversa = usuario.id in conversas_por_usuario
        canal_id = conversas_por_usuario[usuario.id].id if tem_conversa else None

        usuarios_com_info.append({
            'id': usuario.id,
            'username': usuario.username,
            'nome_completo': nome_completo,
            'email': usuario.email,
            'setor': setor,
            'foto': foto,
            'tem_conversa': tem_conversa,
            'canal_id': canal_id,
            'online': True,  # Pode implementar status depois
        })

    context = {
        'usuarios': usuarios_com_info,
        'conversas_por_usuario': conversas_por_usuario,
        'usuario_atual': usuario_atual,
        'conversas_diretas_count': conversas_diretas_count,  # ← ADICIONADO
        'canais_grupo_count': canais_grupo_count,  # ← ADICIONADO
    }
    return render(request, 'recursoshumanos/comunicacao/lista_usuarios.html', context)


# recursoshumanos/views.py - atualize a função iniciar_conversa_direta
@login_required
@require_POST
def iniciar_conversa_direta(request):
    """Iniciar ou continuar conversa direta com um usuário"""
    outro_usuario_id = request.POST.get('usuario_id')

    if not outro_usuario_id:
        return JsonResponse({'error': 'Usuário não especificado'}, status=400)

    try:
        outro_usuario = User.objects.get(id=outro_usuario_id, is_active=True)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Usuário não encontrado'}, status=404)

    usuario_atual = request.user

    # Verificar se já existe conversa direta
    canal_existente = CanalComunicacao.objects.filter(
        tipo='direto',  # ← Use 'tipo' em vez de 'eh_conversa_direta'
        membros=usuario_atual
    ).filter(membros=outro_usuario).first()

    if canal_existente:
        # Já existe conversa, redirecionar para ela
        return JsonResponse({
            'success': True,
            'canal_id': canal_existente.id,
            'action': 'redirect'
        })

    # Criar novo canal direto
    novo_canal = CanalComunicacao.objects.create(
        nome=f"{usuario_atual.username} ↔ {outro_usuario.username}",
        tipo='direto',
        criado_por=usuario_atual,
        eh_conversa_direta=True,
    )

    # Adicionar os dois usuários como membros
    novo_canal.membros.add(usuario_atual, outro_usuario)
    novo_canal.save()

    # Notificar o outro usuário (USANDO O CAMPO CORRETO)
    NotificacaoSistema.objects.create(
        usuario=outro_usuario,
        tipo='mensagem',
        titulo='Nova conversa',
        mensagem=f'{usuario_atual.get_full_name()} iniciou uma conversa com você',
        url_link=f'/rh/comunicacao/canal/{novo_canal.id}/',  # ← CORRIGIDO: url_link em vez de link_url
        modelo_relacionado='CanalComunicacao',
        objeto_id=novo_canal.id,
        prioridade='media'
    )

    return JsonResponse({
        'success': True,
        'canal_id': novo_canal.id,
        'action': 'created'
    })

@login_required
def chat_principal(request):
    """Chat principal"""
    usuario = request.user

    # Canais do usuário
    canais = CanalComunicacao.objects.filter(
        Q(membros=usuario) | Q(enviar_para_todos=True)
    ).exclude(arquivado=True).distinct()

    # Canal geral
    canal_geral, created = CanalComunicacao.objects.get_or_create(
        nome='Geral',
        tipo='geral',
        defaults={'descricao': 'Canal geral para comunicação institucional', 'enviar_para_todos': True}
    )

    context = {
        'canais': canais,
        'canal_geral': canal_geral,
        'usuario': usuario,
    }
    return render(request, 'recursoshumanos/comunicacao/chat_principal.html', context)


# recursoshumanos/views.py - atualize a função canal_chat
@login_required
def canal_chat(request, canal_id):
    """Mensagens de um canal específico"""
    canal = get_object_or_404(CanalComunicacao, id=canal_id)
    usuario = request.user

    # Verificar se é membro
    if not (canal.membros.filter(id=usuario.id).exists() or canal.enviar_para_todos):
        messages.error(request, "Você não tem acesso a este canal.")
        return redirect('chat_principal')

    # Obter mensagens
    mensagens = Mensagem.objects.filter(canal=canal).select_related('remetente').order_by('data_envio')[:100]

    # Usuários disponíveis para adicionar (apenas para canais não diretos)
    usuarios_disponiveis = None
    if canal.tipo != 'direto':
        usuarios_disponiveis = User.objects.filter(
            is_active=True
        ).exclude(
            id__in=canal.membros.values_list('id', flat=True)
        ).exclude(id=usuario.id)

    context = {
        'canal': canal,
        'mensagens': mensagens,
        'usuario': usuario,
        'usuarios_disponiveis': usuarios_disponiveis,
        'today': date.today(),
        'yesterday': date.today() - timedelta(days=1),
    }
    return render(request, 'recursoshumanos/comunicacao/canal_chat.html', context)


# recursoshumanos/views.py - adicione esta função
@login_required
def editar_canal(request, canal_id):
    """Editar canal existente"""
    canal = get_object_or_404(CanalComunicacao, id=canal_id)

    # Verificar permissão (apenas criador ou admin pode editar)
    if canal.criado_por != request.user and not request.user.is_staff:
        messages.error(request, "Você não tem permissão para editar este canal.")
        return redirect('canal_chat', canal_id=canal_id)

    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        tipo = request.POST.get('tipo', canal.tipo)
        enviar_para_todos = request.POST.get('enviar_para_todos') == 'on'
        arquivado = request.POST.get('arquivado') == 'on'

        if not nome:
            messages.error(request, "O nome do canal é obrigatório.")
            return redirect('editar_canal', canal_id=canal_id)

        # Atualizar canal
        canal.nome = nome
        canal.descricao = descricao
        canal.tipo = tipo
        canal.enviar_para_todos = enviar_para_todos
        canal.arquivado = arquivado

        # Não permitir mudar tipo de conversa direta
        if canal.eh_conversa_direta:
            canal.tipo = 'direto'
            messages.info(request, "Tipo de canal fixo como 'direto' para conversas privadas.")

        # Atualizar membros (se não for conversa direta)
        if not canal.eh_conversa_direta:
            membros_ids = request.POST.getlist('membros')
            if membros_ids:
                usuarios = User.objects.filter(id__in=membros_ids)
                canal.membros.set(usuarios)

            # Garantir que o criador continua membro
            if canal.criado_por and not canal.membros.filter(id=canal.criado_por.id).exists():
                canal.membros.add(canal.criado_por)

        canal.save()

        messages.success(request, f'Canal "{nome}" atualizado com sucesso!')
        return redirect('canal_chat', canal_id=canal.id)

    # Listar usuários disponíveis
    usuarios = User.objects.filter(is_active=True).order_by('username')

    context = {
        'canal': canal,
        'usuarios': usuarios,
        'tipos_canal': CanalComunicacao.TIPO_CHOICES,
    }
    return render(request, 'recursoshumanos/comunicacao/editar_canal.html', context)

@login_required
@require_POST
def enviar_mensagem(request, canal_id):
    """Enviar mensagem no chat"""
    canal = get_object_or_404(CanalComunicacao, id=canal_id)
    usuario = request.user

    if not (canal.membros.filter(id=usuario.id).exists() or canal.enviar_para_todos):
        return JsonResponse({'success': False, 'error': 'Sem permissão'})

    conteudo = request.POST.get('conteudo', '').strip()

    if not conteudo and 'arquivo' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'Mensagem vazia'})

    # Validar arquivo
    arquivo = None
    nome_arquivo = ''
    if 'arquivo' in request.FILES:
        arquivo = request.FILES['arquivo']
        nome_arquivo = arquivo.name

        # Não permitir vídeos
        extensao = os.path.splitext(arquivo.name)[1].lower()
        if extensao in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv']:
            return JsonResponse({'success': False, 'error': 'Vídeos não são permitidos'})

    # Criar mensagem
    mensagem = Mensagem.objects.create(
        canal=canal,
        remetente=usuario,
        conteudo=conteudo,
        arquivo=arquivo,
        nome_arquivo=nome_arquivo
    )

    # Notificar destinatários
    destinatarios = canal.membros.exclude(id=usuario.id)
    if canal.enviar_para_todos:
        destinatarios = User.objects.filter(is_active=True).exclude(id=usuario.id)

    if destinatarios.exists():
        Notificador.mensagem_recebida(mensagem, destinatarios)

    return JsonResponse({
        'success': True,
        'mensagem_id': mensagem.id,
        'remetente': usuario.get_full_name() or usuario.username,
        'conteudo': mensagem.conteudo,
        'data_envio': mensagem.data_envio.strftime('%H:%M'),
        'tem_arquivo': bool(mensagem.arquivo),
    })


@login_required
def documentos_institucionais(request):
    """Listar documentos - VERSÃO QUE FUNCIONA"""
    usuario = request.user

    # APENAS documentos públicos
    documentos = DocumentoInstitucional.objects.filter(publico=True)

    # Aplicar filtros
    tipo_filtro = request.GET.get('tipo')
    if tipo_filtro:
        documentos = documentos.filter(tipo=tipo_filtro)

    status_filtro = request.GET.get('status')
    if status_filtro:
        documentos = documentos.filter(status=status_filtro)

    # Ordenar
    documentos = documentos.order_by('-data_documento')

    context = {
        'documentos': documentos,
        'tipos': TipoDocumento.TIPO_CHOICES,
    
        'status_list': DocumentoInstitucional.STATUS_CHOICES,
    }

    return render(request, 'recursoshumanos/comunicacao/documentos.html', context)


@login_required
def criar_documento(request):
    """Criar documento institucional"""
    if request.method == 'POST':
        tipo = request.POST.get('tipo_documento')
        titulo = request.POST.get('titulo')

        # Coletar todos os dados
        dados = {
            'titulo': titulo,
            'numero_oficio': request.POST.get('numero_oficio', ''),
            'destinatario': request.POST.get('destinatario', ''),
            'objetivos': request.POST.get('objetivos', ''),
            'introducao': request.POST.get('introducao', ''),
            'metodologia': request.POST.get('metodologia', ''),
            'resultados': request.POST.get('resultados', ''),
            'recomendacoes': request.POST.get('recomendacoes', ''),
            'assunto': request.POST.get('assunto', ''),
            'conteudo': request.POST.get('conteudo', ''),
            'participantes': request.POST.get('participantes', ''),
            'pauta': request.POST.get('pauta', ''),
            'deliberacoes': request.POST.get('deliberacoes', ''),
        }

        # Aqui você geraria o documento Word/PDF
        # usando python-docx ou reportlab

        # Por enquanto, apenas salva os dados
        documento = DocumentoInstitucional.objects.create(
            tipo=tipo,
            titulo=titulo,
            conteudo=dados,
            data_documento=date.today(),
            criado_por=request.user,
            status='rascunho',
            publico=True
        )

        messages.success(request, 'Documento criado com sucesso!')
        return redirect('/rh/comunicacao/documentos/')

    # GET request
    context = {
        'hoje': date.today(),
    }
    return render(request, 'recursoshumanos/comunicacao/criar_documento.html', context)



@login_required
def relatorios_atividades(request):
    """Listar relatórios"""
    usuario = request.user

    relatorios = RelatorioAtividade.objects.filter(
        Q(publico=True) |
        Q(compartilhar_com=usuario) |
        Q(criado_por=usuario) |
        Q(setor__funcionario__user=usuario)
    ).distinct().order_by('-periodo_inicio')

    # Filtros
    tipo_filtro = request.GET.get('tipo')
    if tipo_filtro:
        relatorios = relatorios.filter(tipo=tipo_filtro)

    context = {
        'relatorios': relatorios,
        'tipos': RelatorioAtividade.TIPO_CHOICES,
    }
    return render(request, 'recursoshumanos/comunicacao/relatorios.html', context)


@login_required
def criar_relatorio(request):
    """Criar novo relatório"""
    if request.method == 'POST':
        titulo = request.POST.get('titulo', '').strip()
        tipo = request.POST.get('tipo', 'mensal')
        descricao = request.POST.get('descricao', '').strip()
        periodo_inicio = request.POST.get('periodo_inicio')
        periodo_fim = request.POST.get('periodo_fim')

        if not titulo or not periodo_inicio or not periodo_fim:
            messages.error(request, "Título e período são obrigatórios.")
            return redirect('criar_relatorio')

        # Obter setor do usuário
        try:
            funcionario = Funcionario.objects.get(user=request.user)
            setor = funcionario.sector
        except:
            setor = None

        # Criar relatório
        relatorio = RelatorioAtividade.objects.create(
            titulo=titulo,
            tipo=tipo,
            descricao=descricao,
            periodo_inicio=periodo_inicio,
            periodo_fim=periodo_fim,
            atividades_realizadas=request.POST.get('atividades_realizadas', ''),
            resultados=request.POST.get('resultados', ''),
            dificuldades=request.POST.get('dificuldades', ''),
            recomendacoes=request.POST.get('recomendacoes', ''),
            criado_por=request.user,
            setor=setor,
        )

        # Processar arquivos
        if 'arquivo_principal' in request.FILES:
            relatorio.arquivo_principal = request.FILES['arquivo_principal']

        if 'anexos' in request.FILES:
            relatorio.anexos = request.FILES['anexos']

        # Configurar compartilhamento
        publico = request.POST.get('publico') == 'on'
        relatorio.publico = publico

        if not publico:
            compartilhar_ids = request.POST.getlist('compartilhar_com')
            if compartilhar_ids:
                usuarios = User.objects.filter(id__in=compartilhar_ids)
                relatorio.compartilhar_com.set(usuarios)

        relatorio.save()

        messages.success(request, 'Relatório criado com sucesso!')
        return redirect('relatorios_atividades')

    usuarios = User.objects.filter(is_active=True)

    context = {
        'usuarios': usuarios,
        'tipos': RelatorioAtividade.TIPO_CHOICES,
    }
    return render(request, 'recursoshumanos/comunicacao/criar_relatorio.html', context)


# ========== APIS PARA NOTIFICAÇÕES ==========

@login_required
def api_notificacoes_pendentes(request):
    """API para notificações pendentes"""
    notificacoes = NotificacaoSistema.objects.filter(
        usuario=request.user,
        lida=False
    ).order_by('-data_criacao')[:10]

    data = []
    for notif in notificacoes:
        data.append({
            'id': notif.id,
            'tipo': notif.get_tipo_display(),
            'titulo': notif.titulo,
            'mensagem': notif.mensagem,
            'link_url': notif.url_link,
            'link_texto': 'Ver detalhes',
            'data_criacao': (notif.data_criacao or timezone.now()).strftime('%H:%M'),
        })

    return JsonResponse({
        'notificacoes': data,
        'total': notificacoes.count(),
    })


@login_required
@require_POST
def api_marcar_notificacao_lida(request, notificacao_id):
    """Marcar notificação como lida"""
    notificacao = get_object_or_404(NotificacaoSistema, id=notificacao_id, usuario=request.user)

    notificacao.lida = True
    notificacao.data_leitura = timezone.now()
    notificacao.save()

    return JsonResponse({'success': True})


@login_required
@require_POST
def api_marcar_todas_notificacoes_lidas(request):
    """Marcar todas notificações como lidas"""
    notificacoes = NotificacaoSistema.objects.filter(
        usuario=request.user,
        lida=False
    )

    atualizadas = notificacoes.update(
        lida=True,
        data_leitura=timezone.now()
    )

    return JsonResponse({'success': True, 'atualizadas': atualizadas})


@login_required
def minhas_notificacoes(request):
    """Página com todas as notificações"""
    notificacoes = NotificacaoSistema.objects.filter(
        usuario=request.user
    ).order_by('-data_criacao')

    # Paginação
    paginator = Paginator(notificacoes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'total_nao_lidas': notificacoes.filter(lida=False).count(),
    }
    return render(request, 'recursoshumanos/notificacoes/minhas.html', context)


@login_required
def configurar_notificacoes(request):
    """Configurar preferências de notificação"""
    config, created = ConfiguracaoNotificacao.objects.get_or_create(
        usuario=request.user,
        defaults={
            'mostrar_licencas': True,
            'mostrar_avaliacoes': True,
            'mostrar_documentos': True,
            'mostrar_mensagens': True,
            'mostrar_sistema': True,
            'som_notificacoes': True,
        }
    )

    if request.method == 'POST':
        config.mostrar_licencas = request.POST.get('mostrar_licencas') == 'on'
        config.mostrar_avaliacoes = request.POST.get('mostrar_avaliacoes') == 'on'
        config.mostrar_documentos = request.POST.get('mostrar_documentos') == 'on'
        config.mostrar_mensagens = request.POST.get('mostrar_mensagens') == 'on'
        config.mostrar_sistema = request.POST.get('mostrar_sistema') == 'on'
        config.som_notificacoes = request.POST.get('som_notificacoes') == 'on'
        config.save()

        messages.success(request, 'Configurações atualizadas!')
        return redirect('configurar_notificacoes')

    context = {'config': config}
    return render(request, 'recursoshumanos/notificacoes/configurar.html', context)


# ========== VISUALIZAR/BAIXAR DOCUMENTOS ==========

@login_required
def visualizar_documento(request, documento_id):
    """Visualizar documento"""
    documento = get_object_or_404(DocumentoInstitucional, id=documento_id)
    usuario = request.user

    # Verificar permissão
    pode_ver = (
            documento.publico or
            documento.criado_por == usuario or
            documento.setores_destino.filter(funcionario__user=usuario).exists() or
            documento.funcionarios_destino.filter(user=usuario).exists()
    )

    if not pode_ver:
        messages.error(request, "Você não tem permissão para visualizar este documento.")
        return redirect('documentos_institucionais')

    context = {
        'documento': documento,
    }
    return render(request, 'recursoshumanos/comunicacao/visualizar_documento.html', context)


@login_required
def download_documento(request, documento_id):
    """Download de documento"""
    documento = get_object_or_404(DocumentoInstitucional, id=documento_id)
    usuario = request.user

    # Verificar permissão
    pode_ver = (
            documento.publico or
            documento.criado_por == usuario or
            documento.setores_destino.filter(funcionario__user=usuario).exists() or
            documento.funcionarios_destino.filter(user=usuario).exists()
    )

    if not pode_ver:
        return HttpResponseForbidden("Acesso negado.")

    response = FileResponse(documento.arquivo.open(),
                            as_attachment=True,
                            filename=documento.arquivo.name.split('/')[-1])
    return response


# views.py (adicione esta view)
@login_required
@require_GET
def api_chat_mensagens(request, canal_id):
    """API para obter mensagens históricas do chat"""
    canal = get_object_or_404(CanalComunicacao, id=canal_id)

    # Verificar acesso
    if not (canal.membros.filter(id=request.user.id).exists() or canal.enviar_para_todos):
        return JsonResponse({'error': 'Acesso negado'}, status=403)

    mensagens = Mensagem.objects.filter(canal=canal).select_related('remetente')[:100]

    data = {
        'messages': [
            {
                'type': 'chat_message',
                'message_id': msg.id,
                'sender_id': msg.remetente.id,
                'sender_name': msg.remetente.get_full_name() or msg.remetente.username,
                'message': msg.conteudo,
                'timestamp': msg.data_envio.isoformat(),
                'has_file': bool(msg.arquivo),
                'file_name': msg.nome_arquivo,
                'file_url': msg.arquivo.url if msg.arquivo else None
            }
            for msg in mensagens
        ]
    }

    return JsonResponse(data)


# recursoshumanos/views.py (adicione estas funções no final do arquivo)

# ========== FUNÇÕES UTILITÁRIAS E APIS ==========

@login_required
@require_POST
def upload_arquivo_chat(request):
    """Upload de arquivos para o chat (API)"""
    import os  # Importação local para garantir

    if 'arquivo' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'Nenhum arquivo enviado'}, status=400)

    arquivo = request.FILES['arquivo']
    nome_arquivo = arquivo.name
    extensao = os.path.splitext(nome_arquivo)[1].lower()

    # Não permitir vídeos
    extensoes_video = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv']
    if extensao in extensoes_video:
        return JsonResponse({'success': False, 'error': 'Vídeos não são permitidos'}, status=400)

    # Salvar arquivo temporariamente
    import uuid
    from django.core.files.storage import default_storage

    nome_unico = f"chat_uploads/{uuid.uuid4()}{extensao}"
    caminho = default_storage.save(nome_unico, arquivo)

    return JsonResponse({
        'success': True,
        'nome_arquivo': nome_arquivo,
        'caminho': caminho,
        'url': default_storage.url(caminho) if default_storage.exists(caminho) else None
    })


@login_required
@require_GET
def calcular_dias_uteis_view(request):
    """API para calcular dias úteis entre duas datas"""
    data_inicio_str = request.GET.get('data_inicio')
    data_fim_str = request.GET.get('data_fim')

    if not data_inicio_str or not data_fim_str:
        return JsonResponse({'error': 'Parâmetros data_inicio e data_fim são obrigatórios'},
                            status=400)

    try:
        data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
        data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()

        if data_fim < data_inicio:
            return JsonResponse({'error': 'Data final deve ser posterior à data inicial'},
                                status=400)

        dias_uteis = calcular_dias_uteis(data_inicio, data_fim)
        dias_totais = (data_fim - data_inicio).days + 1
        fins_semana = dias_totais - dias_uteis

        return JsonResponse({
            'dias_uteis': dias_uteis,
            'dias_totais': dias_totais,
            'fins_semana': fins_semana,
            'data_inicio': data_inicio_str,
            'data_fim': data_fim_str
        })

    except ValueError:
        return JsonResponse({'error': 'Formato de data inválido. Use YYYY-MM-DD'}, status=400)


@login_required
@require_POST
def verificar_ferias_view(request):
    """API para verificar conflito de férias"""
    try:
        funcionario_id = request.POST.get('funcionario_id')
        data_inicio_str = request.POST.get('data_inicio')
        data_fim_str = request.POST.get('data_fim')

        if not funcionario_id or not data_inicio_str or not data_fim_str:
            return JsonResponse({'error': 'Parâmetros obrigatórios faltando'}, status=400)

        funcionario = get_object_or_404(Funcionario, id=funcionario_id)
        data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
        data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()

        conflito = verificar_conflito_ferias(funcionario.id, data_inicio, data_fim)

        return JsonResponse({
            'conflito': conflito,
            'funcionario': funcionario.nome_completo,
            'data_inicio': data_inicio_str,
            'data_fim': data_fim_str
        })

    except ValueError:
        return JsonResponse({'error': 'Formato de data inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def licenca_submetida_view(request, licenca_id):
    """View para submeter licença"""
    licenca = get_object_or_404(Licenca, id=licenca_id)

    # Verificar permissão
    if licenca.funcionario.user != request.user:
        return JsonResponse({'error': 'Permissão negada'}, status=403)

    if licenca.status != 'pendente':
        return JsonResponse({'error': 'Licença já foi submetida'}, status=400)

    # Atualizar status
    licenca.status = 'aguardando_chefe'
    licenca.data_submissao = timezone.now()
    licenca.save()

    # Notificar usando o Notificador
    Notificador.licenca_submetida(licenca)

    return JsonResponse({
        'success': True,
        'message': 'Licença submetida com sucesso',
        'licenca_id': licenca.id,
        'status': licenca.status
    })


@login_required
@require_GET
def relatorio_mensal_view(request, mes, ano):
    """View para gerar relatório mensal em JSON"""
    try:
        # Converter parâmetros
        mes = int(mes)
        ano = int(ano)

        # Verificar valores válidos
        if mes < 1 or mes > 12 or ano < 1900 or ano > 2100:
            return JsonResponse({'error': 'Mês ou ano inválido'}, status=400)

        # Obter funcionário logado
        funcionario = Funcionario.objects.get(user=request.user)

        # Verificar permissão (apenas RH ou chefes podem ver dados completos)
        pode_ver_todos = (request.user.is_staff or
                          request.user.groups.filter(name='rh_staff').exists() or
                          funcionario.funcao in ['chefe', 'coordenador', 'director'])

        if pode_ver_todos:
            # RH/Chefe vê todos do setor
            if funcionario.funcao in ['chefe', 'coordenador']:
                funcionarios_setor = Funcionario.objects.filter(sector=funcionario.sector, ativo=True)
                presencas = gerar_relatorio_presencas_mensal(mes, ano)

                # Filtrar apenas funcionários do setor
                funcionarios_ids = funcionarios_setor.values_list('id', flat=True)
                presencas = [p for p in presencas if p['funcionario'] in funcionarios_ids]

            elif funcionario.funcao == 'director':
                # Diretor vê todos da direção
                funcionarios_direcao = Funcionario.objects.filter(
                    sector__direcao=funcionario.sector.direcao,
                    ativo=True
                )
                presencas = gerar_relatorio_presencas_mensal(mes, ano)
                funcionarios_ids = funcionarios_direcao.values_list('id', flat=True)
                presencas = [p for p in presencas if p['funcionario'] in funcionarios_ids]

            else:  # RH staff
                presencas = gerar_relatorio_presencas_mensal(mes, ano)

        else:
            # Funcionário comum vê apenas seus dados
            presencas = gerar_relatorio_presencas_mensal(mes, ano)
            presencas = [p for p in presencas if p['funcionario'] == funcionario.id]

        # Adicionar informações do funcionário
        for item in presencas:
            func = Funcionario.objects.get(id=item['funcionario'])
            item['nome_funcionario'] = func.nome_completo
            item['setor'] = str(func.sector)
            item['funcao'] = func.get_funcao_display()

        return JsonResponse({
            'mes': mes,
            'ano': ano,
            'total_registros': len(presencas),
            'dados': presencas
        })

    except Funcionario.DoesNotExist:
        return JsonResponse({'error': 'Funcionário não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ========== FUNÇÕES AUXILIARES (adicione antes das views) ==========







from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from .models import *
from .forms import *

# ... existing imports ...

# ========== PROMOÇÕES ==========

@login_required
def lista_promocoes(request):
    """Lista todas as promoções"""
    promocoes = Promocao.objects.all().order_by('-data_promocao')
    
    # Filtros
    search = request.GET.get('search')
    if search:
        promocoes = promocoes.filter(
            Q(funcionario__nome_completo__icontains=search) |
            Q(cargo_atual__icontains=search)
        )

    context = {
        'promocoes': promocoes
    }
    return render(request, 'recursoshumanos/promocoes/lista.html', context)

@login_required
def nova_promocao(request):
    """Registrar nova promoção"""
    # Apenas RH ou Diretores podem registrar promoções
    if not (request.user.is_staff or request.user.groups.filter(name='rh_staff').exists()):
        messages.error(request, "Acesso não autorizado.")
        return redirect('dashboard')

    if request.method == 'POST':
        try:
            funcionario_id = request.POST.get('funcionario')
            data_promocao = request.POST.get('data_promocao')
            cargo_anterior = request.POST.get('cargo_anterior')
            cargo_atual = request.POST.get('cargo_atual')
            nivel_anterior = request.POST.get('nivel_anterior')
            nivel_atual = request.POST.get('nivel_atual')
            salario_anterior = request.POST.get('salario_anterior')
            salario_atual = request.POST.get('salario_atual')
            motivo = request.POST.get('motivo')
            
            funcionario = Funcionario.objects.get(id=funcionario_id)
            
            promocao = Promocao.objects.create(
                funcionario=funcionario,
                data_promocao=data_promocao,
                cargo_anterior=cargo_anterior,
                cargo_atual=cargo_atual,
                nivel_anterior=nivel_anterior,
                nivel_atual=nivel_atual,
                salario_anterior=salario_anterior,
                salario_atual=salario_atual,
                motivo=motivo,
                aprovado_por=request.user
            )

            # Atualizar dados do funcionário
            # Nota: Você pode querer atualizar a função do funcionário aqui se ela estiver mapeada
            
            messages.success(request, f"Promoção de {funcionario.nome_completo} registrada com sucesso!")
            return redirect('lista_promocoes')
            
        except Exception as e:
            messages.error(request, f"Erro ao registrar promoção: {str(e)}")
    
    funcionarios = Funcionario.objects.filter(ativo=True).order_by('nome_completo')
    context = {'funcionarios': funcionarios}
    return render(request, 'recursoshumanos/promocoes/form.html', context)

@login_required
def detalhes_promocao(request, promocao_id):
    """Detalhes de uma promoção"""
    promocao = get_object_or_404(Promocao, id=promocao_id)
    return render(request, 'recursoshumanos/promocoes/detalhes.html', {'promocao': promocao})


# ========== COMPETÊNCIAS ==========

@login_required
def lista_competencias(request):
    """Lista todas as competências de avaliação"""
    competencias = Competencia.objects.all().order_by('nome')
    return render(request, 'recursoshumanos/competencias/lista.html', {'competencias': competencias})

@login_required
def gerir_competencia(request, competencia_id=None):
    """Criar ou editar competência"""
    # Apenas RH
    if not (request.user.is_staff or request.user.groups.filter(name='rh_staff').exists()):
        messages.error(request, "Acesso não autorizado.")
        return redirect('dashboard')

    competencia = None
    if competencia_id:
        competencia = get_object_or_404(Competencia, id=competencia_id)

    if request.method == 'POST':
        nome = request.POST.get('nome')
        descricao = request.POST.get('descricao')
        peso = request.POST.get('peso')
        ativo = request.POST.get('ativo') == 'on'
        
        if competencia:
            competencia.nome = nome
            competencia.descricao = descricao
            competencia.peso = peso
            competencia.ativo = ativo
            competencia.save()
            messages.success(request, "Competência atualizada com sucesso.")
        else:
            Competencia.objects.create(
                nome=nome,
                descricao=descricao,
                peso=peso,
                ativo=ativo
            )
            messages.success(request, "Competência criada com sucesso.")
            
        return redirect('lista_competencias')

    return render(request, 'recursoshumanos/competencias/form.html', {'competencia': competencia})

# ========== DIRETÓRIO DE USUÁRIOS ==========

@login_required
def lista_usuarios_status(request):
    """Lista de usuários com status online/offline"""
    from django.utils import timezone
    from datetime import timedelta
    
    # Consideramos 'online' quem logou nos últimos 5 minutos
    # Mais preciso seria usar cache com middleware, mas isso é um bom proxy
    limite_online = timezone.now() - timedelta(minutes=5)
    
    funcionarios = Funcionario.objects.filter(ativo=True).select_related('user', 'sector')
    
    usuarios_list = []
    for func in funcionarios:
        if func.user:
            is_online = func.user.last_login and func.user.last_login > limite_online
            last_seen = func.user.last_login
        else:
            is_online = False
            last_seen = None
            
        usuarios_list.append({
            'funcionario': func,
            'is_online': is_online,
            'last_seen': last_seen
        })
    
    # Ordenar: Online primeiro
    usuarios_list.sort(key=lambda x: x['is_online'], reverse=True)
    
    return render(request, 'recursoshumanos/usuarios/diretorio.html', {'usuarios': usuarios_list})


@login_required
@chefe_required
def editar_parecer_licenca(request, licenca_id):
    """Permite ao chefe corrigir um parecer (se diretor ainda não analisou)"""
    licenca = get_object_or_404(Licenca, id=licenca_id)
    chefe = get_object_or_404(Funcionario, user=request.user)

    # Permissões
    if licenca.funcionario.sector != chefe.sector:
        messages.error(request, "Sem permissão.")
        return redirect('recursoshumanos:dashboard')

    # Só pode editar se diretor ainda não deu parecer (ou se foi rejeitada pelo proprio chefe)
    if licenca.diretor_aprovador and licenca.status != 'aguardando_diretor':
         messages.error(request, "Não é possível editar: o diretor já processou esta licença.")
         return redirect('recursoshumanos:licencas_setor')
    
    if request.method == 'POST':
        parecer = request.POST.get('parecer', '').strip()
        status_decisao = request.POST.get('status')

        if not parecer:
            messages.error(request, "O parecer não pode estar vazio.")
            return redirect('recursoshumanos:editar_parecer_licenca', licenca_id=licenca_id)

        # Atualizar
        licenca.parecer_chefe = parecer
        licenca.chefe_aprovador = request.user
        licenca.data_parecer_chefe = timezone.now()
        licenca.status_chefia = status_decisao

        if status_decisao == 'favoravel':
            licenca.status = 'aguardando_diretor'
            mensagem_status = 'corrigida para APROVADA'
        else:
            licenca.status = 'rejeitado'
            mensagem_status = 'corrigida para REJEITADA'

        licenca.save()
        messages.success(request, f'Parecer atualizado! Licença {mensagem_status}.')
        return redirect('recursoshumanos:licencas_setor')

    # Contexto para reuso do template
    context = {
        'licenca': licenca,
        'chefe': chefe,
        'mostrar_analise_rh': True,
        'is_edicao': True
    }
    return render(request, 'recursoshumanos/licencas/dar_parecer.html', context)

# ========== GERAÇÃO DE DOCUMENTOS ==========

@login_required
def download_licenca_pdf(request, licenca_id):
    """Gera e baixa o PDF do requerimento de férias"""
    licenca = get_object_or_404(Licenca, id=licenca_id)
    
    # Verificação básica de permissão
    if request.user != licenca.funcionario.user and \
       not (request.user.is_staff or request.user.groups.filter(name__in=['rh_staff']).exists()) and \
       not (hasattr(request.user, 'funcionario') and request.user.funcionario.funcao in ['chefe', 'director']):
        messages.error(request, "Permissão negada.")
        return redirect('recursoshumanos:dashboard')

    from .utils.pdf_generator import render_pdf
    
    context = {
        'licenca': licenca,
        'request': request,
    }
    
    pdf = render_pdf('recursoshumanos/documentos/ferias_anuais_pdf.html', context)
    
    try: 
        filename = f"Licenca_{licenca.funcionario.numero_identificacao}_{licenca.data_inicio}.pdf"
    except:
        filename = f"Licenca_{licenca.id}.pdf"
        
    pdf['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return pdf
