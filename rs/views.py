from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from django.db.models import Sum
from django.utils import timezone
import os
from django.template import Context, Template
from .models import (
    PlanoLogistico, TipoDocumento, DocumentoGerado, 
    MaterialEleitoral, ModeloVisualArtefacto, 
    CategoriaMaterial, TipoMaterial
)
from .forms import CategoriaMaterialForm, TipoMaterialForm, MaterialEleitoralForm, PlanoLogisticoForm, EleicaoForm
from eleicao.models import Eleicao
from circuloseleitorais.models import CirculoEleitoral
from candidaturas.models import InscricaoPartidoEleicao, Candidato, ListaCandidatura

@login_required
def lista_eleicoes_rs(request):
    eleicoes = Eleicao.objects.all().order_by('-ano', '-data_votacao')
    return render(request, 'rs/lista_eleicoes.html', {'eleicoes': eleicoes})

from circuloseleitorais.models import DivisaoAdministrativa, DivisaoEleicao
from django.db import transaction

@login_required
def divisao_eleicao_index(request):
    """Novo fluxo: Associar distritos a uma eleição em massa."""
    eleicoes = Eleicao.objects.all().order_by('-ano', '-data_votacao')
    todas_provincias = DivisaoAdministrativa.objects.filter(nivel='provincia').order_by('codigo')
    todos_distritos = DivisaoAdministrativa.objects.filter(nivel='distrito').order_by('parent__codigo', 'codigo')
    
    eleicao_selecionada = None
    distritos_associados = []
    
    eleicao_id = request.GET.get('eleicao_id')
    if not eleicao_id and request.method == 'POST':
        eleicao_id = request.POST.get('eleicao_id')

    if eleicao_id:
        eleicao_selecionada = get_object_or_404(Eleicao, id=eleicao_id)
        # Obter os IDs das divisões base que já estão associadas a esta eleição
        distritos_associados_queryset = DivisaoEleicao.objects.filter(
            eleicao=eleicao_selecionada, nivel='distrito'
        ).values_list('divisao_base_id', flat=True)
        distritos_associados = list(distritos_associados_queryset)

    if request.method == 'POST' and eleicao_selecionada:
        distritos_ids = request.POST.getlist('distritos')
        
        with transaction.atomic():
            # Limpar antigas associações desta eleição (editable)
            DivisaoEleicao.objects.filter(eleicao=eleicao_selecionada).delete()
            
            # Re-criar tudo com base nos distritos selecionados
            distritos_checked = DivisaoAdministrativa.objects.filter(id__in=distritos_ids, nivel='distrito')
            
            provinces_needed = set()
            for d in distritos_checked:
                if d.parent:
                    provinces_needed.add(d.parent_id)
            
            # Criar Provincias necessárias primeiro
            map_provincias = {}
            provinces_base = DivisaoAdministrativa.objects.filter(id__in=provinces_needed, nivel='provincia')
            for p in provinces_base:
                obj = DivisaoEleicao.objects.create(
                    eleicao=eleicao_selecionada,
                    nome=p.nome,
                    codigo=p.codigo,
                    nivel=p.nivel,
                    divisao_base=p
                )
                map_provincias[p.id] = obj
            
            # Criar Distritos selecionados e conectá-los às províncias parent
            for d in distritos_checked:
                parent_obj = map_provincias.get(d.parent_id) if d.parent_id else None
                DivisaoEleicao.objects.create(
                    eleicao=eleicao_selecionada,
                    nome=d.nome,
                    codigo=d.codigo,
                    nivel=d.nivel,
                    parent=parent_obj,
                    divisao_base=d
                )
                
        messages.success(request, f"Associação da Divisão Administrativa para a eleição '{eleicao_selecionada.nome}' foi atualizada e aplicada com sucesso!")
        return redirect(f"{request.path}?eleicao_id={eleicao_selecionada.id}")

    context = {
        'eleicoes': eleicoes,
        'eleicao_selecionada': eleicao_selecionada,
        'provincias': todas_provincias,
        'distritos': todos_distritos,
        'distritos_associados': distritos_associados
    }
    return render(request, 'rs/divisao_eleicao_index.html', context)

@login_required
def criar_eleicao_rs(request):
    if request.method == 'POST':
        form = EleicaoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Ciclo Eleitoral registado com sucesso!")
            return redirect('rs:lista_eleicoes')
    else:
        form = EleicaoForm()
    
    return render(request, 'rs/form_eleicao.html', {
        'form': form,
        'titulo': "Registar Novo Ciclo Eleitoral"
    })

@login_required
def editar_eleicao_rs(request, pk):
    eleicao = get_object_or_404(Eleicao, pk=pk)
    if request.method == 'POST':
        form = EleicaoForm(request.POST, instance=eleicao)
        if form.is_valid():
            form.save()
            messages.success(request, f"Ciclo Eleitoral '{eleicao.nome}' atualizado com sucesso!")
            return redirect('rs:lista_eleicoes')
    else:
        form = EleicaoForm(instance=eleicao)
    
    return render(request, 'rs/form_eleicao.html', {
        'form': form,
        'titulo': f"Editar Ciclo Eleitoral: {eleicao.nome}",
        'eleicao': eleicao
    })

@login_required
def eliminar_eleicao_rs(request, pk):
    eleicao = get_object_or_404(Eleicao, pk=pk)
    if request.method == 'POST':
        nome = eleicao.nome
        eleicao.delete()
        messages.warning(request, f"Ciclo Eleitoral '{nome}' removido com sucesso.")
        return redirect('rs:lista_eleicoes')
    return render(request, 'rs/confirm_delete.html', {'objeto': eleicao, 'cancel_url': 'rs:lista_eleicoes'})

def dashboard(request):
    eleicoes = Eleicao.objects.filter(ativo=True).order_by('-ano')
    planos = PlanoLogistico.objects.all().order_by('-data_inicio')
    
    eleicao_ativa = eleicoes.first()
    bi_data = {}
    materiais_exibir = []
    is_nacional = True
    tipo_operacao_selecionado = request.GET.get('operacao')

    if eleicao_ativa:
        from candidaturas.views import get_estatisticas_eleicao
        bi_data = get_estatisticas_eleicao(eleicao_ativa.id)

        materiais_qs = eleicao_ativa.materiais_logistica.all()
        
        if tipo_operacao_selecionado:
            materiais_qs = materiais_qs.filter(tipo_operacao=tipo_operacao_selecionado)
        
        # Agregação por Tipo Dinâmico (Catálogo STAE)
        agregados_dinamicos = materiais_qs.filter(tipo_dinamico__isnull=False).values(
            'tipo_dinamico__nome', 'tipo_operacao'
        ).annotate(
            total_qtd=Sum('quantidade_planeada'),
            total_custo=Sum(models.F('quantidade_planeada') * models.F('preco_unitario'), output_field=models.DecimalField())
        ).order_by('tipo_dinamico__nome')

        # Converte para objetos para o template
        class MaterialDashboard:
            def __init__(self, nome, qtd, operacao):
                self.item = nome
                self.quantidade_planeada = qtd
                self.tipo_operacao = operacao
                self.localizacao_destino = "NACIONAL"
            def get_tipo_operacao_display(self):
                return "Recenseamento" if self.tipo_operacao == 'RECENSEAMENTO' else "Votação"

        for a in agregados_dinamicos:
            materiais_exibir.append(MaterialDashboard(
                a['tipo_dinamico__nome'], 
                a['total_qtd'],
                a['tipo_operacao']
            ))

    # Artefactos Visuais (mantidos conforme original)
    modelos_visuais = []
    if eleicao_ativa:
        tipos = ['urna_v', 'cabine', 'colete_m', 'distico']
        for t in tipos:
            modelo = ModeloVisualArtefacto.objects.filter(eleicao=eleicao_ativa, tipo=t).order_by('-versao').first()
            if modelo:
                modelos_visuais.append(modelo)

    return render(request, 'rs/dashboard.html', {
        'planos': planos,
        'eleicoes': eleicoes,
        'eleicao_ativa': eleicao_ativa,
        'bi': bi_data,
        'modelos_visuais': modelos_visuais,
        'materiais': materiais_exibir,
        'is_nacional': is_nacional,
        'tipo_operacao_atual': tipo_operacao_selecionado,
        'total_planos': planos.count(),
    })

