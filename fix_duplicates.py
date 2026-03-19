# fix_duplicates.py
import os
import django
import sys

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')  # Ajuste para seu settings
django.setup()

from recursoshumanos.models import DocumentoInstitucional
from django.db.models import Count
from django.db import connection
import datetime

print("=== CORREÇÃO DE DUPLICATAS numero_completo ===")

# 1. Verificar se a coluna existe
with connection.cursor() as cursor:
    cursor.execute("PRAGMA table_info(recursoshumanos_documentoinstitucional)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'numero_completo' not in columns:
        print("❌ ERRO: A coluna 'numero_completo' não existe na tabela!")
        print("Colunas existentes:", columns)
        print("\nPor favor, aplique as migrações primeiro:")
        print("python manage.py migrate")
        sys.exit(1)
    else:
        print("✅ Coluna 'numero_completo' encontrada na tabela")

# 2. Verificar duplicatas usando SQL direto (mais seguro)
print("\n🔍 Buscando duplicatas...")

with connection.cursor() as cursor:
    cursor.execute("""
        SELECT numero_completo, COUNT(*) as count
        FROM recursoshumanos_documentoinstitucional
        WHERE numero_completo != '' AND numero_completo IS NOT NULL
        GROUP BY numero_completo
        HAVING COUNT(*) > 1
        ORDER BY numero_completo
    """)
    duplicatas = cursor.fetchall()

if not duplicatas:
    print("✅ Nenhuma duplicata encontrada!")
else:
    print(f"📊 Encontradas {len(duplicatas)} duplicatas")

    for numero, count in duplicatas:
        print(f"\n📄 Processando: {numero} ({count} ocorrências)")

        # Obter todos os documentos com este número
        documentos = DocumentoInstitucional.objects.filter(numero_completo=numero).order_by('id')

        if documentos.count() <= 1:
            print("  ✅ Nenhuma correção necessária")
            continue

        # Manter o primeiro (menor ID)
        primeiro = documentos[0]
        print(f"  ✅ Mantendo documento ID {primeiro.id}: {primeiro.titulo[:30]}...")

        # Para cada documento adicional
        for i, doc in enumerate(documentos[1:], start=1):
            print(f"  🔄 Corrigindo documento ID {doc.id}: {doc.titulo[:30]}...")

            # Extrair informações
            ano = doc.data_documento.year
            sigla_tipo = doc.tipo.codigo.upper()[:4] if doc.tipo else 'DOC'

            # Encontrar próximo número sequencial disponível
            ultimo = DocumentoInstitucional.objects.filter(
                tipo=doc.tipo,
                data_documento__year=ano
            ).exclude(numero_completo=numero).aggregate(max_seq=Count('id'))

            ultimo_num = ultimo['max_seq'] or 0
            novo_sequencial = ultimo_num + 1

            # Gerar novo número único
            novo_numero = f"STAE-{sigla_tipo}-{ano}-{novo_sequencial:04d}"

            # Verificar se já existe (segurança extra)
            tentativas = 0
            while DocumentoInstitucional.objects.filter(numero_completo=novo_numero).exists():
                novo_sequencial += 1
                novo_numero = f"STAE-{sigla_tipo}-{ano}-{novo_sequencial:04d}"
                tentativas += 1

                if tentativas > 50:
                    timestamp = datetime.datetime.now().strftime('%H%M%S')
                    novo_numero = f"STAE-{sigla_tipo}-{ano}-{novo_sequencial:04d}-{timestamp}"
                    break

            # Atualizar documento
            doc.numero_sequencial = novo_sequencial
            doc.numero_completo = novo_numero
            doc.save(update_fields=['numero_sequencial', 'numero_completo'])

            print(f"    📝 Novo número: {novo_numero}")

print("\n🎉 Processo de correção concluído!")

# 3. Verificação final
print("\n🔍 Verificando se ainda há duplicatas...")

with connection.cursor() as cursor:
    cursor.execute("""
        SELECT COUNT(*) as dups_count
        FROM (
            SELECT numero_completo, COUNT(*) as count
            FROM recursoshumanos_documentoinstitucional
            WHERE numero_completo != '' AND numero_completo IS NOT NULL
            GROUP BY numero_completo
            HAVING COUNT(*) > 1
        ) as dups
    """)
    dups_restantes = cursor.fetchone()[0]

if dups_restantes == 0:
    print("✅ Perfeito! Não há mais duplicatas!")
else:
    print(f"⚠️  Atenção: Ainda há {dups_restantes} duplicatas")

# 4. Contagem final
total_docs = DocumentoInstitucional.objects.count()
print(f"\n📊 Estatísticas finais:")
print(f"   Total de documentos: {total_docs}")
print(f"   Duplicatas restantes: {dups_restantes}")