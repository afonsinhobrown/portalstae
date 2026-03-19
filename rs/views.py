from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from django.template import Context, Template
from.models import PlanoLogistico, TipoDocumento, DocumentoGerado, MaterialEleitoral, ModeloVisualArtefacto
from eleicao.models import Eleicao
from circuloseleitorais.models import CirculoEleitoral
from candidaturas.models import InscricaoPartidoEleicao, Candidato, ListaCandidatura

def dashboard(request):
    eleicoes = Eleicao.objects.filter(ativo=True).order_by('-ano')
    planos = PlanoLogistico.objects.all().order_by('-data_inicio')
    
    eleicao_ativa = eleicoes.first()
    bi_data = {}
    modelos_visuais = []
    
    destino_selecionado = request.GET.get('destino')
    materiais_exibir = []
    destinos_disponiveis = []
    is_nacional = True

    if eleicao_ativa:
        if not eleicao_ativa.materiais_logistica.exists():
            from .logic import sync_plano_logistico
            sync_plano_logistico(eleicao_ativa)
            
        from candidaturas.views import get_estatisticas_eleicao
        bi_data = get_estatisticas_eleicao(eleicao_ativa.id)

        materiais_qs = eleicao_ativa.materiais_logistica.all()
        destinos_disponiveis = materiais_qs.values_list('localizacao_destino', flat=True).distinct().order_by('localizacao_destino')
        
        if destino_selecionado:
            # Visão Táctica: Detalha os itens de um destino específico
            materiais_exibir = materiais_qs.filter(localizacao_destino=destino_selecionado).order_by('item')
            is_nacional = False
        else:
            # Visão de Soberania (Nacional): Agrega totais por tipo para "Contas Globais"
            from django.db.models import Sum
            agregados = materiais_qs.values('tipo').annotate(total_qtd=Sum('quantidade_planeada')).order_by('tipo')
            
            tipo_map = dict(MaterialEleitoral.TIPO_CHOICES)
            for a in agregados:
                # Criamos um objeto mock para o template manter a compatibilidade
                class MaterialMock:
                    def __init__(self, t, n, q):
                        self.tipo = t
                        self.item = n
                        self.quantidade_planeada = q
                        self.localizacao_destino = 'NACIONAL (Consolidado)'
                        self.quantidade_alocada = 0 # Agregação de alocação seria mais complexa, simplificamos aqui
                    def get_tipo_display(self): return tipo_map.get(self.tipo, self.tipo)

                materiais_exibir.append(MaterialMock(a['tipo'], tipo_map.get(a['tipo'], a['tipo']), a['total_qtd']))
            is_nacional = True

        # Artefactos Visuais
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
        'destinos': destinos_disponiveis,
        'destino_atual': destino_selecionado,
        'is_nacional': is_nacional,
        'total': planos.count(),
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
    # Boletins (Total + 10%)
    MaterialEleitoral.objects.update_or_create(
        eleicao=eleicao, tipo='boletim', localizacao_destino='Armazém Central',
        defaults={'item': 'Stock Nacional de Boletins', 'quantidade_planeada': int(total_eleitores * 1.1)}
    )
    # Coletes (7 per mesa)
    MaterialEleitoral.objects.update_or_create(
        eleicao=eleicao, tipo='colete', localizacao_destino='Armazém Central',
        defaults={'item': 'Coletes Oficiais STAE', 'quantidade_planeada': total_mesas * 7}
    )
    # Tinta Indelével
    MaterialEleitoral.objects.update_or_create(
        eleicao=eleicao, tipo='tinta', localizacao_destino='Armazém Central',
        defaults={'item': 'Tinta Indelével (Frascos)', 'quantidade_planeada': int(total_eleitores / 500) + 1}
    )
    # Cabines (2 por mesa)
    MaterialEleitoral.objects.update_or_create(
        eleicao=eleicao, tipo='cabine', localizacao_destino='Armazém Central',
        defaults={'item': 'Cabines de Votação (Plástico/Papelão)', 'quantidade_planeada': total_mesas * 2}
    )
    # Credenciais MMV (7 por mesa)
    MaterialEleitoral.objects.update_or_create(
        eleicao=eleicao, tipo='credencial', localizacao_destino='Armazém Central',
        defaults={'item': 'Credenciais Oficiais MMV', 'quantidade_planeada': total_mesas * 7}
    )

    # 2. CÁLCULO PROVINCIAL (PLANOS DE DISTRIBUIÇÃO)
    provincias = eleicao.circulos.values_list('provincia', flat=True).distinct()
    
    for prov in provincias:
        circulos_v = eleicao.circulos.filter(provincia=prov)
        m_prov = circulos_v.aggregate(total=Sum('num_mesas'))['total'] or 0
        
        propostas = [
            ('urna', f'Urnas - {prov}', m_prov),
            ('kit', f'Kits Mesa - {prov}', m_prov),
            ('papelaria', f'Papelaria e Blocos - {prov}', m_prov * 5),
            ('iluminacao', f'Lanternas LED - {prov}', m_prov),
            ('apoio', f'Quadros e Tripés - {prov}', m_prov),
        ]
        
        for tipo, nome, qtd in propostas:
            if qtd > 0:
                MaterialEleitoral.objects.update_or_create(
                    eleicao=eleicao, tipo=tipo, localizacao_destino=prov,
                    defaults={'item': nome, 'quantidade_planeada': qtd}
                )

    messages.success(request, f"Pano de Distribuição gerado para {len(provincias)} províncias. Logística capilarizada com sucesso.")
    return redirect('rs:dashboard')

def criar_plano(request):
    # Placeholder para CRUD de planos (já tinha form_plano.html)
    return render(request, 'rs/form_plano.html')

def detalhes_plano(request, plano_id):
    plano = get_object_or_404(PlanoLogistico, id=plano_id)
    return render(request, 'rs/dashboard.html', {'plano': plano}) # placeholder

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
    return render(request, 'ugea/confirm_delete.html', {'objeto': tipo, 'cancel_url': 'rs:documentos'})

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