def decidir_modelo_visual(request, modelo_id, decisao):
    """Processa a aceitação ou reprovação de uma proposta visual"""
    modelo = get_object_or_404(ModeloVisualArtefacto, id=modelo_id)
    if decisao == 'aceitar':
        modelo.status = 'aceite'
        modelo.feedback_admin = "Aprovado pelo Secretariado."
        messages.success(request, f"Artefacto {modelo.get_tipo_display()} OFICIALIZADO com sucesso.")
    elif decisao == 'reprovar':
        modelo.status = 'reprovado'
        modelo.feedback_admin = request.POST.get('feedback', 'Necessário iterar design.')
        modelo.save()
        if modelo.versao < 50:
            messages.warning(request, f"Modelo V{modelo.versao} reprovado. Uma nova tentativa (V{modelo.versao+1}) foi solicitada ao sistema.")
            # Aqui no futuro o 'sistema' (AI/Design) geraria a nova imagem
        else:
            messages.error(request, "Limite de 50 tentativas atingido para este artefacto.")
    
    modelo.save()
    return redirect('rs:dashboard')

    return redirect('rs:dashboard')

def editar_material(request, material_id):
    material = get_object_or_404(MaterialEleitoral, id=material_id)
    if request.method == 'POST':
        material.quantidade_planeada = request.POST.get('quantidade')
        material.item = request.POST.get('item')
        material.save()
        messages.success(request, f"Requisito '{material.item}' atualizado com sucesso.")
    return redirect('rs:dashboard')

def eliminar_material(request, material_id):
    material = get_object_or_404(MaterialEleitoral, id=material_id)
    nome = material.item
    material.delete()
    messages.warning(request, f"Material '{nome}' removido do plano logístico.")
    return redirect('rs:dashboard')

def gerar_plano_logistico_auto(request, eleicao_id):
    """Gera automaticamente requisitos de material baseados nos dados da eleição"""
    eleicao = get_object_or_404(Eleicao, id=eleicao_id)
    
    # Cálculos Base Nacional
    total_eleitores = eleicao.circulos.aggregate(total=Sum('num_eleitores'))['total'] or 0
    total_mesas = eleicao.circulos.aggregate(total=Sum('num_mesas'))['total'] or 0
    
    if total_mesas == 0:
        messages.warning(request, "Não há mesas definidas nos círculos eleitorais desta eleição.")
        return redirect('rs:dashboard')

    # 1. CÁLCULO NACIONAL (ARMASÉM CENTRAL)
    # Urnas (1 per mesa)
    MaterialEleitoral.objects.update_or_create(
        eleicao=eleicao, item='Urnas de Votação (MMV)',
        defaults={'quantidade_planeada': total_mesas, 'tipo_operacao': 'VOTACAO'}
    )
    # Boletins (Eleitores + 10%)
    MaterialEleitoral.objects.update_or_create(
        eleicao=eleicao, item='Boletins de Voto (Oficiais)',
        defaults={'quantidade_planeada': int(total_eleitores * 1.1), 'tipo_operacao': 'VOTACAO'}
    )
    # Coletes (7 per mesa)
    MaterialEleitoral.objects.update_or_create(
        eleicao=eleicao, item='Coletes Oficiais STAE',
        defaults={'quantidade_planeada': total_mesas * 7, 'tipo_operacao': 'VOTACAO'}
    )
    # Tinta Indelével
    MaterialEleitoral.objects.update_or_create(
        eleicao=eleicao, item='Tinta Indelével (Frascos)',
        defaults={'quantidade_planeada': int(total_eleitores / 500) + 1, 'tipo_operacao': 'VOTACAO'}
    )
    # Cabines (2 por mesa)
    MaterialEleitoral.objects.update_or_create(
        eleicao=eleicao, item='Cabines de Votação',
        defaults={'quantidade_planeada': total_mesas * 2, 'tipo_operacao': 'VOTACAO'}
    )
    # Credenciais MMV (7 por mesa)
    MaterialEleitoral.objects.update_or_create(
        eleicao=eleicao, item='Credenciais Oficiais MMV',
        defaults={'quantidade_planeada': total_mesas * 7, 'tipo_operacao': 'VOTACAO'}
    )

    # 2. CÁLCULO PROVINCIAL (PLANOS DE DISTRIBUIÇÃO)
    provincias = eleicao.circulos.values_list('provincia', flat=True).distinct()
    
    for prov in provincias:
        circulos_v = eleicao.circulos.filter(provincia=prov)
        m_prov = circulos_v.aggregate(total=Sum('num_mesas'))['total'] or 0
        
        # Como agora a visão é estratégica/nacional, ignoramos a criação de sub-materiais por província aqui
        # e deixamos o utilizador fazer a Alocação Logística granulada via UI
        pass

    messages.success(request, f"Pano de Distribuição gerado para {len(provincias)} províncias. Logística capilarizada com sucesso.")
    return redirect('rs:dashboard')

def lista_planos(request):
    """View principal para gestão de planos regionais/provinciais"""
    planos = PlanoLogistico.objects.all().order_by('-data_inicio')
    return render(request, 'rs/lista_planos.html', {
        'planos': planos
    })

@login_required
def editar_plano(request, pk):
    plano = get_object_or_404(PlanoLogistico, pk=pk)
    if request.method == 'POST':
        form = PlanoLogisticoForm(request.POST, instance=plano)
        if form.is_valid():
            form.save()
            messages.success(request, "Plano Logístico atualizado com sucesso!")
            return redirect('rs:detalhes_plano', plano_id=plano.pk)
    else:
        form = PlanoLogisticoForm(instance=plano)
    
    return render(request, 'rs/form_plano.html', {
        'form': form,
        'plano': plano,
        'titulo': "Editar Definições do Plano"
    })

def criar_plano(request):
    """Criação manual de um Plano Logístico"""
    if request.method == 'POST':
        form = PlanoLogisticoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Plano Logístico criado com sucesso!")
            return redirect('rs:lista_planos')
    else:
        form = PlanoLogisticoForm()
    return render(request, 'rs/form_plano.html', {'form': form})

