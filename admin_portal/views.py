# admin_portal/views.py
from datetime import timezone

from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.conf import settings
from django.views.decorators.http import require_http_methods
import pandas as pd
import json
import os
import logging

from .models import TemplateImportacao, ImportacaoLog, ConfiguracaoSistema
from .forms import TemplateImportacaoForm, ImportacaoForm, ConfiguracaoSistemaForm
from portalstae.decorators import login_required_for_app

logger = logging.getLogger(__name__)


# ==================== DASHBOARD E PÁGINAS PRINCIPAIS ====================

@login_required_for_app('admin_portal')
def dashboard_admin(request):
    """Dashboard principal do admin portal - apenas administradores"""
    try:
        # Estatísticas
        templates_count = TemplateImportacao.objects.filter(activo=True).count()
        importacoes_recentes = ImportacaoLog.objects.all().order_by('-data_importacao')[:5]

        # Status das importações
        importacoes_status = {
            'sucesso': ImportacaoLog.objects.filter(status='sucesso').count(),
            'erro': ImportacaoLog.objects.filter(status='erro').count(),
            'processando': ImportacaoLog.objects.filter(status='processando').count(),
            'total': ImportacaoLog.objects.count(),
        }

        # Últimas atividades
        atividades_recentes = ImportacaoLog.objects.select_related('template', 'usuario') \
            .order_by('-data_importacao')[:10]

        # Templates mais usados
        templates_ativos = TemplateImportacao.objects.filter(activo=True) \
            .order_by('-ultimo_uso')[:5]

        context = {
            'titulo': 'Dashboard Administrativo',
            'templates_count': templates_count,
            'importacoes_recentes': importacoes_recentes,
            'importacoes_status': importacoes_status,
            'atividades_recentes': atividades_recentes,
            'templates_ativos': templates_ativos,
            'app_name': 'admin_portal',
        }

        return render(request, 'admin_portal/dashboard.html', context)

    except Exception as e:
        logger.error(f"Erro no dashboard admin: {str(e)}")
        messages.error(request, f"Erro ao carregar dashboard: {str(e)}")
        return render(request, 'admin_portal/dashboard.html', {
            'titulo': 'Dashboard Administrativo',
            'app_name': 'admin_portal',
        })


# ==================== GESTÃO DE TEMPLATES ====================

@login_required_for_app('admin_portal')
@require_http_methods(["GET"])
def lista_templates(request):
    """Lista todos os templates de importação"""
    try:
        templates = TemplateImportacao.objects.all().order_by('-data_criacao')

        # Filtros
        status = request.GET.get('status', '')
        if status == 'activo':
            templates = templates.filter(activo=True)
        elif status == 'inactivo':
            templates = templates.filter(activo=False)

        # Pesquisa
        query = request.GET.get('q', '')
        if query:
            templates = templates.filter(
                Q(nome__icontains=query) |
                Q(descricao__icontains=query) |
                Q(tipo_dados__icontains=query)
            )

        # Paginação
        paginator = Paginator(templates, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'titulo': 'Templates de Importação',
            'page_obj': page_obj,
            'templates': page_obj.object_list,
            'query': query,
            'status': status,
            'app_name': 'admin_portal',
        }

        return render(request, 'admin_portal/lista_templates.html', context)

    except Exception as e:
        logger.error(f"Erro ao listar templates: {str(e)}")
        messages.error(request, f"Erro ao carregar templates: {str(e)}")
        return redirect('admin_portal:dashboard')


