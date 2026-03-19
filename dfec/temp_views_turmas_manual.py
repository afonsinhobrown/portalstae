
@login_required_for_app('dfec')
def turma_detalhe(request, turma_id):
    """Exibe os detalhes de uma turma específica e seus participantes"""
    turma = get_object_or_404(Turma, pk=turma_id)
    return render(request, 'dfec/turmas/detalhe_turma.html', {'turma': turma})

@login_required_for_app('dfec')
def turma_criar_manual(request, formacao_id):
    """Cria uma turma manualmente com seleção de participantes"""
    formacao = get_object_or_404(Formacao, pk=formacao_id)
    
    if request.method == 'POST':
        nome = request.POST.get('nome')
        sala = request.POST.get('sala')
        data_inicio = request.POST.get('data_inicio')
        data_fim = request.POST.get('data_fim')
        participantes_ids = request.POST.getlist('participantes')
        
        if not participantes_ids:
            messages.error(request, "É necessário selecionar pelo menos um participante para criar a turma.")
        else:
            try:
                turma = Turma.objects.create(
                    formacao=formacao,
                    nome=nome,
                    sala=sala,
                    data_inicio=data_inicio if data_inicio else None,
                    data_fim=data_fim if data_fim else None
                )
                
                # Se o usuário for staff, atribui como formador (simples) ou poderia vir do form
                if request.user.is_staff:
                    turma.formador_principal = request.user
                    turma.save()
                
                participantes = formacao.participantes.filter(id__in=participantes_ids)
                turma.participantes_atribuidos.set(participantes)
                
                messages.success(request, f"Turma '{turma.nome}' criada com {participantes.count()} participantes.")
                return redirect('dfec:formacao_detalhe', pk=formacao_id)
            except Exception as e:
                messages.error(request, f"Erro ao criar turma: {str(e)}")
    
    # Preparar participantes disponíveis (Aprovados e não alocados em turmas desta formação)
    # Excluir participantes que já estão em alguma turma DESTA formação
    participantes_em_turmas = Turma.objects.filter(formacao=formacao).values_list('participantes_atribuidos', flat=True)
    participantes_disponiveis = formacao.participantes.filter(status='APROVADO').exclude(id__in=participantes_em_turmas)
    
    # Se não houver aprovados disponíveis, mostre todos os aprovados (caso queira redistribuir) 
    # ou mostre mensagem. Vamos mostrar os 'realmente' disponíveis primeiro.
    # Fallback: se quiser permitir que alguém troque de turma, a lógica seria mais complexa.
    # Por enquanto, assume-se alocação única.
    
    context = {
        'formacao': formacao,
        'participantes_disponiveis': participantes_disponiveis
    }
    return render(request, 'dfec/turmas/form.html', context)