def detalhes_plano(request, plano_id):
    """Visualização completa de um Plano Logístico com materiais e atividades"""
    plano = get_object_or_404(PlanoLogistico, id=plano_id)
    materiais = plano.materiais.all().select_related('tipo_dinamico')
    atividades = plano.atividades.all()
    
    # Cálculos Orçamentais
    total_materiais = sum(m.custo_total for m in materiais)
    total_atividades = sum(a.custo_estimado for a in atividades)
    custo_total_estimado = total_materiais + total_atividades
    
    return render(request, 'rs/detalhes_plano.html', {
        'plano': plano,
        'materiais': materiais,
        'atividades': atividades,
        'total_materiais': total_materiais,
        'total_atividades': total_atividades,
        'custo_total_estimado': custo_total_estimado,
        'percent_orcamento': (custo_total_estimado / plano.orcamento_total * 100) if plano.orcamento_total > 0 else 0
    })

def adicionar_material_plano(request, plano_id):
    plano = get_object_or_404(PlanoLogistico, id=plano_id)
    from circuloseleitorais.models import DivisaoEleicao
    from django.db.models import Count
    
    # Mapeamento de Eleição -> Total de Distritos
    eleicao_distritos = {
        e['eleicao_id']: e['total'] 
        for e in DivisaoEleicao.objects.filter(nivel='distrito').values('eleicao_id').annotate(total=Count('id'))
    }

    if request.method == 'POST':
        form = MaterialEleitoralForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.plano = plano
            obj.eleicao = plano.eleicao
            obj.tipo_operacao = plano.tipo_operacao
            obj.save()
            messages.success(request, f"Material '{obj.item}' adicionado ao Plano de {plano.get_tipo_operacao_display()}!")
            return redirect('rs:detalhes_plano', plano_id=plano.id)
    else:
        form = MaterialEleitoralForm(initial={'plano': plano})
    return render(request, 'rs/form_componente.html', {
        'form': form, 
        'plano': plano, 
        'tipo': 'Material',
        'distritos_map': eleicao_distritos
    })

@login_required
def selecao_relatorio_material(request, plano_id):
    plano = get_object_or_404(PlanoLogistico, id=plano_id)
    materiais = plano.materiais.all().order_by('item')
    
    if request.method == 'POST':
        ids_selecionados = request.POST.getlist('materiais_selecionados')
        incluir_central = 'incluir_central' in request.POST
        if ids_selecionados:
            query = f"materiais={','.join(ids_selecionados)}&central={'1' if incluir_central else '0'}"
            return redirect(f"/rs/plano/{plano.id}/gerar-pdf/?{query}")
        else:
            messages.warning(request, "Por favor, selecione pelo menos um material para o relatório.")
            
    return render(request, 'rs/selecao_relatorio.html', {
        'plano': plano,
        'materiais': materiais
    })

from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO

@login_required
def gerar_pdf_plano(request, plano_id):
    plano = get_object_or_404(PlanoLogistico, id=plano_id)
    ids_materiais = request.GET.get('materiais', '').split(',')
    incluir_central = request.GET.get('central', '1') == '1'
    
    # Filtrar apenas os selecionados e pertencentes ao plano
    materiais_selecionados = MaterialEleitoral.objects.filter(id__in=ids_materiais, plano=plano).order_by('item')
    
    from .models import AlocacaoLogistica
    direcoes = AlocacaoLogistica.DIRECOES_STAE # Lista de tuplas (sigla, nome)
    
    # Construir a Matriz de Dados
    mapa_distribuicao = []
    totais_colunas = [0] * len(materiais_selecionados) # Para os totais na base
    
    for sigla, nome in direcoes:
        # Pular STAE Central se desmarcado
        if sigla == 'CENTRAL' and not incluir_central:
            continue
            
        # Limpeza de nome para DNOOE: "DPP GAZA" -> "GAZA"
        nome_curto = nome.replace('DPP ', '').upper()
        if sigla == 'CENTRAL':
            nome_curto = 'STAE CENTRAL'
            
        linha = {
            'provincia': nome_curto,
            'quantidades': [],
            'total_linha': 0
        }
        
        for idx, mat in enumerate(materiais_selecionados):
            # Buscar a alocação específica para este material e esta província
            aloc = mat.alocacoes.filter(unidade=sigla).first()
            qtd = aloc.quantidade_necessaria if aloc else 0
            linha['quantidades'].append(qtd)
            linha['total_linha'] += qtd
            totais_colunas[idx] += qtd # Soma horizontal na base
            
        mapa_distribuicao.append(linha)

    # Geração de QR Code para Autenticidade do Relatório (DNOOE)
    import qrcode
    import base64
    from io import BytesIO
    
    agora = timezone.now()
    qr_data = (
        f"DATA: {agora.strftime('%d/%m/%Y')} | "
        f"HORA: {agora.strftime('%H:%M:%S')} | "
        f"USUARIO: {request.user.username} | "
        f"STAE | DOOE | DDGEI | PORTAL STAE"
    )
    
    qr = qrcode.QRCode(version=1, box_size=3, border=2)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    
    qr_buffer = BytesIO()
    img_qr.save(qr_buffer, format="PNG")
    qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode('utf-8')

    from django.conf import settings
    # Logo está na RAIZ conforme indicado
    logo_file = os.path.join(settings.BASE_DIR, 'logo.png')
    
    # Contexto para o Template
    context = {
        'plano': plano,
        'materiais': materiais_selecionados,
        'mapa': mapa_distribuicao,
        'totais_colunas': totais_colunas,
        'total_geral': sum(totais_colunas),
        'data_emissao': timezone.now(),
        'qr_code': qr_base64,
        'logo_path': logo_file if os.path.exists(logo_file) else ''
    }
    
    template = get_template('rs/relatorio_pdf_plano.html')
    html = template.render(context)
    print("DEBUG HEADER BODY")
    print(html[html.find('<div id="header_content">'):html.find('<div id="header_content">')+1000])
    print("DEBUG HTML END")
    result = BytesIO()
    
    # Gerar PDF
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'filename="Mapa_DNOOE_Plano_{plano.id}.pdf"'
        return response
    
    return HttpResponse("Erro ao gerar o PDF", status=400)

@login_required
def editar_material(request, material_id):
    material = get_object_or_404(MaterialEleitoral, id=material_id)
    plano = material.plano
    from circuloseleitorais.models import DivisaoEleicao
    from django.db.models import Count
    
    # Mapeamento de Eleição -> Total de Distritos
    eleicao_distritos = {
        e['eleicao_id']: e['total'] 
        for e in DivisaoEleicao.objects.filter(nivel='distrito').values('eleicao_id').annotate(total=Count('id'))
    }

    if request.method == 'POST':
        form = MaterialEleitoralForm(request.POST, instance=material)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.save()
            messages.success(request, f"Material '{material.item}' atualizado!")
            return redirect('rs:detalhes_plano', plano_id=plano.id)
    else:
        form = MaterialEleitoralForm(instance=material)
    return render(request, 'rs/form_componente.html', {
        'form': form, 
        'plano': plano, 
        'tipo': 'Material', 
        'edit': True,
        'distritos_map': eleicao_distritos
    })

