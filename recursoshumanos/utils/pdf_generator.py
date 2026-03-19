import os
from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa
from django.conf import settings

def render_pdf(template_src, context_dict={}):
    """
    Renderiza um template HTML para PDF e retorna o HttpResponse com o PDF.
    """
    template = get_template(template_src)
    html = template.render(context_dict)
    
    response = HttpResponse(content_type='application/pdf')
    # Se quiser baixar, descomente a linha abaixo e dê um nome ao arquivo
    # response['Content-Disposition'] = 'attachment; filename="relatorio.pdf"'
    
    # Criar o PDF
    pisa_status = pisa.CreatePDF(
        html, dest=response, link_callback=link_callback
    )
    
    if pisa_status.err:
        return HttpResponse('Tivemos alguns erros <pre>' + html + '</pre>')
        
    return response

def link_callback(uri, rel):
    """
    Converte URLs relativos (estáticos/media) para caminhos absolutos do sistema
    para que o xhtml2pdf consiga encontrar as imagens/css.
    """
    sUrl = settings.STATIC_URL        # Tipicamente /static/
    sRoot = settings.STATIC_ROOT      # Caminho absoluto
    mUrl = settings.MEDIA_URL         # Tipicamente /media/
    mRoot = settings.MEDIA_ROOT       # Caminho absoluto

    if uri.startswith(mUrl):
        path = os.path.join(mRoot, uri.replace(mUrl, ""))
    elif uri.startswith(sUrl):
        path = os.path.join(sRoot, uri.replace(sUrl, ""))
    else:
        return uri

    # Garantir que o arquivo existe
    if not os.path.isfile(path):
        raise Exception(f'Media URI must start with {sUrl} or {mUrl}')
        
    return path

def render_pdf_file(template_src, context_dict={}):
    """
    Renderiza um template HTML para PDF e retorna os bytes do arquivo.
    Usado para salvar em FileField.
    """
    from io import BytesIO
    template = get_template(template_src)
    html = template.render(context_dict)
    
    result = BytesIO()
    
    # Criar o PDF
    pisa_status = pisa.CreatePDF(
        html, dest=result, link_callback=link_callback
    )
    
    if pisa_status.err:
        return None
        
    return result.getvalue()
