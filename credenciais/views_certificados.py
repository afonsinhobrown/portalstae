from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.http import HttpResponse
from .models import ModeloDocumento, ProjetoCertificacao, DocumentoEmitido, Evento, CredencialEmitida
from recursoshumanos.models import Funcionario, Sector
from .utils_pdf import gerar_pdf_certificado
import zipfile
from io import BytesIO
from django.utils.text import slugify

try:
    from dfec.models.completo import Formacao, Participante
    DFEC_AVAILABLE = True
except ImportError:
    DFEC_AVAILABLE = False

def is_admin(user):
    return user.is_staff

@login_required
@user_passes_test(is_admin)
def dashboard(request):
    projetos = ProjetoCertificacao.objects.all().order_by('-created_at')
    return render(request, 'credenciais/certificados/dashboard.html', {'projetos': projetos})

@login_required
@user_passes_test(is_admin)
def novo_projeto(request):
    """Passo 1: Escolher Modelo Base"""
    if request.method == 'POST':
        modelo_id = request.POST.get('modelo')
        nome_projeto = request.POST.get('nome')
        
        modelo = get_object_or_404(ModeloDocumento, id=modelo_id)
        
        projeto = ProjetoCertificacao.objects.create(
            nome=nome_projeto,
            modelo=modelo,
            titulo="DIPLOMA", # Default proposta
            texto_corpo=modelo.html_template, # Copia do modelo
            criado_por=request.user
        )
        return redirect('credenciais:cert_editor', projeto_id=projeto.id)

    # Se não houver modelos, cria defaults
    if not ModeloDocumento.objects.exists():
        ModeloDocumento.objects.create(
            nome="Certificado Padrão STAE",
            html_template="Certificamos que {{ nome }} participou ativamente do evento..."
        )
        ModeloDocumento.objects.create(
            nome="Diploma de Honra",
            html_template="Confere-se o presente Diploma de Honra a {{ nome }} pelos serviços prestados..."
        )

    modelos = ModeloDocumento.objects.filter(ativo=True)
    return render(request, 'credenciais/certificados/novo_projeto.html', {'modelos': modelos})

@login_required
@user_passes_test(is_admin)
def editor_projeto(request, projeto_id):
    """Passo 2: Customizar Texto/Design"""
    projeto = get_object_or_404(ProjetoCertificacao, id=projeto_id)
    
    if request.method == 'POST':
        projeto.titulo = request.POST.get('titulo')
        projeto.texto_corpo = request.POST.get('texto_corpo')
        projeto.data_extenso = request.POST.get('data_extenso')
        projeto.nome_assinatura_1 = request.POST.get('assinatura1')
        projeto.cargo_assinatura_1 = request.POST.get('cargo1')
        projeto.nome_assinatura_2 = request.POST.get('assinatura2')
        projeto.cargo_assinatura_1 = request.POST.get('cargo1')
        projeto.nome_assinatura_2 = request.POST.get('assinatura2')
        projeto.cargo_assinatura_2 = request.POST.get('cargo2')
        projeto.entidade_emissora = request.POST.get('entidade_emissora', 'stae')

        
        if 'fundo' in request.FILES:
            projeto.fundo_personalizado = request.FILES['fundo']
            
        projeto.save()
        messages.success(request, "Alterações salvas!")
        return redirect('credenciais:cert_beneficiarios', projeto_id=projeto.id)
        
    return render(request, 'credenciais/certificados/editor.html', {'projeto': projeto})

