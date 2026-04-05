import os
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from .models import (
    TipoDocumento, TemplateDocumento, ComponenteDocumento, 
    DocumentoPersonalizado, PlanoLogistico, FaseEleitoral,
    MarcoCritico, NecessidadePessoal, RiscoPlaneamento,
    OrcamentoPlaneamento, MaterialEleitoral, AtividadePlano,
    AlocacaoLogistica
)
from .forms import (
    FaseEleitoralForm, RiscoPlaneamentoForm, OrcamentoPlaneamentoForm,
    MaterialEleitoralForm, AtividadePlanoForm, PlanoLogisticoForm
)
from circuloseleitorais.models import CirculoEleitoral, DivisaoEleicao
from eleicao.models import Eleicao
from django.db.models import Count, Sum

def normalizar_provincia_stae(nome):
    """Utilitário de Soberania: Mapeia nomes modernos para o banco legado de 2023"""
    if not nome: return ""
    nome = nome.upper().strip()
    
    # Mapeamento de nomes STAE para nomes no banco de dados
    mapping = {
        # STAE direction names to database province names
        'MAPUTO CIDADE': 'CIDADE DE MAPUTO',
        'MAPUTO_C': 'CIDADE DE MAPUTO',
        'DPP MAPUTO CIDADE': 'CIDADE DE MAPUTO',
        
        'MAPUTO PROVÍNCIA': 'MAPUTO',
        'MAPUTO PROVINCIA': 'MAPUTO',
        'MAPUTO_P': 'MAPUTO',
        'DPP MAPUTO PROVÍNCIA': 'MAPUTO',
        'DPP MAPUTO PROVINCIA': 'MAPUTO',
        
        'GAZA': 'GAZA',
        'INHAMBANE': 'INHAMBANE',
        'SOFALA': 'SOFALA',
        'MANICA': 'MANICA',
        'TETE': 'TETE',
        
        'ZAMBÉZIA': 'ZAMB ZIA',
        'ZAMBEZIA': 'ZAMB ZIA',
        'ZAMB ZIA': 'ZAMB ZIA',
        
        'NAMPULA': 'NAMPULA',
        
        'CABO DELGADO': 'C.DELGADO',
        'CABO_D': 'C.DELGADO',
        'C.DELGADO': 'C.DELGADO',
        
        'NIASSA': 'NIASSA',
        
        # Reverse mappings (database names to themselves)
        'CIDADE DE MAPUTO': 'CIDADE DE MAPUTO',
        'MAPUTO': 'MAPUTO',
    }
    
    # Primeiro tenta mapeamento exato
    if nome in mapping:
        return mapping[nome]
    
    # Se não encontrar, tenta mapeamento parcial
    for key, value in mapping.items():
        if key in nome or nome in key:
            return value
    
    return nome

# ------------------------------------------------------------------------------
# 1. VISÕES DE COCKPIT E HUB ESTRATÉGICO
# ------------------------------------------------------------------------------

