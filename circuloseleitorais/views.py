from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import CirculoEleitoral, PostoVotacao, DivisaoAdministrativa
from .forms import CirculoForm, PostoForm
from eleicao.models import Eleicao
from rs.models import DadosRecenseamento

def dashboard(request):
    total_circulos = CirculoEleitoral.objects.count()
    total_postos = PostoVotacao.objects.count()
    circulos = CirculoEleitoral.objects.all().select_related('eleicao').order_by('-id')
    eleicoes = Eleicao.objects.filter(ativo=True)
    
    context = {
        'total_circulos': total_circulos,
        'total_postos': total_postos,
        'circulos': circulos,
        'eleicoes': eleicoes
    }
    return render(request, 'circuloseleitorais/dashboard.html', context)

def criar_circulo(request):
    eleicao_id = request.GET.get('eleicao_id')
    initial_data = {}
    if eleicao_id:
        initial_data['eleicao'] = eleicao_id

    if request.method == 'POST':
        form = CirculoForm(request.POST)
        if form.is_valid():
            circulo = form.save()
            messages.success(request, 'Círculo criado com sucesso!')
            return redirect('circuloseleitorais:detalhe_circulo', circulo_id=circulo.id)
    else:
        form = CirculoForm(initial=initial_data)
    return render(request, 'circuloseleitorais/form_circulo.html', {'form': form, 'titulo': 'Novo Círculo'})

def detalhe_circulo(request, circulo_id):
    circulo = get_object_or_404(CirculoEleitoral, id=circulo_id)
    postos = circulo.postovotacao_set.all()
    
    if request.method == 'POST': # Adicionar Posto Rápido
        form_posto = PostoForm(request.POST)
        if form_posto.is_valid():
            posto = form_posto.save(commit=False)
            posto.circulo = circulo
            posto.save()
            messages.success(request, 'Posto de votação adicionado!')
            return redirect('circuloseleitorais:detalhe_circulo', circulo_id=circulo.id)
    else:
        form_posto = PostoForm()

    return render(request, 'circuloseleitorais/detalhe_circulo.html', {
        'circulo': circulo,
        'postos': postos,
        'form_posto': form_posto
    })

def editar_circulo(request, circulo_id):
    circulo = get_object_or_404(CirculoEleitoral, id=circulo_id)
    if request.method == 'POST':
        form = CirculoForm(request.POST, instance=circulo)
        if form.is_valid():
            form.save()
            return redirect('circuloseleitorais:detalhe_circulo', circulo_id=circulo.id)
    else:
        form = CirculoForm(instance=circulo)
    return render(request, 'circuloseleitorais/form_circulo.html', {'form': form, 'titulo': f'Editar {circulo.nome}'})

def gerar_circulos_automatico(request, eleicao_id):
    """Gera automaticamente círculos baseados no tipo de eleição e na Divisão Administrativa Real"""
    eleicao = get_object_or_404(Eleicao, id=eleicao_id)
    
    base_dados = []
    if eleicao.tipo in ['geral', 'presidencial', 'legislativa']:
        # Para Gerais, os círculos são as Províncias
        provincias = DivisaoAdministrativa.objects.filter(nivel='provincia').order_by('codigo')
        for p in provincias:
            base_dados.append({
                'nome': p.nome,
                'provincia': p.nome,
                'codigo': p.codigo
            })
    elif eleicao.tipo in ['provincial', 'autarquica']:
        # Para Provinciais e Autárquicas, sugerimos os Distritos
        distritos = DivisaoAdministrativa.objects.filter(nivel='distrito').select_related('parent').order_by('codigo')
        for d in distritos:
            base_dados.append({
                'nome': d.nome,
                'provincia': d.parent.nome if d.parent else "N/A",
                'codigo': d.codigo
            })
    
    if request.method == 'POST':
        selecionados = request.POST.getlist('itens_selecionados')
        map_dados = {item['codigo']: item for item in base_dados}
        
        for codigo in selecionados:
            if codigo in map_dados:
                data = map_dados[codigo]
                CirculoEleitoral.objects.get_or_create(
                    eleicao=eleicao,
                    codigo=codigo,
                    defaults={
                        'nome': data['nome'],
                        'provincia': data['provincia'],
                        'ativo': True
                    }
                )
        messages.success(request, f"Círculos Eleitorais gerados com sucesso para {eleicao.nome}")
        return redirect('circuloseleitorais:dashboard')

    return render(request, 'circuloseleitorais/gerar_circulos.html', {
        'eleicao': eleicao,
        'itens': base_dados
    })

