# recursoshumanos/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import CanalComunicacao, Mensagem, NotificacaoSistema
from datetime import datetime


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.canal_id = self.scope['url_route']['kwargs']['canal_id']
        self.canal_group_name = f'chat_{self.canal_id}'
        self.user = self.scope["user"]

        # Verificar se usu√°rio tem acesso ao canal
        has_access = await self.verificar_acesso_canal()

        if not has_access or not self.user.is_authenticated:
            await self.close()
            return

        # Entrar no grupo
        await self.channel_layer.group_add(
            self.canal_group_name,
            self.channel_name
        )

        await self.accept()

        # Notificar que usu√°rio entrou
        await self.channel_layer.group_send(
            self.canal_group_name,
            {
                'type': 'user_joined',
                'user_id': self.user.id,
                'username': self.user.get_full_name() or self.user.username,
                'timestamp': datetime.now().isoformat()
            }
        )

    async def disconnect(self, close_code):
        # Sair do grupo
        await self.channel_layer.group_discard(
            self.canal_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        tipo_mensagem = data.get('type')

        if tipo_mensagem == 'chat_message':
            await self.processar_mensagem_chat(data)
        elif tipo_mensagem == 'typing':
            await self.processar_typing(data)
        elif tipo_mensagem == 'read_receipt':
            await self.processar_read_receipt(data)

    async def processar_mensagem_chat(self, data):
        # Salvar mensagem no banco de dados
        mensagem_salva = await self.salvar_mensagem(
            data['message'],
            data.get('file_data'),
            data.get('file_name')
        )

        # Enviar mensagem para o grupo
        await self.channel_layer.group_send(
            self.canal_group_name,
            {
                'type': 'chat_message',
                'message_id': mensagem_salva['id'],
                'sender_id': self.user.id,
                'sender_name': self.user.get_full_name() or self.user.username,
                'message': data['message'],
                'timestamp': mensagem_salva['timestamp'],
                'has_file': mensagem_salva['has_file'],
                'file_name': mensagem_salva['file_name'],
                'file_url': mensagem_salva['file_url']
            }
        )

        # Criar notifica√ß√µes para outros membros
        await self.criar_notificacoes(mensagem_salva['id'])

    async def processar_typing(self, data):
        await self.channel_layer.group_send(
            self.canal_group_name,
            {
                'type': 'user_typing',
                'user_id': self.user.id,
                'username': self.user.get_full_name() or self.user.username,
                'is_typing': data['is_typing']
            }
        )

    async def processar_read_receipt(self, data):
        await self.marcar_mensagem_como_lida(data['message_id'])

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message_id': event['message_id'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'message': event['message'],
            'timestamp': event['timestamp'],
            'has_file': event['has_file'],
            'file_name': event.get('file_name'),
            'file_url': event.get('file_url')
        }))

    async def user_typing(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_typing',
            'user_id': event['user_id'],
            'username': event['username'],
            'is_typing': event['is_typing']
        }))

    async def user_joined(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user_id': event['user_id'],
            'username': event['username'],
            'timestamp': event['timestamp']
        }))

    @database_sync_to_async
    def verificar_acesso_canal(self):
        try:
            canal = CanalComunicacao.objects.get(id=self.canal_id)
            if canal.enviar_para_todos:
                return True
            return canal.membros.filter(id=self.user.id).exists()
        except CanalComunicacao.DoesNotExist:
            return False

    @database_sync_to_async
    def salvar_mensagem(self, conteudo, file_data=None, file_name=None):
        canal = CanalComunicacao.objects.get(id=self.canal_id)

        mensagem = Mensagem.objects.create(
            canal=canal,
            remetente=self.user,
            conteudo=conteudo,
            nome_arquivo=file_name
        )

        # Se tiver arquivo, salvar (em sistema real)
        if file_data and file_name:
            # Aqui salvaria o arquivo no sistema de arquivos
            pass

        return {
            'id': mensagem.id,
            'timestamp': mensagem.data_envio.isoformat(),
            'has_file': bool(file_name),
            'file_name': file_name,
            'file_url': mensagem.arquivo.url if mensagem.arquivo else None
        }

    @database_sync_to_async
    def criar_notificacoes(self, mensagem_id):
        mensagem = Mensagem.objects.get(id=mensagem_id)
        canal = mensagem.canal

        # Obter destinat√°rios (todos exceto o remetente)
        if canal.enviar_para_todos:
            destinatarios = User.objects.filter(is_active=True).exclude(id=self.user.id)
        else:
            destinatarios = canal.membros.exclude(id=self.user.id)

        for usuario in destinatarios:
            NotificacaoSistema.objects.create(
                usuario=usuario,
                tipo='mensagem',
                titulo='Nova mensagem',
                mensagem=f'{self.user.get_full_name()} enviou uma mensagem no canal {canal.nome}',
                link_url=f'/comunicacao/canal/{canal.id}/',
                link_texto='Ver mensagem'
            )

    @database_sync_to_async
    def marcar_mensagem_como_lida(self, mensagem_id):
        # Em sistema real, marcar mensagem como lida
        pass
class NotificacaoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            await self.close()
            return

        self.group_name = f'notificacoes_{self.user.id}'

        # Entrar no grupo
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Sair do grupo
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        # Este consumer È principalmente para enviar notificaÁıes do servidor para o cliente
        pass

    # Handler para enviar notificaÁ„o
    async def enviar_notificacao(self, event):
        await self.send(text_data=json.dumps({
            'type': 'nova_notificacao',
            'titulo': event['titulo'],
            'mensagem': event['mensagem'],
            'link_url': event.get('link_url', '#'),
            'timestamp': datetime.now().isoformat()
        }))