@login_required
def dashboard(request):
    """Cockpit Consolidado: Planeamento (Novo) + Execução (Antigo)"""
    from .models import PlanoLogistico, MarcoCritico
    
    # 1. Obter todos os planos para o seletor (Acesso Total às mil pessoas)
    planos_disponiveis = PlanoLogistico.objects.all().order_by('-id')
    
    # 2. Selecionar o plano a exibir
    plano_id = request.GET.get('plano_id')
    if plano_id:
        plano_ativo = get_object_or_404(PlanoLogistico, id=plano_id)
    else:
        # Padrão: O mais recente (Evita o ecrã vazio se nenhum estiver 'esta_ativo=True')
        plano_ativo = planos_disponiveis.first()
    
    # 2.1 Sincronização de Emergência (Garante que materiais novos apareçam no Cockpit)
    if plano_ativo and plano_ativo.eleicao:
        from .logic import sync_plano_logistico
        sync_plano_logistico(plano_ativo)

    context = {
        'plano_ativo': plano_ativo,
        'planos_todos': planos_disponiveis,
        'eleicao_ativa': None, 'fases': [], 'rh_total': 0, 
        'orcamento_total': 0, 'valor_executado': 0, 'riscos_criticos': 0, 
        'materiais': [], 'atividades': [], 'riscos': [], 'territorio': [], 'proximo_marco': None,
        'custo_total_estimado': 0, 'percent_orcamento': 0
    }
    
    if plano_ativo:
        context['eleicao_ativa'] = plano_ativo.eleicao
        context['fases'] = plano_ativo.fases.all().order_by('ordem')
        context['rh_total'] = sum(n.quantidade_por_mesa for n in plano_ativo.rh_necessidades.all())
        context['orcamento_total'] = plano_ativo.orcamento_total
        context['valor_executado'] = sum(o.valor_executado for o in plano_ativo.orcamento_detalhes.all())
        
        # Dados Operativos Reais (O Coração do Sistema)
        context['materiais'] = plano_ativo.materiais.all().select_related('tipo_dinamico')
        context['atividades'] = plano_ativo.atividades.all().order_by('data_prevista')
        context['riscos'] = plano_ativo.riscos.all().order_by('-nivel_impacto')
        context['territorio'] = plano_ativo.territorio.all()
        
        # Métricas de Agregação
        context['riscos_criticos'] = plano_ativo.riscos.filter(nivel_impacto=3).count()
        total_m = sum(m.custo_total for m in context['materiais'])
        total_a = sum(a.custo_estimado for a in context['atividades'])
        context['custo_total_estimado'] = total_m + total_a
        
        if plano_ativo.orcamento_total > 0:
            context['percent_orcamento'] = min(100, (context['custo_total_estimado'] / plano_ativo.orcamento_total) * 100)
            
        context['proximo_marco'] = MarcoCritico.objects.filter(fase__plano=plano_ativo, data_limite__gte=now().date()).order_by('data_limite').first()
        
    return render(request, 'rs/dashboard.html', context)

@login_required
def planeamento_hub(request):
    """Mapa de Soberania (11 Pontos de Planeamento)"""
    plano = PlanoLogistico.objects.filter(esta_ativo=True).first()
    return render(request, 'rs/planeamento_hub.html', {'plano': plano})

# ------------------------------------------------------------------------------
# 2. GESTÃO DE CICLOS E PLANOS (DADOS REAIS DA EQUIPA)
# ------------------------------------------------------------------------------

@login_required
def lista_eleicoes_rs(request):
    from eleicao.models import Eleicao
    eleicoes = Eleicao.objects.all().order_by('-ano')
    return render(request, 'rs/lista_eleicoes.html', {'eleicoes': eleicoes})

@login_required
def criar_eleicao_rs(request): return redirect('rs:lista_eleicoes')

@login_required
def editar_eleicao_rs(request, pk): return redirect('rs:lista_eleicoes')

@login_required
def eliminar_eleicao_rs(request, pk): return redirect('rs:lista_eleicoes')

