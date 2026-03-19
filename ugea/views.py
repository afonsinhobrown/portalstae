from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Avg, Sum
from .models import Concurso, Juri, CadernoEncargos, Proposta, PropostaImagem, InscricaoConcurso, Contrato, Fornecedor, PedidoConsumo
from .forms import ConcursoForm, JuriForm, CadernoEncargosForm, PropostaForm, AvaliacaoPropostaForm, InscricaoConcursoForm, AnuncioForm
from recursoshumanos.models import Funcionario

def dashboard(request):
    concursos = Concurso.objects.all().order_by('-criado_em')
    # KPIs
    total = concursos.count()
    abertos = concursos.filter(status='aberto').count()
    em_avaliacao = concursos.filter(status='avaliacao').count()
    valor_total = concursos.aggregate(Sum('valor_estimado'))['valor_estimado__sum'] or 0
    
    # Contratos
    contratos = Contrato.objects.filter(ativo=True).order_by('-data_assinatura')

    return render(request, 'ugea/dashboard.html', {
        'concursos': concursos,
        'contratos': contratos,
        'total': total,
        'abertos': abertos,
        'em_avaliacao': em_avaliacao,
        'valor_total': valor_total
    })

def criar_concurso(request):
    if request.method == 'POST':
        form = ConcursoForm(request.POST, request.FILES)
        if form.is_valid():
            concurso = form.save()
            messages.success(request, f'Concurso {concurso.numero} iniciado com sucesso.')
            return redirect('ugea:detalhe_concurso', concurso_id=concurso.id)
    else:
        form = ConcursoForm()
    return render(request, 'ugea/form_concurso.html', {'form': form, 'titulo': 'Novo Processo de Contratação'})

def detalhe_concurso(request, concurso_id):
    concurso = get_object_or_404(Concurso, id=concurso_id)
    
    # Contexto auxiliar
    if hasattr(concurso, 'juris'):
        juri = concurso.juris.first() 
    else:
        juri = None
        
    caderno = getattr(concurso, 'cadernoencargos', None)
    propostas = concurso.propostas.all().order_by('valor_proposto')
    
    # Inicializar forms
    form_juri = JuriForm()
    form_proposta = PropostaForm()
    form_proposta.fields['inscricao'].queryset = concurso.inscricoes.all()

    # Processar Forms se POST
    if request.method == 'POST':
        if 'submit_juri' in request.POST:
            form_juri = JuriForm(request.POST)
            if form_juri.is_valid():
                j = form_juri.save(commit=False)
                j.concurso = concurso
                j.save()
                messages.success(request, 'Júri nomeado com sucesso.')
                return redirect('ugea:detalhe_concurso', concurso_id=concurso.id)
            else:
                messages.error(request, 'Erro ao nomear júri. Verifique os campos.')
        
        elif 'submit_proposta' in request.POST:
            form_proposta = PropostaForm(request.POST, request.FILES)
            form_proposta.fields['inscricao'].queryset = concurso.inscricoes.all()
            
            # Verificar se há imagens antes mesmo da validação rigorosa do form
            imagens_list = request.FILES.getlist('arquivos_imagem')
            
            if form_proposta.is_valid() or (not form_proposta.is_valid() and imagens_list and 'inscricao' in form_proposta.cleaned_data):
                p = form_proposta.save(commit=False)
                p.concurso = concurso
                if p.inscricao:
                    p.fornecedor = p.inscricao.empresa_nome
                    p.nuit = p.inscricao.nuit
                p.save()
                
                # Salvar múltiplas imagens
                for i, img in enumerate(imagens_list):
                    PropostaImagem.objects.create(proposta=p, imagem=img, ordem=i)
                
                # Chamar processamento IA
                p.processar_com_ia()
                
                messages.success(request, f'Proposta de {p.fornecedor} registada e processada!')
                return redirect('ugea:detalhe_concurso', concurso_id=concurso.id)
            else:
                messages.error(request, 'Erro na submissão. Certifique-se de que seleccionou a empresa e as imagens.')

    # Busca funcionários para seleção
    funcionarios = Funcionario.objects.all()
        
    return render(request, 'ugea/detalhe_concurso.html', {
        'concurso': concurso,
        'caderno': caderno,
        'juri': juri,
        'funcionarios': funcionarios,
        'propostas': propostas,
        'form_juri': form_juri,
        'form_proposta': form_proposta
    })

