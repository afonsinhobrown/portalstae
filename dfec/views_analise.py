from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib import messages
from django.db.models import Sum, F, ExpressionWrapper, FloatField
from dfec.models import ResultadoEleitoral, Provincia, Distrito, MatrizRecomendacao
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

import io
import base64

class DashboardAnaliseEleitoral(TemplateView):
    template_name = 'dfec/analise/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # ... [Previous code remains same until recommendation block] ...
        
        # Filtros (Get params)
        ano_selecionado = self.request.GET.get('ano', 2024)
        provincia_id = self.request.GET.get('provincia')
        nivel_selecionado = self.request.GET.get('nivel', 'distrital')
        
        # Base Queryset (Filtrada)
        qs = ResultadoEleitoral.objects.filter(ano=ano_selecionado)
        if provincia_id:
            qs = qs.filter(provincia_ref_id=provincia_id)
        
        # Filtros adicionais (cascade)
        distrito_id = self.request.GET.get('distrito')
        posto_nome = self.request.GET.get('posto')
        localidade_nome = self.request.GET.get('localidade')

        if distrito_id:
            qs = qs.filter(distrito_ref_id=distrito_id)
        if posto_nome:
            qs = qs.filter(posto_administrativo=posto_nome)
        if localidade_nome:
            qs = qs.filter(localidade=localidade_nome)

        # 1. KPIs Globais (do filtro atual)
        agregado = qs.aggregate(
            total_inscritos=Sum('eleitores_inscritos'),
            total_votantes=Sum('total_votantes'),
            total_nulos=Sum('votos_nulos'),
            total_brancos=Sum('votos_branco'),
            total_abstencoes=Sum('abstencoes')
        )
        
        inscritos = agregado['total_inscritos'] or 0
        votantes = agregado['total_votantes'] or 0
        nulos = agregado['total_nulos'] or 0
        brancos = agregado['total_brancos'] or 0
        abstencoes = agregado['total_abstencoes'] or 0
        
        taxa_abstencao = (abstencoes / inscritos * 100) if inscritos > 0 else 0
        taxa_nulos = (nulos / votantes * 100) if votantes > 0 else 0
        taxa_brancos = (brancos / votantes * 100) if votantes > 0 else 0
        
        context['kpi'] = {
            'inscritos': inscritos,
            'votantes': votantes,
            'participacao_perc': round(100 - taxa_abstencao, 1),
            'abstencao_perc': round(taxa_abstencao, 1),
            'nulos_perc': round(taxa_nulos, 1),
            'brancos_perc': round(taxa_brancos, 1)
        }

        # 2. Ranking Dinâmico (Agrupamento)
        group_fields = ['provincia_ref__nome'] # Sempre agrupar por província base
        
        if nivel_selecionado == 'provincial':
            pass
        elif nivel_selecionado == 'distrital':
            group_fields.append('distrito_ref__nome')
        elif nivel_selecionado == 'posto':
            group_fields.extend(['distrito_ref__nome', 'posto_administrativo'])
        elif nivel_selecionado == 'localidade':
            group_fields.extend(['distrito_ref__nome', 'posto_administrativo', 'localidade'])
        elif nivel_selecionado == 'assembleia':
            group_fields.extend(['distrito_ref__nome', 'posto_administrativo', 'localidade', 'codigo_assembleia', 'local_votacao'])

        # Agregação Dinâmica
        dados_agrupados = qs.values(*group_fields).annotate(
            d_inscritos=Sum('eleitores_inscritos'),
            d_votantes=Sum('total_votantes'),
            d_nulos=Sum('votos_nulos'),
            d_brancos=Sum('votos_branco'),
            d_abstencoes=Sum('abstencoes')
        )

        if nivel_selecionado == 'distrital':
             dados_agrupados = dados_agrupados.exclude(distrito_ref__isnull=True)

        ranking = []
        for d in dados_agrupados:
            di = d['d_inscritos'] or 0
            dv = d['d_votantes'] or 0
            dn = d['d_nulos'] or 0
            db = d['d_brancos'] or 0
            da = d['d_abstencoes'] or 0
            
            t_abs = (da / di * 100) if di > 0 else 0
            t_nul = (dn / dv * 100) if dv > 0 else 0
            t_bra = (db / dv * 100) if dv > 0 else 0
            
            # Score de Risco
            risco = 'Baixo'
            if t_abs > 40 or t_nul > 10: risco = 'Médio'
            if t_abs > 60 or t_nul > 20: risco = 'Crítico'

            # Determinar label da unidade
            prov = d.get('provincia_ref__nome') or 'Desconhecido'
            dist = d.get('distrito_ref__nome')
            
            if nivel_selecionado == 'provincial':
                unidade = prov
                subtitulo = "Província"
            elif nivel_selecionado == 'distrital':
                unidade = dist or 'N/A'
                subtitulo = prov
            elif nivel_selecionado == 'posto':
                unidade = d.get('posto_administrativo') or 'N/A'
                subtitulo = f"{dist}, {prov}"
            elif nivel_selecionado == 'localidade':
                unidade = d.get('localidade') or 'N/A'
                subtitulo = f"{d.get('posto_administrativo')}, {dist}"
            elif nivel_selecionado == 'assembleia':
                unidade = f"{d.get('codigo_assembleia')} - {d.get('local_votacao')}"
                subtitulo = f"{d.get('localidade')}"

            ranking.append({
                'provincia': prov,
                'distrito': dist,
                'unidade': unidade,
                'subtitulo': subtitulo, 
                'taxa_abstencao': round(t_abs, 1),
                'taxa_nulos': round(t_nul, 1),
                'taxa_brancos': round(t_bra, 1),
                'risco': risco
            })
            
        # Ordenações Completas (Para análise e paginação)
        full_ranking_abstencao = sorted(ranking, key=lambda x: x['taxa_abstencao'], reverse=True)
        full_ranking_nulos = sorted(ranking, key=lambda x: x['taxa_nulos'], reverse=True)
        full_ranking_brancos = sorted(ranking, key=lambda x: x['taxa_brancos'], reverse=True)

        # Paginação para Tabela (Gestão de Espaço)
        from django.core.paginator import Paginator
        paginator = Paginator(full_ranking_abstencao, 20) # 20 itens por página
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['ranking_tabela'] = page_obj # Tabela exibe a página atual
        context['page_obj'] = page_obj
        
        # Top 15 para os Gráficos
        context['ranking_abstencao'] = full_ranking_abstencao[:15] 
        context['ranking_nulos'] = full_ranking_nulos[:15]
        context['ranking_brancos'] = full_ranking_brancos[:15]
        
        # --- DADOS PARA O MAPA ESQUEMÁTICO (SEMPRE NÍVEL PROVINCIAL) ---
        # Agrega dados por província independente do filtro atual
        map_qs = ResultadoEleitoral.objects.filter(ano=ano_selecionado)
        map_agg = map_qs.values('provincia_ref__nome').annotate(
            m_inscritos=Sum('eleitores_inscritos'),
            m_abstencoes=Sum('abstencoes')
        )
        
        map_data = {}
        for m in map_agg:
            p_nome = m['provincia_ref__nome']
            if not p_nome: continue
            
            mi = m['m_inscritos'] or 0
            ma = m['m_abstencoes'] or 0
            rate = (ma / mi * 100) if mi > 0 else 0
            
            # Definir Cor do Mapa
            color_class = 'bg-success' # Verde (<35%)
            if rate >= 45: color_class = 'bg-danger' # Vermelho
            elif rate >= 35: color_class = 'bg-warning text-dark' # Amarelo
            
            # Converter nome para chave válida no template (sem espaços)
            safe_key = p_nome.replace(' ', '_').replace('í', 'i').replace('á', 'a').replace('é', 'e').replace('ã', 'a')
            
            map_data[safe_key] = {
                'rate': round(rate, 1),
                'color': color_class
            }
        context['map_data'] = map_data
        # ---------------------------------------------------------------
        
        # Lista Completa (Top 100) para Relatório PDF detalhado
        context['ranking_tabela_full'] = full_ranking_abstencao[:100]

        # Contexto de Filtros
        context['provincias'] = Provincia.objects.all().order_by('nome')
        
        if provincia_id:
             context['distritos'] = Distrito.objects.filter(provincia_id=provincia_id).order_by('nome')
        else:
             context['distritos'] = Distrito.objects.all().order_by('provincia__nome', 'nome')

        if distrito_id:
             context['postos'] = ResultadoEleitoral.objects.filter(
                 ano=ano_selecionado, 
                 distrito_ref_id=distrito_id
             ).values_list('posto_administrativo', flat=True).distinct().order_by('posto_administrativo')
        
        if posto_nome:
             context['localidades'] = ResultadoEleitoral.objects.filter(
                 ano=ano_selecionado,
                 posto_administrativo=posto_nome
             ).values_list('localidade', flat=True).distinct().order_by('localidade')

        context['anos_disponiveis'] = ResultadoEleitoral.objects.values_list('ano', flat=True).distinct().order_by('-ano')
        context['ano_selecionado'] = int(ano_selecionado)
        context['nivel_selecionado'] = nivel_selecionado

        # --- NOVA LÓGICA DE RECOMENDAÇÕES (CONSOLIDADA POR LOCAL) ---
        recomendacoes = []

        # Iterar sobre TODAS as unidades (ranking_tabela_full)
        for item in full_ranking_abstencao:
            unidade = item['unidade']
            
            # Objeto de Plano de Ação Unificado
            plano_acao = {
                'local': unidade,
                'tipo': 'stae',
                'acoes': [],
                'prioridade_geral': 'baixa' # Será elevada se houver algum indicador crítico
            }
            
            # --- 1. ABSTENÇÃO (Foco STAE - Educação Cívica) ---
            abstencao = item['taxa_abstencao']
            acao_abs = {'tema': 'Mobilização', 'valor': abstencao}

            if abstencao >= 45:
                acao_abs['status'] = 'CRÍTICO'
                acao_abs['texto'] = f"Abstenção alarmante ({abstencao}%). Necessária investigação profunda e brigadas de choque."
                plano_acao['prioridade_geral'] = 'alta'
            elif abstencao >= 35:
                acao_abs['status'] = 'ALERTA'
                acao_abs['texto'] = f"Abstenção elevada ({abstencao}%). Reforçar equipas de educação cívica em zonas de baixa afluência."
                if plano_acao['prioridade_geral'] != 'alta': plano_acao['prioridade_geral'] = 'media'
            elif abstencao >= 20:
                acao_abs['status'] = 'ATENÇÃO'
                acao_abs['texto'] = f"Abstenção moderada ({abstencao}%). Manter ações de sensibilização proativas."
                plano_acao['prioridade_geral'] = 'media'
            else:
                acao_abs['status'] = 'POSITIVO'
                acao_abs['texto'] = f"Excelente participação. Replicar estratégia local."
            
            plano_acao['acoes'].append(acao_abs)

            # --- 2. VOTOS NULOS (Foco STAE - Pedagogia) ---
            nulos = item['taxa_nulos']
            acao_nul = {'tema': 'Pedagogia do Voto', 'valor': nulos}

            if nulos >= 6:
                acao_nul['status'] = 'CRÍTICO'
                acao_nul['texto'] = f"Nulos elevados ({nulos}%). Reforçar demonstrações práticas de votação."
                plano_acao['prioridade_geral'] = 'alta'
            elif nulos >= 3:
                acao_nul['status'] = 'ATENÇÃO'
                acao_nul['texto'] = f"Nulos em nível de atenção ({nulos}%). Reforçar explicação visual do boletim."
                if plano_acao['prioridade_geral'] != 'alta': plano_acao['prioridade_geral'] = 'media'
            else:
                acao_nul['status'] = 'NORMAL'
                acao_nul['texto'] = f"Índice de nulos controlado ({nulos}%). Manter instrução padrão."
            
            plano_acao['acoes'].append(acao_nul)
            
            # Definir Título Baseado na Prioridade Geral
            if plano_acao['prioridade_geral'] == 'alta':
                plano_acao['titulo'] = "Intervenção Prioritária"
            elif plano_acao['prioridade_geral'] == 'media':
                plano_acao['titulo'] = "Reforço e Monitoria"
            else:
                plano_acao['titulo'] = "Manutenção e Consolidação"

            recomendacoes.append(plano_acao)

            # --- 3. VOTOS EM BRANCO (Foco Partidos - Mantido Separado pois é outra seção) ---
            brancos = item['taxa_brancos']
            rec_white = {}
            rec_white['local'] = unidade
            rec_white['tipo'] = 'partidos'
            rec_white['indicador'] = 'Votos em Branco'
            rec_white['valor'] = brancos
            rec_white['titulo'] = "Análise de Espaço Político"
            rec_white['prioridade'] = 'partidaria'

            if brancos >= 5:
                rec_white['descricao'] = f"Percentual de brancos ({brancos}%) indica oportunidade para maior esclarecimento de propostas."
            else:
                rec_white['descricao'] = f"Baixo índice de brancos ({brancos}%). Eleitorado com preferências definidas."
            recomendacoes.append(rec_white)
        
        # -------------------------------------------------------------------

            # Bloco duplicado removido

        
        # -------------------------------------------------------------------
        # --- LÓGICA DE COMPARAÇÃO DE ELEIÇÕES ---
        show_comparison = self.request.GET.get('compare') == 'true'
        comparison_data = []
        ano_anterior = None
        
        if show_comparison:
            # Encontrar ano anterior disponível
            anos = list(ResultadoEleitoral.objects.values_list('ano', flat=True).distinct().order_by('-ano'))
            try:
                curr_idx = anos.index(int(ano_selecionado))
                if curr_idx + 1 < len(anos):
                    ano_anterior = anos[curr_idx + 1]
            except ValueError:
                pass
            
            if ano_anterior:
                # Buscar dados do ano anterior
                qs_prev = ResultadoEleitoral.objects.filter(ano=ano_anterior)
                if provincia_id: qs_prev = qs_prev.filter(provincia_ref_id=provincia_id)
                if distrito_id: qs_prev = qs_prev.filter(distrito_ref_id=distrito_id)

                # Agrupar dados anteriores
                dados_prev = qs_prev.values(*group_fields).annotate(
                    d_abstencoes=Sum('abstencoes'), d_inscritos=Sum('eleitores_inscritos')
                )
                
                # Criar dicionário para acesso rápido {unidade: taxa_abs}
                dict_prev = {}
                for d in dados_prev:
                    if nivel_selecionado == 'provincial': uni = d.get('provincia_ref__nome')
                    elif nivel_selecionado == 'distrital': uni = d.get('distrito_ref__nome')
                    else: uni = d.get('posto_administrativo') # Simplificação
                    
                    di = d['d_inscritos'] or 0
                    da = d['d_abstencoes'] or 0
                    taxa = (da/di*100) if di > 0 else 0
                    dict_prev[uni] = taxa
                
                # Montar lista de comparação
                for item in ranking: # Usando ranking atual
                    u = item['unidade']
                    t_atual = item['taxa_abstencao']
                    t_ant = dict_prev.get(u, 0)
                    delta = t_atual - t_ant
                    
                    comparison_data.append({
                        'unidade': u,
                        'taxa_atual': t_atual,
                        'taxa_anterior': t_ant,
                        'delta': round(delta, 1),
                        'tendencia': 'Piora' if delta > 0 else 'Melhoria'
                    })

        context['show_comparison'] = show_comparison
        context['ano_anterior'] = ano_anterior
        context['comparison_data'] = comparison_data

        # -------------------------------------------------------------------
        # Separar Recomendações por Público Alvo
        rec_stae = [r for r in recomendacoes if r['tipo'] != 'partidos']
        rec_partidos = [r for r in recomendacoes if r['tipo'] == 'partidos']

        # Paginação das Recomendações (Restaurada para evitar exclusões)
        paginator_rec = Paginator(rec_stae, 10) 
        page_number_rec = self.request.GET.get('page_rec')
        page_obj_rec = paginator_rec.get_page(page_number_rec)

        context['recomendacoes'] = page_obj_rec 
        context['rec_partidos'] = rec_partidos    
        context['page_obj_rec'] = page_obj_rec
        
        # Contexto completo para PDF (Listas separadas)
        context['pdf_rec_stae'] = rec_stae
        context['pdf_rec_partidos'] = rec_partidos
        
        # Paginação da Tabela Principal (Ranking)
        # O usuário pediu "paginação nas tabelas", e o template já espera 'page_obj' e 'ranking_tabela'
        paginator_ranking = Paginator(full_ranking_abstencao, 15)
        page_number_ranking = self.request.GET.get('page')
        page_obj_ranking = paginator_ranking.get_page(page_number_ranking)
        
        context['ranking_tabela'] = page_obj_ranking
        context['page_obj'] = page_obj_ranking

        # Lista Completa (SEM LIMITES) para Relatório PDF detalhado
        context['ranking_tabela_full'] = full_ranking_abstencao

        # Contexto de Filtros
        context['provincias'] = Provincia.objects.all().order_by('nome')
        
        if provincia_id:
             context['distritos'] = Distrito.objects.filter(provincia_id=provincia_id).order_by('nome')
        else:
             context['distritos'] = Distrito.objects.all().order_by('provincia__nome', 'nome')

        if distrito_id:
             context['postos'] = ResultadoEleitoral.objects.filter(
                 ano=ano_selecionado, 
                 distrito_ref_id=distrito_id
             ).values_list('posto_administrativo', flat=True).distinct().order_by('posto_administrativo')
        
        if posto_nome:
             context['localidades'] = ResultadoEleitoral.objects.filter(
                 ano=ano_selecionado,
                 posto_administrativo=posto_nome
             ).values_list('localidade', flat=True).distinct().order_by('localidade')

        context['anos_disponiveis'] = ResultadoEleitoral.objects.values_list('ano', flat=True).distinct().order_by('-ano')
        context['ano_selecionado'] = int(ano_selecionado)
        context['nivel_selecionado'] = nivel_selecionado
        return context

