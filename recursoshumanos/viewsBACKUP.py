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
import os  # ADICIONE ESTA LINHA AQUI

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from .decorators import rh_required, chefe_required, director_required
from .models import *
from .forms import *



# ========== DASHBOARD PRINCIPAL ==========
@login_required(login_url='/rh/login/')
def dashboard_completo(request):
    """Dashboard único adaptado ao perfil do usuário"""
    user = request.user
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
            subordinados = Funcionario.objects.filter(
                sector=funcionario.sector
            ).exclude(id=funcionario.id)

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
            chefes_direcao = Funcionario.objects.filter(
                sector__direcao=funcionario.sector.direcao,
                funcao__in=['chefe', 'coordenador']
            ).exclude(id=funcionario.id)

            context['chefes_sob_direcao'] = chefes_direcao
            context['licencas_aguardando_diretor'] = Licenca.objects.filter(
                funcionario__sector__direcao=funcionario.sector.direcao,
                status='aguardando_diretor'
            ).select_related('funcionario')[:5]

    except Funcionario.DoesNotExist:
        pass

    # Verificar se é RH/Staff
    context['is_rh'] = user.is_staff or user.groups.filter(name='rh_staff').exists()

    if context['is_rh']:
        context['licencas_pendentes_rh'] = Licenca.objects.filter(
            status__in=['pendente', 'aguardando_diretor']
        ).select_related('funcionario')[:10]

        context['total_funcionarios'] = Funcionario.objects.filter(ativo=True).count()
        context['funcionarios_novos'] = Funcionario.objects.filter(
            data_admissao__month=date.today().month,
            data_admissao__year=date.today().year
        ).count()

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


@login_required
@rh_required
def criar_funcionario(request):
    """Criar novo funcionário"""
    if request.method == 'POST':
        form = FuncionarioForm(request.POST, request.FILES)
        if form.is_valid():
            funcionario = form.save()
            messages.success(request, 'Funcionário criado com sucesso!')
            return redirect('detalhes_funcionario', funcionario_id=funcionario.id)
    else:
        form = FuncionarioForm()

    context = {'form': form}
    return render(request, 'recursoshumanos/funcionarios/criar.html', context)


# ========== LICENÇAS ==========

@login_required
def minhas_licencas(request):
    """Licenças do funcionário logado"""
    funcionario = get_object_or_404(Funcionario, user=request.user)
    licencas = Licenca.objects.filter(funcionario=funcionario).order_by('-data_inicio')

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
    anos = Licenca.objects.filter(funcionario=funcionario).dates('data_inicio', 'year')
    anos_disponiveis = [ano.year for ano in anos]

    context = {
        'licencas': licencas,
        'anos_disponiveis': sorted(set(anos_disponiveis), reverse=True),
        'ano_filter': ano_filter,
        'tipo_filter': tipo_filter,
        'status_filter': status_filter,
        'funcionario': funcionario,
    }
    return render(request, 'recursoshumanos/licencas/minhas.html', context)


@login_required
def solicitar_licenca(request):
    """Solicitar nova licença"""
    funcionario = get_object_or_404(Funcionario, user=request.user)

    if request.method == 'POST':
        form = LicencaForm(request.POST)
        if form.is_valid():
            licenca = form.save(commit=False)
            licenca.funcionario = funcionario
            licenca.status = 'pendente'
            licenca.save()

            # Notificação automática
            Notificador.licenca_submetida(licenca)

            messages.success(request, 'Licença solicitada com sucesso!')
            return redirect('minhas_licencas')
    else:
        form = LicencaForm()

    # Calcular saldo disponível
    saldo_atual = SaldoFerias.objects.filter(
        funcionario=funcionario,
        ano=date.today().year
    ).first()

    context = {
        'form': form,
        'funcionario': funcionario,
        'saldo_atual': saldo_atual,
    }
    return render(request, 'recursoshumanos/licencas/solicitar.html', context)


@login_required
@chefe_required
def dar_parecer_licenca(request, licenca_id):
    """Chefe dá parecer sobre licença"""
    licenca = get_object_or_404(Licenca, id=licenca_id)
    chefe = get_object_or_404(Funcionario, user=request.user)

    # Verificar se é chefe do funcionário
    if licenca.funcionario.sector != chefe.sector:
        messages.error(request, "Não tem permissão para dar parecer sobre este funcionário.")
        return redirect('dashboard')

    if request.method == 'POST':
        parecer = request.POST.get('parecer', '').strip()
        status = request.POST.get('status', 'favoravel')

        if not parecer:
            messages.error(request, "O parecer não pode estar vazio.")
            return redirect('dar_parecer_licenca', licenca_id=licenca_id)

        # Atualizar licença
        licenca.parecer_chefe = parecer
        licenca.status_chefia = status
        licenca.chefe_aprovador = request.user
        licenca.data_parecer_chefe = timezone.now()

        if status == 'desfavoravel':
            licenca.status = 'rejeitado'
        else:
            licenca.status = 'aguardando_diretor'

        licenca.save()

        # Notificação automática
        Notificador.licenca_parecer_chefe(licenca)

        messages.success(request, 'Parecer registrado com sucesso!')
        return redirect('dashboard')

    context = {
        'licenca': licenca,
        'chefe': chefe,
    }
    return render(request, 'recursoshumanos/licencas/dar_parecer.html', context)


