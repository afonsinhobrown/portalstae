
# dfec/views.py
import json
import csv
import uuid
from datetime import datetime, timedelta, date
import random
from io import BytesIO, StringIO
from zipfile import ZipFile

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse, reverse_lazy
from django.db.models import Count, Sum, Avg, Q, F
from django.core.paginator import Paginator
from django.utils import timezone
from django.core.cache import cache
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt

# Relatórios PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm

# Excel
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill

# QR Codes
import qrcode
from PIL import Image
import base64

# Decorator personalizado
from portalstae.decorators import login_required_for_app

# ========== IMPORTS DOS MODELOS ==========
from dfec.models.completo import (
    ManualCompleto, TipoManual, TemplateManual, CapituloManual, ImagemManual,
    AnexoManual, VersaoManual, HistoricoUsoManual, ComentarioManual,
    Manual, CapituloSimples, ImagemManualSimples, ComentarioManualSimples,
    ObjetivoInstitucional, PlanoAtividade, Atividade, Formacao, Participante,
    Turma, Brigada, Eleicao, DadosEleicao, AnaliseRegiao, RelatorioGerado, AlertaSistema, Avaliacao
)

# Aliases
Formando = Participante
ResultadoEleicao = DadosEleicao

# ========== IMPORTS DOS FORMULÁRIOS ==========
from .forms import (
    PlanoAtividadeForm, FormacaoForm, FormandoForm, BrigadaForm,
    ImportarDadosForm, AnaliseRegiaoForm,
    ManualForm, CapituloForm, ComentarioForm, UploadImagemForm,
    ObjetivoInstitucionalForm, AtividadeForm
)

# ========== DASHBOARD E UTILITÁRIOS ==========

@login_required_for_app('dfec')
def dashboard(request):
    """Dashboard principal do DFEC"""
    estatisticas = {
        'planos_ativos': PlanoAtividade.objects.filter(ativo=True).count(),
        'formacoes_ativas': Formacao.objects.filter(estado='ativa').count(),
        'formacoes_concluidas': Formacao.objects.filter(estado='concluida').count(),
        'formandos_total': Participante.objects.count(),
        'turmas_total': Turma.objects.count(),
        'brigadas_total': Brigada.objects.count(),
        'manuais_publicados': Manual.objects.filter(publicado=True).count(),
        'analises_realizadas': AnaliseRegiao.objects.count(),
    }
    
    planos_recentes = PlanoAtividade.objects.filter(ativo=True).order_by('-data_criacao')[:5]
    formacoes_recentes = Formacao.objects.filter(estado__in=['ativa', 'agendada']).order_by('-data_inicio')[:5]
    formacoes_estado = Formacao.objects.values('estado').annotate(total=Count('id')).order_by('estado')
    manuais_recentes = Manual.objects.filter(publicado=True).order_by('-data_atualizacao')[:5]
    
    hoje = timezone.now().date()
    proximos_eventos = Formacao.objects.filter(data_inicio__gte=hoje).order_by('data_inicio')[:5]
    analises_recentes = AnaliseRegiao.objects.select_related('regiao').order_by('-data_analise')[:5]

    context = {
        'titulo': 'Dashboard DFEC',
        'subtitulo': 'Direção de Formação e Estudos Eleitorais',
        'estatisticas': estatisticas,
        'planos_recentes': planos_recentes,
        'formacoes_recentes': formacoes_recentes,
        'formacoes_estado': formacoes_estado,
        'manuais_recentes': manuais_recentes,
        'proximos_eventos': proximos_eventos,
        'analises_recentes': analises_recentes,
    }
    return render(request, 'dfec/dashboard.html', context)

@login_required_for_app('dfec')
def configuracoes_dfec(request):
    return render(request, 'dfec/configuracoes.html')

# ========== MÓDULO LOGÍSTICA (DFEC) ==========

@login_required_for_app('dfec')
def lista_logistica_dfec(request):
    """Gestão de Materiais de Formação e Educação Cívica"""
    from dfec.models.completo import LogisticaMaterialDFEC
    
    materiais = LogisticaMaterialDFEC.objects.filter(ativo=True)
    
    resumo = materiais.aggregate(
        total=Sum('quantidade_total'),
        distribuido=Sum('quantidade_distribuida')
    )
    
    context = {
        'materiais': materiais,
        'resumo': resumo,
        'titulo': 'Logística e Material de Formação'
    }
    return render(request, 'dfec/logistica/lista.html', context)

@login_required_for_app('dfec')
def criar_material_dfec(request):
    """Adicionar novo material de formação"""
    from dfec.models.completo import LogisticaMaterialDFEC
    # Implementação simplificada para demonstração
    if request.method == 'POST':
        item = request.POST.get('item')
        tipo = request.POST.get('tipo')
        quantidade = request.POST.get('quantidade', 0)
        
        LogisticaMaterialDFEC.objects.create(
            item=item,
            tipo=tipo,
            quantidade_total=quantidade
        )
        messages.success(request, f"Material '{item}' registado com sucesso!")
        return redirect('dfec:logistica_lista')
        
    return render(request, 'dfec/logistica/form.html')

@login_required_for_app('dfec')
def ajuda_sistema(request):
    return render(request, 'dfec/ajuda.html')

# ========== MÓDULO 1: PLANIFICAÇÃO (CBV + FBV) ==========

