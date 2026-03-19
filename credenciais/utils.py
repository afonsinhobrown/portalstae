"""
Utilitários para o sistema de credenciais
"""

from io import BytesIO
from reportlab.lib.pagesizes import A4, mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
import os
from django.conf import settings
from datetime import datetime
import qrcode
from PIL import Image as PILImage
from django.core.files.base import ContentFile
import tempfile


def gerar_qr_code_pil(texto, tamanho=10):
    """Gerar QR code usando PIL (para salvar no modelo)"""
    qr_img = qrcode.make(texto, box_size=tamanho)

    # Converter para bytes
    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    qr_img.save(temp_file, format='PNG')
    temp_file.seek(0)

    return ContentFile(temp_file.read(), name=f'qr_{datetime.now().timestamp()}.png')


def criar_template_pdf_credencial(credencial, tipo='normal'):
    """Função auxiliar para criar templates de PDF"""
    # Esta função está agora implementada diretamente nas views
    # Mantida para compatibilidade
    pass


def formatar_data_br(data):
    """Formatar data no padrão brasileiro"""
    return data.strftime("%d/%m/%Y")


def formatar_data_hora_br(data_hora):
    """Formatar data e hora no padrão brasileiro"""
    return data_hora.strftime("%d/%m/%Y %H:%M")


def gerar_nome_arquivo_credencial(credencial, extensao='pdf'):
    """Gerar nome de arquivo padronizado para credencial"""
    numero_limpo = credencial.numero_credencial.replace('/', '_').replace('\\', '_')
    return f"credencial_{numero_limpo}.{extensao}"


def validar_codigo_offline(codigo):
    """Validar formato do código offline"""
    if not codigo or len(codigo) < 10:
        return False

    # Verificar se tem formato correto (ex: STAE000123-ABC123)
    parts = codigo.split('-')
    if len(parts) != 2:
        return False

    numero, verificador = parts
    return len(numero) >= 6 and len(verificador) >= 3