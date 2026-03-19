from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.text import slugify
from django.db import transaction
from .models import Evento, PedidoCredencial, CredencialEmitida, Solicitante, TipoCredencial, ModeloCredencial
from .utils_pdf import gerar_pdf_cartao_credencial
import uuid
import zipfile
from io import BytesIO
from django.http import HttpResponse
try:
    from dfec.models.completo import Formacao, Participante
    DFEC_AVAILABLE = True
except ImportError:
    DFEC_AVAILABLE = False


def is_admin_dfec(user):
    return user.is_staff

@login_required
@user_passes_test(is_admin_dfec)
def dashboard_dfec(request):
    """Listagem de Cursos/Eventos de Formação"""
    eventos = Evento.objects.filter(categoria='formacao').order_by('-data_inicio')
    return render(request, 'credenciais/dfec/dashboard.html', {'eventos': eventos})


@login_required
@user_passes_test(is_admin_dfec)
def detalhe_curso(request, evento_id):
    """Lista de participantes de um curso"""
    evento = get_object_or_404(Evento, id=evento_id)
    # Buscar credenciais emitidas para este evento
    credenciais = CredencialEmitida.objects.filter(
        pedido__evento=evento
    ).select_related('pedido__solicitante', 'pedido__tipo_credencial')
    
    return render(request, 'credenciais/dfec/detalhe_curso.html', {
        'evento': evento,
        'credenciais': credenciais
    })


