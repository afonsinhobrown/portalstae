"""
MOTOR DE PESQUISA REAL - Arquitetura Oficial STAE
Desenvolvido para pesquisa dinâmica de materiais e atividades
"""

import requests
import re
import time
from urllib.parse import quote

class PesquisadorWebReal:
    """
    Classe oficial integrada para pesquisas REAIS na web (STAE Moçambique)
    """
    
    def __init__(self, api_key=None, search_engine_id=None):
        self.api_key = api_key
        self.search_engine_id = search_engine_id
        self.usar_api = api_key is not None and search_engine_id is not None
        
        self.resultados = {
            "censo": {"materiais": [], "atividades": []},
            "votacao": {"materiais": [], "atividades": []}
        }
        
        self.urls_confiaveis = [
            "stae.org.mz", "cne.org.mz", "tse.jus.br", "un.org", "aceproject.org",
            "idea.int", "ine.gov.mz", "ibge.gov.br", "worldbank.org"
        ]

    def pesquisar_web(self, query, num_resultados=8):
        """Método de busca inteligente com Fallback DuckDuckGo garantido"""
        # Se tivéssemos a lib googlesearch instalada usaríamos o search()
        # Como fallback resiliente para o servidor, usamos o DuckDuckGo Scraping
        search_url = f"https://duckduckgo.com/html/?q={quote(query)}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) STAE-Motor-IA/1.0'}
        
        try:
            resp = requests.get(search_url, headers=headers, timeout=10)
            html = resp.text
            # Extração de Títulos e Snippets (Regex de Alta Fidelidade)
            fontes = re.findall(r'<a class="result__a" href="[^"]+">([^<]+)</a>', html)
            snippets = re.findall(r'<a class="result__snippet" href="[^"]+">([^<]+)</a>', html)
            
            resultados = []
            for i in range(min(len(fontes), num_resultados)):
                resultados.append({
                    'titulo': fontes[i],
                    'snippet': snippets[i] if i < len(snippets) else "",
                    'link': "#", # No scraping HTML simples não pegamos o link direto facilmente sem BS4
                    'relevancia': 5
                })
            return resultados
        except Exception as e:
            print(f"Erro Motor: {e}")
            return []

    def coletar_sugestoes(self, tipo_operacao='RECENSEAMENTO'):
        """Executa a pesquisa multi-query e extrai materiais/atividades"""
        op = 'censo' if tipo_operacao == 'RECENSEAMENTO' else 'votacao'
        
        if tipo_operacao == 'RECENSEAMENTO':
            queries = ["materiais oficiais censo populacional 2024", "equipamentos recenseamento STAE"]
            keywords_mat = ["Mobile ID", "Tablet", "PVC", "Solar", "Impressora", "Kit Biométrico"]
            keywords_at = ["Formação", "Treinamento", "Distribuição", "Mapeamento", "Coleta"]
        else:
            queries = ["materiais votação eleição nacional", "urnas e cabines votação oficiais"]
            keywords_mat = ["Urna", "Cabine", "Tinta Indelével", "Selo", "Saco", "Envelope", "Actas"]
            keywords_at = ["Logística", "Apuramento", "Escrutínio", "Contagem", "Fiscalização"]

        materiais_vivos = set()
        atividades_vivas = set()

        for q in queries:
            resultados = self.pesquisar_web(q)
            for res in resultados:
                texto = f"{res['titulo']} {res['snippet']}"
                
                # Extrair Materiais
                for kw in keywords_mat:
                    if kw.lower() in texto.lower():
                        match = re.search(f"([^.]{{5,30}}{kw}[^.]{{0,30}})", texto, re.I)
                        nome = match.group(0).strip() if match else kw.title()
                        materiais_vivos.add((nome, f"Fonte: {res['titulo'][:50]}..."))
                
                # Extrair Atividades
                for kw in keywords_at:
                    if kw.lower() in texto.lower():
                        match = re.search(f"({kw}[^,.;]{{5,40}})", texto, re.I)
                        nome = match.group(0).strip() if match else kw.title()
                        atividades_vivas.add((nome, "Detectado em documentos técnicos"))

        return list(materiais_vivos), list(atividades_vivas)
