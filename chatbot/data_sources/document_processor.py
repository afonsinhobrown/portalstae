# chatbot/data_sources/document_processor.py
import os
import PyPDF2
from django.conf import settings


class DocumentProcessor:
    """Processa documentos PDF, Word, etc."""

    def __init__(self):
        self.documents_path = os.path.join(settings.MEDIA_ROOT, 'documentos')

    def extract_text_from_pdf(self, file_path):
        """Extrai texto de PDFs"""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            print(f"Erro ao extrair PDF {file_path}: {e}")
            return ""

    def search_in_documents(self, query):
        """Busca query em todos os documentos"""
        results = []

        if not os.path.exists(self.documents_path):
            return results

        for filename in os.listdir(self.documents_path):
            if filename.endswith('.pdf'):
                file_path = os.path.join(self.documents_path, filename)
                content = self.extract_text_from_pdf(file_path)

                if query.lower() in content.lower():
                    results.append({
                        'tipo': 'documento',
                        'titulo': filename,
                        'conteudo': content[:500] + "...",
                        'relevancia': 'alta' if query.lower() in content.lower() else 'media',
                        'fonte': f"Documento: {filename}"
                    })

        return results