@login_required
@user_passes_test(is_admin_dfec)
@transaction.atomic
def inscrever_lote(request, evento_id):
    """Inscrição em massa de formandos/formadores"""
    evento = get_object_or_404(Evento, id=evento_id)
    
    # Lógica de Importação Automática
    # Lógica de Importação Automática
    candidatos_dfec = []
    formacao_match = None
    if DFEC_AVAILABLE:
        # Estratégia de Busca Resiliente (Sincronizada com views_certificados)
        termo_busca = evento.nome
        if ':' in evento.nome:
            termo_busca = evento.nome.split(':', 1)[1].strip()
        else:
            termo_busca = evento.nome.replace('[DFEC]', '').replace('Formação', '').strip()
            
        formacao_match = Formacao.objects.filter(nome__icontains=termo_busca).first()
        if not formacao_match:
             # Fallback
             formacao_match = Formacao.objects.filter(nome__icontains=termo_busca.split(' ')[0]).first()

    if request.method == 'POST':
        if 'importar_dfec' in request.POST and DFEC_AVAILABLE:
            # Importar do DFEC
            count_imported = 0
            
            novos_participantes = []
            if formacao_match:
                # Busca participantes desta formação específica
                novos_participantes = formacao_match.participantes.all()
                if not novos_participantes.exists():
                    novos_participantes = Participante.objects.filter(formacao=formacao_match)
            
            # Se ainda vazio, tenta fallback global (mas avisa)
            if not novos_participantes:
                # Fallback removido para evitar dados incorretos, melhor avisar o user
                messages.warning(request, f"Formação '{termo_busca}' encontrada, mas sem participantes vinculados no DFEC.")
                return redirect('credenciais:dfec_detalhe_curso', evento_id=evento.id)

            modelo_padrao = ModeloCredencial.objects.filter(ativo=True).first() or ModeloCredencial.objects.create(nome="Padrão", ativo=True)
            tipo_obj, _ = TipoCredencial.objects.get_or_create(nome="Formando DFEC", defaults={'cor':'#28a745'})
            
            modelo_padrao = ModeloCredencial.objects.filter(ativo=True).first() or ModeloCredencial.objects.create(nome="Padrão", ativo=True)
            tipo_obj, _ = TipoCredencial.objects.get_or_create(nome="Formando DFEC", defaults={'cor':'#28a745'})

            for p in novos_participantes:
                # Verifica duplicidade
                if PedidoCredencial.objects.filter(evento=evento, solicitante__numero_bi=p.bilhete_identidade).exists():
                    continue

                solicitante, _ = Solicitante.objects.get_or_create(
                    numero_bi=p.bilhete_identidade,
                    defaults={
                        'nome_completo': p.nome_completo,
                        'email': f"{slugify(p.nome_completo)}@stae.local",
                        'tipo': 'singular',
                        'nacionalidade': 'Moçambicana',
                        'telefone': p.telefone or 'N/A'
                    }
                )

                pedido = PedidoCredencial.objects.create(
                    solicitante=solicitante,
                    tipo_credencial=tipo_obj,
                    evento=evento,
                    status='emitido',
                    motivo='Importação Automática DFEC',
                    data_inicio=evento.data_inicio,
                    data_fim=evento.data_fim
                )
                
                num_cred = f"DFEC-AUTO-{pedido.id}"
                CredencialEmitida.objects.create(
                    pedido=pedido,
                    modelo=modelo_padrao,
                    numero_credencial=num_cred,
                    data_validade=evento.data_fim,
                    status='ativa'
                )
                count_imported += 1
            
            messages.success(request, f'{count_imported} participantes importados do DFEC!')
            return redirect('credenciais:dfec_detalhe_curso', evento_id=evento.id)


        nomes_texto = request.POST.get('nomes', '')
        tipo_participante = request.POST.get('tipo', 'Formando') # Nome exato do Tipo
        
        # Garantir TipoCredencial
        tipo_obj, _ = TipoCredencial.objects.get_or_create(
            nome=tipo_participante,
            defaults={
                'cor': '#28a745' if 'Formando' in tipo_participante else '#007bff',
                'descricao': 'Participante de Formação DFEC'
            }
        )
        
        # Garantir Modelo Padrão
        modelo_padrao = ModeloCredencial.objects.filter(ativo=True).first()
        if not modelo_padrao:
             modelo_padrao = ModeloCredencial.objects.create(nome="Padrão", ativo=True)

        nomes = [n.strip() for n in nomes_texto.replace('\r', '').split('\n') if n.strip()]
        criados = 0
        
        for nome in nomes:
            # 1. Criar Solicitante (Participante)
            # Usar identificador único no email para permitir homônimos em cursos diferentes
            uid = str(uuid.uuid4())[:8]
            email_dummy = f"{slugify(nome)}.{uid}@interno.stae"
            
            solicitante = Solicitante.objects.create(
                nome_completo=nome,
                email=email_dummy,
                tipo='singular',
                nacionalidade='Moçambicana',
                telefone='N/A'
            )
            
            # 2. Criar Pedido
            pedido = PedidoCredencial.objects.create(
                solicitante=solicitante,
                tipo_credencial=tipo_obj,
                evento=evento,
                status='emitido', # Direto para emitido
                motivo='Inscrição DFEC em Lote',
                criado_por=request.user,
                data_inicio=evento.data_inicio,
                data_fim=evento.data_fim
            )
            
            # 3. Emitir Credencial
            # Gerar número sequencial único
            num_cred = f"DFEC-{evento.id}-{uid.upper()}"
            
            CredencialEmitida.objects.create(
                pedido=pedido,
                modelo=modelo_padrao,
                numero_credencial=num_cred,
                data_validade=evento.data_fim,
                status='ativa',
                emitida_por=request.user
            )
            criados += 1
            
        messages.success(request, f'{criados} participantes inscritos com sucesso!')
        return redirect('credenciais:dfec_detalhe_curso', evento_id=evento.id)

    return render(request, 'credenciais/dfec/inscricao_form.html', {
        'evento': evento,
        'dfec_available': DFEC_AVAILABLE,
        'formacao_match': formacao_match
    })


@login_required
def imprimir_lista_presenca(request, evento_id):
    """Gera PDF da lista de participantes"""
    # ... Implementar ReportLab table ...
    return HttpResponse("PDF Lista em Construção")

@login_required
def baixar_todas_credenciais(request, evento_id):
    """Baixa ZIP com todos os PDFs de credenciais do evento"""
    evento = get_object_or_404(Evento, id=evento_id)
    credenciais = CredencialEmitida.objects.filter(pedido__evento=evento)
    
    buffer_zip = BytesIO()
    with zipfile.ZipFile(buffer_zip, 'w') as zf:
        for cred in credenciais:
            # Força o cabeçalho oficial do STAE
            pdf_bytes = gerar_pdf_cartao_credencial(cred, extra_context={'entidade': 'stae'})
            nome_arq = f"{slugify(cred.pedido.solicitante.nome_completo)}_{cred.numero_credencial}.pdf"
            zf.writestr(nome_arq, pdf_bytes)
            
    buffer_zip.seek(0)
    response = HttpResponse(buffer_zip, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="credenciais_{slugify(evento.nome)}.zip"'
    return response
