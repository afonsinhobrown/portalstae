# PADRÃO OBRIGATÓRIO - CRACHÁ CREDENCIAL
# ========================================
# TODAS as gerações de crachá PVC DEVEM seguir estas especificações

## TEMPLATE OFICIAL
**Arquivo**: `templates/credenciais/cartao_pvc.html`
**Formato**: CR80 Portrait (54mm x 86mm)
**Motor PDF**: xhtml2pdf (ReportLab backend)

## LOCAIS DE USO (TODOS DEVEM ESTAR SINCRONIZADOS)
1. `credenciais/utils_pdf.py` - Função `gerar_pdf_cartao_credencial()` (linha 90-147)
2. `credenciais/utils_pdf.py` - Função `gerar_imagem_cartao()` (linha 163)
3. `credenciais/views.py` - View de geração manual (linha 1821)

## DIMENSÕES FIXAS (MÁXIMAS - IGUAIS OU MENORES)

### Página
- **54mm x 86mm** (Portrait)
- **Margins**: 0

### Header
- **Altura**: 8mm
- **Cores**: STAE=#003366 | CNE=#d9534f
- **Fonte Linha 1**: 5pt
- **Fonte Linha 2**: 6pt bold uppercase

### Foto
- **MAX 23mm x 30mm** (nunca maior)
- **Fallback**: `c:\Users\Acer\Documents\tecnologias\portalstae\static\img\silhouette_placeholder.png`

### Nome
- **10pt bold uppercase**
- **Truncar**: 28 caracteres

### QR Code
- **MAX 10mm x 10mm** (nunca maior)
- **Geração dinâmica**: Se ausente, gerar em `utils_pdf.py` (linhas 101-136)
- **Formato**: "CREDENCIAL:{numero_credencial}"

### Footer
- **Altura**: 6mm
- **Fonte**: 8pt bold uppercase center
- **Truncar**: 25 caracteres

## REGRAS OBRIGATÓRIAS

### 1. COMPONENTES COMPLETOS
**NENHUM crachá pode ser emitido sem TODOS os componentes:**
- Header (com texto entidade completo)
- Foto ou Placeholder
- Nome
- Detalhes (ID, Departamento, Evento)
- QR Code (gerado dinamicamente se ausente)
- Footer

### 2. DIMENSÕES MÁXIMAS
- Foto: **≤ 23mm x 30mm**
- QR Code: **≤ 10mm x 10mm**
- Textos: **Sempre com `truncatechars`**

### 3. TRUNCAMENTO AUTOMÁTICO
Todos os textos variáveis devem usar `truncatechars:N`:
- Nome: 28
- Departamento: 18
- Evento: 30
- Footer/Função: 25

### 4. PATHS ABSOLUTOS
xhtml2pdf NÃO suporta `{% static %}`. Usar:
```html
<img src="c:\Users\Acer\Documents\tecnologias\portalstae\static\img\silhouette_placeholder.png" />
```

### 5. GERAÇÃO DINÂMICA DE QR
Se `credencial.qr_code` estiver vazio, gerar automaticamente em `utils_pdf.py`:
```python
if not credencial.qr_code:
    # Gerar QR com qrcode lib
    # Salvar em credencial.qr_code
```

## TESTES OBRIGATÓRIOS
Antes de qualquer deploy:
1. Executar `python gerar_preview.py`
2. Verificar `CRACHA_NOVO_LAYOUT.pdf`:
   - Silhueta visível?
   - QR code visível?
   - Todos componentes presentes?
   - Tudo em 1 página?

## HISTÓRICO
- 2025-12-29: Especificação inicial após finalização do layout
