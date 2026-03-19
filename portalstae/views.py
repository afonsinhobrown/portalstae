# portalstae/views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def home(request):
    """Página inicial com links para todas as apps"""
    context = {
        'apps': [
            {'nome': 'Portal Administrativo', 'url': 'portal_admin:dashboard',
             'descricao': 'Gestão do sistema', 'login_required': True, 'tipo': 'admin'},
            {'nome': 'Recursos Humanos', 'url': 'rh:dashboard',
             'descricao': 'Gestão de funcionários', 'login_required': True, 'tipo': 'stae'},
            {'nome': 'Gestão de Equipamentos', 'url': 'equipamentos:dashboard',
             'descricao': 'Controlo de equipamentos', 'login_required': True, 'tipo': 'stae'},
            {'nome': 'Gestão de Combustível', 'url': 'combustivel:dashboard',
             'descricao': 'Controlo de combustível', 'login_required': True, 'tipo': 'stae'},
            {'nome': 'Site Institucional', 'url': 'site:home',
             'descricao': 'Site público do STAE', 'login_required': False, 'tipo': 'publico'},
            {'nome': 'Chatbot', 'url': 'chatbot:home',
             'descricao': 'Assistente virtual', 'login_required': False, 'tipo': 'publico'},
        ]
    }
    return render(request, 'home.html', context)


def login_redirect_inteligente(request):
    """
    Redireciona para o login correto baseado na app desejada.
    Uso: /login-redirect/?app=rh&next=/rh/dashboard/
    """
    app = request.GET.get('app', '').lower()
    next_url = request.GET.get('next', '/')

    login_urls = {
        'rh': 'login_stae',
        'recursoshumanos': 'login_stae',
        'equipamentos': 'login_stae',
        'gestaoequipamentos': 'login_stae',
        'combustivel': 'login_stae',
        'gestaocombustivel': 'login_stae',
        'portal_admin': 'login_admin',
        'admin_portal': 'login_admin',
        'credenciais': 'login_stae',
        'site': 'login_publico',
        'pagina_stae': 'login_publico',
        'chatbot': 'login_publico',
    }

    login_view = login_urls.get(app, 'login_publico')

    from django.urls import reverse
    url = reverse(login_view)

    if next_url:
        url += f'?next={next_url}'

    return redirect(url)


@login_required
def verificar_permissao_app(request, app):
    """API para verificar se usuário tem acesso a uma app"""
    user = request.user

    permissoes = {
        'rh': user.is_authenticated and (
                user.is_staff or
                user.groups.filter(name='STAE').exists() or
                hasattr(user, 'perfil') and user.perfil.tipo in ['funcionario', 'admin']
        ),
        'portal_admin': user.is_authenticated and user.is_staff,
        'equipamentos': user.is_authenticated and (
                user.is_staff or
                user.groups.filter(name='STAE').exists() or
                user.groups.filter(name='TECNICOS').exists()
        ),
        'combustivel': user.is_authenticated and (
                user.is_staff or
                user.groups.filter(name='STAE').exists() or
                user.groups.filter(name='COMBUSTIVEL').exists()
        ),
    }

    tem_permissao = permissoes.get(app, False)

    return JsonResponse({
        'app': app,
        'tem_permissao': tem_permissao,
        'user': {
            'username': user.username,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'groups': list(user.groups.values_list('name', flat=True))
        }
    })