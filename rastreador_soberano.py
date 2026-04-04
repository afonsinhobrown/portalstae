import os

def buscar_string(termo):
    print(f"--- RASTREADOR SOBERANO: Procurando por '{termo}' ---")
    encontrado = False
    extensoes = ('.py', '.json', '.html', '.txt', '.js', '.css')
    
    for root, dirs, files in os.walk('.'):
        if 'venv' in root or '.git' in root or '__pycache__' in root:
            continue
            
        for file in files:
            if file.endswith(extensoes):
                path = os.path.join(root, file)
                try:
                    # Tentar UTF-8 primeiro
                    with open(path, 'r', encoding='utf-8') as f:
                        if termo in f.read():
                            print(f"[OK] ENCONTRADO EM: {path}")
                            encontrado = True
                except:
                    try:
                        # Tentar UTF-16 (para ficheiros Windows)
                        with open(path, 'r', encoding='utf-16') as f:
                            if termo in f.read():
                                print(f"[OK] ENCONTRADO EM: {path} (UTF-16)")
                                encontrado = True
                    except:
                        pass
    
    if not encontrado:
        print("A string não foi encontrada em ficheiros de texto.")

if __name__ == "__main__":
    buscar_string("AUTARQUIAS 2028")
    buscar_string("AUTARQUIAS 2023")
