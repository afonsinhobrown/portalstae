
try:
    with open('gestaocombustivel/models.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "from django.contrib.auth.models import User" not in content:
        content = "from django.contrib.auth.models import User\n" + content
    
    with open('gestaocombustivel/models.py', 'w', encoding='utf-8') as f:
        f.write(content)
        
    print("Imports corrigidos.")
except Exception as e:
    print(f"Erro: {e}")