class UploadResultadosView(TemplateView):
    template_name = 'dfec/analise/upload.html'
    
    def post(self, request, *args, **kwargs):
        from dfec.services import ImportacaoService
        from django.contrib import messages
        
        files = request.FILES.getlist('arquivos_csv')
        
        if not files:
            messages.error(request, "Nenhum arquivo selecionado.")
            return self.render_to_response(self.get_context_data())

        sucesso = 0
        erros = 0
        details = []

        ano = int(request.POST.get('ano', 2018))
        tipo = request.POST.get('tipo', 'AUTO')

        for f in files:
            ok, msg = ImportacaoService.processar_arquivo_imemory(f, f.name, ano=ano, tipo_manual=tipo)
            if ok:
                sucesso += 1
            else:
                erros += 1
                details.append(f"{f.name}: {msg}")
        
        if sucesso > 0:
            messages.success(request, f"{sucesso} arquivos importados com sucesso!")
        
        if erros > 0:
            messages.warning(request, f"{erros} arquivos falharam. Detalhes: {'; '.join(details[:3])}...")
            
        return redirect('dfec:dashboard_analise_eleitoral')

class RelatorioPDFView(DashboardAnaliseEleitoral):
    template_name = 'dfec/analise/report_pdf.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Traduzir IDs para Nomes Legíveis (Filtros)
        prov_id = self.request.GET.get('provincia')
        dist_id = self.request.GET.get('distrito')
        
        if prov_id:
            try:
                p = Provincia.objects.get(id=prov_id)
                context['filtro_provincia_nome'] = p.nome
            except:
                context['filtro_provincia_nome'] = "Desconhecida"
                
        if dist_id:
            try:
                d = Distrito.objects.get(id=dist_id)
                context['filtro_distrito_nome'] = d.nome
            except:
                context['filtro_distrito_nome'] = "Desconhecido"
        
        # Mapeamento para Rótulo do Local (Singular)
        nivel = self.request.GET.get('nivel', 'provincial')
        labels_map = {
            'provincial': 'Província',
            'distrital': 'Distrito',
            'posto': 'Posto Administrativo',
            'localidade': 'Localidade',
            'assembleia': 'Assembleia de Voto'
        }
        context['tipo_local_label'] = labels_map.get(nivel, 'Unidade Territorial')

        # Gerar Gráficos (Servidor)
        try:
            if not MATPLOTLIB_AVAILABLE:
                context['graphics_disabled'] = True
                return context
                
            # 1. Abstenção (Pie)
            ranking_abs = context.get('ranking_abstencao', [])[:5]
            if ranking_abs:
                labels = [str(x['unidade'])[:15] for x in ranking_abs]
                values = [x['taxa_abstencao'] for x in ranking_abs]
                
                fig, ax = plt.subplots(figsize=(5, 3))
                ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, 
                       colors=['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b'])
                ax.axis('equal')
                
                buf = io.BytesIO()
                plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
                buf.seek(0)
                context['chart_abstencao'] = base64.b64encode(buf.read()).decode('utf-8')
                plt.close(fig)

            # 2. Nulos (Bar)
            ranking_nul = context.get('ranking_nulos', [])[:7]
            if ranking_nul:
                labels = [str(x['unidade'])[:12] for x in ranking_nul]
                values = [x['taxa_nulos'] for x in ranking_nul]
                
                fig, ax = plt.subplots(figsize=(6, 3))
                bars = ax.bar(labels, values, color='#f6c23e')
                ax.set_title('Maiores Índices de Nulos (%)', fontsize=9)
                plt.xticks(rotation=45, ha='right', fontsize=8)
                plt.subplots_adjust(bottom=0.2)
                plt.grid(axis='y', linestyle='--', alpha=0.3)
                
                buf = io.BytesIO()
                plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
                buf.seek(0)
                context['chart_nulos'] = base64.b64encode(buf.read()).decode('utf-8')
                plt.close(fig)
        except Exception as e:
            print(f"Erro ao gerar gráficos PDF: {e}")
            
        return context

    def get(self, request, *args, **kwargs):
        from xhtml2pdf import pisa
        from django.http import HttpResponse

        context = self.get_context_data(**kwargs)
        html = render(request, self.template_name, context).content.decode('utf-8')
        
        response = HttpResponse(content_type='application/pdf')
        filename = f"Relatorio_Eleitoral_{context.get('ano_selecionado', 'STAE')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        pisa_status = pisa.CreatePDF(html, dest=response)
        
        if pisa_status.err:
            return HttpResponse('Erro ao gerar PDF', status=500)
        return response

