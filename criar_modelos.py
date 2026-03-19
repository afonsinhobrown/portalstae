# Script para criar modelos de credencial com diferentes tamanhos
# Execute: python manage.py shell < criar_modelos.py

from credenciais.models import ModeloCredencial

# Tamanhos padrão de cartões
tamanhos = [
    {
        'nome': 'Modelo STAE Padrão (ID-1)',
        'descricao': 'Tamanho padrão internacional ID-1 (cartão de crédito)',
        'tamanho': '85x54',
        'cor_fundo': '#ffffff',
        'cor_texto': '#000000'
    },
    {
        'nome': 'Modelo STAE Compacto (ID-000)',
        'descricao': 'Tamanho compacto ID-000',
        'tamanho': '66x45',
        'cor_fundo': '#ffffff',
        'cor_texto': '#000000'
    },
    {
        'nome': 'Modelo STAE Grande (ID-2)',
        'descricao': 'Tamanho grande ID-2',
        'tamanho': '105x74',
        'cor_fundo': '#ffffff',
        'cor_texto': '#000000'
    },
    {
        'nome': 'Modelo STAE Extra Grande (ID-3)',
        'descricao': 'Tamanho extra grande ID-3',
        'tamanho': '125x88',
        'cor_fundo': '#ffffff',
        'cor_texto': '#000000'
    },
    {
        'nome': 'Modelo STAE Crachá Vertical',
        'descricao': 'Crachá vertical para eventos',
        'tamanho': '54x85',
        'cor_fundo': '#ffffff',
        'cor_texto': '#000000'
    },
    {
        'nome': 'Modelo STAE Crachá Horizontal',
        'descricao': 'Crachá horizontal para eventos',
        'tamanho': '100x70',
        'cor_fundo': '#ffffff',
        'cor_texto': '#000000'
    }
]

print("Criando modelos de credencial...")
for modelo_data in tamanhos:
    modelo, created = ModeloCredencial.objects.get_or_create(
        nome=modelo_data['nome'],
        defaults={
            'descricao': modelo_data['descricao'],
            'tamanho': modelo_data['tamanho'],
            'cor_fundo': modelo_data['cor_fundo'],
            'cor_texto': modelo_data['cor_texto'],
            'ativo': True
        }
    )
    if created:
        print(f"✓ Criado: {modelo.nome} ({modelo.tamanho}mm)")
    else:
        print(f"- Já existe: {modelo.nome} ({modelo.tamanho}mm)")

print(f"\nTotal de modelos ativos: {ModeloCredencial.objects.filter(ativo=True).count()}")
