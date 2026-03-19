
@login_required_for_app('dfec')
def gerar_brigadas_automatico(request, formacao_id):
    """
    Gera brigadas automaticamente a partir dos participantes aprovados da formação.
    Agrupa participantes por distrito para formarem brigadas locais.
    """
    from .models import Brigada  # Importação local para evitar circularidade se houver
    
    formacao = get_object_or_404(Formacao, pk=formacao_id)
    
    # 1. Filtrar participantes elegíveis (Aprovados)
    participantes_aprovados = formacao.participantes.filter(status='APROVADO')
    
    if not participantes_aprovados.exists():
        messages.warning(request, "Não há participantes aprovados para formar brigadas. Realize as avaliações primeiro.")
        return redirect('dfec:formacao_detalhe', pk=formacao_id)

    # 2. Agrupar por Distrito (para alocar brigadas na região correta)
    participantes_por_distrito = {}
    for p in participantes_aprovados:
        distrito = p.distrito or "Geral"
        if distrito not in participantes_por_distrito:
            participantes_por_distrito[distrito] = []
        participantes_por_distrito[distrito].append(p)

    brigadas_criadas_count = 0
    TAMANHO_BRIGADA = 3  # Exemplo: 3 pessoas por brigada (Supervisor, Digitador, Entrevistador)
    
    for distrito, lista_participantes in participantes_por_distrito.items():
        # Dividir em grupos de 3
        grupos = [lista_participantes[i:i + TAMANHO_BRIGADA] for i in range(0, len(lista_participantes), TAMANHO_BRIGADA)]
        
        for i, grupo in enumerate(grupos):
            # Criar código único para a brigada
            count_existente = Brigada.objects.filter(formacao=formacao).count()
            codigo_brigada = f"BRG-{formacao.ano}-{count_existente + 1:03d}"
            
            # Tenta definir papéis baseados na ordem (simplificado)
            supervisor = grupo[0].usuario if hasattr(grupo[0], 'usuario') else None # Assumindo que participante pode ter user linkado ou não
            # Como Participante não tem relação direta OneToOne com User no modelo visto, 
            # apenas criamos a Brigada e o usuário terá que editar para atribuir os Users específicos (Supervisor/Digitador)
            # ou, se o Participante fosse um User, faríamos a atribuição.
            # Dado o modelo atual onde Supervisor é um User (FK), e Participante é outro Model,
            # a automação cria a ESTRUTURA da brigada e aloca a "localidade".
            
            # Cria a Brigada
            brigada = Brigada.objects.create(
                codigo=codigo_brigada,
                formacao=formacao,
                provincia=formacao.provincia, # Assumindo mesmo da formação ou do participante
                distrito=distrito,
                localidade=grupo[0].localidade, # Pega localidade do primeiro membro
                ativa=True
            )
            
            # SE o modelo Brigada tiver ManyToMany para membros (como tentei adicionar):
            # brigada.membros.set(grupo) 
            
            # Como o campo 'membros' pode não existir ainda (foi cancelado), 
            # notificamos que a brigada foi criada.
            
            brigadas_criadas_count += 1

    if brigadas_criadas_count > 0:
        messages.success(request, f"{brigadas_criadas_count} brigadas foram geradas com base nos participantes aprovados.")
    else:
        messages.warning(request, "Não foi possível gerar brigadas (número insuficiente de participantes por distrito?).")
        
    return redirect('dfec:formacao_detalhe', pk=formacao_id)
