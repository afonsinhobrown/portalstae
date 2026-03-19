import pypdf
import os

pdf_path = r"c:\Users\Acer\Documents\tecnologias\portalstae\meus docs\Manual-de-procedimentos-do-EGFAE.pdf"
output_file = "extracted_model.txt"

if not os.path.exists(pdf_path):
    print("File not found!")
    exit(1)

try:
    reader = pypdf.PdfReader(pdf_path)
    print(f"Total pages: {len(reader.pages)}")
    
    with open(output_file, "w", encoding="utf-8") as f:
        for i, page in enumerate(reader.pages):
            try:
                text = page.extract_text()
                if not text:
                    continue
                    
                # Search for keywords
                lower_text = text.lower()
                if "licença" in lower_text and ("modelo" in lower_text or "anexo" in lower_text or "pedido" in lower_text):
                    f.write(f"\n--- Possible Model found on Page {i+1} ---\n")
                    f.write(text)
                    f.write("\n" + "-" * 50 + "\n")
            except Exception as e:
                print(f"Error on page {i+1}: {e}")

    print(f"Extraction complete. Check {output_file}")

except Exception as e:
    print(f"Error reading PDF: {e}")
