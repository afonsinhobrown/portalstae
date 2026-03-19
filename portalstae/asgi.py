# portalstae/asgi.py
import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
# django.setup() foi removido pois o get_asgi_application() ja o faz implicitamente.

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import recursoshumanos.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            recursoshumanos.routing.websocket_urlpatterns
        )
    ),
})