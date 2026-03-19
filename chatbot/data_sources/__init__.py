# chatbot/data_sources/__init__.py
# (crie esta pasta e arquivo)
from .mozambique_apis import MozambiqueAPIs
from .document_processor import DocumentProcessor
from .external_databases import ExternalDatabases


class DataSourceManager:
    """Gerenciador central de todas as fontes de dados"""

    def __init__(self):
        self.moz_apis = MozambiqueAPIs()
        self.doc_processor = DocumentProcessor()
        self.external_dbs = ExternalDatabases()
        self.sources = {
            'stae_api': self.moz_apis.get_stae_data,
            'cne_api': self.moz_apis.get_cne_data,
            'documentos': self.doc_processor.search_documents,
            'leis': self.external_dbs.get_legal_documents,
            'locais_voto': self.moz_apis.get_voting_locations
        }

    def query_all_sources(self, query):
        """Consulta todas as fontes e retorna resultados consolidados"""
        results = []

        for source_name, source_func in self.sources.items():
            try:
                source_results = source_func(query)
                if source_results:
                    results.extend(source_results)
            except Exception as e:
                print(f"Erro na fonte {source_name}: {e}")

        return self._rank_results(results)