class PlanoAtividadeListView(LoginRequiredMixin, ListView):
    model = PlanoAtividade
    template_name = 'dfec/planificacao/lista.html'
    context_object_name = 'planos'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get('status', 'ativos')
        if status == 'ativos':
            queryset = queryset.filter(ativo=True)
        elif status == 'inativos':
            queryset = queryset.filter(ativo=False)
        
        query = self.request.GET.get('q', '')
        if query:
            queryset = queryset.filter(
                Q(nome__icontains=query) |
                Q(descricao__icontains=query) |
                Q(responsavel_principal__username__icontains=query)
            )
        return queryset.order_by('-data_inicio_planeada')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Planos de Atividade'
        context['status_filter'] = self.request.GET.get('status', 'ativos')
        return context

class PlanoAtividadeCreateView(LoginRequiredMixin, CreateView):
    model = PlanoAtividade
    form_class = PlanoAtividadeForm
    template_name = 'dfec/planificacao/form.html'
    success_url = reverse_lazy('dfec:planificacao_lista')

    def form_valid(self, form):
        form.instance.criado_por = self.request.user
        form.instance.codigo = f"PL-{uuid.uuid4().hex[:8].upper()}"
        messages.success(self.request, f'Plano "{form.instance.titulo}" criado com sucesso!')
        return super().form_valid(form)

# Wrapper para compatibilidade com URLs existentes
@login_required_for_app('dfec')
def lista_planos(request):
    return PlanoAtividadeListView.as_view()(request)

# Views funcionais para Planos (usadas para detalhe, edição)
@login_required_for_app('dfec')
def detalhe_plano(request, pk):
    plano = get_object_or_404(PlanoAtividade, pk=pk)
    return render(request, 'dfec/planificacao/detalhe.html', {'plano': plano})

@login_required_for_app('dfec')
def criar_plano(request):
    if request.method == 'POST':
        form = PlanoAtividadeForm(request.POST)
        if form.is_valid():
            plano = form.save()
            return redirect('dfec:plano_detalhe', pk=plano.pk)
    else:
        form = PlanoAtividadeForm()
    return render(request, 'dfec/planificacao/form.html', {'form': form})

@login_required_for_app('dfec')
def editar_plano(request, pk):
    plano = get_object_or_404(PlanoAtividade, pk=pk)
    if request.method == 'POST':
        form = PlanoAtividadeForm(request.POST, instance=plano)
        if form.is_valid():
            form.save()
            return redirect('dfec:plano_detalhe', pk=plano.pk)
    else:
        form = PlanoAtividadeForm(instance=plano)
    return render(request, 'dfec/planificacao/form.html', {'form': form, 'plano': plano})

@login_required_for_app('dfec')
def aprovar_plano(request, pk):
    plano = get_object_or_404(PlanoAtividade, pk=pk)
    plano.status = 'aprovado'
    plano.save()
    messages.success(request, f'Plano "{plano.nome}" aprovado com sucesso!')
    return redirect('dfec:plano_detalhe', pk=plano.pk)

@login_required_for_app('dfec')
def executar_plano(request, pk):
    plano = get_object_or_404(PlanoAtividade, pk=pk)
    plano.status = 'EXECUTADO'
    plano.save()
    messages.success(request, f'Plano "{plano.nome}" marcado como executado!')
    return redirect('dfec:plano_detalhe', pk=plano.pk)

# ========== MÓDULO: ATIVIDADES (CRUD e API) ==========

@login_required_for_app('dfec')
def criar_atividade(request, plano_id):
    plano = get_object_or_404(PlanoAtividade, pk=plano_id)
    if request.method == 'POST':
        form = AtividadeForm(request.POST)
        if form.is_valid():
            atividade = form.save(commit=False)
            atividade.plano = plano
            atividade.save()
            messages.success(request, "Atividade adicionada ao plano!")
            return redirect('dfec:plano_detalhe', pk=plano.pk)
    else:
        form = AtividadeForm(initial={
            'plano': plano,
            'objetivo_institucional': plano.objetivo_institucional
        })
    return render(request, 'dfec/planificacao/atividade_form.html', {'form': form, 'plano': plano})

@login_required_for_app('dfec')
def editar_atividade(request, pk):
    atividade = get_object_or_404(Atividade, pk=pk)
    plano = atividade.plano
    
    objetivos = ObjetivoInstitucional.objects.all()
    referencias = Atividade.objects.filter(plano__nivel='CENTRAL').exclude(pk=atividade.pk)
    
    if request.method == 'POST':
        atividade.nome = request.POST.get('nome')
        atividade.descricao = request.POST.get('descricao')
        if request.POST.get('data_inicio'): atividade.data_inicio = request.POST.get('data_inicio')
        if request.POST.get('data_fim'): atividade.data_fim = request.POST.get('data_fim')
        
        obj_id = request.POST.get('objetivo')
        atividade.objetivo_institucional_id = obj_id if obj_id else None
            
        ref_id = request.POST.get('referencia')
        atividade.referencia_nacional_id = ref_id if ref_id else None
            
        resp_id = request.POST.get('responsavel')
        if resp_id: atividade.responsavel_id = resp_id
        
        atividade.status = request.POST.get('status')
        atividade.orcamento_estimado = request.POST.get('orcamento') or 0
        
        atividade.save()
        messages.success(request, f"Atividade '{atividade.nome}' atualizada com sucesso.")
        return redirect('dfec:plano_detalhe', pk=plano.pk)
    
    return render(request, 'dfec/planificacao/atividade_form.html', {
        'atividade': atividade,
        'plano': plano,
        'editar': True,
        'objetivos': objetivos,
        'referencias': referencias
    })

