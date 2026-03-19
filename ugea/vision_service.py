try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False

from PIL import Image
import re
import os

class VisionService:
    @staticmethod
    def extrair_texto(image_path):
        """Usa o motor Tesseract real instalado no sistema."""
        if not PYTESSERACT_AVAILABLE:
            return "AVISO: Motor de Visão (Tesseract) não instalado neste servidor. Carregue os dados manualmente."
            
        try:
            # Caminho oficial
            tess_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            pytesseract.pytesseract.tesseract_cmd = tess_cmd
            
            # Caminho absoluto e limpo para o tessdata
            tessdata_dir = os.path.normpath(os.path.abspath(os.path.join(os.path.dirname(__file__), 'tessdata')))
            
            # Define a variável de ambiente necessária pelo motor
            os.environ['TESSDATA_PREFIX'] = tessdata_dir
            
            # Executa sem a flag redundante config se o PREFIX já estiver setado, 
            # ou garante que a flag não tenha barras duplas problemáticas.
            text = pytesseract.image_to_string(
                Image.open(image_path), 
                lang='por'
            )
            return text
        except Exception as e:
            return f"ERRO CRÍTICO NO MOTOR DE VISÃO: {str(e)}"

    @staticmethod
    def analisar_proposta(texto_completo):
        """
        Analisa o texto usando BUSCA GLOBAL (Heurística).
        Preparado para documentos longos (30+ pág) onde a info pode estar em qualquer lugar.
        """
        # Limpeza e normalização
        t_low = texto_completo.lower()
        t_clean = re.sub(r'\s+', ' ', t_low) # Remove quebras de linha ruidosas para busca contínua

        dados = {
            'entidade': 'Não identificada',
            'valor': 0.0,
            'prazo_execucao': 0,
            'administrativo': {},
            'tecnico': {},
            'financeiro': {},
            'alertas': []
        }

        # --- 1. IDENTIFICAÇÃO DE ENTIDADE (Busca em cascata) ---
        # Prioriza a primeira menção de Empresa/Concorrente
        patterns_entidade = [
            r"proposta\s*-\s*empresa\s*([a-z0-9\s]+)",
            r"empresa\s*([a-z0-9\s]+)\s*vem",
            r"entidade\s*proponente[:\s-]*([a-z0-9\s]+)"
        ]
        for p in patterns_entidade:
            match = re.search(p, t_clean)
            if match:
                dados['entidade'] = match.group(1).strip().upper()
                break

        # --- 2. ÁREA FINANCEIRA (Valor e IVA) ---
        # Captura valores monetários próximos a palavras de preço/total
        # Busca o valor mais provável (normalmente o maior valor perto de 'total')
        valor_match = re.search(r"(?:preço|valor|total|proposto)\s*.*?([\d\.]+,\d{2})\s*mt", t_clean)
        if valor_match:
            valor_str = valor_match.group(1).replace('.', '').replace(',', '.')
            dados['valor'] = float(valor_str)
            dados['financeiro']['Valor Proposto'] = f"{valor_match.group(1)} MT"
        
        if "iva incluído" in t_clean or "com iva" in t_clean:
            dados['financeiro']['IVA'] = "✅ IVA Incluído"
        else:
            dados['financeiro']['IVA'] = "⚠ Não especificado ou Sem IVA"

        # --- 3. ÁREA TÉCNICA (Especificações em qualquer lugar) ---
        keywords_tecnicas = {
            'Material': [r"material[:\s-]*([a-z\s]+)", r"urna\s*em\s*([a-z\s]+)"],
            'Dimensões/Altura': [r"(?:altura|dimensões)(?:\s+mínima)?[:\s-]*([\d\.,]+\s*[a-z]+)", r"dimensões[:\s-]*([a-z0-9\sx\.,]+)"]
        }
        
        for label, patterns in keywords_tecnicas.items():
            for p in patterns:
                match = re.search(p, t_clean)
                if match:
                    dados['tecnico'][label] = match.group(1).strip().capitalize()
                    break

        # Captura genérica de especificações (bullet points)
        specs_gen_match = re.findall(r"-\s*([^;:\.]+)", t_low)
        if specs_gen_match:
            for i, spec in enumerate(specs_gen_match[:5]): # Captura as primeiras 5 specs
                if len(spec.strip()) > 3:
                    dados['tecnico'][f'Detecção {i+1}'] = spec.strip().capitalize()

        # --- 4. CHECKLIST ADMINISTRATIVO ... (código existente sugerido para continuar aqui) ---
        # ...
        
        # --- 5. OBSERVAÇÕES E ALERTAS TÉCNICOS ---
        obsv_patterns = [
            r"observação[:\s-]*([^:\.]+)",
            r"nota[:\s-]*([^:\.]+)",
            r"prazo\s+de\s+execução\s+proposto\s+excede\s+([^:\.]+)"
        ]
        for p in obsv_patterns:
            match = re.search(p, t_clean)
            if match:
                obs_text = match.group(0).strip().capitalize()
                dados['alertas'].append(f"⚠️ {obs_text}")

        # --- 6. CHECKLIST ADMINISTRATIVO (Busca de Presença/Omissão) ---
        docs = {
            'Registo Comercial': ['registo comercial', 'certidão de registo'],
            'Quitação INSS': ['inss'],
            'Quitação Finanças': ['finanças', 'quitacao fiscal'],
            'Garantia Provisória': ['garantia provisória', 'caução', '500.000']
        }
        
        for doc, keys in docs.items():
            encontrado = any(k in t_clean for k in keys)
            negacao = any(f"não {k}" in t_clean or f"sem {k}" in t_clean or f"não apresentada" in t_clean for k in keys)
            
            if encontrado and not negacao:
                dados['administrativo'][doc] = "✅ OK"
            elif negacao:
                dados['administrativo'][doc] = "❌ FALTA/RECUSA"
                dados['alertas'].append(f"Omissão declarada: {doc}")
            else:
                dados['administrativo'][doc] = "❓ NÃO LOCALIZADO"
                dados['alertas'].append(f"Não detectado automaticamente: {doc}")

        # --- 7. PRAZOS ---
        prazo_match = re.search(r"prazo\s*.*?(\d+)\s*dias", t_clean)
        if prazo_match:
            dados['prazo_execucao'] = int(prazo_match.group(1))
            dados['financeiro']['Prazo'] = f"{dados['prazo_execucao']} dias"

        return dados