def eliminar_proposta(request, proposta_id):
    proposta = get_object_or_404(Proposta, id=proposta_id)
    concurso_id = proposta.concurso.id
    fornecedor = proposta.fornecedor
    proposta.delete()
    messages.warning(request, f'Proposta de {fornecedor} foi eliminada. Pode carregar novamente.')
    return redirect('ugea:detalhe_concurso', concurso_id=concurso_id)

def avaliar_proposta(request, proposta_id):
    proposta = get_object_or_404(Proposta, id=proposta_id)
    if request.method == 'POST':
        form = AvaliacaoPropostaForm(request.POST, instance=proposta)
        if form.is_valid():
            p = form.save(commit=False)
            # Calculo simples de pontuação final (ex: média)
            if p.pontuacao_tecnica and p.pontuacao_financeira:
                p.pontuacao_final = (p.pontuacao_tecnica * 0.6) + (p.pontuacao_financeira * 0.4) # Regra 60/40 exemplo
            p.save()
            messages.success(request, 'Avaliação registada.')
            return redirect('ugea:detalhe_concurso', concurso_id=proposta.concurso.id)
    else:
        form = AvaliacaoPropostaForm(instance=proposta)
    
    return render(request, 'ugea/form_avaliacao.html', {'form': form, 'proposta': proposta})

def processar_ocr(request, proposta_id):
    """Gatilho manual para o motor de visão (OCR)"""
    proposta = get_object_or_404(Proposta, id=proposta_id)
    proposta.processar_com_ia()
    messages.info(request, f'Análise OCR concluída para {proposta.fornecedor}.')
    return redirect('ugea:detalhe_concurso', concurso_id=proposta.concurso.id)

def editar_resumo(request, proposta_id):
    """Permite ao Júri corrigir dados Admin e Técnicos, mas bloqueia Financeiro"""
    proposta = get_object_or_404(Proposta, id=proposta_id)
    if request.method == 'POST':
        admin = request.POST.get('admin_data', '')
        tech = request.POST.get('tech_data', '')
        
        # Recupera apenas o que já estava na secção financeira original (extraído pelo OCR)
        import re
        partes = (proposta.resumo_automatico or "").split("--- SECCAO FINANCEIRA ---")
        fin_original = partes[1] if len(partes) > 1 else "Dados Financeiros não localizados."
        
        # Reconstrói ignorando qualquer tentativa de alteração financeira via POST
        novo_resumo = f"{admin}\n\n--- SECCAO TECNICA ---\n{tech}\n\n--- SECCAO FINANCEIRA ---{fin_original}"
        
        proposta.resumo_automatico = novo_resumo
        proposta.save()
        messages.success(request, 'Digitalização confirmada. Dados financeiros preservados conforme o OCR.')
    return redirect('ugea:detalhe_concurso', concurso_id=proposta.concurso.id)

def adjudicar_proposta(request, proposta_id):
    """Oficializa a proposta como vencedora e gera o contrato inicial"""
    proposta = get_object_or_404(Proposta, id=proposta_id)
    concurso = proposta.concurso
    
    # Marcar como vencedor (podemos usar a classificação ou apenas criar o contrato)
    proposta.classificacao = 1
    proposta.save()
    
    # Criar Contrato se não existir
    contrato, created = Contrato.objects.get_or_create(
        concurso=concurso,
        defaults={
            'proposta_vencedora': proposta,
            'numero_contrato': f"CTR/{concurso.id}/{timezone.now().year}",
            'data_inicio': timezone.now().date(),
            'data_fim': (timezone.now() + timezone.timedelta(days=proposta.prazo_entrega_dias)).date(),
            'valor_total': proposta.valor_proposto or 0,
            'tipo_servico': concurso.titulo,
            'ativo': True
        }
    )
    
    if created:
        messages.success(request, f'Proposta de {proposta.fornecedor} adjudicada! Contrato gerado.')
    else:
        messages.info(request, f'Esta proposta já possui um contrato ativo.')
        
    return redirect('ugea:detalhe_concurso', concurso_id=concurso.id)

