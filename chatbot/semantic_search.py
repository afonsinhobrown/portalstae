from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


# REMOVA esta linha: from .models import FAQEntry


class SemanticSearcher:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words=['o', 'a', 'os', 'as', 'de', 'do', 'da', 'em', 'um', 'uma', 'é', 'são']
        )
        self.faqs = []
        self.texts = []
        self.tfidf_matrix = None
        self._build_semantic_index()

    def _build_semantic_index(self):
        """Constrói índice semântico - AGORA COM TEXTO SIMPLES"""
        try:
            from .models import FAQEntry
            self.faqs = list(FAQEntry.objects.all())

            if not self.faqs:
                self.texts = []
                self.tfidf_matrix = None
                return

            # Converte tags de texto para lista
            self.texts = []
            for faq in self.faqs:
                # Se tags for texto, converte para formato de busca
                tags_text = faq.tags if isinstance(faq.tags, str) else ','.join(faq.tags)
                self.texts.append(f"{faq.pergunta} {faq.resposta} {tags_text}")

            if self.texts:
                self.tfidf_matrix = self.vectorizer.fit_transform(self.texts)
            else:
                self.tfidf_matrix = None

        except Exception as e:
            print(f"Aviso: Não foi possível carregar FAQs: {e}")
            self.faqs = []
            self.texts = []
            self.tfidf_matrix = None


    def find_similar_questions(self, user_question, threshold=0.3):
        """Encontra perguntas similares"""
        if not self.faqs or not self.tfidf_matrix:
            return []

        try:
            user_vector = self.vectorizer.transform([user_question])
            similarities = cosine_similarity(user_vector, self.tfidf_matrix)[0]

            similar_indices = np.where(similarities >= threshold)[0]
            similar_results = []

            for idx in similar_indices:
                similar_results.append({
                    'faq': self.faqs[idx],
                    'similarity': similarities[idx],
                    'answer': self.faqs[idx].resposta
                })

            similar_results.sort(key=lambda x: x['similarity'], reverse=True)
            return similar_results[:3]

        except Exception as e:
            print(f"Erro em similaridade semântica: {e}")
            return []