
# Script para atualizar views.py

caminho = 'gestaocombustivel/views.py'
with open(caminho, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Adicionar imports
if "FornecedorManutencao" not in content:
    content = content.replace(
        "FornecedorCombustivel, ContratoCombustivel,",
        "FornecedorCombustivel, ContratoCombustivel, FornecedorManutencao, ContratoManutencao,"
    )

# 2. Adicionar as Views no final
novas_views = """

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
            ContratoManutencao.objects.create(
                fornecedor=fornecedor,
                numero_contrato=numero,
                descricao=descricao,
                valor_total=valor,
                data_inicio=inicio,
                data_fim=fim,
                activo=True
            )
            messages.success(request, 'Contrato registado com sucesso!')
            return redirect('gestaocombustivel:lista_contratos_manutencao')
        except Exception as e:
            messages.error(request, f'Erro ao criar contrato: {e}')

    return render(request, 'gestaocombustivel/contrato_manutencao_form.html', {'oficinas': oficinas})
"""

# Só adiciona se não existir
if "def lista_oficinas" not in content:
    content += novas_views
    print("Views de oficina adicionadas.")
else:
    print("Views já existem.")

with open(caminho, 'w', encoding='utf-8') as f:
    f.write(content)
