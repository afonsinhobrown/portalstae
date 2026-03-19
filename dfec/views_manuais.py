# dfec/views_manuais.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils.text import slugify
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
from datetime import datetime

# Decorator personalizado do sistema
from portalstae.decorators import login_required_for_app
from .forms import ManualForm, CapituloForm, ComentarioForm, ImagemForm, ImpressaoForm

# Forms e Models
from .models import *
from .models.completo import Manual, CapituloManual, ImagemManual, TipoManual, VersaoManual, HistoricoUsoManual


# ==================== MÓDULO 5: MANUAIS ====================

@login_required_for_app('dfec')
def manuais_dashboard(request):
    """Dashboard de manuais - apenas usuários DFEC"""
    # Estatísticas
    estatisticas = {
        'total_manuais': Manual.objects.count(),
        'manuais_publicados': Manual.objects.filter(status='PUBLICADO').count(),
        'manuais_rascunho': Manual.objects.filter(status='RASCUNHO').count(),
        'tipos_manuais': TipoManual.objects.count(),
        'total_downloads': HistoricoUsoManual.objects.filter(acao='DOWNLOAD').count(),
    }

    # Manuais recentes
    manuais_recentes = Manual.objects.order_by('-data_atualizacao')[:5]

    # Manuais por tipo
    manuais_por_tipo = TipoManual.objects.annotate(
        total_manuais=Count('manuais')
    ).order_by('-total_manuais')

    context = {
        'estatisticas': estatisticas,
        'manuais_recentes': manuais_recentes,
        'manuais_por_tipo': manuais_por_tipo,
        'titulo': 'Dashboard de Manuais DFEC'
    }

    return render(request, 'dfec/manuais/dashboard.html', context)


@method_decorator(login_required_for_app('dfec'), name='dispatch')
class ManualListView(ListView):
    """Lista de manuais - protegida para DFEC"""
    model = Manual
    template_name = 'dfec/manuais/lista.html'
    paginate_by = 12
    context_object_name = 'manuais'

    def get_queryset(self):
        queryset = Manual.objects.all()

        # Filtros
        tipo = self.request.GET.get('tipo')
        status = self.request.GET.get('status')
        formato = self.request.GET.get('formato')
        search = self.request.GET.get('q')

        if tipo:
            queryset = queryset.filter(tipo_id=tipo)
        if status:
            queryset = queryset.filter(status=status)
        if formato:
            queryset = queryset.filter(formato=formato)
        if search:
            queryset = queryset.filter(
                Q(titulo__icontains=search) |
                Q(subtitulo__icontains=search) |
                Q(codigo__icontains=search) |
                Q(publico_alvo__icontains=search)
            )

        # Para usuários DFEC não-admin, limitar acesso
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(status='PUBLICADO') |
                Q(colaboradores=self.request.user) |
                Q(revisores=self.request.user) |
                Q(autor_principal=self.request.user)
            ).distinct()

        return queryset.select_related('criado_por')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tipos_manuais'] = TipoManual.objects.all()
        context['titulo'] = 'Catálogo de Manuais DFEC'
        return context


@login_required_for_app('dfec')
def manual_detalhe(request, pk):
    """Página detalhada do manual - protegida para DFEC"""
    manual = get_object_or_404(Manual, pk=pk)

    # Verificar se usuário pode visualizar este manual
    if manual.status != 'publicado': # Note: case sensitive check adjusted based on models
        if not (request.user.is_staff or
                request.user == manual.criado_por):
            messages.error(request, "Você não tem acesso a este manual.")
            return redirect('dfec:manuais_lista')
    
    # HistoricoUsoManual desativado (requer ManualCompleto)
    # manual.incrementar_visualizacao() # Método do model simples

    # Capítulos
    capitulos = manual.capitulos_simples.all().order_by('ordem', 'numero')

    context = {
        'manual': manual,
        'capitulos': capitulos,
        'titulo': f'Manual: {manual.titulo}'
    }

    return render(request, 'dfec/manuais/detalhe.html', context)