@login_required
def divisao_eleicao_index(request):
    """PONTO 2: Mapeamento Geográfico Oficial de Moçambique por Eleição"""
    from eleicao.models import Eleicao
    from circuloseleitorais.models import DivisaoAdministrativa, DivisaoEleicao, CirculoEleitoral
    from django.db.models import Q
    
    eleicoes = Eleicao.objects.all().order_by('-ano')
    eleicao_id = request.GET.get('eleicao_id') or request.POST.get('eleicao_id')
    eleicao_selecionada = None
    distritos_associados = []

    if eleicao_id:
        eleicao_selecionada = get_object_or_404(Eleicao, id=eleicao_id)
        # Recuperar associações existentes
        distritos_associados_novos = list(DivisaoEleicao.objects.filter(
            eleicao=eleicao_selecionada, nivel='distrito'
        ).values_list('divisao_base_id', flat=True))
        
        # Se não houver associações no modelo novo, verificar no legado (CirculoEleitoral)
        if not distritos_associados_novos:
            distritos_associados = list(CirculoEleitoral.objects.filter(
                eleicao=eleicao_selecionada
            ).values_list('id', flat=True))
        else:
            distritos_associados = distritos_associados_novos

    if request.method == 'POST' and eleicao_selecionada:
        novos_distritos_ids = request.POST.getlist('distritos')
        DivisaoEleicao.objects.filter(eleicao=eleicao_selecionada).delete()
        
        distritos_base = DivisaoAdministrativa.objects.filter(id__in=novos_distritos_ids)
        for dist_base in distritos_base:
            prov_base = dist_base.parent
            if prov_base:
                prov_eleicao, _ = DivisaoEleicao.objects.get_or_create(
                    eleicao=eleicao_selecionada,
                    codigo=prov_base.codigo,
                    defaults={'nome': prov_base.nome, 'nivel': 'provincia', 'divisao_base': prov_base}
                )
                DivisaoEleicao.objects.get_or_create(
                    eleicao=eleicao_selecionada,
                    codigo=dist_base.codigo,
                    defaults={'nome': dist_base.nome, 'nivel': 'distrito', 'parent': prov_eleicao, 'divisao_base': dist_base}
                )
        
        messages.success(request, f"Divisão Territorial para {eleicao_selecionada.nome} atualizada!")
        return redirect(f"{reverse('rs:divisao_eleicao_index')}?eleicao_id={eleicao_id}")

    # --- RECUPERAÇÃO DE SOBERANIA ---
    # Busca base estratégica
    provincias_base = DivisaoAdministrativa.objects.filter(nivel='provincia').order_by('nome')
    distritos_base = DivisaoAdministrativa.objects.filter(nivel='distrito').order_by('nome')
    
    if not distritos_base.exists():
        # FALLBACK: Usar CirculoEleitoral como Mapa Base se DivisaoAdministrativa estiver vazia
        legado = CirculoEleitoral.objects.all().order_by('provincia', 'nome')
        mapa_provincias = {}
        for c in legado:
            p_nome = c.provincia.upper()
            if p_nome not in mapa_provincias:
                mapa_provincias[p_nome] = []
            mapa_provincias[p_nome].append({
                'id': c.id, 
                'nome': c.nome,
                'codigo': c.codigo
            })
        
        # Transformar para o formato que o template espera
        provincias_final = []
        for p_nome, dists in mapa_provincias.items():
            provincias_final.append({
                'nome': p_nome,
                'distritos_lista': dists
            })
        
        return render(request, 'rs/divisao_eleicao_index.html', {
            'eleicoes': eleicoes,
            'eleicao_selecionada': eleicao_selecionada,
            'provincias': provincias_final,
            'distritos': [], # Template buscará em distritos_lista dentro de provincias
            'distritos_associados': distritos_associados,
            'soberania_ativa': 'legado'
        })

    return render(request, 'rs/divisao_eleicao_index.html', {
        'eleicoes': eleicoes,
        'eleicao_selecionada': eleicao_selecionada,
        'provincias': provincias_base,
        'distritos': distritos_base,
        'distritos_associados': distritos_associados,
        'soberania_ativa': 'base'
    })

@login_required
def lista_planos(request):
    planos = PlanoLogistico.objects.all().order_by('-id')
    return render(request, 'rs/lista_planos.html', {'planos': planos})

@login_required
def criar_plano(request):
    """Criação de Novo Plano Logístico (Recuperado)"""
    if request.method == 'POST':
        form = PlanoLogisticoForm(request.POST)
        if form.is_valid():
            plano = form.save()
            messages.success(request, f"O plano '{plano.nome}' foi criado com sucesso.")
            return redirect('rs:detalhes_plano', plano_id=plano.id)
    else:
        form = PlanoLogisticoForm()
    return render(request, 'rs/form_plano.html', {
        'form': form, 
        'titulo': 'Criar Novo Plano Logístico'
    })

@login_required
def detalhes_plano(request, plano_id):
    """Pormenores Operativos de um Plano Específico (Soberania)"""
    plano = get_object_or_404(PlanoLogistico, id=plano_id)
    materiais = plano.materiais.all()
    atividades = plano.atividades.all()
    
    # Cálculos Financeiros
    total_materiais = sum(m.custo_total for m in materiais)
    total_atividades = sum(a.custo_estimado for a in atividades)
    custo_total_estimado = total_materiais + total_atividades
    
    percent_orcamento = 0
    if plano.orcamento_total > 0:
        percent_orcamento = (custo_total_estimado / plano.orcamento_total) * 100

    return render(request, 'rs/detalhes_plano.html', {
        'plano': plano, 
        'materiais': materiais,
        'atividades': atividades,
        'total_materiais': total_materiais,
        'total_atividades': total_atividades,
        'custo_total_estimado': custo_total_estimado,
        'percent_orcamento': min(100, percent_orcamento),
        'planos_disponiveis': PlanoLogistico.objects.exclude(id=plano.id)
    })

