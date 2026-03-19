from django.shortcuts import get_object_or_404
from django.conf import settings
from django.core.files.base import ContentFile
from django.http import HttpResponse
from datetime import date

# ReportLab Imports
from reportlab.lib.pagesizes import A4, mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing

# HTML to PDF/Image Imports
from django.template.loader import render_to_string
from io import BytesIO
import os

# =============================================================================
# GERAÇÃO DE PDF (FORMAL - REPORTLAB)
# =============================================================================

def gerar_pdf_credencial(credencial):
    """Gera PDF formal da credencial (A4) usando ReportLab"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Cabeçalho
    if settings.LOGO_PATH and os.path.exists(settings.LOGO_PATH):
        img_path = settings.LOGO_PATH
    else:
        # Fallback se não tiver logo configurado, tenta path relativo
        img_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo_stae.png')
    
    if os.path.exists(img_path):
        logo = Image(img_path, width=1.5*inch, height=1.5*inch)
        logo.hAlign = 'CENTER'
        elements.append(logo)
    
    elements.append(Spacer(1, 0.2*inch))
    
    # Título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        alignment=1, # Center
        spaceAfter=20
    )
    elements.append(Paragraph("CREDENCIAL DE ACESSO", title_style))
    
    # Dados Principais
    elements.append(Paragraph(f"<b>Nº Credencial:</b> {credencial.numero_credencial}", styles['Normal']))
    elements.append(Paragraph(f"<b>Nome:</b> {credencial.pedido.solicitante.nome_completo}", styles['Normal']))
    elements.append(Paragraph(f"<b>Função/Categoria:</b> {credencial.pedido.tipo_credencial.nome}", styles['Normal']))
    
    if credencial.pedido.evento:
        elements.append(Paragraph(f"<b>Evento:</b> {credencial.pedido.evento.nome}", styles['Normal']))
    
    elements.append(Spacer(1, 0.5*inch))
    
    # QR Code
    if credencial.codigo_verificacao:
        qr_code = qr.QrCodeWidget(f"VERIFY:{credencial.codigo_verificacao}")
        qr_code.barWidth = 35 * mm
        qr_code.barHeight = 35 * mm
        qr_code.qrVersion = 1
        d = Drawing(45*mm, 45*mm)
        d.add(qr_code)
        elements.append(d)
        elements.append(Paragraph(f"<font size=8>Verificação: {credencial.codigo_verificacao}</font>", styles['Normal']))

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

def gerar_pdf_credencial_funcionario(credencial):
    """Gera PDF para funcionário (Layout específico)"""
    # Simplificação: Reutiliza a lógica básica por enquanto, mas separado para permitir customização futura
    return gerar_pdf_credencial(credencial)

# =============================================================================
# GERAÇÃO DE CARTÃO (VISUAL - XHTML2PDF / PISA)
# =============================================================================

def gerar_pdf_cartao_credencial(credencial, extra_context=None):
    """Gera PDF renderizando o template HTML do cartão (xhtml2pdf)"""
    from django.template.loader import render_to_string
    from xhtml2pdf import pisa
    import qrcode
    from io import BytesIO
    from PIL import Image as PILImage
    
    # Renderiza o template 'cartao_pvc.html'
    template_name = 'credenciais/cartao_pvc.html'
    
    # ==== GERAÇÃO DINÂMICA DE QR CODE ====
    if not credencial.qr_code:
        # Gera QR code dinamicamente
        qr_data = f"CREDENCIAL:{credencial.numero_credencial}"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=1,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Salva em BytesIO e depois no modelo
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        # Salva no modelo
        credencial.qr_code.save(
            f'qr_{credencial.numero_credencial}.png',
            ContentFile(qr_buffer.read()),
            save=True
        )
    
    # ==== PLACEHOLDER DE FOTO ====
    placeholder_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'silhouette_placeholder.png')
    
    # Contexto
    context = {
        'credencial': credencial,
        'placeholder_foto': placeholder_path if os.path.exists(placeholder_path) else None
    }
    if extra_context:
        context.update(extra_context)

    html = render_to_string(template_name, context)

    buffer = BytesIO()
    # Gera PDF
    pisa_status = pisa.CreatePDF(html.encode('UTF-8'), dest=buffer, encoding='UTF-8')
    
    if pisa_status.err:
        raise Exception("Erro ao gerar PDF do cartão com xhtml2pdf")
        
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

# =============================================================================
# EXPORTAÇÃO DE IMAGEM (IMGKIT)
# =============================================================================

def gerar_imagem_cartao(credencial):
    """Gera PNG do cartão usando imgkit (wkhtmltoimage wrapper)"""
    try:
        import imgkit
    except ImportError:
        return None

    html_content = render_to_string('credenciais/cartao_pvc.html', {
        'credencial': credencial,
        'config': {'entidade': 'stae'}
    })

    
    options = {
        'format': 'png',
        'width': 340,  # CR-80 width approx pixels @ 96dpi ? Ajustar conforme necessário
        'quality': 100,
        'disable-smart-width': ''
    }
    
    try:
        # Nota: imgkit requer wkhtmltopdf instalado no sistema
        img = imgkit.from_string(html_content, False, options=options)
        return img
    except Exception as e:
        print(f"Erro imgkit: {e}")
        return None


# =============================================================================
# GERAÇÃO DE CERTIFICADOS
# =============================================================================

def gerar_pdf_certificado(documento):
    """Gera PDF de certificado/diploma (Landscape)"""
    from django.template.loader import render_to_string
    from xhtml2pdf import pisa
    
    template_name = 'credenciais/certificados/template_base.html'
    
    # Processar Texto (Substituição simples de variáveis no texto do corpo)
    texto_final = documento.projeto.texto_corpo.replace('{{ nome }}', f"<b>{documento.nome_beneficiario}</b>")
    if documento.detalhe_extra:
        texto_final = texto_final.replace('{{ detalhe }}', documento.detalhe_extra)
    else:
        texto_final = texto_final.replace('{{ detalhe }}', "")
    
    context = {
        'documento': documento,
        'projeto': documento.projeto,
        'texto_corpo_processado': texto_final,
        'data_hoje': date.today()
    }

    html = render_to_string(template_name, context)
    buffer = BytesIO()
    # landscape handling is done via CSS inside the template
    pisa_status = pisa.CreatePDF(html.encode('UTF-8'), dest=buffer, encoding='UTF-8')

    if pisa_status.err:
        return None
    return buffer.getvalue()