class CompararEleicoesView(TemplateView):
    template_name = 'dfec/analise/comparar.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Anos Disponíveis
        anos = list(ResultadoEleitoral.objects.values_list('ano', flat=True).distinct().order_by('-ano'))
        context['anos_disponiveis'] = anos
        
        # Seleção
        ano1 = int(self.request.GET.get('ano1', anos[1] if len(anos) > 1 else 2018))
        ano2 = int(self.request.GET.get('ano2', anos[0] if anos else 2024))
        
        context['ano1'] = ano1
        context['ano2'] = ano2
        
        # Buscar Dados (Abstenção E Nulos)
        def get_data(ano):
            return ResultadoEleitoral.objects.filter(ano=ano).values('provincia_ref__nome').annotate(
                t_abs=ExpressionWrapper(100.0 * Sum('abstencoes') / Sum('eleitores_inscritos'), output_field=FloatField()),
                t_nul=ExpressionWrapper(100.0 * Sum('votos_nulos') / (Sum('eleitores_inscritos') - Sum('abstencoes')), output_field=FloatField()) # Nulos sobre Votantes
            )
            
        qs1 = get_data(ano1)
        qs2 = get_data(ano2)
        
        # Indexar
        dict1 = {x['provincia_ref__nome']: x for x in qs1 if x['provincia_ref__nome']}
        dict2 = {x['provincia_ref__nome']: x for x in qs2 if x['provincia_ref__nome']}
        
        comparativo = []
        conclusoes = []
        
        todas_provincias = set(list(dict1.keys()) + list(dict2.keys()))
        
        for prov in sorted(todas_provincias):
            d1 = dict1.get(prov, {'t_abs': 0, 't_nul': 0})
            d2 = dict2.get(prov, {'t_abs': 0, 't_nul': 0})
            
            delta_abs = d2['t_abs'] - d1['t_abs']
            delta_nul = d2['t_nul'] - d1['t_nul']
            
            # Diagnóstico Explícito - Abstenção
            msg_abs = ""
            tendencia_abs = "estavel"
            
            if delta_abs > 5:
                msg_abs = f"Abstenção subiu gravemente (+{round(delta_abs,1)}%)."
                tendencia_abs = "piora"
            elif delta_abs > 0:
                msg_abs = f"Abstenção aumentou ligeiramente (+{round(delta_abs,1)}%)."
                tendencia_abs = "piora"
            elif delta_abs < -5:
                msg_abs = f"Abstenção caiu drasticamente ({round(delta_abs,1)}%). Sucesso."
                tendencia_abs = "melhoria"
            elif delta_abs < 0:
                msg_abs = f"Abstenção reduziu ({round(delta_abs,1)}%)."
                tendencia_abs = "melhoria"
            else:
                msg_abs = "Abstenção mantida."

            # Diagnóstico Explícito - Nulos
            msg_nul = ""
            if delta_nul > 2:
                msg_nul = f"Nulos dispararam (+{round(delta_nul,1)}%). Falha na educação cívica."
            elif delta_nul < -1:
                msg_nul = f"Menos votos nulos ({round(delta_nul,1)}%). Eleitor mais consciente."
            
            # Combinação para o Card de Conclusões
            texto_final = f"{msg_abs}"
            if msg_nul: texto_final += f" {msg_nul}"

            comparativo.append({
                'unidade': prov,
                'abs1': round(d1['t_abs'], 1),
                'abs2': round(d2['t_abs'], 1),
                'delta_abs': round(delta_abs, 1),
                'nul1': round(d1['t_nul'], 1),
                'nul2': round(d2['t_nul'], 1),
                'delta_nul': round(delta_nul, 1),
                'diagnostico_texto': texto_final,
                'tendencia': tendencia_abs
            })
            
            # Adicionar aos destaques se houver movimento significativo
            if abs(delta_abs) >= 3 or abs(delta_nul) >= 1.5:
                conclusoes.append({
                    'unidade': prov,
                    'texto': texto_final,
                    'tendencia': tendencia_abs
                })
                
        context['dados_comparativos'] = comparativo
        context['conclusoes'] = conclusoes[:6]
        
        return context