@login_required
def editar_plano(request, pk):
    """Edição de Plano Logístico (Recuperado)"""
    plano = get_object_or_404(PlanoLogistico, pk=pk)
    if request.method == 'POST':
        form = PlanoLogisticoForm(request.POST, instance=plano)
        if form.is_valid():
            form.save()
            messages.success(request, f"Definições do plano '{plano.nome}' atualizadas.")
            return redirect('rs:detalhes_plano', plano_id=plano.id)
    else:
        form = PlanoLogisticoForm(instance=plano)
    return render(request, 'rs/form_plano.html', {
        'form': form, 
        'plano': plano, 
        'titulo': f'Editar: {plano.nome}'
    })

@login_required
def importar_distribuicao_plano(request, plano_id): return redirect('rs:detalhes_plano', plano_id=plano_id)

@login_required
def adicionar_material_plano(request, plano_id):
    plano = get_object_or_404(PlanoLogistico, id=plano_id)
    if request.method == 'POST':
        form = MaterialEleitoralForm(request.POST)
        if form.is_valid():
            material = form.save(commit=False)
            material.plano = plano
            material.eleicao = plano.eleicao
            material.tipo_operacao = plano.tipo_operacao
            material.save()
            messages.success(request, f"Material '{material.item}' adicionado ao plano.")
            return redirect('rs:detalhes_plano', plano_id=plano.id)
    else:
        form = MaterialEleitoralForm(initial={'eleicao': plano.eleicao})
    # Mapa Geográfico Inteligente (Por Província) - Usando dados reais
    distritos_map = {}
    from django.db.models import Count, Sum
    from circuloseleitorais.models import DivisaoEleicao
    
    # Buscar unidades oficiais para chaves consistentes no mapa JS
    unid_choices = [c[0] for c in AlocacaoLogistica.DIRECOES_STAE if c[0] != 'CENTRAL']
    
    for e in Eleicao.objects.all():
        distritos_map[e.id] = {}
        
        # Tentar primeiro com DivisaoEleicao (dados administrativos)
        divisoes_distritos = DivisaoEleicao.objects.filter(eleicao=e, nivel='distrito')
        divisoes_provincias = DivisaoEleicao.objects.filter(eleicao=e, nivel='provincia')
        
        # Contagem total (fallback)
        total_distritos = divisoes_distritos.count()
        # Para mesas, tentar obter de CirculoEleitoral ou usar estimativa
        total_mesas = 0
        if e.circulos.exists():
            total_mesas = e.circulos.aggregate(t=Sum('num_mesas'))['t'] or 0
        else:
            # Estimativa: 1 mesa por 500 eleitores ou padrão
            total_mesas = total_distritos * 10  # Estimativa conservadora
        
        distritos_map[e.id]['TOTAL'] = {'distritos': total_distritos, 'mesas': total_mesas}
        
        # Contagem por província para cada unidade do STAE
        for code in unid_choices:
            # Traduzir label STAE para nome da província
            label_stae = dict(AlocacaoLogistica.DIRECOES_STAE).get(code, "")
            prov_nome_busca = normalizar_provincia_stae(label_stae.replace('DPP ', ''))
            
            # Tentar encontrar a província correspondente
            provincia_div = divisoes_provincias.filter(nome__iexact=prov_nome_busca).first()
            if provincia_div:
                # Contar distritos desta província
                distritos_prov = divisoes_distritos.filter(parent=provincia_div).count()
                # Para mesas, tentar obter de CirculoEleitoral
                mesas_prov = 0
                if e.circulos.exists():
                    circulos_prov = e.circulos.filter(provincia__iexact=prov_nome_busca)
                    mesas_prov = circulos_prov.aggregate(t=Sum('num_mesas'))['t'] or 0
                else:
                    # Estimativa
                    mesas_prov = distritos_prov * 10
                
                distritos_map[e.id][code] = {
                    'distritos': distritos_prov,
                    'mesas': mesas_prov
                }
            else:
                # Fallback para o método antigo (circulos)
                circulos_prov = e.circulos.filter(provincia__iexact=prov_nome_busca)
                distritos_map[e.id][code] = {
                    'distritos': circulos_prov.count(),
                    'mesas': circulos_prov.aggregate(t=Sum('num_mesas'))['t'] or 0
                }
    
    context = {
        'form': form,
        'plano': plano,
        'eleicao': plano.eleicao,
        'tipo': 'Material',
        'distritos_map': json.dumps(distritos_map)
    }
    return render(request, 'rs/form_componente.html', context)