@login_required
@director_required
def autorizar_licenca(request, licenca_id):
    """Diretor autoriza ou reprova licença"""
    licenca = get_object_or_404(Licenca, id=licenca_id)
    director = get_object_or_404(Funcionario, user=request.user)

    # Verificar se o diretor tem jurisdição
    if licenca.funcionario.sector.direcao != director.sector.direcao:
        messages.error(request, "Não tem jurisdição sobre este setor.")
        return redirect('dashboard')

    if request.method == 'POST':
        acao = request.POST.get('acao')
        parecer = request.POST.get('parecer', '').strip()

        if not parecer and acao == 'autorizar':
            messages.error(request, "É necessário incluir um parecer para autorizar.")
            return redirect('autorizar_licenca', licenca_id=licenca_id)

        licenca.parecer_diretor = parecer
        licenca.diretor_aprovador = request.user
        licenca.data_parecer_diretor = timezone.now()

        if acao == 'autorizar':
            licenca.status = 'aprovado'

            # Gerar documento de férias
            documento = gerar_documento_ferias(licenca)
            if documento:
                licenca.documento_ferias = documento

            # Notificação automática
            Notificador.licenca_autorizada(licenca)
            messages.success(request, 'Licença autorizada e documento gerado!')

        elif acao == 'reprovar':
            licenca.status = 'rejeitado'
            messages.warning(request, 'Licença reprovada!')

        licenca.save()
        return redirect('dashboard')

    context = {
        'licenca': licenca,
        'director': director,
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
    funcionario = get_object_or_404(Funcionario, user=request.user)
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
                    return redirect('avaliar_funcionario', funcionario_id=funcionario_id)

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
            return redirect('dashboard')

        except Exception as e:
            messages.error(request, f'Erro ao processar avaliação: {str(e)}')
            return redirect('avaliar_funcionario', funcionario_id=funcionario_id)

    context = {
        'funcionario': funcionario,
        'competencias': competencias,
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
    """Gerar cartão PVC em PDF"""
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)

    # Gerar QR code se não existir
    if not funcionario.qr_code:
        funcionario.gerar_qr_code()

    # Gerar PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="cartao_{funcionario.numero_identificacao}.pdf"'

    p = canvas.Canvas(response, pagesize=(85.6 * mm, 54 * mm))

    # Fundo
    p.setFillColor(colors.HexColor('#1a4a72'))
    p.rect(0, 0, 85.6 * mm, 54 * mm, fill=True)

    # Foto
    if funcionario.foto:
        try:
            p.drawImage(funcionario.foto.path, 5 * mm, 15 * mm, width=25 * mm, height=35 * mm, mask='auto')
        except:
            pass

    # QR Code
    if funcionario.qr_code:
        try:
            p.drawImage(funcionario.qr_code.path, 55 * mm, 10 * mm, width=25 * mm, height=25 * mm)
        except:
            pass

    # Informações
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(35 * mm, 40 * mm, funcionario.nome_completo[:20])
    p.setFont("Helvetica", 10)
    p.drawString(35 * mm, 35 * mm, f"Setor: {funcionario.sector.codigo}")
    p.drawString(35 * mm, 30 * mm, f"ID: {funcionario.numero_identificacao}")

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


@login_required
def canal_chat(request, canal_id):
    """Mensagens de um canal específico"""
    canal = get_object_or_404(CanalComunicacao, id=canal_id)
    usuario = request.user

    # Verificar se é membro
    if not (canal.membros.filter(id=usuario.id).exists() or canal.enviar_para_todos):
        messages.error(request, "Você não tem acesso a este canal.")
        return redirect('chat_principal')

    mensagens = Mensagem.objects.filter(canal=canal).select_related('remetente')[:100]

    context = {
        'canal': canal,
        'mensagens': mensagens,
        'usuario': usuario,
    }
    return render(request, 'recursoshumanos/comunicacao/canal_chat.html', context)


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
    """Listar documentos"""
    usuario = request.user

    documentos = DocumentoInstitucional.objects.filter(
        Q(publico=True) |
        Q(setores_destino__funcionario__user=usuario) |
        Q(funcionarios_destino__user=usuario) |
        Q(criado_por=usuario)
    ).distinct().order_by('-data_documento')

    # Filtros
    tipo_filtro = request.GET.get('tipo')
    if tipo_filtro:
        documentos = documentos.filter(tipo=tipo_filtro)

    status_filtro = request.GET.get('status')
    if status_filtro:
        documentos = documentos.filter(status=status_filtro)

    context = {
        'documentos': documentos,
        'tipos': DocumentoInstitucional.TIPO_CHOICES,
        'status_list': DocumentoInstitucional.STATUS_CHOICES,
    }
    return render(request, 'recursoshumanos/comunicacao/documentos.html', context)


@login_required
def criar_documento(request):
    """Criar novo documento"""
    if request.method == 'POST':
        titulo = request.POST.get('titulo', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        tipo = request.POST.get('tipo', 'relatorio')
        data_documento = request.POST.get('data_documento')

        if not titulo or 'arquivo' not in request.FILES:
            messages.error(request, "Título e arquivo são obrigatórios.")
            return redirect('criar_documento')

        arquivo = request.FILES['arquivo']
        extensao = os.path.splitext(arquivo.name)[1].lower()

        # Validar tipo
        if extensao in ['.mp4', '.avi', '.mov', '.wmv']:
            messages.error(request, "Vídeos não são permitidos.")
            return redirect('criar_documento')

        # Criar documento
        documento = DocumentoInstitucional.objects.create(
            titulo=titulo,
            descricao=descricao,
            tipo=tipo,
            arquivo=arquivo,
            data_documento=data_documento if data_documento else date.today(),
            criado_por=request.user,
            status='rascunho',
        )

        # Configurar destinatários
        publico = request.POST.get('publico') == 'on'
        documento.publico = publico

        if not publico:
            setores_ids = request.POST.getlist('setores')
            funcionarios_ids = request.POST.getlist('funcionarios')

            if setores_ids:
                setores = Sector.objects.filter(id__in=setores_ids)
                documento.setores_destino.set(setores)

            if funcionarios_ids:
                funcionarios = Funcionario.objects.filter(id__in=funcionarios_ids)
                documento.funcionarios_destino.set(funcionarios)

        documento.save()

        # Notificar destinatários
        usuarios_destino = []
        if documento.publico:
            usuarios_destino = User.objects.filter(is_active=True)
        else:
            usuarios_setores = User.objects.filter(
                funcionario__sector__in=documento.setores_destino.all()
            )
            usuarios_funcionarios = User.objects.filter(
                id__in=documento.funcionarios_destino.values_list('user__id', flat=True)
            )
            usuarios_destino = set(list(usuarios_setores) + list(usuarios_funcionarios))

        if usuarios_destino:
            Notificador.documento_compartilhado(documento, usuarios_destino)

        messages.success(request, 'Documento criado com sucesso!')
        return redirect('documentos_institucionais')

    setores = Sector.objects.all()
    funcionarios = Funcionario.objects.filter(ativo=True)

    context = {
        'setores': setores,
        'funcionarios': funcionarios,
        'tipos': DocumentoInstitucional.TIPO_CHOICES,
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
            'link_url': notif.link_url,
            'link_texto': notif.link_texto,
            'data_criacao': notif.data_criacao.strftime('%H:%M'),
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

def calcular_dias_uteis(data_inicio, data_fim):
    """
    Calcula dias úteis (exclui fins de semana)
    """
    dias = 0
    current_date = data_inicio

    while current_date <= data_fim:
        if current_date.weekday() < 5:  # 0-4 = segunda a sexta
            dias += 1
        current_date += timedelta(days=1)

    return dias


def gerar_relatorio_presencas_mensal(mes, ano):
    """
    Gera relatório de presenças para o mês
    Retorna dados para integração com outras apps
    """
    data_inicio = date(ano, mes, 1)
    if mes == 12:
        data_fim = date(ano + 1, 1, 1) - timedelta(days=1)
    else:
        data_fim = date(ano, mes + 1, 1) - timedelta(days=1)

    presencas = RegistroPresenca.objects.filter(
        data_hora__date__gte=data_inicio,
        data_hora__date__lte=data_fim
    ).values('funcionario').annotate(
        dias_presentes=Count('id', filter=Q(tipo='entrada')),
        total_horas=Sum('horas_trabalhadas')
    )

    return list(presencas)


def verificar_conflito_ferias(funcionario_id, data_inicio, data_fim):
    """
    Verifica se há conflito com outras férias ou licenças
    """
    conflitos = Licenca.objects.filter(
        funcionario_id=funcionario_id,
        status='aprovado',
        data_inicio__lte=data_fim,
        data_fim__gte=data_inicio
    ).exists()

    return conflitos


# ========== NOTIFICADOR TEMPORÁRIO ==========
class Notificador:
    """Sistema de notificações temporário"""

    @staticmethod
    def licenca_submetida(licenca):
        from .models import NotificacaoSistema
        try:
            NotificacaoSistema.objects.create(
                usuario=licenca.funcionario.user,
                tipo='licenca',
                titulo='Licença Submetida',
                mensagem='Sua licença foi submetida para aprovação',
                link_url=f'/rh/licencas/minhas/'
            )
        except:
            pass
        return True

    @staticmethod
    def licenca_parecer_chefe(licenca):
        return True

    @staticmethod
    def licenca_autorizada(licenca):
        return True

    @staticmethod
    def avaliacao_realizada(avaliacao):
        return True

    @staticmethod
    def mensagem_recebida(mensagem, destinatarios):
        return True

    @staticmethod
    def documento_compartilhado(documento, usuarios):
        return True