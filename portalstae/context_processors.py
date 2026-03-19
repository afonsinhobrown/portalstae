# portalstae/context_processors.py
from django.conf import settings

def login_urls(request):
    """Adiciona URLs de login ao contexto de templates"""
    return {
        'LOGIN_URLS': getattr(settings, 'LOGIN_URLS', {}),
        'LOGIN_REDIRECT_URLS': getattr(settings, 'LOGIN_REDIRECT_URLS', {}),
        'CURRENT_APP': getattr(request.resolver_match, 'app_name', '') if hasattr(request.resolver_match, 'app_name') else '',
    }