@login_required
def adicionar_atividade_plano(request, plano_id):
    plano = get_object_or_404(PlanoLogistico, id=plano_id)
    if request.method == 'POST':
        form = AtividadePlanoForm(request.POST)
        if form.is_valid():
            atividade = form.save(commit=False)
            atividade.plano = plano
            atividade.save()
            messages.success(request, f"Atividade '{atividade.nome}' registada.")
            return redirect('rs:detalhes_plano', plano_id=plano.id)
    else:
        form = AtividadePlanoForm()
    return render(request, 'rs/form_componente.html', {
        'form': form, 
        'plano': plano,
        'tipo': 'Atividade'
    })

# ------------------------------------------------------------------------------
# 3. OS 11 PONTOS OPERACIONAIS (CRONOGRAMA, RISCO, FINANCEIRO)
# ------------------------------------------------------------------------------

@login_required
def calendario_eleitoral(request):
    plano = PlanoLogistico.objects.filter(esta_ativo=True).first()
    if request.method == 'POST' and request.POST.get('action') == 'add_fase' and plano:
        form = FaseEleitoralForm(request.POST)
        if form.is_valid():
            fase = form.save(commit=False); fase.plano = plano; fase.save()
            messages.success(request, f"Fase '{fase.nome}' registada com sucesso.")
            return redirect('rs:calendario_eleitoral')
    form = FaseEleitoralForm()
    fases = plano.fases.all().order_by('ordem') if plano else []
    return render(request, 'rs/calendario.html', {'fases': fases, 'plano': plano, 'form': form})

@login_required
def gestao_rh_plano(request):
    plano = PlanoLogistico.objects.filter(esta_ativo=True).first()
    return render(request, 'rs/gestao_rh.html', {'plano': plano, 'necessidades': plano.rh_necessidades.all() if plano else []})

@login_required
def matriz_riscos(request):
    plano = PlanoLogistico.objects.filter(esta_ativo=True).first()
    if request.method == 'POST' and request.POST.get('action') == 'add_risco' and plano:
        form = RiscoPlaneamentoForm(request.POST)
        if form.is_valid():
            risco = form.save(commit=False); risco.plano = plano; risco.save()
            messages.success(request, f"Risco '{risco.area}' catalogado.")
            return redirect('rs:matriz_riscos')
    form = RiscoPlaneamentoForm()
    return render(request, 'rs/matriz_riscos.html', {'riscos': plano.riscos.all() if plano else [], 'plano': plano, 'form': form})

@login_required
def planeamento_financeiro(request):
    plano = PlanoLogistico.objects.filter(esta_ativo=True).first()
    if request.method == 'POST' and request.POST.get('action') == 'add_financeiro' and plano:
        form = OrcamentoPlaneamentoForm(request.POST)
        if form.is_valid():
            orc = form.save(commit=False); orc.plano = plano; orc.save()
            messages.success(request, "Orçamento registado.")
            return redirect('rs:planeamento_financeiro')
    form = OrcamentoPlaneamentoForm()
    return render(request, 'rs/financeiro.html', {'orcamentos': plano.orcamento_detalhes.all() if plano else [], 'plano': plano, 'form': form})

@login_required
def planeamento_territorial(request):
    plano = PlanoLogistico.objects.filter(esta_ativo=True).first()
    return render(request, 'rs/territorial.html', {'plano': plano, 'territorio': plano.territorio.all() if plano else []})

# ------------------------------------------------------------------------------
# 4. CONSTRUTOR E MOCKS TÉCNICOS (MANUTENÇÃO DE SISTEMA)
# ------------------------------------------------------------------------------

@login_required
def documentos_view(request):
    from .models import TipoDocumento
    return render(request, 'rs/documentos.html', {'tipos': TipoDocumento.objects.all().order_by('nome')})

@login_required
def galeria_templates(request, tipo_id):
    from .models import TipoDocumento, TemplateDocumento
    tipo = get_object_or_404(TipoDocumento, id=tipo_id)
    return render(request, 'rs/galeria_templates.html', {'tipo': tipo, 'templates': tipo.templates.filter(ativo=True)})

@login_required
def construtor_documento(request, tipo_id):
    from .models import TipoDocumento, TemplateDocumento, ComponenteDocumento
    tipo = get_object_or_404(TipoDocumento, id=tipo_id)
    return render(request, 'rs/construtor_documento.html', {'tipo': tipo, 'componentes_agrupados': {}})

@csrf_exempt
@login_required
def guardar_documento_ajax(request): return JsonResponse({'status': 'ok'})

@login_required
def exportar_pdf_documento(request, doc_id=None): return HttpResponse("PDF")

