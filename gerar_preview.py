import os
import django
import sys

# Setup Django Environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

from credenciais.models import CredencialEmitida
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from io import BytesIO
import qrcode

try:
    # GERA QR CODE TEMPORÁRIO
    qr_data = "CREDENCIAL:STAE000001"
    qr = qrcode.QRCode(version=1, box_size=10, border=1)
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Salva QR temporário
    qr_path = os.path.join(os.getcwd(), 'temp_qr.png')
    qr_img.save(qr_path)
    print(f"QR Code gerado em: {qr_path}")
    
    # FORÇA uso de placeholder
    class MockQRCode:
        path = qr_path
    
    class MockSolicitante:
        nome_completo = "NOME EXEMPLO"
        foto = None
    
    class MockPedido:
        solicitante = MockSolicitante()
        tipo_credencial = type('obj', (object,), {'nome': 'Participante'})()
        evento = type('obj', (object,), {'nome': 'SIMULAÇÃO RECENSEAMENTO ELEITORAL'})()
    
    class MockCredencial:
        numero_credencial = "STAE000001"
        pedido = MockPedido()
        qr_code = MockQRCode()
    
    mock_cred = MockCredencial()
    
    context = {
        'credencial': mock_cred,
        'funcionario_real': type('obj', (object,), {
            'nome_completo': 'GUIMARAES PINTO COSSA',
            'foto': None,
            'funcao': 'IMPRENSA',
            'sector': None
        })(),
        'config': {'entidade': 'stae'}
    }
    
    html = render_to_string('credenciais/cartao_pvc.html', context)
    
    buffer = BytesIO()
    pisa_status = pisa.CreatePDF(html.encode('UTF-8'), dest=buffer, encoding='UTF-8')
    
    if pisa_status.err:
        print(f"Erro: {pisa_status.err}")
    else:
        pdf = buffer.getvalue()
        buffer.close()
        
        with open('CRACHA_NOVO_LAYOUT.pdf', 'wb') as f:
            f.write(pdf)
        
        print("SUCESSO: Arquivo 'CRACHA_NOVO_LAYOUT.pdf' gerado na raiz do projeto.")
    
    # Limpa QR temporário
    if os.path.exists(qr_path):
        os.remove(qr_path)
        
except Exception as e:
    import traceback
    print(f"ERRO CRÍTICO: {str(e)}")
    traceback.print_exc()
