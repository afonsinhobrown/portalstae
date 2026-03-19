import requests
import json
from django.conf import settings


class FreeAIService:
    def __init__(self):
        self.models = {
            'portuguese_llm': 'pierreguillou/bert-large-cased-squad-v1.1-portuguese'
        }

    def get_free_response(self, user_message, context):
        """Usa modelos gratuitos do Hugging Face"""
        try:
            API_URL = f"https://api-inference.huggingface.co/models/{self.models['portuguese_llm']}"
            headers = {"Authorization": f"Bearer {getattr(settings, 'HF_API_KEY', '')}"}

            prompt = f"""
            Contexto STAE Moçambique: {context}
            Pergunta: {user_message}
            Resposta como assistente do STAE:
            """

            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_length": 300,
                    "temperature": 0.7,
                    "do_sample": True
                }
            }

            response = requests.post(API_URL, headers=headers, json=payload, timeout=30)

            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get('generated_text', 'Desculpe, não consegui processar a resposta.')
                return "Desculpe, não consegui gerar uma resposta."
            else:
                return self._get_rule_based_response(user_message)

        except Exception as e:
            return self._get_rule_based_response(user_message)

    def _get_rule_based_response(self, user_message):
        """Resposta baseada em regras quando a IA falha"""
        return "Desculpe, estou com dificuldades técnicas. Pode contactar o STAE directamente: +258 21 123 456"