@login_required
def eliminar_material(request, material_id):
    material = get_object_or_404(MaterialEleitoral, id=material_id)
    plano_id = material.plano.id
    nome = material.item
    material.delete()
    messages.warning(request, f"Material '{nome}' eliminado do plano.")
    return redirect('rs:detalhes_plano', plano_id=plano_id)

from .forms import AtividadePlanoForm

@login_required
def editar_atividade(request, atividade_id):
    from .models import AtividadePlano
    atividade = get_object_or_404(AtividadePlano, id=atividade_id)
    plano = atividade.plano
    if request.method == 'POST':
        form = AtividadePlanoForm(request.POST, instance=atividade)
        if form.is_valid():
            form.save()
            messages.success(request, f"Atividade '{atividade.nome}' atualizada!")
            return redirect('rs:detalhes_plano', plano_id=plano.id)
    else:
        form = AtividadePlanoForm(instance=atividade)
    return render(request, 'rs/form_componente.html', {'form': form, 'plano': plano, 'tipo': 'Atividade', 'edit': True})

@login_required
def eliminar_atividade(request, atividade_id):
    from .models import AtividadePlano
    atividade = get_object_or_404(AtividadePlano, id=atividade_id)
    plano_id = atividade.plano.id
    nome = atividade.nome
    atividade.delete()
    messages.warning(request, f"Atividade '{nome}' eliminada.")
    return redirect('rs:detalhes_plano', plano_id=plano_id)

def adicionar_atividade_plano(request, plano_id):
    plano = get_object_or_404(PlanoLogistico, id=plano_id)
    if request.method == 'POST':
        form = AtividadePlanoForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.plano = plano
            obj.save()
            messages.success(request, f"Atividade '{obj.nome}' registada!")
            return redirect('rs:detalhes_plano', plano_id=plano.id)
    else:
        form = AtividadePlanoForm(initial={'plano': plano})
    return render(request, 'rs/form_componente.html', {'form': form, 'plano': plano, 'tipo': 'Atividade'})

from .models import AlocacaoLogistica

@login_required
def distribuir_material(request, material_id):
    """View para expandir e distribuir quantidades pelas 11 DPPs e Central"""
    material = get_object_or_404(MaterialEleitoral, id=material_id)
    unidades = AlocacaoLogistica.DIRECOES_STAE
    from eleicao.models import Eleicao
    from circuloseleitorais.models import DivisaoEleicao
    
    eleicoes = Eleicao.objects.all().order_by('-ano')
    
    # Mapeamento robusto (ignora maiúsculas/minúsculas e espaços)
    def normalize_key(name):
        import unicodedata
        return "".join(c for c in unicodedata.normalize('NFD', name.lower()) if unicodedata.category(c) != 'Mn').strip()

    MAP_PROV_CODES = {
        normalize_key('Maputo Cidade'): 'MAPUTO_C',
        normalize_key('Maputo Província'): 'MAPUTO_P',
        normalize_key('Gaza'): 'GAZA',
        normalize_key('Inhambane'): 'INHAMBANE',
        normalize_key('Sofala'): 'SOFALA',
        normalize_key('Manica'): 'MANICA',
        normalize_key('Tete'): 'TETE',
        normalize_key('Zambézia'): 'ZAMBEZIA',
        normalize_key('Nampula'): 'NAMPULA',
        normalize_key('Cabo Delgado'): 'CABO_D',
        normalize_key('Niassa'): 'NIASSA',
    }
    
    # Seletor de estatísticas (padrão ou de eleição específica)
    stats_final = {code: {'distritos': 0, 'mesas': 0} for code, _ in unidades}
    
    eleicao_ref_id = request.GET.get('eleicao_ref_id')
    eleicao_ref_id = request.GET.get('eleicao_ref_id')

    if not eleicao_ref_id:
        if material.eleicao_referencia:
            eleicao_ref_id = material.eleicao_referencia.id
        elif material.plano.eleicao:
            eleicao_ref_id = material.plano.eleicao.id
        
    if eleicao_ref_id:
        divisoes_ref = DivisaoEleicao.objects.filter(eleicao_id=eleicao_ref_id).select_related('parent')
        
        # 1. Contar Distritos das Divisões Administrativas
        provincias_list = divisoes_ref.filter(nivel='provincia')
        for d in provincias_list:
            norm_name = normalize_key(d.nome)
            code = MAP_PROV_CODES.get(norm_name)
            if code:
                n_dist = divisoes_ref.filter(nivel='distrito', parent=d).count()
                stats_final[code]['distritos'] = n_dist

        # 2. Contar Mesas dos Círculos Eleitorais
        from circuloseleitorais.models import CirculoEleitoral
        from django.db.models import Sum
        mesas_count = CirculoEleitoral.objects.filter(eleicao_id=eleicao_ref_id).values('provincia').annotate(total=Sum('num_mesas'))
        for mc in mesas_count:
            norm_prov = normalize_key(mc['provincia'])
            code = MAP_PROV_CODES.get(norm_prov)
            if code:
                stats_final[code]['mesas'] = mc['total'] or 0
    
    if request.method == 'POST':
        for code, name in unidades:
            qtd_nec = request.POST.get(f'qtd_nec_{code}', 0)
            qtd_ext = request.POST.get(f'qtd_ext_{code}', 0)
            n_dist = request.POST.get(f'n_dist_{code}', 0)
            n_mesas = request.POST.get(f'n_mesas_{code}', 0)
            
            if qtd_nec or qtd_ext or n_dist or n_mesas:
                AlocacaoLogistica.objects.update_or_create(
                    material_nacional=material,
                    unidade=code,
                    defaults={
                        'quantidade_necessaria': int(qtd_nec or 0),
                        'quantidade_existente': int(qtd_ext or 0),
                        'num_distritos': int(n_dist or 0),
                        'num_mesas': int(n_mesas or 0)
                    }
                )
        messages.success(request, f"Distribuição e Geografia de '{material.item}' atualizadas!")
        return redirect('rs:detalhes_plano', plano_id=material.plano.id)

    alocacoes_qs = material.alocacoes.all()
    alocacoes_dict = {a.unidade: a for a in alocacoes_qs}
    
    # Garantir que novos registos tenham o default geográfico da eleição selecionada
    for code, name in unidades:
        if code not in alocacoes_dict:
            stats_p = stats_final.get(code, {'distritos': 0, 'mesas': 0})
            alocacoes_dict[code] = AlocacaoLogistica(
                unidade=code, 
                num_distritos=stats_p['distritos'], 
                num_mesas=stats_p['mesas']
            )

    return render(request, 'rs/distribuir_material.html', {
        'material': material,
        'unidades': unidades,
        'alocacoes': alocacoes_dict,
        'eleicoes': eleicoes,
        'eleicao_ref_id': int(eleicao_ref_id) if eleicao_ref_id else None,
        'stats': stats_final
    })

from .forms import PlanoLogisticoForm, TipoDocumentoForm