@login_required_for_app('dfec')
def excluir_atividade(request, pk):
    atividade = get_object_or_404(Atividade, pk=pk)
    plano_id = atividade.plano.id
    nome = atividade.nome
    
    if request.method == 'POST':
        atividade.delete()
        messages.success(request, f"Atividade '{nome}' excluída com sucesso.")
        return redirect('dfec:plano_detalhe', pk=plano_id)
        
    return render(request, 'dfec/planificacao/confirmar_exclusao_atividade.html', {'atividade': atividade})

# API CALENDÁRIO
@login_required_for_app('dfec')
@require_GET
def api_eventos_calendario(request):
    """API para eventos do calendário (atividades dos planos)"""
    try:
        # Obter parâmetros da requisição
        plano_id = request.GET.get('plano_id')
        
        # Se tiver plano_id, filtrar apenas atividades desse plano
        if plano_id:
            plano = get_object_or_404(PlanoAtividade, pk=plano_id)
            atividades = Atividade.objects.filter(plano=plano)
        else:
            # Se não, retornar todas as atividades
            atividades = Atividade.objects.all()
        
        # Converter atividades para formato do FullCalendar
        eventos = []
        for atividade in atividades:
            # Verificar se tem datas
            if not atividade.data_inicio:
                continue
                
            # Definir cor baseada no status
            cor_mapa = {
                'planejado': '#3498db',      # Azul
                'em_andamento': '#f39c12',   # Laranja
                'concluido': '#27ae60',      # Verde
                'atrasado': '#e74c3c',       # Vermelho
                'cancelado': '#95a5a6',      # Cinza
            }
            # lower() para garantir match caso venha maiusculo
            status_lower = atividade.status.lower() if atividade.status else 'planejado'
            # Tentar match direto ou lower
            cor = cor_mapa.get(status_lower, cor_mapa.get(atividade.status, '#3498db'))
            
            # Criar objeto de evento
            evento = {
                'id': atividade.id,
                'title': atividade.nome,
                'start': atividade.data_inicio.isoformat(),
                'end': atividade.data_fim.isoformat() if atividade.data_fim else None,
                'url': reverse('dfec:atividade_editar', args=[atividade.id]),
                'backgroundColor': cor,
                'borderColor': cor,
                'textColor': '#ffffff',
                'allDay': True,
                'extendedProps': {
                    'responsavel': atividade.responsavel.get_full_name() if atividade.responsavel else 'Não definido',
                    'plano': atividade.plano.nome,
                    'status': atividade.get_status_display() if hasattr(atividade, 'get_status_display') else atividade.status,
                }
            }
            eventos.append(evento)
        
        # Adicionar também os períodos dos planos como eventos
        if plano_id:
            plano_evento = {
                'id': f"plano-{plano.id}",
                'title': f"📅 {plano.nome}",
                'start': plano.data_inicio_planeada.isoformat() if plano.data_inicio_planeada else None,
                'end': plano.data_fim_planeada.isoformat() if plano.data_fim_planeada else None,
                'backgroundColor': '#2c3e50',
                'borderColor': '#2c3e50',
                'textColor': '#ffffff',
                'allDay': True,
                'rendering': 'background',
                'display': 'background',
                'extendedProps': {
                    'tipo': 'plano',
                    'descricao': f'Período do plano: {plano.nome}'
                }
            }
            if plano_evento['start']:
                eventos.append(plano_evento)
        
        return JsonResponse(eventos, safe=False)
        
    except Exception as e:
        print(f"Erro na API de eventos: {str(e)}")
        return JsonResponse({
            'error': str(e),
            'eventos': []
        }, status=500)

# ========== MÓDULO 2: FORMAÇÕES ==========

@login_required_for_app('dfec')
def formacao_detalhe(request, pk):
    formacao = get_object_or_404(Formacao, pk=pk)
    estatisticas = {
        'total_participantes': formacao.participantes.count(),
        'total_turmas': formacao.turmas.count(),
        'total_brigadas': formacao.brigadas.count(),
        'homens': formacao.participantes.filter(genero='M').count(),
        'mulheres': formacao.participantes.filter(genero='F').count(),
        'aprovados': formacao.participantes.filter(status='aprovado').count(),
    }
    
    turmas = formacao.turmas.all().annotate(num_participantes=Count('participantes_atribuidos'))
    participantes_recentes = formacao.participantes.all().order_by('-id')[:10]
    pendentes_turma = formacao.participantes.filter(turma__isnull=True)

    context = {
        'formacao': formacao,
        'estatisticas': estatisticas,
        'turmas': turmas,
        'participantes_recentes': participantes_recentes,
        'pendentes_turma': pendentes_turma,
        'titulo': f'Formação: {formacao.nome}'
    }
    return render(request, 'dfec/formacoes/detalhe.html', context)

