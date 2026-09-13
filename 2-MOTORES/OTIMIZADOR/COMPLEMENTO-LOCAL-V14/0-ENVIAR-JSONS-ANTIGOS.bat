@echo off
setlocal
cd /d "%~dp0..\OPERACAO-LOCAL-JSON"
echo Envie os resultados antigos com o PROCESSADOR parado.
echo Resultados e recibos existentes serao preservados.
"bin\OperacaoLocalJson.exe" enviar
set "codigo=%ERRORLEVEL%"
if not "%codigo%"=="0" goto falha
echo Envio encerrado. Agora abra os botoes 1 e 2 do COMPLEMENTO-LOCAL-V14.
goto fim
:falha
echo O envio encontrou erro. Nao inicie a correcao antes de resolver.
:fim
pause
exit /b %codigo%
