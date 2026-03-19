# recursoshumanos/routing.py
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/chat/<int:canal_id>/', consumers.ChatConsumer.as_asgi()),
    path('ws/notificacoes/', consumers.NotificacaoConsumer.as_asgi()),
]