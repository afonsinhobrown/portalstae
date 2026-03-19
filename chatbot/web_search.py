import requests
from bs4 import BeautifulSoup
import time
from django.conf import settings


class WebSearcher:
    def __init__(self):
        self.official_sources = [
            'https://www.stae.gov.mz',
            'https://www.cne.org.mz',
            'https://www.portaldogoverno.gov.mz',
        ]

    def search_real_time(self, query, context="STAE Moçambique eleições"):
        """Pesquisa em fontes oficiais"""
        try:
            results = []

            # Pesquisa em sites oficiais
            for site in self.official_sources:
                site_result = self._search_site(site, query)
                if site_result:
                    results.append(site_result)

            return self._process_search_results(results, query)

        except Exception as e:
            return f"Desculpe, não consegui pesquisar informação atualizada. {str(e)}"

    def _search_site(self, site_url, query):
        """Pesquisa em site específico"""
        try:
            response = requests.get(site_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Procura conteúdo relevante
            relevant_elements = soup.find_all(['p', 'article', 'div'],
                                              string=lambda text: text and query.lower() in text.lower())

            if relevant_elements:
                content = " ".join([elem.get_text()[:200] for elem in relevant_elements[:2]])
                return f"**Fonte oficial**: {site_url}\n{content}"

        except Exception as e:
            print(f"Erro ao pesquisar {site_url}: {e}")

        return None

    def _process_search_results(self, results, original_query):
        """Processa resultados da pesquisa"""
        if not results:
            return self._get_fallback_response(original_query)

        summary = f"**Informação de fontes oficiais:**\n\n"

        for i, result in enumerate(results[:3], 1):
            summary += f"{i}. {result}\n\n"

        summary += "*Para verificação completa, visite os sites oficiais do STAE e CNE.*"

        return summary

    def _get_fallback_response(self, query):
        return f"Não encontrei informação específica sobre '{query}' em fontes oficiais. Recomendo contactar o STAE directamente."