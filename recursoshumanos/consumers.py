import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import CanalComunicacao, Mensagem, NotificacaoSistema
import os

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.canal_id = self.scope['url_route']['kwargs']['canal_id']
        self.canal_group_name = f'chat_{self.canal_id}'
        self.user = self.scope['user']

        # Verificar autenticação
        if self.user.is_anonymous:
            await self.close()
            return

        # Entrar no grupo
        await self.channel_layer.group_add(
            self.canal_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Sair do grupo
        await self.channel_layer.group_discard(
            self.canal_group_name,
            self.channel_name
        )

    # Receber mensagem do WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type', 'chat_message')
        
        if message_type == 'chat_message':
            message = text_data_json['message']
            file_data = text_data_json.get('file_data')
            file_name = text_data_json.get('file_name')

            # Salvar mensagem no banco de dados
            mensagem_salva = await self.salvar_mensagem(
                message,
                file_data,
                file_name
            )

            # Enviar mensagem para o grupo
            await self.channel_layer.group_send(
                self.canal_group_name,
                {
                    'type': 'chat_message',
                    'message_id': mensagem_salva['id'],
                    'sender_id': self.user.id,
                    'sender_name': self.user.get_full_name() or self.user.username,
                    'message': message,
                    'timestamp': mensagem_salva['timestamp'],
                    'has_file': mensagem_salva['has_file'],
                    'file_name': mensagem_salva['file_name'],
                    'file_url': mensagem_salva['file_url']
                }
            )

            # Criar notificações para outros membros
            await self.criar_notificacoes(mensagem_salva['id'])

    # Receber mensagem do grupo
    async def chat_message(self, event):
        # Enviar mensagem para o WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message_id': event['message_id'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'message': event['message'],
            'timestamp': event['timestamp'],
            'has_file': event['has_file'],
            'file_name': event['file_name'],
            'file_url': event['file_url']
        }))

    @database_sync_to_async
    def salvar_mensagem(self, conteudo, file_data=None, file_name=None):
        try:
            canal = CanalComunicacao.objects.get(id=self.canal_id)
            
            mensagem = Mensagem.objects.create(
                canal=canal,
                remetente=self.user,
                conteudo=conteudo,
                nome_arquivo=file_name if file_name else ''
            )

            return {
                'id': mensagem.id,
                'timestamp': mensagem.data_envio.isoformat(),
                'has_file': bool(file_name),
                'file_name': file_name,
                'file_url': mensagem.arquivo.url if mensagem.arquivo else None
            }
        except Exception as e:
            print(f"Erro ao salvar mensagem: {e}")
            raise e

    async def criar_notificacoes(self, mensagem_id):
        mensagem = await self.get_mensagem(mensagem_id)
        if not mensagem:
            return

        canal = await self.get_canal(mensagem.canal_id)
        destinatarios = await self.get_destinatarios(canal)
        
        # Link correto
        link = f'/recursoshumanos/comunicacao/chat/{canal.id}/' 

        for usuario in destinatarios:
            await self.criar_notificacao_sistema(
                usuario,
                'mensagem_recebida',
                'Nova mensagem',
                f'Nova mensagem em {canal.nome}',
                link
            )

    @database_sync_to_async
    def get_mensagem(self, mensagem_id):
        try:
            return Mensagem.objects.get(id=mensagem_id)
        except Mensagem.DoesNotExist:
            return None

    @database_sync_to_async
    def get_canal(self, canal_id):
        return CanalComunicacao.objects.get(id=canal_id)

    @database_sync_to_async
    def get_destinatarios(self, canal):
        if canal.enviar_para_todos:
            return list(User.objects.filter(is_active=True).exclude(id=self.user.id))
        return list(canal.membros.exclude(id=self.user.id))

    @database_sync_to_async
    def criar_notificacao_sistema(self, usuario, tipo, titulo, mensagem, link):
        try:
            NotificacaoSistema.objects.create(
                usuario=usuario,
                tipo=tipo,
                titulo=titulo,
                mensagem=mensagem,
                url_link=link  # CORRIGIDO: link_url -> url_link
            )
        except Exception as e:
            print(f"Erro criando notificação: {e}")


class NotificacaoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if self.user.is_anonymous:
            await self.close()
            return

        self.group_name = f'notificacoes_{self.user.id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def enviar_notificacao(self, event):
        await self.send(text_data=json.dumps(event['conteudo']))
