# REMOVA estas linhas:
# from .semantic_search import SemanticSearcher
# from .web_search import WebSearcher


class IntelligentFallback:
    def __init__(self):
        self.semantic_searcher = None  # Mude para None
        self.web_searcher = None       # Mude para None

    def get_semantic_searcher(self):
        """Lazy loading para semantic searcher"""
        if self.semantic_searcher is None:
            from .semantic_search import SemanticSearcher
            self.semantic_searcher = SemanticSearcher()
        return self.semantic_searcher

    def get_web_searcher(self):
        """Lazy loading para web searcher"""
        if self.web_searcher is None:
            from .web_search import WebSearcher
            self.web_searcher = WebSearcher()
        return self.web_searcher

    def handle_unknown_question(self, user_question, conversation_context):
        """Sistema inteligente para perguntas desconhecidas"""

        # 1. Tenta similaridade semântica (com lazy loading)
        semantic_searcher = self.get_semantic_searcher()
        semantic_results = semantic_searcher.find_similar_questions(user_question)

        if semantic_results and semantic_results[0]['similarity'] > 0.6:
            best_match = semantic_results[0]
            return f"**Pergunta similar**: '{best_match['faq'].pergunta}'\n\n{best_match['answer']}"

        # 2. Pesquisa na web (com lazy loading)
        web_searcher = self.get_web_searcher()
        web_result = web_searcher.search_real_time(user_question)

        if "não encontrei" not in web_result.lower():
            return web_result

        # 3. Fallback contextual
        return self._contextual_fallback(user_question)

    def _contextual_fallback(self, user_question):
        """Fallback baseado em palavras-chave"""
        keywords = {
            'documento': "📄 **Documentos para votar**: Bilhete de Identidade + Cartão de Eleitor (ambos obrigatórios)",
            'local': "📍 **Local de voto**: Consulte no seu Cartão de Eleitor ou STAE mais próximo",
            'horario': "🕒 **Horários STAE**: Segunda a Sexta, 7h30-15h30",
            'denuncia': "🚨 **Denúncias**: Linha 848 | email: denuncias@stae.gov.mz",
            'calendario': "📅 **Calendário**: Consulte site oficial da CNE para datas eleitorais",
            'votar': "🗳️ **Para votar**: BI + Cartão Eleitor + Secção de voto (no cartão)",
            'registar': "📋 **Registo eleitoral**: STAE mais próximo + BI + Comprovativo residência"
        }

        for keyword, response in keywords.items():
            if keyword in user_question.lower():
                return response

        # Resposta genérica mas útil
        return f"""
🤔 **Não tenho uma resposta específica para isso ainda.**

**Posso ajudar com:**
• 📄 Documentação necessária
• 📍 Locais de voto  
• 🕒 Horários e prazos
• 📞 Contactos do STAE
• 🗳️ Processo de votação

**Contacte directamente:** +258 21 123 456 | info@stae.gov.mz
"""