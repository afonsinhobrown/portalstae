
@login_required_for_app('dfec')
def limpar_turmas(request, formacao_id):
    """Remove todas as turmas de uma formação"""
    formacao = get_object_or_404(Formacao, pk=formacao_id)
    count = formacao.turmas.count()
    formacao.turmas.all().delete()
    messages.success(request, f"{count} turmas foram removidas com sucesso.")
    return redirect('dfec:formacao_detalhe', pk=formacao_id)

@login_required_for_app('dfec')
def gerar_turmas_inteligente(request, formacao_id):
    """Gera turmas automaticamente com opções configuráveis"""
    formacao = get_object_or_404(Formacao, pk=formacao_id)
    
    # Se for POST, processa as configurações
    if request.method == "POST":
        qtd_turmas = int(request.POST.get('qtd_turmas', 0))
        distribuir_genero = request.POST.get('distribuir_genero') == 'on'
        
        # 1. Obter participantes aprovados ou inscritos (prioridade para aprovados)
        participantes = list(formacao.participantes.filter(status='APROVADO'))
        if not participantes:
            participantes = list(formacao.participantes.all())
            
        if not participantes:
            messages.warning(request, "Não há participantes para distribuir.")
            return redirect('dfec:formacao_detalhe', pk=formacao_id)
            
        total_parts = len(participantes)
        
        # Calcular tamanho da turma
        if qtd_turmas > 0:
            tamanho_turma = -(-total_parts // qtd_turmas) # Teto da divisão
        else:
            tamanho_turma = 60 # Default
            qtd_turmas = -(-total_parts // tamanho_turma)
            
        # Limpar turmas anteriores se solicitado (implícito na geração 'inteligente' nova)
        # formacao.turmas.all().delete() # Opcional, talvez perigoso apagar sem pedir
        
        # Distribuir
        random.shuffle(participantes) # Misturar para aleatoriedade
        
        chunks = [participantes[i:i + tamanho_turma] for i in range(0, len(participantes), tamanho_turma)]
        
        contador = formacao.turmas.count()
        
        for i, chunk in enumerate(chunks):
            contador += 1
            nome_turma = f"Turma {contador}"
            
            turma = Turma.objects.create(
                formacao=formacao,
                nome=nome_turma,
                data_inicio=formacao.data_inicio_real or formacao.data_inicio_planeada,
                data_fim=formacao.data_fim_real or formacao.data_fim_planeada
            )
            
            # Adicionar participantes
            turma.participantes_atribuidos.set(chunk)
            
            # Tentar atribuir um formador disponível (se houver users com grupo Formador)
            # Placeholder: pega o próprio usuário logado como formador se for staff, ou deixa vazio
            if request.user.is_staff:
                turma.formador_principal = request.user
                turma.save()
                
        messages.success(request, f"{len(chunks)} turmas geradas com sucesso!")
        return redirect('dfec:formacao_detalhe', pk=formacao_id)
    
    # Se for GET, redireciona (deveria ser POST via modal)
    messages.warning(request, "Use o formulário para gerar turmas.")
    return redirect('dfec:formacao_detalhe', pk=formacao_id)