@login_required_for_app('admin_portal')
@require_http_methods(["GET", "POST"])
def criar_template(request):
    """Cria um novo template de importação"""
    if request.method == 'POST':
        form = TemplateImportacaoForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                template = form.save(commit=False)
                template.criado_por = request.user
                template.save()

                # Criar pasta para arquivos do template
                template_dir = os.path.join(settings.MEDIA_ROOT, 'templates', str(template.id))
                os.makedirs(template_dir, exist_ok=True)

                messages.success(request, f'Template "{template.nome}" criado com sucesso!')
                logger.info(f"Template criado: {template.nome} por {request.user.username}")
                return redirect('admin_portal:detalhe_template', template_id=template.id)

            except Exception as e:
                logger.error(f"Erro ao criar template: {str(e)}")
                messages.error(request, f'Erro ao criar template: {str(e)}')
    else:
        form = TemplateImportacaoForm()

    context = {
        'form': form,
        'titulo': 'Criar Template de Importação',
        'app_name': 'admin_portal',
    }

    return render(request, 'admin_portal/form_template.html', context)


@login_required_for_app('admin_portal')
def detalhe_template(request, template_id):
    """Detalhes de um template específico"""
    template = get_object_or_404(TemplateImportacao, id=template_id)

    # Importações usando este template
    importacoes = ImportacaoLog.objects.filter(template=template) \
        .order_by('-data_importacao')[:10]

    context = {
        'template': template,
        'importacoes': importacoes,
        'titulo': f'Template: {template.nome}',
        'app_name': 'admin_portal',
    }

    return render(request, 'admin_portal/detalhe_template.html', context)


@login_required_for_app('admin_portal')
@require_http_methods(["GET", "POST"])
def editar_template(request, template_id):
    """Edita um template existente"""
    template = get_object_or_404(TemplateImportacao, id=template_id)

    if request.method == 'POST':
        form = TemplateImportacaoForm(request.POST, request.FILES, instance=template)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f'Template "{template.nome}" atualizado com sucesso!')
                logger.info(f"Template editado: {template.nome} por {request.user.username}")
                return redirect('admin_portal:detalhe_template', template_id=template.id)
            except Exception as e:
                logger.error(f"Erro ao editar template: {str(e)}")
                messages.error(request, f'Erro ao atualizar template: {str(e)}')
    else:
        form = TemplateImportacaoForm(instance=template)

    context = {
        'form': form,
        'titulo': f'Editar Template: {template.nome}',
        'template': template,
        'app_name': 'admin_portal',
    }

    return render(request, 'admin_portal/form_template.html', context)


@login_required_for_app('admin_portal')
@require_http_methods(["POST"])
def ativar_desativar_template(request, template_id):
    """Ativa/desativa um template"""
    template = get_object_or_404(TemplateImportacao, id=template_id)

    try:
        template.activo = not template.activo
        template.save()

        acao = "ativado" if template.activo else "desativado"
        messages.success(request, f'Template "{template.nome}" {acao} com sucesso!')
        logger.info(f"Template {acao}: {template.nome} por {request.user.username}")

    except Exception as e:
        logger.error(f"Erro ao alterar status template: {str(e)}")
        messages.error(request, f'Erro ao alterar status: {str(e)}')

    return redirect('admin_portal:lista_templates')


# ==================== IMPORTAÇÃO DE DADOS ====================

@login_required_for_app('admin_portal')
@require_http_methods(["GET", "POST"])
def importar_dados(request):
    """Interface para importação de dados"""
    if request.method == 'POST':
        form = ImportacaoForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                importacao = form.save(commit=False)
                importacao.usuario = request.user
                importacao.save()

                # Processar importação (em background ou sincrona)
                resultado = processar_importacao_sincrona(importacao.id)

                if resultado['sucesso']:
                    messages.success(request, 'Importação concluída com sucesso!')
                    logger.info(f"Importação concluída: {importacao.id} por {request.user.username}")
                else:
                    messages.warning(request, f'Importação concluída com avisos: {resultado["mensagem"]}')

                return redirect('admin_portal:detalhe_importacao', importacao_id=importacao.id)

            except Exception as e:
                logger.error(f"Erro na importação: {str(e)}")
                messages.error(request, f'Erro na importação: {str(e)}')
    else:
        form = ImportacaoForm()

    # Templates disponíveis
    templates_ativos = TemplateImportacao.objects.filter(activo=True)

    context = {
        'form': form,
        'titulo': 'Importar Dados',
        'templates_ativos': templates_ativos,
        'app_name': 'admin_portal',
    }

    return render(request, 'admin_portal/importar_dados.html', context)


