from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    path('', views.chat_interface, name='chat_interface'),
    path('api/', views.advanced_chat_api, name='chat_api'),
    path('widget/', views.chat_widget, name='chat_widget'),
    path('contribuicao/', views.contribuicao_painel, name='contribuicao_painel'),
    path('estatisticas/', views.estatisticas_painel, name='estatisticas_painel'),
]