@login_required_for_app('dfec')
def manual_criar(request):
    """Criar novo manual - apenas usuários com permissão"""
    # Verificar permissão específica
    if not request.user.has_perm('dfec.add_manual'):
        messages.error(request, "Você não tem permissão para criar manuais.")
        return redirect('dfec:manuais_lista')

    if request.method == 'POST':
        form = ManualForm(request.POST, request.FILES)

        if form.is_valid():
            manual = form.save(commit=False)
            manual.autor_principal = request.user

            # Gerar código automático se não fornecido
            if not manual.codigo:
                tipo_codigo = manual.tipo.codigo if manual.tipo else 'MAN'
                ano = datetime.now().year
                sequencia = Manual.objects.filter(
                    codigo__startswith=f"{tipo_codigo}-{ano}-"
                ).count() + 1
                manual.codigo = f"{tipo_codigo}-{ano}-{sequencia:04d}"

            manual.save()
            form.save_m2m()

            messages.success(request, "Manual criado com sucesso!")
            return redirect('dfec:manual_editar', pk=manual.pk)
    else:
        form = ManualForm()

    context = {
        'form': form,
        'titulo': 'Criar Novo Manual'
    }
    return render(request, 'dfec/manuais/form.html', context)


@login_required_for_app('dfec')
def manual_editar(request, pk):
    """Editor de manual - apenas autores/colaboradores"""
    manual = get_object_or_404(Manual, pk=pk)

    # Verificar permissões de edição
    pode_editar = (
            request.user.has_perm('dfec.change_manual') or
            request.user == manual.criado_por # Colaboradores removidos (não existe em Manual simples)
    )

    if not pode_editar:
        messages.error(request, "Você não tem permissão para editar este manual.")
        return redirect('dfec:manual_detalhe', pk=pk)

    if request.method == 'POST':
        form = ManualForm(request.POST, request.FILES, instance=manual)

        if form.is_valid():
            manual_antigo = Manual.objects.get(pk=pk)
            novo_manual = form.save()

            # Registrar mudanças significativas
            mudancas = []
            if manual_antigo.titulo != novo_manual.titulo:
                mudancas.append(f"Título alterado: {manual_antigo.titulo} → {novo_manual.titulo}")
            if manual_antigo.versao != novo_manual.versao:
                mudancas.append(f"Versão alterada: {manual_antigo.versao} → {novo_manual.versao}")

            if mudancas:
                pass

            messages.success(request, "Manual atualizado com sucesso!")
            return redirect('dfec:manual_editar', pk=pk)
    else:
        form = ManualForm(instance=manual)

    # Capítulos
    capitulos = manual.capitulos_simples.all().order_by('ordem', 'numero')

    # Imagens disponíveis
    imagens = []

    context = {
        'manual': manual,
        'form': form,
        'capitulos': capitulos,
        'imagens': imagens,
        'titulo': f'Editar Manual: {manual.titulo}'
    }

    return render(request, 'dfec/manuais/form.html', context)


@login_required_for_app('dfec')
def capitulo_criar(request, manual_id):
    """Criar novo capítulo - apenas autores/colaboradores"""
    manual = get_object_or_404(Manual, pk=manual_id)

    # Verificar permissões
    pode_editar = (
            request.user.has_perm('dfec.change_manual') or
            request.user in manual.colaboradores.all() or
            request.user == manual.autor_principal
    )

    if not pode_editar:
        messages.error(request, "Você não tem permissão para adicionar capítulos.")
        return redirect('dfec:manual_detalhe', pk=manual_id)

    if request.method == 'POST':
        form = CapituloForm(request.POST)

        if form.is_valid():
            try:
                capitulo = form.save(commit=False)
                capitulo.manual = manual

                # Definir ordem automática
                ultimo_capitulo = manual.capitulos_simples.order_by('ordem').last()
                capitulo.ordem = ultimo_capitulo.ordem + 1 if ultimo_capitulo else 1

                capitulo.save()
                print(f"DEBUG: Capítulo salvo com sucesso! ID={capitulo.id}, Manual={manual.id}")

                messages.success(request, "Capítulo criado com sucesso!")
                return redirect('dfec:manual_detalhe', pk=manual_id)
            except Exception as e:
                print(f"DEBUG: Erro ao salvar capítulo: {e}")
                messages.error(request, f"Erro ao salvar: {e}")
        else:
            print(f"DEBUG: Form inválido: {form.errors}")
            for field, errors in form.errors.items():
                messages.error(request, f"Erro no campo {field}: {errors}")
    else:
        form = CapituloForm()

    context = {
        'form': form,
        'manual': manual,
        'titulo': 'Adicionar Capítulo'
    }
    return render(request, 'dfec/manuais/capitulo_form.html', context)


