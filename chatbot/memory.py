from django.core.cache import cache
import json


class ConversationMemory:
    def __init__(self, session_id):
        self.session_id = f"chatbot_{session_id}"

    def get_context(self):
        """Obtém contexto da conversa"""
        context = cache.get(self.session_id, {})
        return context.get('conversation', [])

    def add_interaction(self, user_message, bot_response):
        """Adiciona interação à memória"""
        conversation = self.get_context()
        conversation.append({"user": user_message, "bot": bot_response})
        conversation = conversation[-8:]  # Mantém últimas 8

        cache.set(self.session_id, {'conversation': conversation}, timeout=3600)

    def get_conversation_summary(self):
        """Cria resumo da conversa"""
        conversation = self.get_context()
        if not conversation:
            return "Sem histórico de conversa."

        summary = "Histórico recente:\n"
        for i, msg in enumerate(conversation[-3:], 1):
            summary += f"{i}. Utilizador: {msg['user']}\n   Assistente: {msg['bot'][:100]}...\n"

        return summary