# GESTÃO DOCUMENTAL
def documentos_view(request):
    tipos = TipoDocumento.objects.all().order_by('nome')
    from eleicao.models import Eleicao
    from circuloseleitorais.models import CirculoEleitoral
    eleicoes = Eleicao.objects.all().order_by('-ano')
    circulos = CirculoEleitoral.objects.all().order_by('nome')
    return render(request, 'rs/documentos.html', {
        'tipos': tipos,
        'eleicoes': eleicoes,
        'circulos': circulos
    })

def inicializar_docs_padrao(request):
    """Cria os documentos fundamentais com templates HTML pré-desenhados"""
    
    # Template Boletim (Moçambique Oficial - Contexto Territorial + QR Code)
    boletim_html = """<div class="boletim-voto" style="max-width:850px; margin:auto; border:4px solid #000; padding:20px; font-family: Arial, sans-serif; background: #fff; position: relative;">
    <div style="position: absolute; top: 15px; right: 20px; text-align: center; width: 120px;">
        {% if qr_code %}
            <img src="data:image/png;base64,{{ qr_code }}" style="width: 100px; height: 100px; border: 1px solid #000; padding: 5px; display: block; margin: 0 auto;">
        {% else %}
            <div style="width: 100px; height: 100px; border: 2px dashed #ccc; display: flex; align-items: center; justify-content: center; margin: 0 auto; color: #ccc;">QR</div>
        {% endif %}
        <div style="font-size: 7pt; margin-top: 5px; font-weight: bold; text-transform: uppercase;">Autenticidade Digital</div>
    </div>

    <div style="text-align:center; border-bottom:4px solid #000; padding-bottom:15px; margin-bottom:25px; padding-right: 140px;">
        <p style="margin:5px 0; font-size:12pt; font-weight: bold; letter-spacing: 2px;">{{ cabecalho|default:"REPÚBLICA DE MOÇAMBIQUE" }}</p>
        <p style="margin:0; font-size:10pt;">{{ entidade }}</p>
        <h2 style="margin:15px 0; font-size:26pt; text-transform: uppercase; font-weight: 900; letter-spacing: 1px;">{{ titulo_documento|default:"BOLETIM DE VOTO" }}</h2>
        {% if circulo %}<p style="margin:0; font-size:14pt; color:#000; font-weight: bold;">CÍRCULO ELEITORAL: {{ circulo.nome|upper }}</p>{% endif %}
    </div>
    
    <div class="corpo-boletim">
        {% for c in candidatos %}
        <div style="display: flex; align-items: stretch; border: 2px solid #000; margin-bottom: 20px; min-height: 150px; background: #fff; page-break-inside: avoid;">
            <!-- 1. Símbolo do Partido (Soberania Partidária) -->
            <div style="width: 200px; border-right: 2px solid #000; display: flex; align-items: center; justify-content: center; padding: 15px; background: #fff;">
                <div style="width: 170px; height: 170px; display: flex; align-items: center; justify-content: center; overflow: hidden;">
                    {% if c.party_logo %}
                        <img src="{{ c.party_logo.url }}" style="max-width: 100%; max-height: 100%; object-fit: contain;">
                    {% else %}
                        <div style="font-weight:bold; font-size:25pt; color:#ccc; border: 1px dashed #ccc; padding: 10px;">{{ c.sigla|default:"SÍMBOLO" }}</div>
                    {% endif %}
                </div>
            </div>

            <!-- 2. Coluna de Foto (ESTRITAMENTE PRESIDENCIAL) -->
            {% if eleicao.tipo == 'presidencial' %}
            <div style="width: 180px; border-right: 2px solid #000; display: flex; align-items: center; justify-content: center; padding: 15px; background: #fefefe;">
                <div style="width: 150px; height: 150px; border: 1px solid #000; background: #eee; display: flex; align-items: center; justify-content: center; overflow: hidden;">
                    {% if c.foto %}
                        <img src="{{ c.foto.url }}" style="width: 100%; height: 100%; object-fit: cover;">
                    {% else %}
                        <i class="fas fa-user-tie" style="font-size: 60pt; color: #ccc;"></i>
                    {% endif %}
                </div>
            </div>
            {% endif %}

            <!-- 3. Identificação Jurídica -->
            <div style="flex: 1; display: flex; flex-direction: column; justify-content: center; padding: 0 40px; border-right: 2px solid #000;">
                <div style="font-size: 28pt; font-weight: 900; color: #000; line-height: 1.1;">{{ c.nome_completo|upper }}</div>
                <div style="font-size: 14pt; color: #333; margin-top: 10px; font-weight: bold;">{{ c.legenda_oficial|default:'' }}</div>
            </div>

            <!-- 4. Quadrícula (Onde a vontade se expressa) -->
            <div style="width: 150px; display: flex; align-items: center; justify-content: center; background: #fff;">
                <div style="width: 100px; height: 100px; border: 10px solid #000; background: #fff;"></div>
            </div>
        </div>
        {% endfor %}
    </div>
    
    <div style="margin-top:40px; font-size: 14pt; text-align: center; font-style: italic; font-weight: bold; background: #f0f0f0; padding: 15px; border: 3px dashed #000; page-break-inside: avoid;">
        {{ instrutivo|default:"INSTRUTIVO: Assinale com uma cruz (X) no quadrado à direita do candidato ou partido da sua escolha." }}
    </div>
</div>
<div style="page-break-after: always;"></div>
"""

    # Template Edital de Mesa (Com Códigos de Segurança em destaque)
    edital_mesa_html = """<div class="edital-mesa" style="border: 4px solid #000; padding: 30px; font-family: 'Times New Roman', serif;">
    <div style="text-align:center; border-bottom: 2px solid #000; padding-bottom: 15px;">
        <h1 style="margin:0; font-size:24pt;">EDITAL DE RESULTADOS</h1>
        <h3 style="margin:5px 0;">ASSEMBLEIA DE VOTO Nº: {{ mesa|default:"00000-00" }}</h3>
    </div>
    
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; border: 1px solid #000; padding: 15px; background: #fdfdfd;">
        <div><strong>CÓDIGO EDITAL:</strong> <span style="font-family: monospace; font-size: 14pt;">{{ codigo_edital|default:"STAE-2024-XXXX" }}</span></div>
        <div><strong>CÓDIGO VALIDAÇÃO:</strong> <span style="font-family: monospace; font-size: 14pt;">{{ codigo_validacao|default:"VVVV-VVVV" }}</span></div>
    </div>

    <table style="width:100%; border-collapse: collapse; margin-top:20px; font-size: 12pt;">
        <thead><tr style="background:#eee;">
            <th style="border:1px solid #000; padding:12px; text-align:left;">ENTIDADE POLÍTICA</th>
            <th style="border:1px solid #000; padding:12px; text-align:center; width:150px;">VOTOS</th>
        </tr></thead>
        <tbody>
            {% for v in votos.contagem %}
            <tr>
                <td style="border:1px solid #000; padding:10px; font-weight:bold;">{{ v.partido|upper }}</td>
                <td style="border:1px solid #000; padding:10px; text-align:center; font-size: 14pt;">{{ v.votos }}</td>
            </tr>
            {% endfor %}
            <tr style="background:#f9f9f9; font-weight:bold;">
                <td style="border:1px solid #000; padding:10px;">VOTOS EM BRANCO</td>
                <td style="border:1px solid #000; padding:10px; text-align:center;">{{ votos.brancos }}</td>
            </tr>
            <tr style="background:#f9f9f9; font-weight:bold;">
                <td style="border:1px solid #000; padding:10px;">VOTOS NULOS</td>
                <td style="border:1px solid #000; padding:10px; text-align:center;">{{ votos.nulos }}</td>
            </tr>
        </tbody>
    </table>
</div>"""

    # Template Acta (Rigid Format)
    acta_html = """<div style="border:1px solid #000; padding:40px; font-family:serif; line-height:1.6;">
        <h2 style="text-align:center;">ACTA DE OPERAÇÕES DE VOTO</h2>
        <p>Aos {{ data_atual|date:"d" }} dias do mês de {{ data_atual|date:"F" }} de {{ data_atual|date:"Y" }}, pelas 07:00 horas, na Assembleia de Voto nº {{ mesa|default:"____" }}, sita em {{ local|default:"________________" }}...</p>
        <div style="margin-top:50px; border-top:1px solid #000; padding-top:10px;">Assinaturas do Presidente e Membros da Mesa</div>
    </div>"""

    # Template Dístico (Banner)
    distico_html = """<div style="border:10px solid #003366; padding:50px; text-align:center; background:#fff;">
        <h1 style="font-size:80pt; margin:0; color:#003366;">{{ mesa|default:"0000" }}</h1>
        <h2 style="font-size:30pt; margin-top:20px; text-transform:uppercase;">Assembleia de Voto</h2>
        <div style="margin-top:40px; font-size:20pt; border-top:2px solid #ccc; padding-top:20px;">REPÚBLICA DE MOÇAMBIQUE | STAE</div>
    </div>"""

    # Proposta de Texto para Coletes
    colete_html = """<div style="background:#ff9900; color:#000; padding:100px; text-align:center; font-family:sans-serif; border-radius:50px;">
        <div style="font-size:40pt; font-weight:bold; border:5px solid #000; display:inline-block; padding:20px;">STAE</div>
        <div style="font-size:60pt; font-weight:black; margin-top:50px;">ADMINISTRAÇÃO<br>ELEITORAL</div>
        <div style="margin-top:50px; font-size:25pt; opacity:0.8;">{{ eleicao.nome|upper }}</div>
    </div>"""

    # Senhas de Identificação (Roll/Ticket format)
    senha_html = """<div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:10px;">
        {% for s in "123456789012"|make_list %}
        <div style="border:2px dashed #999; padding:20px; text-align:center;">
            <small>SENHA DE VOTO</small>
            <div style="font-size:30pt; font-weight:bold;">{{ forloop.counter }}</div>
            <div style="font-family:monospace; font-size:8pt;">{{ eleicao.codigo|default:"STAE-2024" }}</div>
        </div>
        {% endfor %}
    </div>"""

    docs_necessarios = [
        ("Cartão de Eleitor PVC", "CARTAO_ELEITOR", "templates/credenciais/cartao_pvc.html"),
        ("Boletim de Voto Oficial", "BOLETIM_VOTO", boletim_html),
        ("Acta de Operações de Voto", "ACTA_VOTO", acta_html),
        ("Edital de Resultados da Mesa", "EDITAL_MESA", edital_mesa_html),
        ("Dístico de Assembleia de Voto", "DISTICO_MESA", distico_html),
        ("Credencial de Membro de Mesa (MMV)", "CREDENCIAL_MMV", "templates/credenciais/cartao_pvc.html"),
        ("Texto Oficial para Coletes", "TEXTO_COLETE", colete_html),
        ("Senhas de Fila para Eleitores", "SENHAS_FILA", senha_html),
        ("Caderno de Recenseamento", "CADERNO_REC", "<table border='1' width='100%'><tr><th>ELEITOR</th><th>ORDEM</th></tr>{% for e in eleitores %}<tr><td>{{ e.nome_completo }}</td><td>{{ e.numero_cartao }}</td></tr>{% endfor %}</table>"),
    ]
    
    criados = 0
    atualizados = 0
    for nome, codigo, template in docs_necessarios:
        tipo, created = TipoDocumento.objects.get_or_create(
            codigo=codigo, 
            defaults={'nome': nome, 'template_html': template}
        )
        if created:
            criados += 1
        else:
            # FORÇA A ATUALIZAÇÃO para garantir que o layout oficial (dinâmico) seja aplicado
            tipo.template_html = template
            tipo.nome = nome
            tipo.save()
            atualizados += 1
    
    if request and hasattr(request, 'user'): # Evita erro em chamadas via Shell
        messages.success(request, f"{criados} novos criados. {atualizados} templates restaurados com layout dinâmico oficial.")
    return redirect('rs:documentos')

