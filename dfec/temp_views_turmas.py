
@login_required_for_app('dfec')
def gerar_turmas_inteligente(request, formacao_id):
    """Gera turmas automaticamente distribuindo participantes"""
    formacao = get_object_or_404(Formacao, pk=formacao_id)
    
    # 1. Obter participantes sem turma
    # Nota: O modelo Turma tem ManyToManyField para participantes_atribuidos.
    # Para simplificar, vamos pegar todos os participantes inscritos.
    # Numa implementação mais robusta, filtraríamos os que já estão em turmas.
    todos_participantes = list(formacao.participantes.all())
    
    if not todos_participantes:
        messages.warning(request, "Não há participantes para distribuir em turmas.")
        return redirect('dfec:formacao_detalhe', pk=formacao_id)
    
    # Tamanho da turma (padrão 60)
    TAMANHO_TURMA = 60
    
    # Split list into chunks
    chunks = [todos_participantes[i:i + TAMANHO_TURMA] for i in range(0, len(todos_participantes), TAMANHO_TURMA)]
    
    # Criar turmas
    turmas_criadas = 0
    
    # Limpar turmas vazias antigas se desejar (opcional)
    # formacao.turmas.filter(participantes_atribuidos__isnull=True).delete()
    
    for i, chunk in enumerate(chunks):
        nome_turma = f"Turma {i + 1} - Automática"
        
        # Verificar se já existe turma com esse nome para evitar duplicatas óbvias
        turma, created = Turma.objects.get_or_create(
            formacao=formacao,
            nome=nome_turma,
            defaults={
                'data_inicio': formacao.data_inicio_real or formacao.data_inicio_planeada,
                'data_fim': formacao.data_fim_real or formacao.data_fim_planeada
            }
        )
        
        if created:
            turmas_criadas += 1
            
        # Adicionar participantes
        turma.participantes_atribuidos.set(chunk)
        turma.save()
        
    messages.success(request, f"{turmas_criadas} turmas geradas/atualizadas com sucesso!")
    return redirect('dfec:formacao_detalhe', pk=formacao_id)

@login_required_for_app('dfec')
def criar_turma_vazia(request, formacao_id):
    """Cria uma única turma vazia"""
    formacao = get_object_or_404(Formacao, pk=formacao_id)
    
    # Encontrar o próximo número de turma
    count = formacao.turmas.count() + 1
    nome_turma = f"Turma {count}"
    
    Turma.objects.create(
        formacao=formacao,
        nome=nome_turma,
        data_inicio=formacao.data_inicio_real or formacao.data_inicio_planeada,
        data_fim=formacao.data_fim_real or formacao.data_fim_planeada
    )
    
    messages.success(request, "Nova turma criada com sucesso!")
    return redirect('dfec:formacao_detalhe', pk=formacao_id)
