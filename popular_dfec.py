# popular_dfec.py
import os
import django
import random
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

from dfec.models.completo import ObjetivoInstitucional, PlanoAtividade, Atividade, Formacao, Participante
from django.contrib.auth.models import User

def populate():
    print("Iniciando povoamento de dados DFEC...")
    
    # 1. Usuário admin se não existir
    admin, _ = User.objects.get_or_create(username='admin', is_staff=True, is_superuser=True)
    if _: admin.set_password('admin123'); admin.save()

    # 2. Objetivo Institucional
    obj, _ = ObjetivoInstitucional.objects.get_or_create(
        ano=2024,
        titulo="Expansão Nacional da Educação Cívica Eleitoral",
        descricao="Garantir que 90% da população tenha acesso a informação eleitoral de qualidade.",
        ativo=True
    )

    # 3. Plano Nacional
    plano_nac, _ = PlanoAtividade.objects.get_or_create(
        nome="Plano Central de Educação Cívica 2024",
        objetivo_institucional=obj,
        nivel='CENTRAL',
        tipo="Educação Cívica",
        data_inicio_planeada=date(2024, 1, 1),
        data_fim_planeada=date(2024, 12, 31),
        responsavel_principal=admin,
        orcamento_planeado=5000000.00
    )

    # 4. Atividade Nacional de Formação
    at_nac, _ = Atividade.objects.get_or_create(
        plano=plano_nac,
        nome="Formação Nacional de Formadores",
        data_inicio=date(2024, 2, 1),
        data_fim=date(2024, 2, 28),
        orcamento_estimado=200000.00,
        status='aprovado'
    )

    # 5. Plano Provincial (Gaza)
    plano_prov, _ = PlanoAtividade.objects.get_or_create(
        nome="Plano Operacional Gaza 2024",
        objetivo_institucional=obj,
        nivel='PROVINCIAL',
        provincia='GAZA',
        plano_pai=plano_nac,
        tipo="Educação Cívica",
        data_inicio_planeada=date(2024, 3, 1),
        data_fim_planeada=date(2024, 11, 30),
        responsavel_principal=admin
    )

    # 6. Atividade Provincial (Gaza)
    at_prov, _ = Atividade.objects.get_or_create(
        plano=plano_prov,
        nome="Formação de Brigadistas de Gaza",
        referencia_nacional=at_nac,
        data_inicio=date(2024, 3, 15),
        data_fim=date(2024, 4, 15),
        status='planejado'
    )

    # 7. Formação Específica
    formacao, _ = Formacao.objects.get_or_create(
        atividade=at_prov,
        nome="Treinamento Intensivo Gaza - Fase 1",
        nivel='PROVINCIAL',
        provincia='GAZA',
        tipo_formacao="Técnico-Operacional",
        vagas_planeadas=200,
        status='ativa'
    )

    # 8. Participantes (120 pessoas para testar turmas de 60)
    nomes = ["João", "Maria", "António", "Isabel", "Manuel", "Ana", "Francisco", "Teresa", "José", "Helena", "Titos", "Luísa", "Armando", "Bernardo", "Catarina", "Daniel", "Eunice", "Filipe", "Gisela", "Humberto"]
    apelidos = ["Mabunda", "Langa", "Sitoe", "Tembe", "Matusse", "Chivambo", "Nhaca", "Cuamba", " Mondlane", "Chissano"]
    categorias = ['BRIGADISTA', 'MMV', 'AGENTE_EC']

    print(f"Gerando 120 participantes para a formação {formacao.nome}...")
    for i in range(120):
        genero = 'M' if i % 2 == 0 else 'F'
        nome_completo = f"{random.choice(nomes)} {random.choice(apelidos)} {random.choice(apelidos)} ({i})"
        
        # Data de nascimento aleatória (entre 18 e 50 anos)
        hoje = date.today()
        nasc = hoje - timedelta(days=random.randint(18*365, 50*365))
        
        Participante.objects.create(
            formacao=formacao,
            nome_completo=nome_completo,
            categoria=random.choice(categorias),
            bilhete_identidade=f"1200{i:05d}",
            telefone=f"84{random.randint(1000000, 9999999)}",
            genero=genero,
            data_nascimento=nasc,
            provincia='GAZA',
            distrito="XAI-XAI"
        )

    print("População concluída com sucesso!")

if __name__ == '__main__':
    populate()
