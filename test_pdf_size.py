import sys
from xhtml2pdf import pisa
from io import BytesIO

def test_size(name, css_size):
    print(f"Testing {name} with rule: {css_size}")
    html = f"""
    <html>
    <head>
        <style>
            @page {{
                {css_size}
                margin: 1cm;
                background-color: #eee;
            }}
            body {{ font-family: sans-serif; }}
        </style>
    </head>
    <body>
        <h1>Teste de Tamanho: {name}</h1>
        <p>Se você consegue ler isso, o PDF foi gerado.</p>
    </body>
    </html>
    """
    
    output = BytesIO()
    try:
        pisa_status = pisa.CreatePDF(html, dest=output)
        if pisa_status.err:
            print(f"FAILED: {name} (Pisa Error)")
        else:
            print(f"SUCCESS: {name}")
            with open(f"test_{name}.pdf", "wb") as f:
                f.write(output.getvalue())
    except Exception as e:
        print(f"CRASH: {name} - {str(e)}")

if __name__ == "__main__":
    # Test 1: CM Dimensions
    test_size("cm", "size: 10.5cm 17.8cm;")
    
    # Test 2: Point Dimensions
    test_size("pt", "size: 297pt 504pt;")
    
    # Test 3: Named + Portrait
    test_size("a5_portrait", "size: a5 portrait;")
    
    # Test 4: Named Only
    test_size("a5_simple", "size: a5;")
