@login_required_for_app('dfec')
def editar_atividade(request, pk):
    """Edita uma atividade existente"""
    atividade = get_object_or_404(Atividade, pk=pk)
    plano = atividade.plano
    
    # Carregar dados para os selects
    objetivos = ObjetivoInstitucional.objects.all()
    # Para referência nacional, buscamos atividades de Planos Nacionais (Centrais)
    # Excluindo a própria atividade para evitar auto-referência
    referencias = Atividade.objects.filter(plano__nivel='CENTRAL').exclude(pk=atividade.pk)
    
    if request.method == 'POST':
        atividade.nome = request.POST.get('nome')
        atividade.descricao = request.POST.get('descricao')
        
        # Datas
        data_ini = request.POST.get('data_inicio')
        if data_ini: atividade.data_inicio = data_ini
        
        data_fim = request.POST.get('data_fim')
        if data_fim: atividade.data_fim = data_fim
        
        # FKs
        obj_id = request.POST.get('objetivo')
        if obj_id:
            atividade.objetivo_institucional_id = obj_id
        else:
            atividade.objetivo_institucional = None
            
        ref_id = request.POST.get('referencia')
        if ref_id:
            atividade.referencia_nacional_id = ref_id
        else:
            atividade.referencia_nacional = None
            
        resp_id = request.POST.get('responsavel')
        if resp_id:
            atividade.responsavel_id = resp_id
        
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

# Vamos manter o resto (excluir_atividade) inalterado ou reescrevê-lo se necessário, mas vou focar em sobrescrever a função correta.
# Melhor usar a ferramenta multi_replace se o arquivo já existir no main views.py, mas como é um temp file que eu injeto, vou reescrever e injetar novamente sobrescrevendo a função anterior no views.py?
# Não, o python permite redefinição de função, mas o arquivo views.py vai ficar com código duplicado.
# O mais limpo é eu editar o views.py diretamente agora que sei onde está.
