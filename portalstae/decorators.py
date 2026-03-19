# portalstae/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.conf import settings


def login_required_for_app(app_name):
    """
    Decorator que redireciona para o login CORRETO da app.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Se não está autenticado, redireciona para login da app
            if not request.user.is_authenticated:
                app_login_urls = getattr(settings, 'APP_LOGIN_URLS', {})
                login_url = app_login_urls.get(app_name, settings.LOGIN_URL)
                return redirect(f"{login_url}?next={request.path}")

            # Se está autenticado, verifica se pode acessar esta app
            if not user_can_access_app(request.user, app_name):
                messages.error(request, f"Você não tem acesso à área {app_name}.")
                return redirect('home')

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def user_can_access_app(user, app_name):
    """Verifica se usuário pode acessar determinada app"""

    # Se é superusuário, tem acesso a tudo
    if user.is_superuser:
        return True

    # Mapeamento de permissões por app
    permissions = {
        'rh': lambda u: (
                u.is_staff or
                u.groups.filter(name='STAE').exists() or
                hasattr(u, 'perfil') and u.perfil.tipo in ['funcionario', 'admin']
        ),
        'admin_portal': lambda u: u.is_staff,
        'gestaoequipamentos': lambda u: (
                u.is_staff or
                u.groups.filter(name='STAE').exists() or
                u.groups.filter(name='TECNICOS').exists()
        ),
        'gestaocombustivel': lambda u: (
                u.is_staff or
                u.groups.filter(name='STAE').exists() or
                u.groups.filter(name='COMBUSTIVEL').exists()
        ),
        'dfec': lambda u: (  # PERMISSÕES DO DFEC
                u.is_staff or
                u.groups.filter(name='STAE').exists() or
                u.groups.filter(name='DFEC').exists() or
                hasattr(u, 'perfil') and u.perfil.tipo in ['admin', 'dfec']
        ),
        'credenciais': lambda u: u.is_authenticated,
        'pagina_stae': lambda u: True,  # Público
        'site': lambda u: True,  # Público
        'chatbot': lambda u: True,  # Público
    }

    check = permissions.get(app_name, lambda u: False)
    return check(user)