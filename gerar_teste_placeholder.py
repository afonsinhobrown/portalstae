import os
import django
import sys

# Setup Django Environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

from credenciais.models import CredencialEmitida
from credenciais.utils_pdf import gerar_pdf_cartao_credencial

try:
    # Busca primeira credencial que tenha solicitante
    cred = CredencialEmitida.objects.filter(pedido__solicitante__isnull=False).first()
    
    if cred:
        print(f"Credencial encontrada: {cred.numero_credencial}")
        print(f"Solicitante: {cred.pedido.solicitante.nome_completo}")
        
        # REMOVE foto e QR para forçar geração dinâmica
        cred.pedido.solicitante.foto = None
        cred.pedido.solicitante.save()
        
        if cred.qr_code:
            cred.qr_code.delete()
            cred.qr_code = None
            cred.save()
        
        print("Foto e QR removidos para teste.")
        
        # Gerar PDF com placeholder e QR dinâmico
        pdf_content = gerar_pdf_cartao_credencial(cred, extra_context={'config': {'entidade': 'stae'}})
        
        output_filename = 'CRACHA_TESTE_PLACEHOLDER.pdf'
        with open(output_filename, 'wb') as f:
            f.write(pdf_content)
        
        print(f"SUCESSO: Arquivo '{output_filename}' gerado na raiz do projeto.")
    else:
        print("ERRO: Nenhuma credencial encontrada no banco de dados.")
except Exception as e:
    import traceback
    print(f"ERRO CRÍTICO: {str(e)}")
    traceback.print_exc()
