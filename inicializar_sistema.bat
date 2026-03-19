@echo off
TITLE Portal STAE - Inicializador de Sistema
COLOR 0A
CLS

echo ========================================================
echo   PORTAL STAE - INICIALIZADOR DE SISTEMA
echo   Soberania e Transparencia Eleitoral
echo ========================================================
echo.

:: 1. Verificação do Ambiente Python
echo [1/5] Verificando ambiente Python...
if not exist "venv/Scripts/python.exe" (
    echo [ERRO] Ambiente virtual nao encontrado!
    echo Por favor, crie o venv ou verifique o caminho.
    PAUSE
    EXIT
)
echo [OK] Ambiente virtual detectado.
echo.

:: 2. Aplicação de Migrações Pendentes
echo [2/5] Verificando integridade da base de dados...
venv\Scripts\python.exe manage.py makemigrations
venv\Scripts\python.exe manage.py migrate
echo [OK] Base de dados sincronizada.
echo.

:: 3. Sincronização de Templates e Documentos de Soberania
echo [3/5] Restaurando padroes de Soberania Documental...
venv\Scripts\python.exe manage.py shell -c "from rs.views import inicializar_docs_padrao; from django.test import RequestFactory; factory = RequestFactory(); request = factory.get('/'); inicializar_docs_padrao(request); print('  > Templates de Soberania: OK')"
echo [OK] Documentos oficiais prontos.
echo.

:: 4. Sincronização de Logística 360 (35+ Itens)
echo [4/5] Atualizando Plano Logistico Nacional...
venv\Scripts\python.exe manage.py shell -c "from eleicao.models import Eleicao; from rs.logic import sync_plano_logistico; e = Eleicao.objects.filter(ativo=True).first(); sync_plano_logistico(e); print(f'  > Logistica Sincronizada para: {e.nome if e else 'N/A'}')"
echo [OK] Plano Logistico atualizado.
echo.

:: 5. Início do Servidor
echo [5/5] Iniciando o servidor...
echo.
echo ========================================================
echo   SISTEMA PRONTO - ACESSE: http://localhost:8000
echo ========================================================
echo.
venv\Scripts\python.exe manage.py runserver 8000

PAUSE