def sincronizar_dados_rs(request, eleicao_id):
    """Busca dados de eleitores e mesas no módulo RS"""
    eleicao = get_object_or_404(Eleicao, id=eleicao_id)
    circulos = CirculoEleitoral.objects.filter(eleicao=eleicao)
    
    atualizados = 0
    for circulo in circulos:
        dados_rs = DadosRecenseamento.objects.filter(
            distrito__icontains=circulo.nome,
            ano__lte=eleicao.ano
        ).order_by('-ano').first()
        
        if dados_rs:
            circulo.num_eleitores = dados_rs.total_eleitores
            circulo.num_mesas = dados_rs.total_mesas
            circulo.save()
            atualizados += 1
            
    messages.info(request, f"Sincronização concluída: {atualizados} círculos atualizados com dados do RS.")
    return redirect('circuloseleitorais:dashboard')
import pandas as pd
import io

def importar_postos(request, circulo_id):
    """Importação em massa de Postos de Votação e Mesas para um Círculo"""
    circulo = get_object_or_404(CirculoEleitoral, id=circulo_id)
    
    if request.method == 'POST':
        file = request.FILES.get('arquivo')
        if not file:
            messages.error(request, 'Nenhum ficheiro selecionado.')
            return redirect('circuloseleitorais:importar_postos', circulo_id=circulo_id)

        try:
            if file.name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file)
                # Normalizar colunas
                mapping = {
                    'Código': 'codigo', 'Codigo': 'codigo',
                    'Nome': 'nome',
                    'Mesas': 'num_mesas', 'Mesa': 'num_mesas',
                    'Endereço': 'endereco', 'Endereco': 'endereco'
                }
                df.columns = [mapping.get(str(c).strip().capitalize(), str(c).strip().lower()) for c in df.columns]
                
                criados = 0
                for _, row in df.iterrows():
                    PostoVotacao.objects.create(
                        circulo=circulo,
                        codigo=str(row.get('codigo', '')),
                        nome=str(row.get('nome', '')),
                        num_mesas=int(row.get('num_mesas', 1)),
                        endereco=str(row.get('endereco', ''))
                    )
                    criados += 1
                messages.success(request, f"Sucesso: {criados} postos e respetivas mesas importados.")
            
            else: # CSV
                import csv
                decoded_file = file.read().decode('utf-8').splitlines()
                reader = csv.DictReader(decoded_file)
                criados = 0
                for row in reader:
                    PostoVotacao.objects.create(
                        circulo=circulo,
                        codigo=row.get('Código', row.get('codigo', '')),
                        nome=row.get('Nome', row.get('nome', '')),
                        num_mesas=int(row.get('Mesas', row.get('num_mesas', 1))),
                        endereco=row.get('Endereço', row.get('endereco', ''))
                    )
                    criados += 1
                messages.success(request, f"Sucesso: {criados} postos/mesas importados via CSV.")
                
            return redirect('circuloseleitorais:detalhe_circulo', circulo_id=circulo_id)
        except Exception as e:
            messages.error(request, f"Erro ao processar ficheiro: {str(e)}")
            
    return render(request, 'circuloseleitorais/importar_postos.html', {'circulo': circulo})
def eliminar_circulo(request, circulo_id):
    """Elimina um círculo e todos os seus dados vinculados"""
    circulo = get_object_or_404(CirculoEleitoral, id=circulo_id)
    nome = circulo.nome
    circulo.delete()
    messages.warning(request, f"Círculo '{nome}' removido definitivamente do sistema.")
    return redirect('circuloseleitorais:dashboard')
