import re
from datetime import datetime


# REMOVA: from .models import FAQEntry
# REMOVA: from .fallback_system import IntelligentFallback
# REMOVA: from .memory import ConversationMemory
# REMOVA: from .learning import LearningSystem
# REMOVA: from .integrations import FreeAIService


class AdvancedChatbotEngine:
    def __init__(self):
        self.fallback_system = None
        self.learning_system = None
        self.free_ai = None
        self.data_manager = None

    def get_fallback_system(self):
        """Lazy loading para fallback system"""
        if self.fallback_system is None:
            from .fallback_system import IntelligentFallback
            self.fallback_system = IntelligentFallback()
        return self.fallback_system

    def get_learning_system(self):
        """Lazy loading para learning system"""
        if self.learning_system is None:
            from .learning import LearningSystem
            self.learning_system = LearningSystem()
        return self.learning_system

    def get_free_ai(self):
        """Lazy loading para AI service"""
        if self.free_ai is None:
            from .integrations import FreeAIService
            self.free_ai = FreeAIService()
        return self.free_ai

    def get_data_manager(self):
        """Lazy loading para data manager"""
        if self.data_manager is None:
            from .mozambique_sources import DataSourceManager
            self.data_manager = DataSourceManager()
        return self.data_manager

    def process_message_advanced(self, user_message, session_id):
        """Processamento avançado de mensagens COM FONTES EXTERNAS"""

        # 1. Análise de intenção
        intent = self._analyze_intent(user_message)

        # 2. Busca na base de conhecimento local
        kb_response = self._knowledge_base_search(user_message, intent)

        if kb_response['confidence'] > 0.8:
            return kb_response['answer']

        # 3. NOVO: Busca em fontes externas (APIs, dados oficiais)
        external_response = self._search_external_sources(user_message, intent)
        if external_response:
            return external_response

        # 4. Similaridade semântica
        semantic_response = self._semantic_search(user_message)
        if semantic_response:
            return semantic_response

        # 5. Fallback inteligente
        fallback_system = self.get_fallback_system()
        memory = self._get_conversation_memory(session_id)
        context = memory.get_conversation_summary() if memory else ""

        final_response = fallback_system.handle_unknown_question(user_message, context)

        # Guarda na memória
        if memory:
            memory.add_interaction(user_message, final_response)

        return final_response

    def _get_conversation_memory(self, session_id):
        """Lazy loading para conversation memory"""
        try:
            from .memory import ConversationMemory
            return ConversationMemory(session_id)
        except Exception as e:
            print(f"Aviso: Não foi possível carregar ConversationMemory: {e}")
            return None

    def _analyze_intent(self, message):
        """Análise de intenção com NLP básico"""
        message = message.lower()

        intents = {
            'saudacao': any(
                word in message for word in ['ola', 'oi', 'olá', 'bom dia', 'boa tarde', 'boa noite', 'hey', 'hello']),
            'despedida': any(word in message for word in ['tchau', 'adeus', 'sair', 'bye', 'até logo']),
            'votacao': any(word in message for word in ['votar', 'voto', 'urna', 'eleitor', 'cédula']),
            'documentos': any(
                word in message for word in ['documento', 'bilhete', 'cartão', 'carta', 'bi', 'identidade']),
            'local': any(word in message for word in ['onde', 'local', 'endereço', 'proximo', 'secção']),
            'horario': any(word in message for word in ['horario', 'hora', 'funciona', 'aberto', 'fechado']),
            'denuncia': any(
                word in message for word in ['denúncia', 'denuncia', 'irregularidade', 'problema', 'queixa']),
            'calendario': any(word in message for word in ['quando', 'data', 'calendário', 'eleição']),
            'registro': any(word in message for word in ['registar', 'inscrever', 'cadastro', 'recenseamento']),
            'resultado': any(word in message for word in ['resultado', 'apuracao', 'vencedor', 'apurado']),
            'legislacao': any(word in message for word in ['lei', 'legislação', 'regulamento', 'norma']),
            'contacto': any(word in message for word in ['contacto', 'telefone', 'email', 'falar', 'linha'])
        }

        # Retorna a intenção com maior probabilidade
        for intent, detected in intents.items():
            if detected:
                return intent

        return 'outro'

    def _knowledge_base_search(self, user_message, intent):
        """Busca na base de conhecimento local com try-except"""
        try:
            from .models import FAQEntry

            # Busca exata
            exact_match = FAQEntry.objects.filter(
                pergunta__icontains=user_message
            ).first()

            if exact_match:
                return {'answer': exact_match.resposta, 'confidence': 0.9}

            # Busca por tags/intenção
            tag_match = FAQEntry.objects.filter(
                tags__contains=[intent]
            ).first()

            if tag_match:
                return {'answer': tag_match.resposta, 'confidence': 0.7}

            # Busca no conteúdo da resposta
            content_match = FAQEntry.objects.filter(
                resposta__icontains=user_message
            ).first()

            if content_match:
                return {'answer': content_match.resposta, 'confidence': 0.6}

        except Exception as e:
            print(f"Aviso: Erro na busca da base de conhecimento: {e}")

        return {'answer': None, 'confidence': 0.0}

    def _search_external_sources(self, user_message, intent):
        """NOVO: Busca em fontes externas de dados"""
        try:
            data_manager = self.get_data_manager()
            external_results = data_manager.query_all_sources(user_message)

            if external_results:
                best_result = external_results[0]

                # Formata resposta baseada no tipo de dado
                if best_result['tipo'] == 'local_voto':
                    return f"📍 **Informação de Locais de Voto:**\n\n{best_result['conteudo']}\n\n_Fonte: {best_result['fonte']}_"

                elif best_result['tipo'] == 'calendario':
                    return f"📅 **Calendário Eleitoral:**\n\n{best_result['conteudo']}\n\n_Fonte: {best_result['fonte']}_"

                elif best_result['tipo'] == 'contacto':
                    return f"📞 **Contactos Oficiais:**\n\n{best_result['conteudo']}\n\n_Fonte: {best_result['fonte']}_"

                elif best_result['tipo'] == 'resultado':
                    return f"📊 **Resultados Eleitorais:**\n\n{best_result['conteudo']}\n\n_Fonte: {best_result['fonte']}_"

                elif best_result['tipo'] == 'legislacao':
                    return f"📚 **Legislação Eleitoral:**\n\n{best_result['conteudo']}\n\n_Fonte: {best_result['fonte']}_"

                else:
                    return f"📋 **Informação Encontrada:**\n\n{best_result['conteudo']}\n\n_Fonte: {best_result['fonte']}_"

        except Exception as e:
            print(f"Aviso: Erro na busca em fontes externas: {e}")

        return None

    def _semantic_search(self, user_message):
        """Busca semântica com lazy loading"""
        try:
            fallback_system = self.get_fallback_system()
            semantic_searcher = fallback_system.get_semantic_searcher()
            similar = semantic_searcher.find_similar_questions(user_message)
            if similar and similar[0]['similarity'] > 0.5:
                return similar[0]['answer']
        except Exception as e:
            print(f"Aviso: Erro na busca semântica: {e}")
        return None

    def _get_time_based_greeting(self):
        """Saudação baseada na hora"""
        current_hour = datetime.now().hour

        if 5 <= current_hour < 12:
            return "Bom dia"
        elif 12 <= current_hour < 18:
            return "Boa tarde"
        else:
            return "Boa noite"

    def get_available_data_sources(self):
        """NOVO: Retorna informações sobre fontes de dados disponíveis"""
        sources_info = {
            'fontes_internas': 'Base de conhecimento local com FAQs e documentos',
            'fontes_externas': [
                'STAE - Dados de locais de voto e contactos',
                'CNE - Calendário eleitoral e resultados',
                'Legislação - Leis e regulamentos eleitorais'
            ],
            'busca_semantica': 'Sistema de similaridade para perguntas relacionadas',
            'fallback_inteligente': 'Respostas contextuais baseadas em palavras-chave'
        }
        return sources_info