@login_required
def api_dados_eleicao(request, eleicao_id=None):
    """API Real de Soberania: Recupera qualquer eleição ativa ou histórica"""
    from eleicao.models import Eleicao
    if eleicao_id:
        eleicao = get_object_or_404(Eleicao, id=eleicao_id)
    else:
        eleicao = Eleicao.objects.filter(ativo=True).order_by('-ano').first()
    
    if not eleicao:
        return JsonResponse({'status': 'erro', 'message': 'Nenhuma eleição configurada no sistema.'}, status=404)

    return JsonResponse({
        'eleicao': {
            'id': eleicao.id,
            'nome': eleicao.nome,
            'ano': eleicao.ano,
            'tipo': eleicao.tipo,
            'data': eleicao.data_votacao.isoformat() if eleicao.data_votacao else None
        },
        'circulos': list(eleicao.circulos.values('id', 'nome', 'num_eleitores', 'num_mesas'))
    })

@login_required
def inicializar_templates_padrao(request): return redirect('rs:documentos')

@login_required
def sugerir_ia_logistica(request, plano_id): return JsonResponse({'status': 'ok'})

@login_required
def distribuir_material(request, material_id):
    """PONTO 2 e 4: Distribuição Geográfica e Provincial de Soberania"""
    from django.db import connection
    try:
        material = get_object_or_404(MaterialEleitoral, id=material_id)
    except Exception as e:
        if "localizacao_destino" in str(e) or "column" in str(e):
            # AUTO-REPARO DE EMERGÊNCIA
            with connection.cursor() as cursor:
                cursor.execute("ALTER TABLE rs_materialeleitoral ADD COLUMN IF NOT EXISTS localizacao_destino VARCHAR(100);")
                cursor.execute("ALTER TABLE rs_atividadeplano ADD COLUMN IF NOT EXISTS responsaveis TEXT;")
            material = get_object_or_404(MaterialEleitoral, id=material_id)
        else:
            raise e
    # Importar AlocacaoLogistica diretamente para evitar circular imports se necessário
    from .models import AlocacaoLogistica
    from eleicao.models import Eleicao
    from circuloseleitorais.models import CirculoEleitoral
    from django.db.models import Sum
    
    unidades = AlocacaoLogistica.DIRECOES_STAE
    eleicao_ref_id = request.GET.get('eleicao_ref_id')
    stats = {}
    
    if eleicao_ref_id:
        e_ref = get_object_or_404(Eleicao, id=eleicao_ref_id)
        # Tentar obter estatísticas do legado de Moçambique
        for code, name in unidades:
            if code == 'CENTRAL': continue
            # Normalização de Soberania (Tratar abreviaturas do banco legado como C.DELGADO)
            prov_nome = normalizar_provincia_stae(name.replace('DPP ', ''))
            circulos = CirculoEleitoral.objects.filter(eleicao=e_ref, provincia__iexact=prov_nome)
            stats[code] = {
                'distritos': circulos.count(),
                'mesas': circulos.aggregate(t=Sum('num_mesas'))['t'] or 0
            }

    if request.method == 'POST':
        for code, name in unidades:
            val_nec = request.POST.get(f'qtd_nec_{code}')
            val_ext = request.POST.get(f'qtd_ext_{code}')
            val_dist = request.POST.get(f'n_dist_{code}')
            val_mesas = request.POST.get(f'n_mesas_{code}')
            
            if val_nec is not None and val_ext is not None:
                qtd_nec = int(val_nec or 0)
                qtd_ext = int(val_ext or 0)
                n_dist = int(val_dist or 0)
                n_mesas = int(val_mesas or 0)
                
                if qtd_nec > 0 or qtd_ext > 0:
                    AlocacaoLogistica.objects.update_or_create(
                        material_nacional=material, unidade=code,
                        defaults={
                            'quantidade_necessaria': qtd_nec,
                            'quantidade_existente': qtd_ext,
                            'num_distritos': n_dist,
                            'num_mesas': n_mesas
                        }
                    )
        messages.success(request, f"Distribuição de '{material.item}' guardada com sucesso.")
        return redirect('rs:detalhes_plano', plano_id=material.plano.id)

    alocacoes = {aloc.unidade: aloc for aloc in material.alocacoes.all()}
    eleicoes = Eleicao.objects.all().order_by('-ano')
    
    return render(request, 'rs/distribuir_material.html', {
        'material': material,
        'unidades': unidades,
        'alocacoes': alocacoes,
        'eleicoes': eleicoes,
        'eleicao_ref_id': int(eleicao_ref_id) if eleicao_ref_id else None,
        'stats': stats
    })

