
try:
    with open('gestaocombustivel/models.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    removed = 0
    for line in lines:
        if line.strip() == '"':
            removed += 1
            continue
        new_lines.append(line)
    
    with open('gestaocombustivel/models.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
        
    print(f"Sucesso: {removed} linhas com aspas removidas.")
except Exception as e:
    print(f"Erro: {e}")