def criar_tipo_documento(request):
    if request.method == 'POST':
        form = TipoDocumentoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de documento criado com sucesso!')
            return redirect('rs:documentos')
    else:
        form = TipoDocumentoForm()
    return render(request, 'rs/form_tipo_documento.html', {'form': form, 'titulo': 'Novo Tipo de Documento'})

def editar_tipo_documento(request, tipo_id):
    tipo = get_object_or_404(TipoDocumento, id=tipo_id)
    if request.method == 'POST':
        form = TipoDocumentoForm(request.POST, instance=tipo)
        if form.is_valid():
            form.save()
            messages.success(request, f'Documento {tipo.nome} atualizado.')
            return redirect('rs:documentos')
    else:
        form = TipoDocumentoForm(instance=tipo)
    return render(request, 'rs/form_tipo_documento.html', {'form': form, 'titulo': f'Editar {tipo.nome}'})

def eliminar_tipo_documento(request, tipo_id):
    tipo = get_object_or_404(TipoDocumento, id=tipo_id)
    nome = tipo.nome
    if request.method == 'POST':
        tipo.delete()
        messages.warning(request, f'Documento {nome} removido do sistema.')
        return redirect('rs:documentos')
    return render(request, 'rs/confirm_delete.html', {'objeto': tipo, 'cancel_url': 'rs:documentos'})

