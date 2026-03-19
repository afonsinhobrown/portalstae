@login_required_for_app('dfec')
def editar_atividade(request, pk):
    """Edita uma atividade existente"""
    atividade = get_object_or_404(Atividade, pk=pk)
    plano = atividade.plano
    
    if request.method == 'POST':
        # Simples update manual por enquanto, ou usar form se houver
        atividade.nome = request.POST.get('nome')
        atividade.data_inicio = request.POST.get('data_inicio')
        atividade.data_fim = request.POST.get('data_fim')
        atividade.status = request.POST.get('status')
        # Outros campos se necessário
        atividade.save()
        messages.success(request, f"Atividade '{atividade.nome}' atualizada com sucesso.")
        return redirect('dfec:plano_detalhe', pk=plano.pk)
    
    # Se for GET, renderiza o form (reutilizando atividade_form.html se existir, ou criar)
    return render(request, 'dfec/planificacao/atividade_form.html', {
        'atividade': atividade,
        'plano': plano,
        'editar': True
    })

@login_required_for_app('dfec')
def excluir_atividade(request, pk):
    """Exclui uma atividade"""
    atividade = get_object_or_404(Atividade, pk=pk)
    plano_id = atividade.plano.id
    nome = atividade.nome
    
    if request.method == 'POST':
        atividade.delete()
        messages.success(request, f"Atividade '{nome}' excluída com sucesso.")
        return redirect('dfec:plano_detalhe', pk=plano_id)
        
    # Se for GET, confirmação? Ou apenas POST direto do modal/form
    # Vamos assumir post direto ou página de confirmação.
    # Para simplificar, vou fazer redirecionar se for GET com warning, ou view de confirmação.
    return render(request, 'dfec/planificacao/confirmar_exclusao_atividade.html', {'atividade': atividade})