@login_required_for_app('dfec')
def capitulo_editar(request, pk):
    """Editar capítulo - apenas autores/colaboradores"""
    capitulo = get_object_or_404(CapituloSimples, pk=pk)
    manual = capitulo.manual

    # Verificar permissões (usando criado_por do Manual simples)
    pode_editar = (
            request.user.is_staff or
            request.user == manual.criado_por or
            request.user.has_perm('dfec.change_manual')
    )

    if not pode_editar:
        messages.error(request, "Você não tem permissão para editar capítulos.")
        return redirect('dfec:manual_detalhe', pk=manual.pk)

    if request.method == 'POST':
        form = CapituloForm(request.POST, instance=capitulo)

        if form.is_valid():
            novo_capitulo = form.save()
            messages.success(request, "Capítulo atualizado com sucesso!")
            return redirect('dfec:manual_detalhe', pk=manual.pk)
    else:
        form = CapituloForm(instance=capitulo)

    context = {
        'form': form,
        'manual': manual,
        'capitulo': capitulo,
        'titulo': f'Editar Capítulo: {capitulo.titulo}'
    }
    return render(request, 'dfec/manuais/capitulo_form.html', context)


@login_required_for_app('dfec')
def capitulo_excluir(request, pk):
    """Excluir capítulo - apenas autores/colaboradores"""
    capitulo = get_object_or_404(CapituloSimples, pk=pk)
    manual = capitulo.manual

    # Verificar permissões
    pode_editar = (
            request.user.is_staff or
            request.user == manual.criado_por or
            request.user.has_perm('dfec.change_manual')
    )

    if not pode_editar:
        messages.error(request, "Você não tem permissão para excluir capítulos.")
        return redirect('dfec:manual_detalhe', pk=manual.pk)
    
    # Exclusão direta (idealmente via POST, mas acessível via GET protegido por permissão)
    titulo_cap = capitulo.titulo
    capitulo.delete()
    messages.success(request, f"Capítulo '{titulo_cap}' excluído com sucesso.")
    return redirect('dfec:manual_editar', pk=manual.pk)


def gerar_css_dinamico(formato_papel='a4'):
    """Gerar CSS dinâmico para o PDF baseado no formato"""
    # Dimensões
    sizes = {
        'pocket': '10.5cm 17.8cm', 
        'a5': '14.8cm 21.0cm',
        '16x23': '16.0cm 23.0cm',
        'a4': '21.0cm 29.7cm'
    }
    
    # Margens laterais (frames usarão estas coordenadas)
    margins_left = {
        'pocket': '1.0cm',
        'a5': '1.5cm',
        '16x23': '2.0cm',
        'a4': '2.0cm'
    }
    
    frame_widths = {
        'pocket': '8.5cm',
        'a5': '11.8cm',
        '16x23': '12.0cm',
        'a4': '17.0cm'
    }
    
    # Posições do topo
    # Header sempre no topo da margem
    # Content começa após o header
    header_height = '2.5cm'
    content_top = {
        'pocket': '4.0cm',
        'a5': '4.5cm',
        '16x23': '5.0cm',
        'a4': '5.0cm'
    }
    
    # Alturas de conteúdo (calculadas para não bater no footer)
    content_heights = {
        'pocket': '11.0cm',
        'a5': '13.5cm',
        '16x23': '15.0cm',
        'a4': '21.0cm'
    }
    
    formato = formato_papel.lower() if formato_papel else 'a4'
    m_left = margins_left.get(formato, margins_left['a4'])
    f_width = frame_widths.get(formato, frame_widths['a4'])
    c_top = content_top.get(formato, content_top['a4'])
    c_height = content_heights.get(formato, content_heights['a4'])
    
    return f"""
    <style>
        @page {{
            size: {sizes.get(formato, sizes['a4'])};
            margin: 0.5cm; /* Margem mínima de segurança */
            
            @frame header_frame {{
                -pdf-frame-content: header_content;
                top: 1.0cm;
                left: {m_left};
                width: {f_width};
                height: {header_height};
            }}
            
            @frame footer_frame {{
                -pdf-frame-content: footer_content;
                bottom: 1.0cm;
                left: {m_left};
                width: {f_width};
                height: 1.2cm;
            }}
            
            @frame content_frame {{
                left: {m_left};
                top: {c_top};
                width: {f_width};
                height: {c_height};
            }}
        }}
        
        body {{
            font-family: Helvetica, Arial, sans-serif;
            font-size: 11pt;
            line-height: 1.5;
            color: #000;
        }}
        
        .header {{
            text-align: center;
            border-bottom: 1px solid #0d6efd;
        }}
        
        .header h1 {{
            color: #0d6efd;
            font-size: 18pt;
            margin: 0;
            padding: 0;
        }}
        
        h2 {{
            color: #333;
            font-size: 16pt;
            margin-top: 20px;
            margin-bottom: 10px;
            border-bottom: 1px solid #eee;
        }}
        
        h3 {{
            color: #444;
            font-size: 13pt;
            margin-top: 15px;
            margin-bottom: 5px;
        }}
        
        .chapter {{
            page-break-before: always;
        }}
        
        .first-chapter {{
            page-break-before: avoid;
        }}
        
        .chapter-title {{
            background-color: #f8f9fa;
            padding: 10px;
            border-left: 5px solid #0d6efd;
            margin-bottom: 20px;
        }}
        
        .content p {{
            text-align: justify;
            margin: 10px 0;
        }}
        
        img {{
            max-width: 100%;
            height: auto;
            margin: 10px 0;
        }}
        
        .footer-text {{
            text-align: center;
            color: #666;
            font-size: 9pt;
            border-top: 0.5px solid #ccc;
        }}
    </style>
    """


