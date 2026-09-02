@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

echo.
echo ============================================================
echo  5 - ADOTAR E REPARAR ESTA PASTA
echo ============================================================
echo.
echo Reescreve TODOS os arquivos a partir do GitHub aplicando as
echo regras de fim de linha do .gitattributes. Nada que nao esteja
echo no GitHub e apagado: config.txt e RESULTADOS-JSON ficam como
echo estao.
echo.

echo ---- instalando os arquivos do GitHub...
git checkout -f -B main origin/main
if errorlevel 1 goto ERRO

rem O git guarda data e tamanho de cada arquivo e nao percebe sozinho que a
rem regra de fim de linha mudou. Tirar tudo do indice e trazer de volta
rem obriga a releitura. E o que faz a FORMULA_APROVADA e o sha256 do pacote
rem selado voltarem a bater numa copia que ja veio convertida.
echo ---- reescrevendo tudo sem conversao de fim de linha...
git rm --cached -r -q .
if errorlevel 1 goto ERRO
git checkout -f HEAD -- .
if errorlevel 1 goto ERRO

git remote set-url origin https://github.com/luisferps/ClubEFootball-.git

echo.
echo ============================================================
echo  PRONTO
echo ============================================================
for /f "delims=" %%H in ('git rev-parse HEAD 2^>nul') do echo Commit instalado: %%H
echo.
echo Agora abra PROCESSAR-FILA-PRINCIPAL.bat em
echo 2-MOTORES\OTIMIZADOR\OPERACAO-LOCAL-JSON
echo.
pause
exit /b 0

:ERRO
echo.
echo ============================================================
echo  NAO DEU
echo ============================================================
echo Manda esta tela para o Claude.
echo.
pause
exit /b 1