@login_required
@user_passes_test(is_admin)
def gerir_beneficiarios(request, projeto_id):
    """Passo 3: Selecionar Pessoas"""
    projeto = get_object_or_404(ProjetoCertificacao, id=projeto_id)
    
    if request.method == 'POST':
        acao = request.POST.get('acao')
        
        count = 0
        
        # 1. Adicionar Manual
        if acao == 'manual':
            nomes = request.POST.get('lista_nomes', '').split('\n')
            for nome in nomes:
                if nome.strip():
                    DocumentoEmitido.objects.create(projeto=projeto, nome_beneficiario=nome.strip())
                    count += 1
                    
        # 2. Importar Funcionários
        elif acao == 'funcionarios':
            sector_id = request.POST.get('sector')
            funcs = Funcionario.objects.filter(ativo=True)
            if sector_id:
                funcs = funcs.filter(sector_id=sector_id)
            
            for f in funcs:
                DocumentoEmitido.objects.get_or_create(
                    projeto=projeto, 
                    nome_beneficiario=f.nome_completo,
                    defaults={'detalhe_extra': f.funcao}
                )
                count += 1

        # 3. Importar Formandos (DFEC)
        elif acao == 'dfec':
            evento_id = request.POST.get('evento')
            # Busca credenciais desse evento
            creds = CredencialEmitida.objects.filter(pedido__evento_id=evento_id)
            for c in creds:
                nome = c.pedido.solicitante.nome_completo
                # Evitar duplicatas no projeto
                DocumentoEmitido.objects.get_or_create(projeto=projeto, nome_beneficiario=nome)
                count += 1
            
            # Fonte 2: DFEC Direto (Caso não tenha credenciais emitidas ainda)
            if DFEC_AVAILABLE:
                evento = Evento.objects.get(id=evento_id)
                
                # Estratégia de Busca Resiliente
                # Formato Esperado: "[DFEC] Tipo: Nome"
                termo_busca = evento.nome
                if ':' in evento.nome:
                    # Pega a parte do nome real (após o primeiro :)
                    termo_busca = evento.nome.split(':', 1)[1].strip()
                else:
                    termo_busca = evento.nome.replace('[DFEC]', '').replace('Formação', '').strip()

                # Busca Formação
                formacao_match = Formacao.objects.filter(nome__icontains=termo_busca).first()
                # Fallback: Tenta buscar inverso (se nome do evento estiver contido no nome da formação)
                if not formacao_match:
                     formacao_match = Formacao.objects.filter(nome__icontains=termo_busca.split(' ')[0]).first()

                if formacao_match:
                    # Busca participantes desta formação específica
                    # Usa related_name='participantes' definido em dfec.models.completo
                    parts = formacao_match.participantes.all()
                    
                    # Se vazio, tenta filtro explícito (redundância)
                    if not parts.exists():
                        parts = Participante.objects.filter(formacao=formacao_match)

                    count_dfec = 0
                    for p in parts:
                        # Verifica se nome_beneficiario já existe neste projeto
                        if not DocumentoEmitido.objects.filter(projeto=projeto, nome_beneficiario=p.nome_completo).exists():
                            DocumentoEmitido.objects.create(
                                projeto=projeto, 
                                nome_beneficiario=p.nome_completo,
                                detalhe_extra=f"{formacao_match.nome}"
                            )
                            count_dfec += 1
                    
                    count += count_dfec
                    if count_dfec > 0:
                        messages.success(request, f"Sucesso: {count_dfec} participantes importados da formação '{formacao_match.nome}'.")
                    else:
                        messages.warning(request, f"Conexão OK com '{formacao_match.nome}', mas não há participantes cadastrados nela.")
                else:
                    messages.error(request, f"Erro: Não foi encontrada a Formação original para '{termo_busca}'. Verifique se o nome corresponde no DFEC.")

        
        messages.success(request, f"{count} beneficiários adicionados.")
        
        # Define tab ativa baseada na ação
        active_tab = 'manual'
        if acao == 'funcionarios': active_tab = 'rh'
        elif acao == 'dfec': active_tab = 'dfec'
        
        return redirect(reverse('credenciais:cert_beneficiarios', kwargs={'projeto_id': projeto.id}) + f'?tab={active_tab}')

    # Contexto para filtros
    active_tab = request.GET.get('tab', 'manual')
    sectores = Sector.objects.filter(ativo=True)
    eventos = Evento.objects.filter(ativo=True).order_by('-data_inicio')
    beneficiarios = projeto.documentos.all().order_by('-id')

    return render(request, 'credenciais/certificados/beneficiarios.html', {
        'projeto': projeto,
        'sectores': sectores,
        'eventos': eventos,
        'beneficiarios': beneficiarios,
        'active_tab': active_tab
    })

@login_required
def baixar_pdf_unico(request, doc_id):
    doc = get_object_or_404(DocumentoEmitido, id=doc_id)
    pdf = gerar_pdf_certificado(doc)
    if not pdf:
        return HttpResponse("Erro ao gerar PDF", status=500)
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'filename="certificado_{slugify(doc.nome_beneficiario)}.pdf"'
    return response

@login_required
def baixar_lote_certificado(request, projeto_id):
    projeto = get_object_or_404(ProjetoCertificacao, id=projeto_id)
    docs = projeto.documentos.all()
    
    buffer_zip = BytesIO()
    with zipfile.ZipFile(buffer_zip, 'w') as zf:
        for doc in docs:
            pdf = gerar_pdf_certificado(doc)
            if pdf:
                nome = f"{slugify(doc.nome_beneficiario)}_{doc.id}.pdf"
                zf.writestr(nome, pdf)
    
    buffer_zip.seek(0)
    response = HttpResponse(buffer_zip, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="diplomas_{slugify(projeto.nome)}.zip"'
    return response

@login_required
def remover_beneficiario(request, doc_id):
    doc = get_object_or_404(DocumentoEmitido, id=doc_id)
    proj_id = doc.projeto.id
    doc.delete()
    messages.success(request, "Removido.")
    return redirect('credenciais:cert_beneficiarios', projeto_id=proj_id)