class MapaInterativoView(TemplateView):
    template_name = 'dfec/analise/mapa.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ano_selecionado = self.request.GET.get('ano', 2024)
        
        # Dados Provinciais para o Mapa
        qs = ResultadoEleitoral.objects.filter(ano=ano_selecionado)
        agregado = qs.values('provincia_ref__nome').annotate(
            m_inscritos=Sum('eleitores_inscritos'),
            m_abstencoes=Sum('abstencoes'),
            m_nulos=Sum('votos_nulos')
        )
        
        map_data = {}
        for m in agregado:
            p_nome = m['provincia_ref__nome']
            if not p_nome: continue
            
            mi = m['m_inscritos'] or 0
            ma = m['m_abstencoes'] or 0
            mn = m['m_nulos'] or 0
            
            rate = (ma / mi * 100) if mi > 0 else 0
            rate_nulos = (mn / (mi-ma) * 100) if (mi-ma) > 0 else 0
            
            color_class = '#198754' # Success hex
            if rate >= 45: color_class = '#dc3545' # Danger
            elif rate >= 35: color_class = '#ffc107' # Warning
            else: color_class = '#198754' # Success
            
            # Sanitizar chave
            safe_key = p_nome.replace(' ', '_').replace('í', 'i').replace('á', 'a').replace('é', 'e').replace('ã', 'a')
            map_data[safe_key] = {
                'rate': round(rate, 1), 
                'color': color_class, 
                'nome_real': p_nome,
                'inscritos': mi,
                'abstencoes_abs': ma,
                'nulos_abs': mn,
                'taxa_nulos': round(rate_nulos, 1)
            }
            
        context['map_data'] = map_data
        context['ano_selecionado'] = int(ano_selecionado)
        context['anos_disponiveis'] = ResultadoEleitoral.objects.values_list('ano', flat=True).distinct().order_by('-ano')
        return context

