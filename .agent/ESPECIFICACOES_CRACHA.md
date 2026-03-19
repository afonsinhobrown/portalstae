# ESPECIFICAÇÕES TÉCNICAS - CRACHÁ PVC (CR80 Portrait)
# ======================================================
# Data: 2025-12-29
# Template: templates/credenciais/cartao_pvc.html
# Motor: xhtml2pdf (ReportLab backend)

## DIMENSÕES GERAIS
- **Tamanho da Página**: 54mm x 86mm (CR80 Portrait)
- **Margens**: 0 (página completa)
- **Padding Interno**: 1mm

## CABEÇALHO
- **Altura**: 8mm
- **Cor Fundo STAE**: #003366 (Azul)
- **Cor Fundo CNE**: #d9534f (Vermelho)
- **Cor Texto**: Branco
- **Padding**: 1.5mm
- **Linha 1**: "República de Moçambique" - 5pt
- **Linha 2**: Nome Completo da Entidade - 6pt, bold, uppercase, line-height: 1.2

## FOTO
- **Largura**: 23mm
- **Altura**: 30mm
- **Borda**: 1px solid #000
- **Fundo**: #f0f0f0
- **Alinhamento**: Centralizada (margin: 0 auto)
- **Comportamento**: max-width/max-height com auto para preservar aspect ratio
- **Placeholder**: c:\Users\Acer\Documents\tecnologias\portalstae\static\img\silhouette_placeholder.png

## NOME
- **Tamanho Fonte**: 10pt
- **Peso**: Bold
- **Transformação**: Uppercase
- **Cor**: #000
- **Margin**: 0
- **Alinhamento**: Left
- **Truncamento**: 28 caracteres

## LINHAS SEPARADORAS
- **Linha Grossa**: 1px, #000, width: 30mm, margin: 0.5mm 0
- **Linha Fina**: 0.5px, #ccc, width: 30mm, margin: 0.5mm 0

## DETALHES (Tabela Interna)
### Estrutura
- **Width**: 100%
- **Border-collapse**: collapse
- **Margin**: 0

### Coluna Esquerda (Texto)
- **Width**: 38mm
- **Vertical-align**: top
- **Padding**: 0

#### ID
- **Tamanho Fonte**: 7pt
- **Peso**: Bold
- **Cor**: #333
- **Margin**: 0

#### Departamento
- **Tamanho Fonte**: 8pt
- **Peso**: Bold
- **Cor**: #000
- **Transformação**: Uppercase
- **Margin**: 0
- **Truncamento**: 18 caracteres

#### Evento
- **Tamanho Fonte**: 4pt
- **Cor**: #666
- **Margin**: 0
- **Truncamento**: 30 caracteres

### Coluna Direita (QR Code)
- **Vertical-align**: top
- **Text-align**: right
- **Padding**: 0

#### QR Code
- **Largura**: 10mm
- **Altura**: 10mm
- **Borda**: 1px solid #ccc
- **Geração Dinâmica**: Biblioteca `qrcode`, version=1, box_size=10, border=1
- **Dados**: "CREDENCIAL:{numero_credencial}"

## RODAPÉ
- **Altura**: 6mm
- **Cor Fundo**: Mesma do cabeçalho (#003366 ou #d9534f)
- **Cor Texto**: Branco
- **Padding**: 2mm
- **Text-align**: Center
- **Tamanho Fonte**: 8pt
- **Peso**: Bold
- **Transformação**: Uppercase
- **Truncamento**: 25 caracteres

## NOTAS TÉCNICAS
1. **xhtml2pdf não suporta**:
   - CSS Flexbox
   - Pseudo-elementos (:before, :after)
   - border-radius (renderização inconsistente)
   - Posicionamento com `bottom` (usar `top` calculado)
   - `{% static %}` tags (usar caminhos absolutos)

2. **Usar sempre**:
   - Tables para layout lado-a-lado
   - Estilos inline para elementos críticos
   - Dimensões em mm (não %, não vh/vw)
   - Paths absolutos do filesystem (.path, não .url)

3. **Geração de Fallbacks**:
   - Foto ausente: c:\Users\Acer\Documents\tecnologias\portalstae\static\img\silhouette_placeholder.png
   - QR ausente: Gerar dinamicamente em `utils_pdf.py` linha 91-126

## ARQUIVOS RELACIONADOS
- Template: `templates/credenciais/cartao_pvc.html`
- Geração PDF: `credenciais/utils_pdf.py` função `gerar_pdf_cartao_credencial()`
- Preview: `gerar_preview.py`
- Silhueta: `static/img/silhouette_placeholder.png`
