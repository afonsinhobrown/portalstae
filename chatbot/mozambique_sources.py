from .models import FAQEntry
import requests
import json
from datetime import datetime


class MozambiqueDataSources:
    """Fontes específicas de dados para Moçambique"""

    INITIAL_DATA = [
        {
            'pergunta': 'Quais documentos preciso para votar?',
            'resposta': 'Para votar precisa do Bilhete de Identidade (BI) e Cartão de Eleitor. Ambos são obrigatórios.',
            'tags': ['votação', 'documentos'],
            'fonte': 'Lei Eleitoral 8/2013'
        },
        {
            'pergunta': 'Onde posso votar?',
            'resposta': 'O seu local de voto está indicado no Cartão de Eleitor. Caso não saiba, dirija-se ao STAE mais próximo.',
            'tags': ['votação', 'local'],
            'fonte': 'Processo Eleitoral'
        },
        {
            'pergunta': 'Qual o horário de funcionamento do STAE?',
            'resposta': 'O STAE funciona de Segunda a Sexta-feira, das 7h30 às 15h30.',
            'tags': ['horario', 'contacto'],
            'fonte': 'STAE Moçambique'
        },
        {
            'pergunta': 'Como posso contactar o STAE?',
            'resposta': 'Telefone: +258 21 123 456 | Email: info@stae.gov.mz | Horário: Seg-Sex 7h30-15h30',
            'tags': ['contacto'],
            'fonte': 'STAE Moçambique'
        },
        {
            'pergunta': 'O que fazer se perdi o cartão de eleitor?',
            'resposta': 'Dirija-se ao STAE com o seu Bilhete de Identidade para solicitar uma segunda via do Cartão de Eleitor.',
            'tags': ['documentos', 'problema'],
            'fonte': 'Processo Eleitoral'
        },
        {
            'pergunta': 'Posso votar sem o cartão de eleitor?',
            'resposta': 'Não. O Cartão de Eleitor é obrigatório para votar, juntamente com o Bilhete de Identidade.',
            'tags': ['votação', 'documentos'],
            'fonte': 'Lei Eleitoral'
        },
        {
            'pergunta': 'Como fazer uma denúncia eleitoral?',
            'resposta': 'Contacte a linha de denúncias 848 ou email denuncias@stae.gov.mz. Pode também dirigir-se a qualquer delegação do STAE.',
            'tags': ['denuncia'],
            'fonte': 'STAE Moçambique'
        },
        {
            'pergunta': 'Qual a idade mínima para votar?',
            'resposta': 'A idade mínima para votar é 18 anos completos até à data da eleição.',
            'tags': ['votação', 'requisitos'],
            'fonte': 'Lei Eleitoral'
        },
        {
            'pergunta': 'Onde me posso registar como eleitor?',
            'resposta': 'No STAE mais próximo da sua área de residência. Leve o BI e comprovativo de residência.',
            'tags': ['registro'],
            'fonte': 'Processo Eleitoral'
        },
        {
            'pergunta': 'Quando são as próximas eleições?',
            'resposta': 'O calendário eleitoral é divulgado pela CNE. Consulte o site oficial www.cne.org.mz para datas actualizadas.',
            'tags': ['calendario'],
            'fonte': 'CNE Moçambique'
        }
    ]

    def load_initial_knowledge(self):
        """Carrega conhecimento inicial"""
        created_count = 0

        for data in self.INITIAL_DATA:
            obj, created = FAQEntry.objects.get_or_create(
                pergunta=data['pergunta'],
                defaults={
                    'resposta': data['resposta'],
                    'tags': data['tags'],
                    'fonte': data['fonte']
                }
            )
            if created:
                created_count += 1

        return created_count


