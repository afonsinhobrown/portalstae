# dfec/views_auth.py
from django.shortcuts import render
from django.contrib.auth.views import LoginView
from portalstae.decorators import login_required_for_app


def dfec_login(request):
    """View customizada de login para DFEC"""
    return LoginView.as_view(
        template_name='dfec/login_dfec.html',
        redirect_authenticated_user=True,
        extra_context={
            'titulo': 'Sistema DFEC - Direção de Formação e Estudos Eleitorais',
            'subtitulo': 'Acesso ao Sistema de Gestão Eleitoral'
        }
    )(request)


@login_required_for_app('dfec')
def dashboard(request):
    """Dashboard principal do DFEC - apenas usuários autorizados"""
    from django.db.models import Count
    from .models import PlanoAtividade, Formacao, Manual

    # Estatísticas
    estatisticas = {
        'planos_ativos': PlanoAtividade.objects.filter(ativo=True).count(),
        'formacoes_ativas': Formacao.objects.filter(estado='ativa').count(),
        'formacoes_concluidas': Formacao.objects.filter(estado='concluida').count(),
        'formandos_total': Formacao.objects.aggregate(
            total=Count('formandos')
        )['total'] or 0,
        'manuais_publicados': Manual.objects.filter(publicado=True).count(),
        'manuais_rascunho': Manual.objects.filter(publicado=False).count(),
    }

    # Planos recentes
    planos_recentes = PlanoAtividade.objects.filter(
        ativo=True
    ).order_by('-data_inicio')[:5]

    # Formações recentes
    formacoes_recentes = Formacao.objects.filter(
        estado__in=['ativa', 'agendada']
    ).order_by('-data_inicio')[:5]

    # Manuais recentes
    manuais_recentes = Manual.objects.filter(
        publicado=True
    ).order_by('-data_criacao')[:5]

    context = {
        'titulo': 'Dashboard DFEC',
        'estatisticas': estatisticas,
        'planos_recentes': planos_recentes,
        'formacoes_recentes': formacoes_recentes,
        'manuais_recentes': manuais_recentes,
    }

    return render(request, 'dfec/dashboard.html', context)