@login_required_for_app('dfec')
def gerar_pdf_manual(request, pk):
    """Gerar PDF do manual - protegido para DFEC"""
    manual = get_object_or_404(Manual, pk=pk)

    # Verificar permissões de visualização
    if manual.status != 'PUBLICADO':
        if not (request.user.is_staff or
                request.user in manual.colaboradores.all() or
                request.user == manual.autor_principal):
            messages.error(request, "Você não tem permissão para exportar este manual.")
            return redirect('dfec:manual_detalhe', pk=pk)

    try:
        from xhtml2pdf import pisa
        from django.template.loader import get_template
        from django.http import HttpResponse
        import os
        
        template_path = 'dfec/manuais/pdf.html'
        
        # Gerar CSS dinâmico
        dynamic_css = gerar_css_dinamico(manual.formato_papel)

        # Contexto para o template - INCLUIR request.user
        context = {
            'manual': manual,
            'capitulos': manual.capitulos_simples.all().order_by('ordem', 'numero'),
            'data_geracao': datetime.now(),
            'dynamic_css': dynamic_css,
            'usuario': request.user,  # Adicionar usuário ao contexto
        }
        
        response = HttpResponse(content_type='application/pdf')
        nome_arquivo = manual.codigo or f"manual_{manual.pk}"
        response['Content-Disposition'] = f'inline; filename="{nome_arquivo}.pdf"'
        
        template = get_template(template_path)
        html = template.render(context)
        
        # Função callback para resolver caminhos de imagem
        def link_callback(uri, rel):
            import os
            from django.conf import settings
            
            sUrl = settings.STATIC_URL
            sRoot = settings.STATIC_ROOT
            mUrl = settings.MEDIA_URL
            mRoot = settings.MEDIA_ROOT

            if uri.startswith(mUrl):
                path = os.path.join(mRoot, uri.replace(mUrl, "").lstrip('/').lstrip('\\'))
            elif uri.startswith(sUrl):
                path = os.path.join(sRoot, uri.replace(sUrl, "").lstrip('/').lstrip('\\'))
            else:
                return uri

            # Debug para verificar caminhos (aparecerá no terminal do servidor)
            print(f"PDF Link Callback: URI={uri} -> PATH={path}")

            if not os.path.isfile(path):
                if uri.startswith(sUrl) and settings.DEBUG:
                    for dir in settings.STATICFILES_DIRS:
                        possible_path = os.path.join(dir, uri.replace(sUrl, ""))
                        if os.path.isfile(possible_path):
                            return possible_path
                            
            return path

        pisa_status = pisa.CreatePDF(
            html, dest=response, encoding='utf-8', link_callback=link_callback
        )
        
        if pisa_status.err:
            messages.error(request, f"Erro ao gerar PDF: {pisa_status.err}")
            return redirect('dfec:manual_detalhe', pk=pk)
            
        # Registrar download
        try:
            HistoricoUsoManual.objects.create(
                manual=manual,
                usuario=request.user,
                acao='DOWNLOAD',
                detalhes={'formato': 'PDF'},
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        except Exception:
            pass
            
        return response

    except Exception as e:
        messages.error(request, f"Erro ao gerar PDF: {str(e)}")
        return redirect('dfec:manual_detalhe', pk=pk)
    

@login_required_for_app('dfec')
def solicitar_impressao(request, pk):
    """Solicitar impressão física - apenas com permissão específica"""
    manual = get_object_or_404(Manual, pk=pk)

    # Verificar permissão específica
    if not request.user.has_perm('dfec.imprimir_manual'):
        messages.error(request, "Você não tem permissão para solicitar impressão.")
        return redirect('dfec:manual_detalhe', pk=pk)

    if not manual.pode_imprimir:
        messages.error(request, "Este manual não está disponível para impressão.")
        return redirect('dfec:manual_detalhe', pk=pk)

    if request.method == 'POST':
        form = ImpressaoForm(request.POST)

        if form.is_valid():
            # Processar solicitação de impressão
            quantidade = form.cleaned_data['quantidade']
            observacoes = form.cleaned_data['observacoes']

            # Registrar solicitação
            HistoricoUsoManual.objects.create(
                manual=manual,
                usuario=request.user,
                acao='IMPRESSAO',
                detalhes={
                    'quantidade': quantidade,
                    'observacoes': observacoes,
                    'solicitacao_id': f"IMP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                }
            )

            messages.success(request, f"Solicitação de impressão para {quantidade} cópias registrada!")
            return redirect('dfec:manual_detalhe', pk=pk)
    else:
        form = ImpressaoForm()

    context = {
        'manual': manual,
        'form': form,
        'titulo': 'Solicitar Impressão'
    }
    return render(request, 'dfec/manuais/impressao.html', context)


@login_required_for_app('dfec')
def biblioteca_imagens(request):
    """Biblioteca de imagens - apenas DFEC"""
    imagens = ImagemManual.objects.all().order_by('-id')

    # Filtros
    manual_id = request.GET.get('manual')
    tag = request.GET.get('tag')
    search = request.GET.get('q')

    if manual_id:
        imagens = imagens.filter(Q(manual_id=manual_id) | Q(manual__isnull=True))
    if tag:
        imagens = imagens.filter(tags__icontains=tag)
    if search:
        imagens = imagens.filter(
            Q(titulo__icontains=search) |
            Q(descricao__icontains=search) |
            Q(tags__icontains=search)
        )

    # Paginação
    paginator = Paginator(imagens, 24)
    page = request.GET.get('page')
    imagens_pagina = paginator.get_page(page)

    # Manuais para filtro
    manuais = Manual.objects.all()

    context = {
        'imagens': imagens_pagina,
        'manuais': manuais,
        'titulo': 'Biblioteca de Imagens'
    }

    return render(request, 'dfec/manuais/biblioteca_imagens.html', context)


@login_required_for_app('dfec')
@require_POST
def upload_imagem(request):
    """Upload de imagem - apenas DFEC"""
    form = ImagemForm(request.POST, request.FILES)

    if form.is_valid():
        imagem = form.save(commit=False)

        # Associar ao usuário atual
        if not imagem.autor:
            imagem.autor = request.user.get_full_name() or request.user.username

        imagem.save()

        return JsonResponse({
            'success': True,
            'imagem_id': imagem.id,
            'imagem_url': imagem.imagem.url,
            'miniatura_url': imagem.miniatura.url if imagem.miniatura else imagem.imagem.url,
            'titulo': imagem.titulo
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors
        })


@login_required_for_app('dfec')
@require_POST
def comentario_adicionar(request, manual_id):
    """Adicionar comentário - apenas DFEC"""
    manual = get_object_or_404(Manual, pk=manual_id)

    form = ComentarioForm(request.POST)

    if form.is_valid():
        comentario = form.save(commit=False)
        comentario.manual = manual
        comentario.usuario = request.user
        comentario.save()

        messages.success(request, "Comentário adicionado com sucesso!")

    return redirect('dfec:manual_detalhe', pk=manual_id)


@login_required_for_app('dfec')
@require_POST
def publicar_manual(request, pk):
    """Publicar manual - apenas com permissão específica"""
    manual = get_object_or_404(Manual, pk=pk)

    if not request.user.has_perm('dfec.publicar_manual'):
        messages.error(request, "Você não tem permissão para publicar manuais.")
        return redirect('dfec:manual_detalhe', pk=pk)

    manual.status = 'PUBLICADO'
    manual.data_publicacao = datetime.now().date()
    manual.save()

    # Registrar versão de publicação
    VersaoManual.objects.create(
        manual=manual,
        versao=manual.versao,
        autor_mudanca=request.user,
        descricao_mudanca="Manual publicado"
    )

    messages.success(request, "Manual publicado com sucesso!")
    return redirect('dfec:manual_detalhe', pk=pk)


# ==================== APIs ====================

@login_required_for_app('dfec')
@require_GET
def api_manuais_tipo(request, tipo_codigo):
    """API para listar manuais por tipo - protegida para DFEC"""
    # Verificar se usuário pode acessar
    if not request.user.groups.filter(name='DFEC').exists() and not request.user.is_staff:
        return JsonResponse({'error': 'Acesso negado'}, status=403)

    manuais = Manual.objects.filter(
        tipo__codigo=tipo_codigo,
        status='PUBLICADO'
    ).order_by('-data_atualizacao')

    data = []
    for manual in manuais:
        data.append({
            'id': manual.id,
            'titulo': manual.titulo,
            'subtitulo': manual.subtitulo,
            'versao': manual.versao,
            'idioma': manual.idioma,
            'data_publicacao': manual.data_publicacao,
            'url': request.build_absolute_uri(manual.get_absolute_url()),
            'download_url': request.build_absolute_uri(f'/manuais/{manual.id}/pdf/'),
        })

    return JsonResponse({'manuais': data})


@login_required_for_app('dfec')
@require_GET
def api_estatisticas_manuais(request):
    """API para estatísticas de manuais - protegida para DFEC"""
    # Estatísticas gerais
    estatisticas = {
        'total_manuais': Manual.objects.count(),
        'publicados': Manual.objects.filter(status='PUBLICADO').count(),
        'rascunhos': Manual.objects.filter(status='RASCUNHO').count(),
        'por_tipo': {},
        'downloads_mes': HistoricoUsoManual.objects.filter(
            acao='DOWNLOAD',
            data_hora__month=datetime.now().month
        ).count(),
    }

    # Por tipo
    tipos = TipoManual.objects.all()
    for tipo in tipos:
        estatisticas['por_tipo'][tipo.nome] = tipo.manuais.count()

    return JsonResponse(estatisticas)


# ==================== FUNÇÕES AUXILIARES ====================

def user_pode_visualizar_manual(user, manual):
    """Verificar se usuário pode visualizar manual"""
    if manual.status == 'PUBLICADO':
        return True

    return (
            user.is_staff or
            user in manual.colaboradores.all() or
            user == manual.autor_principal or
            user.has_perm('dfec.view_manual')
    )


def user_pode_editar_manual(user, manual):
    """Verificar se usuário pode editar manual"""
    return (
            user.has_perm('dfec.change_manual') or
            user in manual.colaboradores.all() or
            user == manual.autor_principal
    )


@csrf_exempt
@login_required_for_app('dfec')
def upload_imagem_editor(request):
    """Upload de imagem via TinyMCE"""
    if request.method == 'POST' and request.FILES.get('file'):
        file_obj = request.FILES['file']
        
        # Validar tipo
        if not file_obj.content_type.startswith('image/'):
            return JsonResponse({'error': 'Arquivo inválido. Envie uma imagem.'}, status=400)
            
        # Salvar imagem
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        import os
        
        # Nome único
        filename, ext = os.path.splitext(file_obj.name)
        new_filename = f"{filename}_{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}"
        path = default_storage.save(f'manuais/uploads/{new_filename}', ContentFile(file_obj.read()))
        url = default_storage.url(path)
        
        return JsonResponse({'location': url})
    return JsonResponse({'error': 'Erro no upload'}, status=400)