def editar_concurso(request, concurso_id):
    concurso = get_object_or_404(Concurso, id=concurso_id)
    if request.method == 'POST':
        form = ConcursoForm(request.POST, instance=concurso)
        if form.is_valid():
            form.save()
            return redirect('ugea:detalhe_concurso', concurso_id=concurso.id)
    else:
        form = ConcursoForm(instance=concurso)
    return render(request, 'ugea/form_concurso.html', {'form': form, 'titulo': f'Editar {concurso.numero}'})

def editar_caderno(request, concurso_id):
    concurso = get_object_or_404(Concurso, id=concurso_id)
    from .forms import ItemCadernoEncargosFormSet
    
    # Tenta obter caderno existente ou None
    try:
        caderno = concurso.cadernoencargos
    except CadernoEncargos.DoesNotExist:
        caderno = None

    if request.method == 'POST':
        form = CadernoEncargosForm(request.POST, request.FILES, instance=caderno)
        if form.is_valid():
            c = form.save(commit=False)
            c.concurso = concurso
            c.save()
            
            # Salvar itens do caderno
            formset = ItemCadernoEncargosFormSet(request.POST, instance=c)
            if formset.is_valid():
                formset.save()
                
            messages.success(request, 'Caderno de Encargos e Lista de Serviços salvos com sucesso!')
            return redirect('ugea:detalhe_concurso', concurso_id=concurso.id)
    else:
        form = CadernoEncargosForm(instance=caderno)
        formset = ItemCadernoEncargosFormSet(instance=caderno)
    
    return render(request, 'ugea/editor_caderno.html', {
        'form': form, 
        'formset': formset,
        'concurso': concurso
    })

def imprimir_caderno(request, concurso_id):
    concurso = get_object_or_404(Concurso, id=concurso_id)
    caderno = get_object_or_404(CadernoEncargos, concurso=concurso)
    return render(request, 'ugea/print_caderno_completo.html', {'concurso': concurso, 'caderno': caderno})

def lista_cadernos(request):
    cadernos = CadernoEncargos.objects.select_related('concurso').all()
    concursos_sem_caderno = Concurso.objects.filter(cadernoencargos__isnull=True)
    return render(request, 'ugea/lista_cadernos.html', {
        'cadernos': cadernos, 
        'concursos_pendentes': concursos_sem_caderno
    })

def lista_contratos(request):
    """Lista completa de contratos geridos na UGEA."""
    contratos = Contrato.objects.all().order_by('-data_assinatura')
    return render(request, 'ugea/lista_contratos.html', {'contratos': contratos})

def lista_fornecedores(request):
    """Gestão Central de Fornecedores"""
    fornecedores = Fornecedor.objects.all().order_by('nome')
    return render(request, 'ugea/lista_fornecedores.html', {'fornecedores': fornecedores})

def novo_fornecedor(request):
    if request.method == 'POST':
        form = FornecedorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fornecedor registado com sucesso!')
            return redirect('ugea:lista_fornecedores')
    else:
        form = FornecedorForm()
    return render(request, 'ugea/form_generico.html', {'form': form, 'titulo': 'Novo Fornecedor'})

def novo_contrato(request):
    if request.method == 'POST':
        form = ContratoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Contrato registado com sucesso!')
            return redirect('ugea:lista_contratos')
    else:
        form = ContratoForm()
    return render(request, 'ugea/form_generico.html', {'form': form, 'titulo': 'Novo Contrato'})

def aprovacoes(request):
    """Painel de Aprovação de Pedidos de Consumo"""
    pedidos_pendentes = PedidoConsumo.objects.filter(status='pendente').order_by('-data_pedido')
    ultimos_aprovados = PedidoConsumo.objects.exclude(status='pendente').order_by('-data_pedido')[:10]
    
    return render(request, 'ugea/aprovacoes.html', {
        'pedidos': pedidos_pendentes,
        'historico': ultimos_aprovados
    })

