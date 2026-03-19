from django.core.management.base import BaseCommand
from dfec.models import MatrizRecomendacao

class Command(BaseCommand):
    help = 'Popula a Matriz de Recomendações com melhores práticas internacionais'

    def handle(self, *args, **options):
        self.stdout.write("Populando Matriz de Recomendações...")
        MatrizRecomendacao.objects.all().delete()
        
        regras = [
            # --- ABSTENÇÃO ---
            {
                'metrica': 'taxa_abstencao', 'min': 35, 'max': 60, 'nivel': 'provincial',
                'titulo': 'Oportunidade de Melhoria no Engajamento',
                'acao': 'Analisar alocação de recursos para Educação Cívica. Região apresenta potencial para maior participação.',
                'prioridade': 'media'
            },
            {
                'metrica': 'taxa_abstencao', 'min': 35, 'max': 60, 'nivel': 'distrital',
                'titulo': 'Verificação de Acessibilidade',
                'acao': 'Sugerida verificação da distribuição geográfica das mesas em {unidade} para facilitar o acesso.',
                'prioridade': 'media'
            },
            {
                'metrica': 'taxa_abstencao', 'min': 35, 'max': 60, 'nivel': 'posto',
                'titulo': 'Desafios Logísticos Potenciais',
                'acao': 'Monitorar abertura das mesas e cadernos eleitorais em {unidade}.',
                'prioridade': 'alta'
            },
            {
                'metrica': 'taxa_abstencao', 'min': 60, 'max': 100, 'nivel': 'todos',
                'titulo': 'Atenção Prioritária à Participação',
                'acao': 'Taxa de participação atípica em {unidade}. Recomenda-se auditoria de dados para garantir consistência.',
                'prioridade': 'critica'
            },

            # --- NULOS ---
            {
                'metrica': 'taxa_nulos', 'min': 5, 'max': 10, 'nivel': 'provincial',
                'titulo': 'Reforço na Comunicação do Voto',
                'acao': 'Reforçar campanhas informativas sobre o preenchimento do boletim nesta região.',
                'prioridade': 'media'
            },
            {
                'metrica': 'taxa_nulos', 'min': 5, 'max': 10, 'nivel': 'distrital',
                'titulo': 'Capacitação de MMVs',
                'acao': 'Recomendado reforço na capacitação dos Membros das Mesas em {unidade} para apoio ao eleitor.',
                'prioridade': 'alta'
            },
            {
                'metrica': 'taxa_nulos', 'min': 10, 'max': 100, 'nivel': 'todos',
                'titulo': 'Padrão Atípico de Votos',
                'acao': 'Índice de nulos acima da média em {unidade}. Sugere-se análise detalhada das atas.',
                'prioridade': 'critica'
            },

            # --- BRANCOS ---
            {
                'metrica': 'taxa_brancos', 'min': 4, 'max': 100, 'nivel': 'todos',
                'titulo': 'Indicador de Preferência Eleitoral',
                'acao': 'Percentual de brancos em {unidade} sugere espaço para maior diálogo político com o eleitorado local.',
                'prioridade': 'media'
            }
        ]
        
        for r in regras:
            MatrizRecomendacao.objects.create(
                metrica=r['metrica'],
                min_valor=r['min'],
                max_valor=r['max'],
                nivel_analise=r['nivel'],
                titulo=r['titulo'],
                acao_sugerida=r['acao'],
                prioridade=r['prioridade']
            )
            
        self.stdout.write(self.style.SUCCESS(f"Criadas {len(regras)} regras de recomendação."))