@login_required
def criar_tipo_documento(request): return redirect('rs:documentos')

@login_required
def editar_tipo_documento(request, tipo_id): return redirect('rs:documentos')

@login_required
def eliminar_tipo_documento(request, tipo_id): return redirect('rs:documentos')

@login_required
def inicializar_docs_padrao(request): return redirect('rs:documentos')

@login_required
def preview_cartao_eleitor(request): return HttpResponse("M")

@login_required
def preview_generico(request, tipo_id): return HttpResponse("M")

@login_required
def lancar_edital(request): return redirect('rs:dashboard')

@login_required
def gerar_plano_logistico_auto(request, eleicao_id): return redirect('rs:dashboard')

@login_required
def decidir_modelo_visual(request, modelo_id, decisao): return redirect('rs:dashboard')

@login_required
def editar_material(request, material_id):
    material = get_object_or_404(MaterialEleitoral, id=material_id)
    if request.method == 'POST':
        form = MaterialEleitoralForm(request.POST, instance=material)
        if form.is_valid():
            form.save()
            messages.success(request, f"Material '{material.item}' atualizado.")
            return redirect('rs:detalhes_plano', plano_id=material.plano.id)
    else:
        form = MaterialEleitoralForm(instance=material)
        
    # Mapa Geográfico Inteligente (Por Província) para Edição
    distritos_map = {}
    unid_choices = [c[0] for c in AlocacaoLogistica.DIRECOES_STAE if c[0] != 'CENTRAL']
    for e in Eleicao.objects.all():
        distritos_map[e.id] = {'TOTAL': e.circulos.count()}
        for code in unid_choices:
            label_stae = dict(AlocacaoLogistica.DIRECOES_STAE)[code]
            prov_nome_busca = normalizar_provincia_stae(label_stae.replace('DPP ', ''))
            distritos_map[e.id][code] = e.circulos.filter(provincia__iexact=prov_nome_busca).count()

    return render(request, 'rs/form_componente.html', {
        'form': form,
        'plano': material.plano,
        'material': material,
        'tipo': 'Material',
        'edit': True,
        'distritos_map': json.dumps(distritos_map)
    })

@login_required
def eliminar_material(request, material_id):
    material = get_object_or_404(MaterialEleitoral, id=material_id)
    plano_id = material.plano.id
    nome = material.item
    material.delete()
    messages.warning(request, f"O material '{nome}' foi removido do plano.")
    return redirect('rs:detalhes_plano', plano_id=plano_id)

@login_required
def criar_requisito_material(request): return redirect('rs:dashboard')

@login_required
def gestao_categorias_materiais(request): return render(request, 'rs/dashboard.html')

@login_required
def gestao_tipos_materiais(request): return render(request, 'rs/dashboard.html')

@login_required
def eliminar_tipo_material(request, pk): return redirect('rs:dashboard')

@login_required
def editar_atividade(request, atividade_id):
    atividade = get_object_or_404(AtividadePlano, id=atividade_id)
    if request.method == 'POST':
        form = AtividadePlanoForm(request.POST, instance=atividade)
        if form.is_valid():
            form.save()
            messages.success(request, f"Atividade '{atividade.nome}' atualizada.")
            return redirect('rs:detalhes_plano', plano_id=atividade.plano.id)
    else:
        form = AtividadePlanoForm(instance=atividade)
    return render(request, 'rs/form_componente.html', {
        'form': form, 
        'atividade': atividade, 
        'plano': atividade.plano,
        'tipo': 'Atividade',
        'edit': True
    })

@login_required
def eliminar_atividade(request, atividade_id):
    atividade = get_object_or_404(AtividadePlano, id=atividade_id)
    plano_id = atividade.plano.id
    nome = atividade.nome
    atividade.delete()
    messages.warning(request, f"A atividade '{nome}' foi eliminada.")
    return redirect('rs:detalhes_plano', plano_id=plano_id)

@login_required
def selecao_relatorio_material(request, plano_id): return render(request, 'rs/dashboard.html')

@login_required
def gerar_pdf_plano(request, plano_id): return HttpResponse("PDF")

@login_required
def inicializar_catalogo_stae(request): return redirect('rs:dashboard')