@login_required
def avaliar_pedido(request, pedido_id):
    """Análise detalhada de um pedido de consumo (UGEA)"""
    pedido_ugea = get_object_or_404(PedidoConsumo, id=pedido_id)
    context = {'pedido': pedido_ugea}
    
    # Se for do módulo de combustível, buscar o pedido original para detalhes técnicos
    if pedido_ugea.modulo_origem == 'gestaocombustivel' and pedido_ugea.ref_id:
        from gestaocombustivel.models import PedidoCombustivel
        pedido_combustivel = PedidoCombustivel.objects.filter(id=pedido_ugea.ref_id).first()
        context['pedido_origem'] = pedido_combustivel
        context['tipo_analise'] = 'combustivel'

    if request.method == 'POST':
        acao = request.POST.get('acao')
        obs = request.POST.get('observacoes', '')
        
        if acao in ['aprovar', 'rejeitar']:
            novo_status = 'aprovado' if acao == 'aprovar' else 'rejeitado'
            pedido_ugea.status = novo_status
            pedido_ugea.observacao_aprovacao = obs
            pedido_ugea.save()
            
            # SINCRONIZAR COM MÓDULO DE ORIGEM (FUEL)
            if pedido_ugea.modulo_origem == 'gestaocombustivel' and context.get('pedido_origem'):
                p_fuel = context['pedido_origem']
                p_fuel.status = novo_status
                p_fuel.data_aprovacao = timezone.now()
                p_fuel.aprovado_por = request.user
                p_fuel.save()

            messages.success(request, f"Pedido {acao.capitalize()} com sucesso!")
            return redirect('ugea:aprovacoes')

    return render(request, 'ugea/avaliar_pedido.html', context)

def detalhe_contrato(request, contrato_id):
    contrato = get_object_or_404(Contrato, id=contrato_id)
    pagamentos = contrato.pagamentos.all().order_by('-data_pagamento')
    pedidos = contrato.pedidos_consumo.all().order_by('-data_pedido')
    
    if request.method == 'POST':
        # Registar Pagamento Rápido
        valor = request.POST.get('valor')
        ref = request.POST.get('referencia')
        if valor and ref:
            from .models import Pagamento
            Pagamento.objects.create(
                contrato=contrato,
                valor=valor,
                referencia=ref,
                descricao=request.POST.get('descricao', '')
            )
            messages.success(request, 'Pagamento registado com sucesso!')
            return redirect('ugea:detalhe_contrato', contrato_id=contrato.id)

    # Tentar vincular com Fornecedor real pelo NUIT para dados ricos
    from .models import Fornecedor
    fornecedor_obj = Fornecedor.objects.filter(nuit=contrato.proposta_vencedora.nuit).first()

    # Cálculos Financeiros Detalhados
    pagamento_executado = contrato.pagamentos.aggregate(Sum('valor'))['valor__sum'] or 0
    consumo_confirmado = contrato.pedidos_consumo.filter(status='aprovado').aggregate(Sum('valor_estimado'))['valor_estimado__sum'] or 0
    valor_divida = consumo_confirmado - pagamento_executado

    return render(request, 'ugea/detalhe_contrato.html', {
        'contrato': contrato,
        'pagamentos': pagamentos,
        'pedidos': pedidos,
        'fornecedor_obj': fornecedor_obj,
        'valor_contrato': contrato.valor_total,
        'pagamento_executado': pagamento_executado,
        'consumo_confirmado': consumo_confirmado,
        'valor_divida': valor_divida
    })

