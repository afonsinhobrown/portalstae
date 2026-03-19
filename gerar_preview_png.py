from PIL import Image, ImageDraw, ImageFont
import qrcode
import os

# Dimensões CR80 Portrait em pixels @ 300 DPI
WIDTH = 638  # 54mm
HEIGHT = 1016  # 86mm

# Cores
STAE_BLUE = (0, 51, 102)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (102, 102, 102)
LIGHT_GRAY = (240, 240, 240)

# Criar imagem
img = Image.new('RGB', (WIDTH, HEIGHT), WHITE)
draw = ImageDraw.Draw(img)

# Fonts (usar default, depois melhorar)
try:
    font_header_small = ImageFont.truetype("arial.ttf", 16)
    font_header_large = ImageFont.truetype("arialbd.ttf", 20)
    font_name = ImageFont.truetype("arialbd.ttf", 35)
    font_id = ImageFont.truetype("arialbd.ttf", 24)
    font_dept = ImageFont.truetype("arialbd.ttf", 28)
    font_event = ImageFont.truetype("arial.ttf", 18)
    font_footer = ImageFont.truetype("arialbd.ttf", 28)
except:
    font_header_small = ImageFont.load_default()
    font_header_large = ImageFont.load_default()
    font_name = ImageFont.load_default()
    font_id = ImageFont.load_default()
    font_dept = ImageFont.load_default()
    font_event = ImageFont.load_default()
    font_footer = ImageFont.load_default()

# HEADER (8mm = 95px @ 300dpi)
header_height = 95
draw.rectangle([0, 0, WIDTH, header_height], fill=STAE_BLUE)
draw.text((WIDTH//2, 25), "República de Moçambique", fill=WHITE, font=font_header_small, anchor="mm")
draw.text((WIDTH//2, 60), "Secretariado Técnico de Administração Eleitoral", fill=WHITE, font=font_header_large, anchor="mm")

# FOTO (23mm x 30mm = 272px x 354px @ 300dpi)
y_current = header_height + 25
silhouette_path = r'c:\Users\Acer\Documents\tecnologias\portalstae\static\img\silhouette_placeholder.png'
if os.path.exists(silhouette_path):
    foto = Image.open(silhouette_path).resize((272, 354))
    img.paste(foto, (25, y_current))
else:
    # Desenhar retângulo de placeholder
    draw.rectangle([25, y_current, 25+272, y_current+354], outline=BLACK, fill=LIGHT_GRAY)

y_current += 354 + 15

# LINHA
draw.line([25, y_current, WIDTH//2, y_current], fill=BLACK, width=2)
y_current += 10

# NOME
draw.text((25, y_current), "GUIMARAES PINTO COSSA", fill=BLACK, font=font_name)
y_current += 45

# LINHA FINA
draw.line([25, y_current, WIDTH//2, y_current], fill=GRAY, width=1)
y_current += 15

# DETALHES + QR (lado a lado)
# QR Code (10mm = 118px @ 300dpi)
qr_data = "CREDENCIAL:STAE000001"
qr = qrcode.QRCode(version=1, box_size=10, border=1)
qr.add_data(qr_data)
qr.make(fit=True)
qr_img = qr.make_image(fill_color="black", back_color="white")
qr_resized = qr_img.resize((118, 118))

# Posicionar QR no canto direito
qr_x = WIDTH - 118 - 25
qr_y = y_current
img.paste(qr_resized, (qr_x, qr_y))

# ID
draw.text((25, y_current), "ID: STAE000001", fill=BLACK, font=font_id)
y_current += 35

# DEPARTAMENTO
draw.text((25, y_current), "MARKETING", fill=BLACK, font=font_dept)
y_current += 40

# EVENTO
draw.text((25, y_current), "SIMULAÇÃO RECENSEAMENTO ELEIT...", fill=GRAY, font=font_event)

# FOOTER (6mm = 71px @ 300dpi)
footer_y = HEIGHT - 71
draw.rectangle([0, footer_y, WIDTH, HEIGHT], fill=STAE_BLUE)
draw.text((WIDTH//2, footer_y + 35), "IMPRENSA", fill=WHITE, font=font_footer, anchor="mm")

# Salvar
img.save('CRACHA_NOVO_LAYOUT.png')
print("SUCESSO: Arquivo 'CRACHA_NOVO_LAYOUT.png' gerado na raiz do projeto.")
