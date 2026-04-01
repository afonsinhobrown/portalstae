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

:: 2. Verificação de Base de Dados (Otimizado)
echo [2/5] Ignorando migrações automatizadas para velocidade máxima...
:: venv\Scripts\python.exe manage.py migrate --noinput
echo [OK] Pronto para iniciar.
echo.

:: 3. Sincronização de Templates (Otimizado)
echo [3/5] Pulando sincronização de templates para arranque instantâneo...
:: venv\Scripts\python.exe manage.py shell -c "..."
echo [OK] Pronto.
echo.

:: 4. Sincronização de Logística 360 (35+ Itens)
:: echo [4/5] Atualizando Plano Logistico Nacional...
:: venv\Scripts\python.exe manage.py shell -c "from eleicao.models import Eleicao; from rs.logic import sync_plano_logistico; e = Eleicao.objects.filter(ativo=True).first(); sync_plano_logistico(e); print(f'  > Logistica Sincronizada para: {e.nome if e else 'N/A'}')"
:: echo [OK] Plano Logistico atualizado.
:: echo.

:: 5. Início do Servidor
echo [5/5] Iniciando o servidor...
echo.
echo ========================================================
echo   SISTEMA PRONTO - ACESSE: http://localhost:8000
echo ========================================================
echo.
venv\Scripts\python.exe manage.py runserver 8000

PAUSE