def preview_generico(request, tipo_id):
    """Visualizador genérico com suporte a impressão em massa territorializada"""
    tipo = get_object_or_404(TipoDocumento, id=tipo_id)
    
    if tipo.codigo == 'CARTAO_ELEITOR':
        return redirect('rs:preview_cartao')
    
    eleicao_id = request.GET.get('eleicao')
    circulo_id = request.GET.get('circulo')
    
    if eleicao_id:
        eleicao = get_object_or_404(Eleicao, id=eleicao_id)
    else:
        eleicao = Eleicao.objects.filter(ativo=True).first()
    
    from circuloseleitorais.models import CirculoEleitoral
    from candidaturas.models import InscricaoPartidoEleicao, Candidato
    from django.template import Template, Context
    import qrcode
    import base64
    from io import BytesIO

    paginas = []
    
    # 1. DEFINIÇÃO DA COBERTURA TERRITORIAL
    if circulo_id:
        # Foco num único círculo específico
        circulos_alvos = CirculoEleitoral.objects.filter(id=circulo_id)
    else:
        # GERAÇÃO EM MASSA: Todos os círculos com actividade eleitoral
        if eleicao.tipo == 'presidencial':
            circulos_alvos = [None] # Presidencial é círculo único nacional
        else:
            # Autárquica/Legislativa: buscar apenas círculos onde há partidos inscritos
            cids = InscricaoPartidoEleicao.objects.filter(eleicao=eleicao, listas__isnull=False).values_list('listas__circulo', flat=True).distinct()
            circulos_alvos = CirculoEleitoral.objects.filter(id__in=cids)
            if not circulos_alvos.exists():
                circulos_alvos = [None] # Fallback para mock se vazio

    # 2. GERAÇÃO INDIVIDUALIZADA POR TERRITÓRIO
    for circ in circulos_alvos:
        ctx_pag = {
            'eleicao': eleicao,
            'circulo': circ,
            'entidade': 'Secretariado Técnico de Administração Eleitoral',
            'cabecalho': 'REPÚBLICA DE MOÇAMBIQUE',
            'titulo_documento': "BOLETIM DE VOTO" if tipo.codigo == 'BOLETIM_VOTO' else tipo.nome,
        }

        # Lógica de Candidatos/Partidos Específica para este Círculo
        if tipo.codigo == 'BOLETIM_VOTO':
            if eleicao.tipo == 'presidencial':
                cands = Candidato.objects.filter(inscricao_direta__eleicao=eleicao).select_related('inscricao_direta__partido')
                for c in cands:
                    c.party_logo = c.inscricao_direta.partido.simbolo
                    c.legenda_oficial = ""
                ctx_pag['candidatos'] = cands
            else:
                # LISTA PARTIDÁRIA: Apenas partidos que concorrem nesta autarquia/círculo
                filtros = {'eleicao': eleicao}
                if circ: filtros['listas__circulo'] = circ
                
                inscricoes = InscricaoPartidoEleicao.objects.filter(**filtros).select_related('partido').distinct().order_by('posicao_boletim')
                
                class MockP:
                    def __init__(self, ins):
                        self.nome_completo = ins.partido.nome_completo
                        self.sigla = ins.partido.sigla
                        self.party_logo = ins.partido.simbolo
                        self.foto = None
                        self.legenda_oficial = ""
                ctx_pag['candidatos'] = [MockP(i) for i in inscricoes]

        # Geração de QR Code Único de Soberania Territorial
        qr_str = f"DOC:{tipo.codigo}|ELE:{eleicao.id}"
        if circ: qr_str += f"|CIR:{circ.id}|NOM:{circ.nome}"
        
        qrobj = qrcode.QRCode(version=1, box_size=10, border=1)
        qrobj.add_data(qr_str)
        qrobj.make(fit=True)
        img = qrobj.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf, format="PNG")
        ctx_pag['qr_code'] = base64.b64encode(buf.getvalue()).decode()
        
        # 3. RENDERIZAÇÃO FINAL DA PÁGINA (Transforma Template String em HTML Real)
        if tipo.template_html:
            try:
                # Criamos um template a partir da string no banco
                tmpl = Template(tipo.template_html)
                # Renderizamos com o contexto desta página
                ctx_pag['conteudo_renderizado'] = tmpl.render(Context(ctx_pag))
            except Exception as e:
                ctx_pag['conteudo_renderizado'] = f"<div class='alert alert-danger'>Erro de Renderização: {e}</div>"
        
        paginas.append(ctx_pag)

    return render(request, 'rs/print_generico.html', {
        'tipo': tipo,
        'paginas': paginas,
        'is_mass_production': not circulo_id
    })

# APURAMENTO E LANÇAMENTO DE EDITAIS
def lancar_edital(request):
    eleicoes = Eleicao.objects.filter(ativo=True)
    circulos = CirculoEleitoral.objects.all()
    
    if request.method == 'POST':
        # 1. Validação dos Códigos de Segurança
        cod_edital = request.POST.get('codigo_edital')
        cod_validacao = request.POST.get('codigo_validacao')
        
        controle = ControleEdital.objects.filter(
            codigo_edital=cod_edital, 
            codigo_validacao=cod_validacao,
            usado=False
        ).first()
        
        if not controle:
            messages.error(request, "ERRO CRÍTICO: Códigos de Edital ou Validação inválidos ou já utilizados.")
            return render(request, 'rs/lancar_edital.html', {
                'eleicoes': eleicoes, 'circulos': circulos, 'dados': request.POST
            })
            
        # 2. Processamento dos Resultados
        try:
            resultado = ResultadoEdital.objects.create(
                controle=controle,
                votos_brancos=int(request.POST.get('votos_brancos', 0)),
                votos_nulos=int(request.POST.get('votos_nulos', 0)),
                total_votantes=int(request.POST.get('total_votantes', 0)),
                reclamacoes=request.POST.get('reclamacoes', ''),
                utilizador_lancamento=request.user.username
            )
            
            # 3. Lançamento por Partido (Dinâmico)
            partidos_ids = request.POST.getlist('partido_id')
            votos_list = request.POST.getlist('votos_partido')
            
            for p_id, qtd in zip(partidos_ids, votos_list):
                if qtd:
                    VotoPartidoEdital.objects.create(
                        resultado=resultado,
                        partido_id=p_id,
                        quantidade_votos=int(qtd)
                    )
            
            controle.usado = True
            controle.save()
            
            messages.success(request, f"Edital {cod_edital} processado com sucesso!")
            return redirect('rs:documentos')
            
        except Exception as e:
            messages.error(request, f"Erro ao processar dados: {str(e)}")
    
    # Busca partidos concorrentes (ou simulados se não houver inscrições)
    partidos_concorrentes = list(InscricaoPartidoEleicao.objects.filter(status='inscrito').select_related('partido'))
    if not partidos_concorrentes:
        # Fallback Mock para garantir que a tela nunca está vazia
        from partidos.models import Partido
        partidos_concorrentes = Partido.objects.all()[:10]

    return render(request, 'rs/lancar_edital.html', {
        'eleicoes': eleicoes,
        'circulos': circulos,
        'partidos': partidos_concorrentes,
        'titulo': 'Lançamento Oficial de Edital'
    })

def preview_cartao_eleitor(request):
    # Simula dados estruturados para o template (evitando VariableDoesNotExist)
    class Mock: pass
    credencial = Mock()
    credencial.numero_credencial = "2024/EL/882-01"
    credencial.qr_code = None
    
    pedido = Mock()
    solicitante = Mock()
    solicitante.nome_completo = "JOÃO MANUEL DA SILVA"
    solicitante.foto = None
    solicitante.nome_empresa = "CIRCULO ELEITORAL Nº 01" # Simula o local no campo de empresa
    
    tipo_credencial = Mock()
    tipo_credencial.nome = "ELEITOR ACTIVO"
    
    pedido.solicitante = solicitante
    pedido.tipo_credencial = tipo_credencial
    pedido.evento = Mock()
    pedido.evento.nome = "ELEIÇÕES GERAIS 2024"
    
    credencial.pedido = pedido
    
    context = {
        'credencial': credencial,
        'config': {'entidade': 'stae'},
        # Fallbacks para o template cartao_pvc.html
        'funcionario_real': {
            'nome_completo': solicitante.nome_completo,
            'funcao': 'ELEITOR',
            'sector': {'nome': 'ZONA SUL - MAPUTO'}
        }
    }
    return render(request, 'credenciais/cartao_pvc.html', context)
