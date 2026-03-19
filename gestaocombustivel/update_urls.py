
# Script Adiciona URLs
caminho = 'gestaocombustivel/urls.py'
with open(caminho, 'r', encoding='utf-8') as f:
    content = f.read()

url_novas = """
    # Oficinas e Contratos Manutenção
    path('manutencao/oficinas/', views.lista_oficinas, name='lista_oficinas'),
    path('manutencao/oficinas/nova/', views.nova_oficina, name='nova_oficina'),
    path('manutencao/contratos/', views.lista_contratos_manutencao, name='lista_contratos_manutencao'),
    path('manutencao/contratos/novo/', views.novo_contrato_manutencao, name='novo_contrato_manutencao'),
"""

if "lista_oficinas" not in content:
    content = content.replace("    # Rotas", url_novas + "\n    # Rotas")
    
with open(caminho, 'w', encoding='utf-8') as f:
    f.write(content)