class RecomendacoesView(TemplateView):
    template_name = 'dfec/analise/recomendacoes.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # --- FILTROS (Cópia da Lógica de Dashboard) ---
        ano_selecionado = self.request.GET.get('ano', 2024)
        provincia_id = self.request.GET.get('provincia')
        distrito_id = self.request.GET.get('distrito')
        
        # QuerySet Base
        qs = ResultadoEleitoral.objects.filter(ano=ano_selecionado)
        
        # Aplicar Filtros
        if provincia_id:
            qs = qs.filter(provincia_ref_id=provincia_id)
        if distrito_id:
            qs = qs.filter(distrito_ref_id=distrito_id)

        # Agrupamento para gerar cards
        # Se filtrou distrito, mostra postos. Se não, mostra distritos.
        # Agrupamento para gerar cards
        # Se filtrou distrito, mostra postos. Se não, mostra distritos.
        # Novo Filtro de Nível
        nivel_selecionado = self.request.GET.get('nivel', 'distrital') # Default: Distrital
        
        # Agrupamento Dinâmico Baseado no Nível
        group_fields = []
        exclude_nulls = {}
        
        if nivel_selecionado == 'provincial':
            group_fields = ['provincia_ref__nome']
            field_unidade = 'provincia_ref__nome'
            field_pai = 'ano' # Dummy
        elif nivel_selecionado == 'distrital':
            group_fields = ['provincia_ref__nome', 'distrito_ref__nome']
            field_unidade = 'distrito_ref__nome'
            field_pai = 'provincia_ref__nome'
            exclude_nulls = {'distrito_ref__isnull': True}
        elif nivel_selecionado == 'posto':
            group_fields = ['distrito_ref__nome', 'posto_administrativo']
            field_unidade = 'posto_administrativo'
            field_pai = 'distrito_ref__nome'
            exclude_nulls = {'posto_administrativo__isnull': True}
        
        # Executar Query Agregada
        dados = qs.values(*group_fields).annotate(
            d_inscritos=Sum('eleitores_inscritos'),
            d_abstencoes=Sum('abstencoes'),
            d_nulos=Sum('votos_nulos'),
            d_brancos=Sum('votos_branco')
        )
        
        if exclude_nulls:
            dados = dados.exclude(**exclude_nulls)
        
        recomendacoes = []
        for d in dados:
            di = d['d_inscritos'] or 0
            da = d['d_abstencoes'] or 0
            dn = d['d_nulos'] or 0
            db = d['d_brancos'] or 0
            
            votantes = di - da
            abstencao = (da/di*100) if di > 0 else 0
            nulos = (dn/votantes*100) if votantes > 0 else 0 # Nulos sobre votantes
            brancos = (db/votantes*100) if votantes > 0 else 0
            
            nome_unidade = d.get(field_unidade) or 'Desconhecido'
            nome_pai = d.get(field_pai) or ''
            
            plano = { 
                'local': f"{nome_unidade} ({nome_pai})", 
                'acoes': [], 
                'prioridade_geral': 'baixa',
                # Dados Brutos para o Modal de Detalhes
                'stats': {
                    'inscritos': di,
                    'abstencoes': da,
                    'taxa_abstencao': round(abstencao, 1),
                    'nulos': dn,
                    'taxa_nulos': round(nulos, 1),
                    'brancos': db,
                    'taxa_brancos': round(brancos, 1)
                }
            }
            
            # 1. Análise Abstenção
            acao = {'tema': 'Mobilização', 'valor': abstencao}
            if abstencao >= 45:
                acao['status'] = 'CRÍTICO'
                acao['texto'] = "Abstenção Elevada. Recomenda-se intensificação das campanhas de educação cívica."
                plano['prioridade_geral'] = 'alta'
            elif abstencao >= 35:
                acao['status'] = 'ALERTA'
                acao['texto'] = "Alto risco. Reforçar educação cívica."
                if plano['prioridade_geral'] != 'alta': plano['prioridade_geral'] = 'media'
            else:
                acao['status'] = 'POSITIVO'
                acao['texto'] = "Situação Estável. Manter monitoria."
            plano['acoes'].append(acao)

            # 2. Análise Nulos
            if nulos >= 6:
                plano['acoes'].append({'tema': 'Pedagogia', 'status': 'CRÍTICO', 'valor': nulos, 'texto': f"Índice de votos nulos acima do esperado. Necessária revisão dos métodos de instrução de voto."})
                plano['prioridade_geral'] = 'alta'
            elif nulos >= 4:
                plano['acoes'].append({'tema': 'Pedagogia', 'status': 'ALERTA', 'valor': nulos, 'texto': f"Nulos elevados. Reforçar campanhas sobre 'Como Votar'."})
                if plano['prioridade_geral'] != 'alta': plano['prioridade_geral'] = 'media'

            # 3. Análise Brancos
            if brancos >= 4:
                plano['acoes'].append({'tema': 'Análise', 'status': 'ALERTA', 'valor': brancos, 'texto': f"Votos em branco acima da média. Avaliar eficácia da comunicação eleitoral."})
                if plano['prioridade_geral'] != 'alta': plano['prioridade_geral'] = 'media'
            
            if plano['prioridade_geral'] == 'alta': plano['titulo'] = "Prioridade Máxima"
            elif plano['prioridade_geral'] == 'media': plano['titulo'] = "Atenção"
            else: plano['titulo'] = "Manutenção"
            
            recomendacoes.append(plano)
            
        # Ordenar (Prioridade Alta -> Baixa)
        recomendacoes.sort(key=lambda x: 0 if x['prioridade_geral'] == 'alta' else (1 if x['prioridade_geral'] == 'media' else 2))
        
        from django.core.paginator import Paginator
        paginator = Paginator(recomendacoes, 20)
        page_obj = paginator.get_page(self.request.GET.get('page'))
        
        context['recomendacoes'] = page_obj
        context['ano_selecionado'] = int(ano_selecionado)
        context['nivel_selecionado'] = nivel_selecionado
        context['anos_disponiveis'] = ResultadoEleitoral.objects.values_list('ano', flat=True).distinct().order_by('-ano')
        
        # Contexto para os Dropdowns de Filtro
        context['provincias'] = Provincia.objects.all().order_by('nome')
        if provincia_id:
             context['distritos'] = Distrito.objects.filter(provincia_id=provincia_id).order_by('nome')
        else:
             context['distritos'] = Distrito.objects.all().order_by('provincia__nome', 'nome')
             
        # Manter estado dos filtros
        context['provincia_id'] = int(provincia_id) if provincia_id else None
        context['distrito_id'] = int(distrito_id) if distrito_id else None

        return context