@login_required_for_app('admin_portal')
def lista_importacoes(request):
    """Lista todas as importações realizadas"""
    try:
        importacoes = ImportacaoLog.objects.all().select_related(
            'template', 'usuario'
        ).order_by('-data_importacao')

        # Filtros
        status = request.GET.get('status', '')
        if status in ['sucesso', 'erro', 'processando']:
            importacoes = importacoes.filter(status=status)

        template_id = request.GET.get('template', '')
        if template_id:
            importacoes = importacoes.filter(template_id=template_id)

        usuario_id = request.GET.get('usuario', '')
        if usuario_id:
            importacoes = importacoes.filter(usuario_id=usuario_id)

        # Pesquisa
        query = request.GET.get('q', '')
        if query:
            importacoes = importacoes.filter(
                Q(arquivo_original__icontains=query) |
                Q(observacoes__icontains=query)
            )

        # Paginação
        paginator = Paginator(importacoes, 15)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Templates para filtro
        templates = TemplateImportacao.objects.filter(activo=True)
        usuarios = User.objects.filter(is_staff=True)

        context = {
            'titulo': 'Histórico de Importações',
            'page_obj': page_obj,
            'importacoes': page_obj.object_list,
            'templates': templates,
            'usuarios': usuarios,
            'query': query,
            'status': status,
            'app_name': 'admin_portal',
        }

        return render(request, 'admin_portal/lista_importacoes.html', context)

    except Exception as e:
        logger.error(f"Erro ao listar importações: {str(e)}")
        messages.error(request, f"Erro ao carregar histórico: {str(e)}")
        return redirect('admin_portal:dashboard')


@login_required_for_app('admin_portal')
def detalhe_importacao(request, importacao_id):
    """Detalhes de uma importação específica"""
    importacao = get_object_or_404(ImportacaoLog, id=importacao_id)

    # Tentar carregar erros como JSON
    erros = []
    if importacao.erros:
        try:
            erros = json.loads(importacao.erros)
            if not isinstance(erros, list):
                erros = [erros]
        except:
            erros = [importacao.erros]

    context = {
        'importacao': importacao,
        'erros': erros,
        'titulo': f'Importação #{importacao.id}',
        'app_name': 'admin_portal',
    }

    return render(request, 'admin_portal/detalhe_importacao.html', context)


@login_required_for_app('admin_portal')
@require_http_methods(["POST"])
def reprocessar_importacao(request, importacao_id):
    """Reprocessa uma importação existente"""
    importacao = get_object_or_404(ImportacaoLog, id=importacao_id)

    try:
        # Clonar a importação para reprocessar
        nova_importacao = ImportacaoLog.objects.create(
            template=importacao.template,
            usuario=request.user,
            arquivo_original=importacao.arquivo_original,
            observacoes=f"Reprocessamento de #{importacao.id}"
        )

        # Processar
        resultado = processar_importacao_sincrona(nova_importacao.id)

        if resultado['sucesso']:
            messages.success(request, 'Reprocessamento concluído com sucesso!')
        else:
            messages.warning(request, f'Reprocessamento com avisos: {resultado["mensagem"]}')

        return redirect('admin_portal:detalhe_importacao', importacao_id=nova_importacao.id)

    except Exception as e:
        logger.error(f"Erro ao reprocessar importação: {str(e)}")
        messages.error(request, f'Erro ao reprocessar: {str(e)}')
        return redirect('admin_portal:detalhe_importacao', importacao_id=importacao_id)


# ==================== CONFIGURAÇÕES DO SISTEMA ====================