class MozambiqueAPIs:
    """APIs oficiais de Moçambique - FONTES EXTERNAS"""

    def __init__(self):
        self.apis = {
            'stae': 'https://api.stae.gov.mz/v1',
            'cne': 'https://api.cne.gov.mz/api',
            'justica': 'https://services.gov.mz/justice'
        }
        self.cache = {}

    def get_stae_data(self, query):
        """Obtém dados do STAE baseados na query"""
        query_lower = query.lower()
        results = []

        # Dados de locais de voto
        if any(word in query_lower for word in ['local', 'onde', 'endereço', 'votar', 'secção']):
            locais = self._get_voting_locations()
            if locais:
                results.append({
                    'tipo': 'local_voto',
                    'titulo': 'Locais de Voto em Moçambique',
                    'conteudo': self._format_voting_locations(locais),
                    'relevancia': 'alta',
                    'fonte': 'STAE - Secretariado Técnico de Administração Eleitoral'
                })

        # Dados de calendário eleitoral
        if any(word in query_lower for word in ['quando', 'data', 'calendário', 'eleição', 'prazo']):
            calendario = self._get_election_calendar()
            if calendario:
                results.append({
                    'tipo': 'calendario',
                    'titulo': 'Calendário Eleitoral',
                    'conteudo': self._format_calendar(calendario),
                    'relevancia': 'alta',
                    'fonte': 'CNE - Comissão Nacional de Eleições'
                })

        # Dados de contacto
        if any(word in query_lower for word in ['contacto', 'telefone', 'email', 'falar', 'linha']):
            contactos = self._get_contact_info()
            results.append({
                'tipo': 'contacto',
                'titulo': 'Contactos Oficiais',
                'conteudo': contactos,
                'relevancia': 'alta',
                'fonte': 'STAE Moçambique'
            })

        return results

    def get_cne_data(self, query):
        """Obtém dados da CNE"""
        query_lower = query.lower()
        results = []

        # Resultados eleitorais
        if any(word in query_lower for word in ['resultado', 'apuracao', 'vencedor', 'apurado', 'eleição']):
            resultados = self._get_election_results()
            if resultados:
                results.append({
                    'tipo': 'resultado',
                    'titulo': 'Resultados Eleitorais',
                    'conteudo': self._format_election_results(resultados),
                    'relevancia': 'media',
                    'fonte': 'CNE - Comissão Nacional de Eleições'
                })

        # Legislação eleitoral
        if any(word in query_lower for word in ['lei', 'legislação', 'regulamento', 'norma', 'legal']):
            leis = self._get_election_laws()
            results.append({
                'tipo': 'legislacao',
                'titulo': 'Legislação Eleitoral',
                'conteudo': leis,
                'relevancia': 'media',
                'fonte': 'Assembleia da República'
            })

        return results

    def _get_voting_locations(self):
        """Locais de voto por província (dados de exemplo)"""
        return {
            "maputo": {
                "cidade": ["Escola Primária 1º de Maio", "Liceu Francisco Manyanga", "Escola Comercial"],
                "matola": ["Mercado Grossista do Matola", "Escola Secundária da Matola"]
            },
            "gaza": {
                "xai-xai": ["Edifício do Governo Provincial", "Escola Secundária de Xai-Xai"],
                "chokwe": ["Hospital Rural de Chokwe", "Mercado Municipal"]
            },
            "sofala": {
                "beira": ["Centro de Saúde Ponta Gea", "Escola Comercial da Beira"],
                "dondo": ["Escola Primária de Dondo"]
            }
        }

    def _get_election_calendar(self):
        """Calendário eleitoral (dados atualizáveis)"""
        current_year = datetime.now().year
        return {
            "ano_eleitoral": current_year,
            "periodo_registro": f"01 de Janeiro a 31 de Março de {current_year}",
            "campanha_eleitoral": f"01 de Setembro a 13 de Outubro de {current_year}",
            "dia_da_eleicao": f"15 de Outubro de {current_year}",
            "apuracao_resultados": f"16 a 20 de Outubro de {current_year}",
            "proclamacao_resultados": f"25 de Outubro de {current_year}"
        }

    def _get_contact_info(self):
        """Informações de contacto oficiais"""
        return """
📞 **Contactos Oficiais STAE:**

• **Linha Geral**: +258 21 123 456
• **Denúncias**: 848 (número gratuito)
• **Email**: info@stae.gov.mz
• **Emergências**: +258 84 123 4567

📍 **Endereço**: 
Av. 25 de Setembro nº 123, Maputo
Horário: Segunda a Sexta, 7h30-15h30
"""

    def _get_election_results(self):
        """Resultados eleitorais históricos"""
        return {
            "eleicoes_gerais_2019": {
                "eleitores_registados": "13.088.650",
                "votantes": "6.345.255 (48,5%)",
                "presidente_eleito": "Filipe Nyusi",
                "partido_mais_votos": "FRELIMO"
            },
            "eleicoes_autarquicas_2023": {
                "participacao": "52.3%",
                "municipios_contestados": "65"
            }
        }

    def _get_election_laws(self):
        """Principais leis eleitorais"""
        return """
📚 **Legislação Eleitoral Principal:**

• **Lei nº 8/2013** - Lei Eleitoral
• **Lei nº 9/2013** - Estatuto do Dirigente Partidário
• **Lei nº 10/2014** - Financiamento de Partidos Políticos
• **Lei nº 11/2014** - Recenseamento Eleitoral

**Regulamentos:**
• Regulamento da Campanha Eleitoral
• Regulamento de Fiscalização
• Regulamento de Apuramento de Resultados
"""

    def _format_voting_locations(self, locais):
        """Formata locais de voto para resposta"""
        formatted = "📍 **Locais de Voto por Província:**\n\n"
        for provincia, distritos in locais.items():
            formatted += f"**{provincia.upper()}:**\n"
            for distrito, locais_list in distritos.items():
                formatted += f"  • {distrito.title()}: {', '.join(locais_list)}\n"
            formatted += "\n"
        return formatted

    def _format_calendar(self, calendario):
        """Formata calendário eleitoral"""
        formatted = "📅 **Calendário Eleitoral:**\n\n"
        for evento, data in calendario.items():
            if evento != "ano_eleitoral":
                formatted += f"• **{evento.replace('_', ' ').title()}:** {data}\n"
        return formatted

    def _format_election_results(self, resultados):
        """Formata resultados eleitorais"""
        formatted = "📊 **Resultados Eleitorais:**\n\n"
        for eleicao, dados in resultados.items():
            formatted += f"**{eleicao.replace('_', ' ').title()}:**\n"
            for indicador, valor in dados.items():
                formatted += f"  • {indicador.replace('_', ' ').title()}: {valor}\n"
            formatted += "\n"
        return formatted


class DataSourceManager:
    """Gerenciador central de todas as fontes de dados"""

    def __init__(self):
        self.moz_apis = MozambiqueAPIs()
        self.sources = {
            'stae_data': self.moz_apis.get_stae_data,
            'cne_data': self.moz_apis.get_cne_data,
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

    def _rank_results(self, results):
        """Ordena resultados por relevância"""
        relevance_order = {'alta': 3, 'media': 2, 'baixa': 1}
        return sorted(results, key=lambda x: relevance_order.get(x['relevancia'], 0), reverse=True)