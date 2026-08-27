@echo off
chcp 65001 > nul
title SUBIR PRO GITHUB - ClubEfootball
cd /d "%~dp0"
if not exist "config.txt" cd ..
if not exist "config.txt" (
  echo.
  echo   ^>^> nao achei o config.txt nem aqui nem na pasta de cima.
  echo.
  pause
  exit /b 1
)
cls
echo.
echo  ================================================================
echo    SUBIR PRO GITHUB   -   ClubEfootball
echo  ================================================================
echo.
echo    O .gitignore filtra sozinho. Medido na sua pasta:
echo       sobem .......  372 arquivos     18,6 MB
echo       ficam fora ..  367 arquivos  1.472,0 MB
echo.
echo    O config.txt NAO sobe. Este programa PARA se ele aparecer.
echo.
echo  ----------------------------------------------------------------

git --version > nul 2>&1
if errorlevel 1 goto :sem_git
for /f "delims=" %%v in ('git --version') do echo    git ................ %%v

findstr /c:"ClubEfootball" .gitignore > nul 2>&1
if errorlevel 1 goto :gitignore_velho
echo    .gitignore ......... o novo, de 16/08

if exist "github.txt" goto :tem_url
echo.
echo  ----------------------------------------------------------------
echo    PRIMEIRA VEZ - preciso da URL do repositorio.
echo  ----------------------------------------------------------------
echo.
echo    1. Abra:  https://github.com/new
echo    2. Repository name:  ClubEfootball
echo    3. Marque PRIVATE
echo    4. NAO marque nada em "Initialize this repository with"
echo    5. Clique em Create repository
echo    6. Copie a URL, do tipo:
echo         https://github.com/SEU-USUARIO/ClubEfootball.git
echo.
set /p REPO=   Cole a URL aqui e de Enter: 
>github.txt echo %REPO%
echo.

:tem_url
set /p REPO=<github.txt
echo    repositorio ........ %REPO%

git config user.name  > nul 2>&1 || git config user.name  "Luis Fernando"
git config user.email > nul 2>&1 || git config user.email "luis.soares.177@gmail.com"

if exist ".git" goto :tem_repo
echo.
echo    criando o repositorio local...
git init > nul
git branch -M main > nul 2>&1

:tem_repo
echo.
echo  ----------------------------------------------------------------
echo    Separando o que sobe...
echo  ----------------------------------------------------------------
git add -A
if errorlevel 1 goto :add_falhou

git diff --cached --name-only > O-QUE-VAI-SUBIR.txt
findstr /x /c:"config.txt" O-QUE-VAI-SUBIR.txt > nul
if not errorlevel 1 goto :segredo

echo    ok - o config.txt NAO esta na lista
for /f %%n in ('find /c /v "" ^< O-QUE-VAI-SUBIR.txt') do echo    arquivos que vao subir .... %%n
echo.
echo    A lista inteira ficou em  O-QUE-VAI-SUBIR.txt
echo    (abre com dois cliques, e um arquivo de texto)
echo.
echo  ----------------------------------------------------------------
echo    Confira o numero acima. Se estiver estranho, feche a janela
echo    AGORA - nada foi enviado ainda.
echo  ----------------------------------------------------------------
pause

echo.
git commit -m "ClubEfootball: o sistema inteiro, com a reforma de 16/08" > nul 2>&1
if errorlevel 1 echo    (nada novo para gravar - seguindo para o envio)

git remote remove origin > nul 2>&1
git remote add origin %REPO%
echo.
echo    enviando...
echo.
echo    ^>^> Se abrir uma janela do navegador pedindo login do GitHub,
echo       faca o login por la. Voce NAO digita senha nesta janela.
echo.
git push -u origin main
if errorlevel 1 goto :push_falhou

echo.
echo  ================================================================
echo    PRONTO. O sistema esta no GitHub.
echo  ================================================================
echo.
echo    %REPO%
echo.
echo    Daqui pra frente, toda vez que quiser mandar o que mudou,
echo    e so clicar neste mesmo arquivo.
echo.
pause
exit /b 0

:sem_git
echo.
echo   ^>^> O GIT NAO ESTA INSTALADO nesta maquina.
echo.
echo      Baixe em:  https://git-scm.com/download/win
echo      Instale com TODAS as opcoes no padrao, feche esta janela
echo      e clique aqui de novo.
echo.
pause
exit /b 1

:gitignore_velho
echo.
echo   ^>^> O .gitignore desta pasta ainda e o antigo, de 08/08.
echo      Ele deixa passar 371 MB. PAREI antes de fazer besteira.
echo.
echo      Coloque o .gitignore novo nesta pasta primeiro.
echo.
pause
exit /b 1

:add_falhou
echo.
echo   ^>^> o git add falhou. Leia o motivo acima. Nada foi enviado.
echo.
pause
exit /b 1

:segredo
echo.
echo  ================================================================
echo    PAREI. O config.txt ENTROU NA LISTA.
echo  ================================================================
echo    Ele tem a chave de escrita do banco. NAO PODE SUBIR.
echo    Nada foi enviado. Me avise antes de tentar de novo.
echo.
git reset > nul
pause
exit /b 1

:push_falhou
echo.
echo  ================================================================
echo    O ENVIO NAO FECHOU.
echo  ================================================================
echo    Motivos comuns:
echo      - o login do GitHub nao foi concluido no navegador
echo      - a URL em github.txt esta errada. Apague o github.txt e
echo        clique aqui de novo para colar a URL de novo.
echo      - o repositorio foi criado JA COM arquivo dentro
echo        (README ou gitignore). Crie um vazio.
echo.
pause
exit /b 1