@login_required
def editar_contrato(request, contrato_id):
    contrato = get_object_or_404(Contrato, id=contrato_id)
    
    from .forms import ContratoForm, ItemContratoFormSet

    if request.method == 'POST':
        form = ContratoForm(request.POST, request.FILES, instance=contrato)
        formset = ItemContratoFormSet(request.POST, instance=contrato)
        
        if form.is_valid() and formset.is_valid():
            try:
                contrato = form.save()
                itens = formset.save()
                
                num_novos = len(formset.new_objects)
                num_mudados = len(formset.changed_objects)
                num_apagados = len(formset.deleted_objects)
                
                messages.success(request, f'Sucesso! {num_novos} novos itens adicionados.')
                return redirect('ugea:detalhe_contrato', contrato_id=contrato.id)
            except Exception as e:
                messages.error(request, f'Erro ao salvar no banco: {e}')
        else:
            # LOGS PARA O DESENVOLVEDOR (Ver no terminal)
            print("--- ERROS FORM CONTRATO ---")
            print(form.errors)
            print("--- ERROS FORMSET ITENS ---")
            print(formset.errors)
            messages.error(request, "Erro na validação. Certifique-se de que todos os itens têm Nome e Preço.")
    else:
        form = ContratoForm(instance=contrato)
        formset = ItemContratoFormSet(instance=contrato)

    return render(request, 'ugea/editar_contrato.html', {
        'form': form,
        'formset': formset,
        'contrato': contrato
    })

@login_required
def adicionar_item_rapido(request, contrato_id):
    """Adiciona um item ao contrato sem precisar da tela de edição completa"""
    if request.method == 'POST':
        contrato = get_object_or_404(Contrato, id=contrato_id)
        descricao = request.POST.get('descricao')
        preco = request.POST.get('preco_unitario')
        
        if descricao and preco:
            try:
                from .models import ItemContrato
                ItemContrato.objects.create(
                    contrato=contrato,
                    descricao=descricao,
                    preco_unitario=preco
                )
                messages.success(request, f'Serviço "{descricao}" adicionado!')
            except Exception as e:
                messages.error(request, f'Erro: {e}')
        else:
            messages.error(request, 'Preencha descrição e preço.')
            
    return redirect('ugea:detalhe_contrato', contrato_id=contrato_id)

@login_required
def excluir_item_contrato(request, item_id):
    """Exclui um item do contrato diretamente da lista de detalhes"""
    item = get_object_or_404(ItemContrato, id=item_id)
    contrato_id = item.contrato.id
    descricao = item.descricao
    
    if request.method == 'POST':
        item.delete()
        messages.success(request, f'Item "{descricao}" removido.')
    
    return redirect('ugea:detalhe_contrato', contrato_id=contrato_id)

def gestao_vendas(request, concurso_id):
    concurso = get_object_or_404(Concurso, id=concurso_id)
    inscricoes = concurso.inscricoes.all().order_by('-data_inscricao')
    
    if request.method == 'POST':
        form = InscricaoConcursoForm(request.POST, request.FILES)
        if form.is_valid():
            inscricao = form.save(commit=False)
            inscricao.concurso = concurso
            inscricao.save()
            messages.success(request, f'Inscrição da empresa {inscricao.empresa_nome} registada!')
            return redirect('ugea:gestao_vendas', concurso_id=concurso.id)
    else:
        form = InscricaoConcursoForm()
    
    return render(request, 'ugea/gestao_vendas.html', {
        'concurso': concurso,
        'inscricoes': inscricoes,
        'form': form
    })

@login_required
def editar_item_contrato(request, item_id):
    """Edita um item (serviço) do contrato"""
    from .models import ItemContrato
    item = get_object_or_404(ItemContrato, id=item_id)
    contrato_id = item.contrato.id
    
    if request.method == 'POST':
        item.descricao = request.POST.get('descricao')
        item.preco_unitario = request.POST.get('preco_unitario')
        item.save()
        messages.success(request, f'Item "{item.descricao}" atualizado com sucesso.')
    
    return redirect('ugea:detalhe_contrato', contrato_id=contrato_id)

    return redirect('ugea:detalhe_contrato', contrato_id=contrato_id)