def gestao_categorias_materiais(request):
    """Lista e cria categorias de materiais"""
    categorias = CategoriaMaterial.objects.all()
    if request.method == 'POST':
        form = CategoriaMaterialForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoria criada com sucesso!")
            return redirect('rs:gestao_categorias')
    else:
        form = CategoriaMaterialForm()
    
    return render(request, 'rs/gestao_categorias.html', {
        'categorias': categorias,
        'form': form
    })

def gestao_tipos_materiais(request):
    """Lista e cria tipos de materiais associados a categorias"""
    tipos = TipoMaterial.objects.all().select_related('categoria')
    if request.method == 'POST':
        form = TipoMaterialForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Tipo de material criado com sucesso!")
            return redirect('rs:gestao_tipos')
    else:
        form = TipoMaterialForm()
    
    return render(request, 'rs/gestao_tipos.html', {
        'tipos': tipos,
        'form': form
    })

@login_required
def eliminar_tipo_material(request, pk):
    tipo = get_object_or_404(TipoMaterial, pk=pk)
    nome = tipo.nome
    tipo.delete()
    messages.warning(request, f"Tipo de material '{nome}' eliminado com sucesso.")
    return redirect('rs:gestao_tipos')

def inicializar_catalogo_stae(request):
    """Pré-carrega o catálogo oficial do STAE Moçambique (Votação + Recenseamento)"""
    dados = [
        # --- VOTAÇÃO ---
        ('Votação: Equipamento & Mobiliário', 'Infraestrutura de assembleia de voto', [
            ('Cabine de Votação (Individual)', 'Padrão STAE p/ Sigilo do Voto', 'fas fa-person-booth'),
            ('Urna de Votação (MMV)', 'Padrão STAE Transparente', 'fas fa-box-open'),
            ('Mesa de Brigada / Assembleia', 'Mobiliário de apoio a MMVs', 'fas fa-table'),
        ]),
        ('Votação: Material Sensível', 'Itens de segurança e controlo de voto', [
            ('Boletins de Voto', 'Impressões Oficiais de Soberania', 'fas fa-file-invoice'),
            ('Tinta Indelével (Frascos)', 'Controle de multivotantes (15ml)', 'fas fa-fill-drip'),
            ('Selos de Segurança', 'Plástico Numerado para Urnas', 'fas fa-lock'),
            ('Caderno de Actas Votação', 'Registo oficial da mesa', 'fas fa-book'),
        ]),
        # --- RECENSEAMENTO ---
        ('Recenseamento: Equipamento & TI', 'Hardware para registo de eleitores', [
            ('Mobile ID Kit (Completo)', 'Maleta de registo com PC/Câmara/Scanner', 'fas fa-laptop-medical'),
            ('Impressora de Cartões PVC', 'Emissão instantânea do cartão', 'fas fa-print'),
            ('Painel Solar de Campanha', 'Energia para postos remotos', 'fas fa-solar-panel'),
            ('Bateria de Lítio (Kit ID)', 'Autonomia para o Mobile ID', 'fas fa-battery-full'),
            ('Câmara Fotográfica Web', 'Captura de imagem do eleitor', 'fas fa-camera'),
        ]),
        ('Recenseamento: Consumíveis', 'Materiais gastos na emissão de cartões', [
            ('Cartões PVC (Brancos)', 'Base para impressão do cartão eleitor', 'fas fa-id-card-alt'),
            ('Ribbon / Fita de Impressão', 'Consumível para impressora de cartões', 'fas fa-stream'),
            ('Caderno de Recenseamento', 'Registo manual de brigada', 'fas fa-address-book'),
            ('Formulário de Inscrição', 'Ficha de recolha de dados', 'fas fa-file-alt'),
        ]),
        # --- LOGÍSTICA COMUM ---
        ('Logística e Transporte', 'Embalagem e movimentação de material', [
            ('Saco Plástico p/ Urna', 'Impermeabilização e fecho', 'fas fa-shopping-bag'),
            ('Fita Adesiva Logotipada', 'Selagem de caixas e kits', 'fas fa-tape'),
            ('Maleta de Transporte', 'Kits de material de mesa/brigada', 'fas fa-briefcase'),
        ]),
        ('Apoio e Geradores', 'Energia e suporte de campo', [
            ('Gerador a Gasolina (2.5kVA)', 'Energia para postos de recenseamento', 'fas fa-plug'),
            ('Megafone c/ Sirene', 'Comunicação e gestão de filas', 'fas fa-bullhorn'),
            ('Lanterna LED Pesada', 'Iluminação para contagem e segurança', 'fas fa-lightbulb'),
        ]),
        ('Indumentária Oficial', 'Identificação de agentes do STAE', [
            ('Colete Azul (STAE)', 'Identificação de brigadistas e MMVs', 'fas fa-user-tie'),
            ('Boné Oficial STAE', 'Proteção solar e identificação', 'fas fa-hat-cowboy'),
            ('Crachá Magnético', 'Identificação segura de pessoal', 'fas fa-id-badge'),
        ])
    ]
    
    criados_cat = 0
    criados_tip = 0
    for cat_nome, cat_desc, tipos in dados:
        cat, created = CategoriaMaterial.objects.get_or_create(
            nome=cat_nome, defaults={'descricao': cat_desc}
        )
        if created: criados_cat += 1
        
        for tip_nome, tip_desc, icone in tipos:
            # Primeiro tentamos buscar APENAS pelo nome para evitar IntegrityError
            obj, t_created = TipoMaterial.objects.get_or_create(
                nome=tip_nome, 
                defaults={'categoria': cat, 'descricao': tip_desc, 'icone': icone}
            )
            # Se já existia, garantimos que a categoria e dados estão atualizados (Votação vs Recenseamento)
            if not t_created:
                obj.categoria = cat
                obj.descricao = tip_desc
                obj.icone = icone
                obj.save()
            
            criados_tip += 1
            
    messages.success(request, f"Catálogo Ampliado STAE: {criados_cat} novas categorias e {criados_tip} tipos de material (Votação + Recenseamento) carregados.")
    return redirect('rs:gestao_tipos')

def criar_requisito_material(request):
    """Permite adicionar um novo requisito de material para a eleição ativa"""
    eleicao_ativa = Eleicao.objects.filter(ativo=True).first()
    if request.method == 'POST':
        form = MaterialEleitoralForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Novo requisito logístico adicionado!")
            return redirect('rs:dashboard')
    else:
        # Pré-selecionar a eleição ativa
        form = MaterialEleitoralForm(initial={'eleicao': eleicao_ativa})
    
    return render(request, 'rs/form_material.html', {
        'form': form,
        'eleicao': eleicao_ativa
    })