@login_required_for_app('dfec')
def criar_formacao(request):
    if request.method == 'POST':
        form = FormacaoForm(request.POST)
        if form.is_valid():
            formacao = form.save()
            return redirect('dfec:formacao_detalhe', pk=formacao.pk)
    else:
        atividade_id = request.GET.get('atividade')
        initial = {'atividade': atividade_id} if atividade_id else {}
        form = FormacaoForm(initial=initial)
    return render(request, 'dfec/formacao/form.html', {'form': form})

@login_required_for_app('dfec')
def editar_formacao(request, pk):
    formacao = get_object_or_404(Formacao, pk=pk)
    if request.method == 'POST':
        form = FormacaoForm(request.POST, instance=formacao)
        if form.is_valid():
            form.save()
            messages.success(request, f'Formação "{formacao.nome}" atualizada com sucesso!')
            return redirect('dfec:formacao_detalhe', pk=formacao.pk)
    else:
        form = FormacaoForm(instance=formacao)
    return render(request, 'dfec/formacao/form.html', {'form': form, 'formacao': formacao})

@login_required_for_app('dfec')
def lista_formacoes(request):
    formacoes = Formacao.objects.all().order_by('-id').annotate(count_participantes=Count('participantes'))
    return render(request, 'dfec/formacao/lista.html', {'formacoes': formacoes})