@login_required_for_app('admin_portal')
def configuracao_sistema(request):
    """Configurações do sistema"""
    configuracoes = ConfiguracaoSistema.objects.all().order_by('categoria', 'chave')

    if request.method == 'POST':
        form = ConfiguracaoSistemaForm(request.POST)
        if form.is_valid():
            try:
                config = form.save()
                messages.success(request, f'Configuração "{config.chave}" salva com sucesso!')
                logger.info(f"Configuração salva: {config.chave} por {request.user.username}")
                return redirect('admin_portal:configuracao_sistema')
            except Exception as e:
                logger.error(f"Erro ao salvar configuração: {str(e)}")
                messages.error(request, f'Erro ao salvar configuração: {str(e)}')
    else:
        form = ConfiguracaoSistemaForm()

    # Agrupar por categoria
    categorias = {}
    for config in configuracoes:
        if config.categoria not in categorias:
            categorias[config.categoria] = []
        categorias[config.categoria].append(config)

    context = {
        'categorias': categorias,
        'form': form,
        'titulo': 'Configurações do Sistema',
        'app_name': 'admin_portal',
    }

    return render(request, 'admin_portal/configuracao_sistema.html', context)


@login_required_for_app('admin_portal')
@require_http_methods(["GET", "POST"])
def editar_configuracao(request, config_id):
    """Edita uma configuração específica"""
    config = get_object_or_404(ConfiguracaoSistema, id=config_id)

    if request.method == 'POST':
        form = ConfiguracaoSistemaForm(request.POST, instance=config)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f'Configuração "{config.chave}" atualizada!')
                return redirect('admin_portal:configuracao_sistema')
            except Exception as e:
                messages.error(request, f'Erro ao atualizar: {str(e)}')
    else:
        form = ConfiguracaoSistemaForm(instance=config)

    context = {
        'form': form,
        'config': config,
        'titulo': f'Editar: {config.chave}',
        'app_name': 'admin_portal',
    }

    return render(request, 'admin_portal/form_configuracao.html', context)


# ==================== RELATÓRIOS E ESTATÍSTICAS ====================

@login_required_for_app('admin_portal')
def relatorios_dashboard(request):
    """Dashboard de relatórios"""
    # Estatísticas gerais
    total_importacoes = ImportacaoLog.objects.count()
    importacoes_mes = ImportacaoLog.objects.filter(
        data_importacao__month=timezone.now().month
    ).count()

    # Template mais usado
    from django.db.models import Count
    template_mais_usado = ImportacaoLog.objects.values('template__nome') \
        .annotate(total=Count('id')) \
        .order_by('-total') \
        .first()

    # Usuário mais ativo
    usuario_mais_ativo = ImportacaoLog.objects.values('usuario__username') \
        .annotate(total=Count('id')) \
        .order_by('-total') \
        .first()

    context = {
        'titulo': 'Relatórios e Estatísticas',
        'total_importacoes': total_importacoes,
        'importacoes_mes': importacoes_mes,
        'template_mais_usado': template_mais_usado,
        'usuario_mais_ativo': usuario_mais_ativo,
        'app_name': 'admin_portal',
    }

    return render(request, 'admin_portal/relatorios_dashboard.html', context)