@login_required
def sincronizar_itens_contrato(request, contrato_id):
    """Importa itens do Caderno de Encargos para o contrato se estiverem vazios"""
    from .models import Contrato, ItemContrato
    contrato = get_object_or_404(Contrato, id=contrato_id)
    caderno = getattr(contrato.concurso, 'cadernoencargos', None)
    
    if not caderno:
        messages.error(request, "Este contrato não possui um Caderno de Encargos associado.")
        return redirect('ugea:detalhe_contrato', contrato_id=contrato.id)
        
    itens_caderno = caderno.itens.all()
    if not itens_caderno.exists():
        messages.warning(request, "O Caderno de Encargos não possui itens listados.")
        return redirect('ugea:detalhe_contrato', contrato_id=contrato.id)
        
    count = 0
    for it in itens_caderno:
        _, created = ItemContrato.objects.get_or_create(
            contrato=contrato,
            descricao=it.descricao,
            defaults={'preco_unitario': 0}
        )
        if created: count += 1
        
    if count > 0:
        messages.success(request, f"{count} itens importados do Caderno de Encargos com sucesso!")
    else:
        messages.info(request, "Todos os itens do Caderno já existem neste contrato.")
        
    return redirect('ugea:detalhe_contrato', contrato_id=contrato.id)

@login_required
def carregar_template_caderno(request, concurso_id):
    """Injeta itens padrão no caderno dependendo do tipo de concurso"""
    from .models import ItemCadernoEncargos
    concurso = get_object_or_404(Concurso, id=concurso_id)
    caderno = getattr(concurso, 'cadernoencargos', None)
    
    if not caderno:
        messages.error(request, "Crie primeiro o Caderno de Encargos.")
        return redirect('ugea:detalhe_concurso', concurso_id=concurso.id)
        
    tipo = request.GET.get('tipo', 'manutencao')
    templates = {
        'manutencao': [
            'Manutenção Preventiva', 'Manutenção Correctiva', 'Troca de Óleo', 
            'Troca de Filtros', 'Troca de Bateria', 'Sistema de Travões', 
            'Sistema Elétrico', 'Troca de Pneus', 'Inspecção Periódica'
        ],
        'combustivel': [
            'Gasolina', 'Diesel'
        ]
    }
    
    items = templates.get(tipo, [])
    count = 0
    for desc in items:
        _, created = ItemCadernoEncargos.objects.get_or_create(
            caderno=caderno,
            descricao=desc,
            defaults={'unidade': 'Unidade' if tipo == 'manutencao' else 'Litros'}
        )
        if created: count += 1
        
    messages.success(request, f"{count} itens de {tipo} injetados no Caderno.")
    return redirect('ugea:editar_caderno', concurso_id=concurso.id)

def editar_anuncio(request, concurso_id):
    concurso = get_object_or_404(Concurso, id=concurso_id)
    
    if not concurso.texto_anuncio:
        # Gera texto padrão
        concurso.texto_anuncio = f"""O Secretariado Técnico de Administração Eleitoral (STAE) convida empresas interessadas a apresentar propostas para o Concurso {concurso.numero} referente a: {concurso.titulo}.

1. O concurso será regido pelo Regulamento de Contratação de Empreitada de Obras Públicas, Fornecimento de Bens e Prestação de Serviços ao Estado.

2. Os documentos do concurso podem ser adquiridos pelos interessados no endereço abaixo, mediante pagamento de uma taxa não reembolsável de {concurso.preco_caderno} MT.

3. As propostas devem ser entregues no endereço abaixo até: {concurso.data_encerramento.strftime('%d/%m/%Y às %H:%M')}.

4. A abertura das propostas será pública.

Local de Entrega: {concurso.local_entrega}
"""
    
    if request.method == 'POST':
        form = AnuncioForm(request.POST, instance=concurso)
        if form.is_valid():
            form.save()
            messages.success(request, 'Anúncio atualizado com sucesso!')
            return redirect('ugea:detalhe_concurso', concurso_id=concurso.id)
    else:
        form = AnuncioForm(instance=concurso)
        
    return render(request, 'ugea/editor_anuncio.html', {'form': form, 'concurso': concurso})

def imprimir_anuncio(request, concurso_id):
    concurso = get_object_or_404(Concurso, id=concurso_id)
    return render(request, 'ugea/print_anuncio.html', {'concurso': concurso})

def imprimir_recibo(request, inscricao_id):
    inscricao = get_object_or_404(InscricaoConcurso, id=inscricao_id)
    return render(request, 'ugea/print_recibo_venda.html', {'inscricao': inscricao})
