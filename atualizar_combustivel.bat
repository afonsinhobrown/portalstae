@echo off
echo ===================================================
echo   ATUALIZACAO DO SISTEMA - GESTAO DE COMBUSTIVEL
echo ===================================================
echo.
echo Passo 1: Criando arquivos de migracao (NIF -> NUIT, Contratos)...
python manage.py makemigrations gestaocombustivel
if %errorlevel% neq 0 (
    echo [ERRO] Falha ao criar migracoes. Verifique se o servidor esta parado.
    pause
    exit /b %errorlevel%
)

echo.
echo Passo 2: Aplicando alteracoes no Banco de Dados...
python manage.py migrate gestaocombustivel
if %errorlevel% neq 0 (
    echo [ERRO] Falha ao aplicar migracoes.
    pause
    exit /b %errorlevel%
)

echo.
echo Passo 3: Limpando dados antigos incompativeis...
python manage.py limpar_pedidos_combustivel

echo.
echo ===================================================
echo   SUCESSO! O sistema esta atualizado.
echo   Pode iniciar o servidor com: python manage.py runserver
echo ===================================================
pause
