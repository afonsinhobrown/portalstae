# portalstae/asgi.py
import os
import django
from django.core.asgi import get_asgi_application

# 1. Definir o ambiente
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')

# 2. Inicializar o Django e obter a aplicação HTTP primeiro
# Isso garante que o AppRegistry esteja pronto antes de importarmos o routing/consumers
django_asgi_app = get_asgi_application()

# 3. Agora podemos importar o resto com segurança
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import recursoshumanos.routing

# 4. Definir o roteador final
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            recursoshumanos.routing.websocket_urlpatterns
        )
    ),
})