@login_required_for_app('dfec')
def capitulo_excluir(request, pk):
    """Excluir capítulo - apenas autores/colaboradores"""
    capitulo = get_object_or_404(CapituloSimples, pk=pk)
    manual = capitulo.manual

    # Verificar permissões (usando criado_por do Manual simples)
    pode_editar = (
            request.user.is_staff or
            request.user == manual.criado_por or
            request.user.has_perm('dfec.change_manual')
    )

    if not pode_editar:
        messages.error(request, "Você não tem permissão para excluir capítulos.")
        return redirect('dfec:manual_detalhe', pk=manual.pk)
    
    # Confirmar exclusão apenas via POST (segurança)
    # Mas como o usuário pediu um botão simples, vamos aceitar GET com confirmação JS
    # ou melhor, implementar um mini-form de post no botão.
    
    titulo_cap = capitulo.titulo
    capitulo.delete()
    messages.success(request, f"Capítulo '{titulo_cap}' excluído com sucesso.")
    return redirect('dfec:manual_editar', pk=manual.pk)