@login_required_for_app('admin_portal')
def exportar_relatorio(request, tipo):
    """Exporta relatórios em diferentes formatos"""
    try:
        if tipo == 'importacoes':
            # Exportar histórico de importações
            importacoes = ImportacaoLog.objects.all().select_related('template', 'usuario')

            # Criar DataFrame
            data = []
            for imp in importacoes:
                data.append({
                    'ID': imp.id,
                    'Data': imp.data_importacao.strftime('%Y-%m-%d %H:%M'),
                    'Template': imp.template.nome if imp.template else '',
                    'Usuário': imp.usuario.username if imp.usuario else '',
                    'Arquivo': imp.arquivo_original,
                    'Registros': imp.registros_processados or 0,
                    'Importados': imp.registros_importados or 0,
                    'Status': imp.status,
                    'Observações': imp.observacoes or '',
                })

            df = pd.DataFrame(data)

            # Exportar para Excel
            response = HttpResponse(content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = 'attachment; filename="relatorio_importacoes.xlsx"'

            with pd.ExcelWriter(response, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Importações', index=False)

            logger.info(f"Relatório exportado: {tipo} por {request.user.username}")
            return response

        elif tipo == 'templates':
            # Exportar templates
            templates = TemplateImportacao.objects.all()

            data = []
            for tmp in templates:
                data.append({
                    'ID': tmp.id,
                    'Nome': tmp.nome,
                    'Descrição': tmp.descricao or '',
                    'Tipo': tmp.tipo_dados,
                    'Ativo': 'Sim' if tmp.activo else 'Não',
                    'Criado em': tmp.data_criacao.strftime('%Y-%m-%d'),
                    'Último uso': tmp.ultimo_uso.strftime('%Y-%m-%d %H:%M') if tmp.ultimo_uso else '',
                    'Criado por': tmp.criado_por.username if tmp.criado_por else '',
                })

            df = pd.DataFrame(data)

            response = HttpResponse(content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = 'attachment; filename="relatorio_templates.xlsx"'

            with pd.ExcelWriter(response, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Templates', index=False)

            logger.info(f"Relatório exportado: {tipo} por {request.user.username}")
            return response

        else:
            messages.error(request, 'Tipo de relatório inválido')
            return redirect('admin_portal:relatorios_dashboard')

    except Exception as e:
        logger.error(f"Erro ao exportar relatório {tipo}: {str(e)}")
        messages.error(request, f'Erro ao exportar relatório: {str(e)}')
        return redirect('admin_portal:relatorios_dashboard')


# ==================== APIs INTERNAS ====================

@login_required_for_app('admin_portal')
@require_http_methods(["GET"])
def api_estatisticas(request):
    """API para estatísticas em tempo real"""
    try:
        # Estatísticas rápidas
        total_templates = TemplateImportacao.objects.count()
        templates_ativos = TemplateImportacao.objects.filter(activo=True).count()

        total_importacoes = ImportacaoLog.objects.count()
        importacoes_hoje = ImportacaoLog.objects.filter(
            data_importacao__date=timezone.now().date()
        ).count()

        importacoes_status = {
            'sucesso': ImportacaoLog.objects.filter(status='sucesso').count(),
            'erro': ImportacaoLog.objects.filter(status='erro').count(),
            'processando': ImportacaoLog.objects.filter(status='processando').count(),
        }

        return JsonResponse({
            'sucesso': True,
            'dados': {
                'templates': {
                    'total': total_templates,
                    'ativos': templates_ativos,
                },
                'importacoes': {
                    'total': total_importacoes,
                    'hoje': importacoes_hoje,
                    'status': importacoes_status,
                },
                'timestamp': timezone.now().isoformat(),
            }
        })

    except Exception as e:
        logger.error(f"Erro na API estatísticas: {str(e)}")
        return JsonResponse({
            'sucesso': False,
            'erro': str(e)
        }, status=500)


@login_required_for_app('admin_portal')
@require_http_methods(["GET"])
def api_importacoes_recentes(request):
    """API para importações recentes"""
    try:
        limite = int(request.GET.get('limite', 10))

        importacoes = ImportacaoLog.objects.select_related('template', 'usuario') \
            .order_by('-data_importacao')[:limite]

        dados = []
        for imp in importacoes:
            dados.append({
                'id': imp.id,
                'data': imp.data_importacao.strftime('%d/%m/%Y %H:%M'),
                'template': imp.template.nome if imp.template else 'N/A',
                'usuario': imp.usuario.username if imp.usuario else 'N/A',
                'arquivo': imp.arquivo_original,
                'status': imp.status,
                'registros': imp.registros_processados or 0,
                'importados': imp.registros_importados or 0,
            })

        return JsonResponse({
            'sucesso': True,
            'dados': dados
        })

    except Exception as e:
        logger.error(f"Erro na API importações recentes: {str(e)}")
        return JsonResponse({
            'sucesso': False,
            'erro': str(e)
        }, status=500)


# ==================== FUNÇÕES AUXILIARES ====================

def processar_importacao_sincrona(importacao_id):
    """
    Processa importação de forma síncrona
    Retorna: {'sucesso': bool, 'mensagem': str, 'dados': dict}
    """
    importacao = ImportacaoLog.objects.get(id=importacao_id)

    try:
        importacao.status = 'processando'
        importacao.save()

        # Simular processamento (substituir pela lógica real)
        import time
        time.sleep(2)  # Simular processamento

        # Atualizar template
        if importacao.template:
            importacao.template.ultimo_uso = timezone.now()
            importacao.template.save()

        # Resultados simulados
        importacao.registros_processados = 100
        importacao.registros_importados = 95
        importacao.erros = json.dumps([
            "Linha 15: CPF inválido",
            "Linha 42: Email duplicado",
            "Linha 78: Data de nascimento futura"
        ])
        importacao.status = 'sucesso'
        importacao.save()

        return {
            'sucesso': True,
            'mensagem': 'Importação processada com sucesso',
            'dados': {
                'processados': importacao.registros_processados,
                'importados': importacao.registros_importados,
                'erros': json.loads(importacao.erros)
            }
        }

    except Exception as e:
        logger.error(f"Erro ao processar importação {importacao_id}: {str(e)}")

        importacao.status = 'erro'
        importacao.erros = json.dumps([str(e)])
        importacao.save()

        return {
            'sucesso': False,
            'mensagem': f'Erro no processamento: {str(e)}',
            'dados': None
        }

# ==================== SUPER PLANILHA EXCEL (FUTURISTICA) ====================
from django.apps import apps

@login_required_for_app('admin_portal')
def super_planilha(request):
    """Renderiza a super planilha futurística estilo Excel"""
    context = {
        'titulo': 'Super Planilha STAE',
        'app_name': 'admin_portal',
    }
    return render(request, 'admin_portal/super_planilha.html', context)

import json
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@login_required_for_app('admin_portal')
def api_super_planilha(request):
    """API Dinâmica para a Super Planilha Excel"""
    try:
        model_map = {
            'rh': ('recursoshumanos', 'Funcionario'),
            'transportes': ('gestaocombustivel', 'Viatura'),
            'equipamento': ('gestaoequipamentos', 'Equipamento')
        }
        
        tab = request.GET.get('tab', 'rh')
        if tab not in model_map:
            return JsonResponse({'sucesso': False, 'erro': 'Aba inválida'})
            
        app_label, model_name = model_map[tab]
        ModelClass = apps.get_model(app_label, model_name)
        
        if request.method == 'GET':
            data = []
            resource = request.GET.get('resource', 'default')
            from django.db.models import Sum, F, Count
            from django.utils import timezone
            from datetime import timedelta
            now = timezone.now()

            # --- MAPEAR TUDO (TUDO MESMO) ---
            if tab == 'rh':
                if resource == 'licencas':
                    from recursoshumanos.models import Licenca
                    records = Licenca.objects.select_related('funcionario').all()
                    for obj in records:
                        data.append({'id': obj.id, 'nome': obj.funcionario.nome_completo, 'tipo': obj.tipo, 'inicio': obj.data_inicio, 'fim': obj.data_fim, 'ia_insight': "Verificar Justificativo" if not obj.documento_ferias else "Documentado"})
                elif resource == 'avaliacoes':
                    from recursoshumanos.models import AvaliacaoDesempenho
                    records = AvaliacaoDesempenho.objects.select_related('funcionario').all()
                    for obj in records:
                        data.append({'id': obj.id, 'nome': obj.funcionario.nome_completo, 'periodo': obj.periodo, 'nota': obj.pontuacao_final, 'ia_insight': "🏆 Top Performer" if obj.pontuacao_final > 90 else "Estável"})
                elif resource == 'ferias':
                    from recursoshumanos.models import PedidoFerias
                    records = PedidoFerias.objects.select_related('funcionario').all()
                    for obj in records:
                        data.append({'id': obj.id, 'nome': obj.funcionario.nome_completo, 'inicio': obj.data_inicio, 'fim': obj.data_fim, 'status': obj.status, 'ia_insight': "Normal"})
                else: # Default: Colaboradores
                    from recursoshumanos.models import Funcionario
                    records = Funcionario.objects.select_related('sector').all()
                    for obj in records:
                        data.append({'id': obj.id, 'nome_completo': obj.nome_completo, 'sector': obj.sector.nome if obj.sector else "-", 'ia_insight': "Pronto p/ Missão", 'funcao': obj.funcao})

            elif tab == 'transportes':
                if resource == 'viagens':
                    from gestaocombustivel.models import RegistroUtilizacao
                    records = RegistroUtilizacao.objects.select_related('viatura', 'motorista').all()[:200]
                    for obj in records:
                        data.append({'id': obj.id, 'viatura': obj.viatura.matricula, 'motorista': obj.motorista.nome_completo, 'km_i': obj.km_inicial, 'km_f': obj.km_final, 'ia_insight': f"Destino: {obj.localizacao_actual or 'Local'}"})
                elif resource == 'manutencoes':
                    from gestaocombustivel.models import ManutencaoViatura
                    records = ManutencaoViatura.objects.select_related('viatura').all()
                    for obj in records:
                        data.append({'id': obj.id, 'viatura': obj.viatura.matricula, 'tipo': obj.tipo_manutencao, 'data': obj.data_realizacao, 'custo': obj.custo_total, 'ia_insight': "Manut. Ativa"})
                elif resource == 'combustivel':
                    from gestaocombustivel.models import PedidoCombustivel
                    records = PedidoCombustivel.objects.select_related('viatura').all()
                    for obj in records:
                        data.append({'id': obj.id, 'viatura': obj.viatura.matricula, 'litros': obj.quantidade_litros, 'custo': obj.custo_total, 'ia_insight': "Abastecimento OK"})
                else: # Default: Frota
                    from gestaocombustivel.models import Viatura
                    records = Viatura.objects.all()
                    for obj in records:
                        data.append({'id': obj.id, 'matricula': obj.matricula, 'viatura': f"{obj.marca} {obj.modelo}", 'km': obj.kilometragem_actual, 'ia_insight': "Ativo Frota"})

            elif tab == 'equipamento':
                from gestaoequipamentos.models import Equipamento, Inventario
                records = Equipamento.objects.select_related('tipo').all()
                for obj in records:
                    inv = Inventario.objects.filter(equipamento=obj).first()
                    data.append({
                        'id': obj.id, 'serial': obj.numero_serie, 'alias': obj.tipo.nome if obj.tipo else "Item",
                        'local': inv.localizacao_especifica if inv else "Não Alocado",
                        'ia_insight': "Estável"
                    })

            return JsonResponse(data, safe=False)
            
        elif request.method == 'POST':
            # Manter logica de escrita simplificada para o Master Object do tab
            body = json.loads(request.body)
            action = body.get('action')
            row_data = body.get('data', {})
            
            if action == 'update':
                obj = ModelClass.objects.get(id=row_data.get('id'))
                for key, value in row_data.items():
                    if hasattr(obj, key) and key != 'id':
                        setattr(obj, key, value)
                obj.save()
                return JsonResponse({'sucesso': True, 'id': obj.id})
            elif action == 'delete':
                obj = ModelClass.objects.get(id=row_data.get('id'))
                obj.delete()
                return JsonResponse({'sucesso': True})
                
    except Exception as e:
        return JsonResponse({'sucesso': False, 'erro': str(e)}, status=500)