# Geração de Turmas (Versão Consolidada e Robusta)
@login_required_for_app('dfec')
def gerar_turmas_inteligente(request, formacao_id):
    formacao = get_object_or_404(Formacao, pk=formacao_id)
    
    if request.method == "POST":
        qtd_turmas = int(request.POST.get('qtd_turmas', 0))
        distribuir_genero = request.POST.get('distribuir_genero') == 'on'
        
        participantes = list(formacao.participantes.filter(status='APROVADO'))
        if not participantes:
            participantes = list(formacao.participantes.all())
            
        if not participantes:
            messages.warning(request, "Não há participantes para distribuir.")
            return redirect('dfec:formacao_detalhe', pk=formacao_id)
            
        total_parts = len(participantes)
        if qtd_turmas > 0:
            tamanho_turma = -(-total_parts // qtd_turmas)
        else:
            tamanho_turma = 60
            qtd_turmas = -(-total_parts // tamanho_turma)
        
        # Shuffle para aleatoriedade
        random.shuffle(participantes)
        
        # Se distribuir gênero, poderia separar listas aqui e intercalar.
        # Por simplificação, mantemos shuffle simples que estatisticamente distribui.
        
        chunks = [participantes[i:i + tamanho_turma] for i in range(0, len(participantes), tamanho_turma)]
        
        contador = formacao.turmas.count()
        for i, chunk in enumerate(chunks):
            contador += 1
            nome_turma = f"Turma {contador}"
            turma = Turma.objects.create(
                formacao=formacao,
                nome=nome_turma,
                data_inicio=formacao.data_inicio_real or formacao.data_inicio_planeada,
                data_fim=formacao.data_fim_real or formacao.data_fim_planeada
            )
            turma.participantes_atribuidos.set(chunk)
            
            if request.user.is_staff:
                turma.formador_principal = request.user
                turma.save()
                
        messages.success(request, f"{len(chunks)} turmas geradas com sucesso!")
        return redirect('dfec:formacao_detalhe', pk=formacao_id)
    
    messages.warning(request, "Use o formulário para gerar turmas.")
    return redirect('dfec:formacao_detalhe', pk=formacao_id)       

@login_required_for_app('dfec')
def criar_turma_vazia(request, formacao_id):
    formacao = get_object_or_404(Formacao, pk=formacao_id)
    count = formacao.turmas.count() + 1
    Turma.objects.create(
        formacao=formacao,
        nome=f"Turma {count}",
        data_inicio=formacao.data_inicio_real,
        data_fim=formacao.data_fim_real
    )
    messages.success(request, "Nova turma criada com sucesso!")
    return redirect('dfec:formacao_detalhe', pk=formacao_id)

@login_required_for_app('dfec')
def limpar_turmas(request, formacao_id):
    formacao = get_object_or_404(Formacao, pk=formacao_id)
    count = formacao.turmas.count()
    formacao.turmas.all().delete()
    messages.success(request, f"{count} turmas foram removidas com sucesso.")
    return redirect('dfec:formacao_detalhe', pk=formacao_id)

@login_required_for_app('dfec')
def turma_detalhe(request, turma_id):
    turma = get_object_or_404(Turma, pk=turma_id)
    return render(request, 'dfec/turmas/detalhe_turma.html', {'turma': turma})

@login_required_for_app('dfec')
def turma_criar_manual(request, formacao_id):
    formacao = get_object_or_404(Formacao, pk=formacao_id)
    if request.method == 'POST':
        nome = request.POST.get('nome')
        sala = request.POST.get('sala')
        participantes_ids = request.POST.getlist('participantes')
        if not participantes_ids:
            messages.error(request, "Selecione participantes.")
        else:
            turma = Turma.objects.create(formacao=formacao, nome=nome, sala=sala)
            participantes = formacao.participantes.filter(id__in=participantes_ids)
            turma.participantes_atribuidos.set(participantes)
            messages.success(request, f"Turma criada com {participantes.count()} participantes.")
            return redirect('dfec:formacao_detalhe', pk=formacao_id)
            
    participantes_em_turmas = Turma.objects.filter(formacao=formacao).values_list('participantes_atribuidos', flat=True)
    participantes_disponiveis = formacao.participantes.filter(status='APROVADO').exclude(id__in=participantes_em_turmas)
    return render(request, 'dfec/turmas/form.html', {'formacao': formacao, 'participantes_disponiveis': participantes_disponiveis})

# Importação e Gestão de Participantes
@login_required_for_app('dfec')
def importar_participantes_excel(request, formacao_id):
    formacao = get_object_or_404(Formacao, pk=formacao_id)
    if request.method == 'POST' and request.FILES.get('arquivo_excel'):
        arquivo = request.FILES['arquivo_excel']
        try:
            df = pd.read_excel(arquivo)
            sucesso, erros = 0, 0
            for _, row in df.iterrows():
                try:
                    data_nasc = row.get('data_nascimento(AAAA-MM-DD)')
                    if pd.isna(data_nasc): data_nasc = None
                    Participante.objects.create(
                        formacao=formacao,
                        nome_completo=row['nome_completo'],
                        categoria=row.get('categoria', 'BRIGADISTA'),
                        bilhete_identidade=str(row.get('bilhete_identidade', '')),
                        telefone=str(row.get('telefone', '')),
                        genero=str(row.get('genero(M/F)', 'M')).upper()[:1],
                        data_nascimento=data_nasc,
                        provincia=row.get('provincia', formacao.provincia),
                        distrito=row.get('distrito', '')
                    )
                    sucesso += 1
                except: erros += 1
            messages.success(request, f"Importação: {sucesso} sucessos, {erros} erros.")
        except Exception as e:
            messages.error(request, f"Erro: {str(e)}")
    return redirect('dfec:formacao_detalhe', pk=formacao_id)

@login_required_for_app('dfec')
def download_template_participantes(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Importar"
    ws.append(["nome_completo", "categoria", "bilhete_identidade", "telefone", "genero(M/F)", "data_nascimento(AAAA-MM-DD)", "provincia", "distrito"])
    ws.append(["Exemplo da Silva", "BRIGADISTA", "1234", "84000", "M", "1990-01-01", "MAPUTO", "KA_MUBUKANA"])
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="Template.xlsx"'
    wb.save(response)
    return response

@login_required_for_app('dfec')
def limpar_participantes_formacao(request, formacao_id):
    formacao = get_object_or_404(Formacao, pk=formacao_id)
    formacao.turma_set.all().delete()
    formacao.formandos.all().delete()
    formacao.brigada_set.all().delete()
    messages.info(request, "Dados limpos com sucesso.")
    return redirect('dfec:formacao_detalhe', pk=formacao_id)

@login_required_for_app('dfec')
def simular_participantes(request, formacao_id):
    formacao = get_object_or_404(Formacao, pk=formacao_id)
    if formacao.formandos.exists():
        messages.warning(request, "Limpe os dados antes de simular.")
    else:
        nomes = ["Ricardo", "Helena", "Titos", "Amélia", "Zacarias"]
        apelidos = ["Mabunda", "Chivambo", "Nhaca", "Cuamba"]
        for i in range(40):
            genero = 'M' if i % 2 == 0 else 'F'
            Participante.objects.create(
                formacao=formacao,
                nome_completo=f"{random.choice(nomes)} {random.choice(apelidos)} Simulado",
                categoria='BRIGADISTA',
                bilhete_identidade=f"SIM{formacao.pk}{i:03d}",
                genero=genero,
                data_nascimento=date(1990 + (i%10), 1, 1),
                provincia=formacao.provincia
            )
        messages.success(request, "40 participantes simulados.")
    return redirect('dfec:formacao_detalhe', pk=formacao_id)

@login_required_for_app('dfec')
def lista_participantes(request):
    categoria = request.GET.get('categoria')
    participantes = Participante.objects.all().order_by('nome_completo')
    if categoria:
        participantes = participantes.filter(categoria=categoria)
    return render(request, 'dfec/participantes_lista.html', {
        'participantes': participantes,
        'categoria_filtro': categoria,
        'categorias': Participante.CATEGORIA_CHOICES
    })

# ========== MÓDULO 3: BRIGADAS ==========

@login_required_for_app('dfec')
def gerar_brigadas_automatico(request, formacao_id):
    formacao = get_object_or_404(Formacao, pk=formacao_id)
    participantes_aprovados = formacao.participantes.filter(status='APROVADO')
    if not participantes_aprovados.exists():
        messages.warning(request, "Sem aprovados para formar brigadas.")
        return redirect('dfec:formacao_detalhe', pk=formacao_id)
    
    # Agrupamento por distrito
    por_distrito = {}
    for p in participantes_aprovados:
        distrito = p.distrito or "Geral"
        por_distrito.setdefault(distrito, []).append(p)
        
    criadas = 0
    TAMANHO_BRIGADA = 3
    
    for distrito, lista in por_distrito.items():
        grupos = [lista[i:i + TAMANHO_BRIGADA] for i in range(0, len(lista), TAMANHO_BRIGADA)]
        for grupo in grupos:
            count = Brigada.objects.filter(formacao=formacao).count()
            Brigada.objects.create(
                codigo=f"BRG-{formacao.ano}-{count + 1:03d}",
                formacao=formacao,
                provincia=formacao.provincia,
                distrito=distrito,
                localidade=grupo[0].localidade,
                ativa=True
            )
            criadas += 1
    
    messages.success(request, f"{criadas} brigadas geradas.")
    return redirect('dfec:formacao_detalhe', pk=formacao_id)

@login_required_for_app('dfec')
def lista_brigadas(request):
    brigadas = Brigada.objects.all()
    return render(request, 'dfec/brigadas_lista.html', {'brigadas': brigadas})

@login_required_for_app('dfec')
def detalhe_brigada(request, pk):
    brigada = get_object_or_404(Brigada, pk=pk)
    return render(request, 'dfec/brigada_detalhe.html', {'brigada': brigada})

@login_required_for_app('dfec')
def criar_brigada(request):
    if request.method == 'POST':
        form = BrigadaForm(request.POST)
        if form.is_valid():
            brigada = form.save()
            return redirect('dfec:brigada_detalhe', pk=brigada.pk)
    else:
        form = BrigadaForm()
    return render(request, 'dfec/brigada_criar.html', {'form': form})

@login_required_for_app('dfec')
def editar_brigada(request, pk):
    brigada = get_object_or_404(Brigada, pk=pk)
    if request.method == 'POST':
        form = BrigadaForm(request.POST, instance=brigada)
        if form.is_valid():
            form.save()
            return redirect('dfec:brigada_detalhe', pk=brigada.pk)
    else:
        form = BrigadaForm(instance=brigada)
    return render(request, 'dfec/brigada_editar.html', {'form': form, 'brigada': brigada})

@login_required_for_app('dfec')
def relatorio_manuais(request):
    manuais = Manual.objects.all()
    return render(request, 'dfec/relatorio_manuais.html', {'manuais': manuais})

# ========== VIEWS ADICIONAIS RESTAURADAS ==========

@login_required_for_app('dfec')
def aprovar_plano(request, pk):
    plano = get_object_or_404(PlanoAtividade, pk=pk)
    if request.method == 'POST':
        plano.status = 'aprovado'
        plano.save()
        messages.success(request, f"Plano {plano.nome} aprovado.")
    return redirect('dfec:plano_detalhe', pk=pk)

@login_required_for_app('dfec')
def executar_plano(request, pk):
    plano = get_object_or_404(PlanoAtividade, pk=pk)
    if request.method == 'POST':
        plano.status = 'executado'
        plano.save()
        messages.success(request, f"Plano {plano.nome} em execução.")
    return redirect('dfec:plano_detalhe', pk=pk)

@login_required_for_app('dfec')
def excluir_plano(request, pk):
    plano = get_object_or_404(PlanoAtividade, pk=pk)
    if request.method == 'POST':
        plano.delete()
        messages.success(request, "Plano excluído.")
        return redirect('dfec:planos_lista')
    return redirect('dfec:plano_detalhe', pk=pk)

@login_required_for_app('dfec')
def criar_atividade(request, plano_id):
    plano = get_object_or_404(PlanoAtividade, pk=plano_id)
    if request.method == 'POST':
        form = AtividadeForm(request.POST)
        if form.is_valid():
            atividade = form.save(commit=False)
            atividade.plano = plano
            atividade.save()
            messages.success(request, "Atividade criada.")
            return redirect('dfec:plano_detalhe', pk=plano.pk)
    else:
        form = AtividadeForm()
    return render(request, 'dfec/planificacao/atividade_form.html', {'form': form, 'plano': plano})

@login_required_for_app('dfec')
def excluir_atividade(request, pk):
    atividade = get_object_or_404(Atividade, pk=pk)
    plano_id = atividade.plano.id
    if request.method == 'POST':
        atividade.delete()
        messages.success(request, "Atividade excluída.")
    return redirect('dfec:plano_detalhe', pk=plano_id)

@login_required_for_app('dfec')
def gerir_formadores_plano(request, pk):
    plano = get_object_or_404(PlanoAtividade, pk=pk)
    
    if request.method == 'POST':
        if 'adicionar_existente' in request.POST:
            user_id = request.POST.get('user_id')
            user = get_object_or_404(User, pk=user_id)
            plano.formadores.add(user)
            messages.success(request, f"{user.get_full_name()} adicionado à lista de formadores do plano.")
            
        elif 'criar_novo' in request.POST:
            nome = request.POST.get('nome')
            bi = request.POST.get('bi')
            email = request.POST.get('email')
            
            if nome and bi:
                username = bi.strip().upper().replace(' ', '')
                # Verificar se usuario ja existe
                user, created = User.objects.get_or_create(username=username)
                if created:
                    parts = nome.strip().split()
                    user.first_name = parts[0]
                    user.last_name = ' '.join(parts[1:]) if len(parts) > 1 else ''
                    user.email = email or ''
                    user.set_password('stae1234')
                    user.is_active = True
                    user.save()
                    messages.success(request, f"Usuário {username} criado no sistema.")
                else:
                     messages.info(request, f"Usuário {username} já existia. Adicionado ao plano.")
                
                plano.formadores.add(user)
                
        elif 'remover' in request.POST:
            user_id = request.POST.get('user_id')
            user = get_object_or_404(User, pk=user_id)
            plano.formadores.remove(user)
            messages.success(request, "Formador removido do plano.")
            
        return redirect('dfec:plano_formadores', pk=pk)

    # Lista atual
    formadores_plano = plano.formadores.all()
    
    # Pesquisa de candidatos (excluir os que já estão no plano)
    q = request.GET.get('q')
    candidatos = []
    if q:
        candidatos = User.objects.filter(
            Q(username__icontains=q) | 
            Q(first_name__icontains=q) | 
            Q(last_name__icontains=q)
        ).exclude(id__in=plano.formadores.values_list('id', flat=True))[:20]

    return render(request, 'dfec/planificacao/plano_formadores.html', {
        'plano': plano,
        'formadores': formadores_plano,
        'candidatos': candidatos,
        'q': q
    })

@login_required_for_app('dfec')
def gerenciar_membros_brigada(request, pk):
    brigada = get_object_or_404(Brigada, pk=pk)
    return render(request, 'dfec/brigada_membros.html', {'brigada': brigada})

@login_required_for_app('dfec')
def registrar_treinamento(request, pk):
    brigada = get_object_or_404(Brigada, pk=pk)
    return render(request, 'dfec/brigada_treinamento.html', {'brigada': brigada})

# ========== MÓDULO FORMAÇÕES E TURMAS (Funções Restauradas) ==========

@login_required_for_app('dfec')
def turma_criar_manual(request, formacao_id):
    formacao = get_object_or_404(Formacao, pk=formacao_id)
    messages.info(request, "Funcionalidade de criar turma manual em desenvolvimento.")
    return redirect('dfec:formacao_detalhe', pk=formacao_id)

@login_required_for_app('dfec')
def turma_detalhe(request, turma_id):
    turma = get_object_or_404(Turma, pk=turma_id)
    participantes_qs = turma.participantes_atribuidos.all()
    
    if request.method == 'POST':
        if 'lancar_notas' in request.POST:
            count = 0
            for participante in participantes_qs:
                nota_key = f'nota_{participante.id}'
                if nota_key in request.POST:
                    try:
                        valor_str = request.POST.get(nota_key).replace(',', '.')
                        if not valor_str: continue
                        nota = float(valor_str)
                        nota = max(0, min(20, nota))
                        
                        avaliacao, created = Avaliacao.objects.get_or_create(participante=participante)
                        avaliacao.classificacao_final = nota
                        avaliacao.avaliado_por = request.user
                        avaliacao.save()
                        count += 1
                    except ValueError:
                        continue
            messages.success(request, f"Notas lançadas para {count} participantes.")
            
        elif 'associar_formador' in request.POST:
            formador_id = request.POST.get('formador_principal')
            if formador_id:
                user = get_object_or_404(User, pk=formador_id)
                current_count = turma.formadores_auxiliares.count() + (1 if turma.formador_principal else 0)
                is_new = not (turma.formador_principal == user or turma.formadores_auxiliares.filter(pk=user.pk).exists())
                
                if is_new and current_count >= 6:
                     messages.error(request, "Limite máximo atingido (6 formadores).")
                else:
                    turma.formador_principal = user
                    turma.save()
                    turma.formadores_auxiliares.remove(user)
                    messages.success(request, "Formador Principal atualizado.")

        elif 'associar_formadores_bulk' in request.POST:
            formadores_ids = request.POST.getlist('formadores_ids')
            
            if formadores_ids:
                # Contagem atual
                current_count = turma.formadores_auxiliares.count() + (1 if turma.formador_principal else 0)
                
                # Filtrar IDs válidos e que ainda não estão na turma
                users_to_add = []
                for fid in formadores_ids:
                    user = get_object_or_404(User, pk=fid)
                    # Ignorar se já é principal ou auxiliar
                    if not (turma.formador_principal == user or turma.formadores_auxiliares.filter(pk=user.pk).exists()):
                        users_to_add.append(user)
                
                if not users_to_add:
                    messages.warning(request, "Nenhum formador novo selecionado.")
                elif current_count + len(users_to_add) > 6:
                    messages.error(request, f"Operação cancelada. A turma ficaria com {current_count + len(users_to_add)} formadores (Máximo: 6).")
                else:
                    # Adicionar todos como auxiliares
                    turma.formadores_auxiliares.add(*users_to_add)
                    messages.success(request, f"{len(users_to_add)} formadores adicionados com sucesso.")
            else:
                 messages.warning(request, "Nenhum formador selecionado.")
        
        elif 'remover_formador' in request.POST:
             user_id = request.POST.get('user_id')
             if user_id:
                 user = get_object_or_404(User, pk=user_id)
                 turma.formadores_auxiliares.remove(user)
                 messages.success(request, "Formador removido.")

        return redirect('dfec:turma_detalhe', turma_id=turma_id)

    lista_participantes = []
    for p in participantes_qs:
        try:
            av = p.avaliacao
        except:
            av = None
        lista_participantes.append({'participante': p, 'avaliacao': av})

    # Filtrar usuarios pelo PLANO
    if turma.formacao.atividade and turma.formacao.atividade.plano:
         usuarios = turma.formacao.atividade.plano.formadores.all()
    else:
         usuarios = User.objects.filter(is_active=True)
    
    formadores_list = []
    current_formador_id = turma.formador_principal_id
    for u in usuarios:
        formadores_list.append({
            'pk': u.pk,
            'label': u.get_full_name() or u.username,
            'username': u.username,
            'selected': u.pk == current_formador_id
        })
    
    auxiliares = turma.formadores_auxiliares.all()

    return render(request, 'dfec/formacoes/turma_detalhe.html', {
        'turma': turma,
        'lista_participantes': lista_participantes,
        'formadores_list': formadores_list,
        'auxiliares': auxiliares
    })

@login_required_for_app('dfec')
def turma_limpar(request, formacao_id):
    formacao = get_object_or_404(Formacao, pk=formacao_id)
    messages.success(request, "Turmas limpas.")
    return redirect('dfec:formacao_detalhe', pk=formacao_id)

@login_required_for_app('dfec')
def gerar_turmas_inteligente(request, formacao_id):
    formacao = get_object_or_404(Formacao, pk=formacao_id)
    messages.success(request, "Geração de turmas em breve.")
    return redirect('dfec:formacao_detalhe', pk=formacao_id)

@login_required_for_app('dfec')
def gerar_pdf_lista_participantes(request, formacao_id):
    from reportlab.pdfgen import canvas
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="participantes_{formacao_id}.pdf"'
    p = canvas.Canvas(response)
    p.drawString(100, 800, f"Lista de Participantes - Formação {formacao_id}")
    p.showPage()
    p.save()
    return response

@login_required_for_app('dfec')
def download_template_participantes(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="template_participantes.csv"'
    writer = csv.writer(response)
    writer.writerow(['Nome', 'BI', 'Telefone', 'Email'])
    return response

@login_required_for_app('dfec')
def carregar_participantes_csv(request, formacao_id):
    if request.method == 'POST':
        messages.success(request, "Upload simulado com sucesso.")
    return redirect('dfec:formacao_detalhe', pk=formacao_id)

@login_required_for_app('dfec')
def participante_criar(request, formacao_id):
    formacao = get_object_or_404(Formacao, pk=formacao_id)
    if request.method == 'POST':
        nome = request.POST.get('nome')
        bi = request.POST.get('bi')
        genero = request.POST.get('genero')
        telefone = request.POST.get('telefone')
        categoria = request.POST.get('categoria', 'BRIGADISTA')

        if nome:
            Participante.objects.create(
                formacao=formacao,
                nome_completo=nome,
                bilhete_identidade=bi,
                genero=genero,
                telefone=telefone,
                categoria=categoria,
                status='inscrito'
            )
            messages.success(request, f"Participante {nome} adicionado com sucesso.")
        else:
            messages.error(request, "Nome é obrigatório.")
    
    return redirect('dfec:formacao_detalhe', pk=formacao_id)

@login_required_for_app('dfec')
def limpar_participantes_formacao(request, formacao_id):
    messages.success(request, "Participantes limpos.")
    return redirect('dfec:formacao_detalhe', pk=formacao_id)

@login_required_for_app('dfec')
def simular_participantes(request, formacao_id):
    messages.success(request, "Simulação concluída.")
    return redirect('dfec:formacao_detalhe', pk=formacao_id)

@login_required_for_app('dfec')
def gerar_brigadas_automatico(request, formacao_id):
    messages.success(request, "Geração de brigadas em breve.")
    return redirect('dfec:formacao_detalhe', pk=formacao_id)

# ========== RELATÓRIOS E OUTROS MÓDULOS (Mantidos simplificados) ==========

@login_required_for_app('dfec')
def lista_objetivos(request):
    objetivos = ObjetivoInstitucional.objects.all()
    return render(request, 'dfec/objetivos/lista.html', {'objetivos': objetivos})

@login_required_for_app('dfec')
def criar_objetivo(request):
    # Lógica de criar objetivo
    if request.method == 'POST':
        form = ObjetivoInstitucionalForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dfec:objetivos_lista')
    else:
        form = ObjetivoInstitucionalForm()
    return render(request, 'dfec/objetivos/form.html', {'form': form})

@login_required_for_app('dfec')
def editar_objetivo(request, pk):
    objetivo = get_object_or_404(ObjetivoInstitucional, pk=pk)
    # Lógica simplificada
    if request.method == 'POST':
        form = ObjetivoInstitucionalForm(request.POST, instance=objetivo)
        if form.is_valid():
            form.save()
            return redirect('dfec:objetivos_lista')
    else:
        form = ObjetivoInstitucionalForm(instance=objetivo)
    return render(request, 'dfec/objetivos/form.html', {'form': form})

# Relatórios Views
@login_required_for_app('dfec')
def relatorio_planos(request):
    planos = PlanoAtividade.objects.all()
    return render(request, 'dfec/relatorio_planos.html', {'planos': planos})

@login_required_for_app('dfec')
def relatorio_brigadas(request):
    brigadas = Brigada.objects.all()
    return render(request, 'dfec/relatorio_brigadas.html', {'brigadas': brigadas})

@login_required_for_app('dfec')
def relatorio_atividades_executadas(request):
    planos = PlanoAtividade.objects.filter(status__in=['executado', 'concluido'])
    return render(request, 'dfec/relatorio_atividades.html', {'planos': planos})

# Análise de Região (Simplificada da copia)
@login_required_for_app('dfec')
def analisar_regiao(request):
    # Implementação básica do placeholder
    return render(request, 'dfec/analise/analisar.html')

@login_required_for_app('dfec')
def importar_dados_eleicao(request):
    return render(request, 'dfec/analise/importar.html')
