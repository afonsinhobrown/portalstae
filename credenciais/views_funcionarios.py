from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.http import HttpResponse
from .models import Evento, PedidoCredencial, CredencialEmitida, Solicitante, TipoCredencial, ModeloCredencial
from .utils_pdf import gerar_pdf_cartao_credencial
from recursoshumanos.models import Funcionario, Sector
import zipfile
from io import BytesIO
from django.utils.text import slugify

def is_admin_credencial(user):
    return user.is_staff

@login_required
@user_passes_test(is_admin_credencial)
def configurar_emissao_lote(request):
    """Página de configuração para emissão em massa para funcionários"""
    eventos = Evento.objects.filter(ativo=True).order_by('-data_inicio')
    sectores = Sector.objects.filter(ativo=True).order_by('nome')
    
    return render(request, 'credenciais/funcionarios/configurar_lote.html', {
        'eventos': eventos,
        'sectores': sectores
    })

@login_required
@user_passes_test(is_admin_credencial)
def processar_emissao_lote(request):
    """Processa a emissão e gera o ZIP"""
    if request.method != 'POST':
        return redirect('credenciais:func_configurar_lote')

    evento_id = request.POST.get('evento')
    sector_id = request.POST.get('sector')
    
    evento = get_object_or_404(Evento, id=evento_id)
    
    # Filtra funcionários
    funcionarios = Funcionario.objects.filter(ativo=True)
    if sector_id:
        funcionarios = funcionarios.filter(sector_id=sector_id)
    
    if not funcionarios.exists():
        messages.error(request, 'Nenhum funcionário encontrado para os critérios selecionados.')
        return redirect('credenciais:func_configurar_lote')

    # Configuração Visual (Interactive Fields)
    config = {
        'mostrar_nome': 'show_nome' in request.POST,
        'mostrar_cargo': 'show_cargo' in request.POST,
        'mostrar_sector': 'show_sector' in request.POST,
        'mostrar_qr': 'show_qr' in request.POST,
        'texto_livre_topo': request.POST.get('texto_topo', ''),
        'texto_livre_rodape': request.POST.get('texto_rodape', ''),
        'entidade': request.POST.get('entidade', 'cne'),
        'cor_fundo': request.POST.get('cor_fundo', '#ffffff')
    }
    
    # Prepara ZIP
    buffer_zip = BytesIO()
    count_sucesso = 0
    
    # Tipo e Modelo padrão
    tipo_cred, _ = TipoCredencial.objects.get_or_create(nome="Staff STAE", defaults={'cor': '#343a40'})
    modelo_padrao = ModeloCredencial.objects.filter(ativo=True).first()
    
    with zipfile.ZipFile(buffer_zip, 'w') as zf:
        for func in funcionarios:
            try:
                # 1. Garantir Solicitante
                email = func.email_institucional or f"{func.numero_identificacao}@stae.local"
                solicitante, _ = Solicitante.objects.get_or_create(
                    email=email,
                    defaults={
                        'nome_completo': func.nome_completo,
                        'numero_bi': func.numero_bi,
                        'telefone': func.telefone,
                        'tipo': 'instituicao',
                        'nome_empresa': 'STAE'
                    }
                )
                
                # 2. Garantir Pedido (Evita duplicatas para o mesmo evento)
                pedido, _ = PedidoCredencial.objects.get_or_create(
                    solicitante=solicitante,
                    evento=evento,
                    defaults={
                        'tipo_credencial': tipo_cred,
                        'status': 'emitido',
                        'motivo': 'Emissão em Lote Funcionários',
                        'data_inicio': evento.data_inicio,
                        'data_fim': evento.data_fim,
                        'quantidade': 1
                    }
                )
                
                # 3. Garantir Credencial
                credencial, created = CredencialEmitida.objects.get_or_create(
                    pedido=pedido,
                    defaults={
                        'modelo': modelo_padrao,
                        'numero_credencial': f"STAE-{evento.id}-{func.numero_identificacao}",
                        'data_validade': evento.data_fim,
                        'status': 'ativa'
                    }
                )

                # 4. Gerar PDF com Configuração Personalizada
                # Passamos o funcionário no contexto extra para pegar dados como 'Sector' atualizado, 
                # caso o solicitante esteja desatualizado.
                extra_context = {
                    'config': config,
                    'funcionario_real': func # Dados frescos do RH
                }
                
                pdf_bytes = gerar_pdf_cartao_credencial(credencial, extra_context=extra_context)
                
                filename = f"{slugify(func.nome_completo)}_{func.numero_identificacao}.pdf"
                zf.writestr(filename, pdf_bytes)
                count_sucesso += 1
                
            except Exception as e:
                print(f"Erro ao processar {func}: {e}")
                continue

    if count_sucesso == 0:
        messages.error(request, "Erro ao gerar arquivos. Verifique os logs.")
        return redirect('credenciais:func_configurar_lote')

    buffer_zip.seek(0)
    response = HttpResponse(buffer_zip, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="credenciais_stae_{slugify(evento.nome)}.zip"'
    return response
