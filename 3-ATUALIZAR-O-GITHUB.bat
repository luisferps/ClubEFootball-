@echo off
chcp 65001 >nul
setlocal EnableExtensions EnableDelayedExpansion
title 3 - PUBLICAR TODAS AS ALTERACOES COM SEGURANCA
cd /d "%~dp0"

set "LOG=%TEMP%\cf-subir.log"
set "STATUS_FILE=%TEMP%\cf-status-%RANDOM%-%RANDOM%.txt"
set "DELETED_FILE=%TEMP%\cf-excluidos-%RANDOM%-%RANDOM%.txt"
set "UNTRACKED_FILE=%TEMP%\cf-novos-%RANDOM%-%RANDOM%.txt"
set "LARGE_FILE=%TEMP%\cf-grandes-%RANDOM%-%RANDOM%.txt"
set "REPO_ESPERADO=https://github.com/luisferps/ClubEFootball-.git"
set "REPO_ATUAL="
set "BRANCH="
set "LOCAL_AHEAD=0"
set "REMOTE_AHEAD=0"
set "TOTAL=0"
set "DELETED=0"
set "UNTRACKED=0"
set "MODO_VERIFICAR=0"
if /I "%~1"=="VERIFICAR" set "MODO_VERIFICAR=1"

>"%LOG%" echo ============================================
>>"%LOG%" echo PUBLICAR TODAS AS ALTERACOES  %DATE% %TIME%
>>"%LOG%" echo pasta: %CD%
>>"%LOG%" echo ============================================

echo.
echo  ============================================================
echo   3 - PUBLICAR TODAS AS ALTERACOES COM SEGURANCA
echo  ============================================================
echo.
echo   Pasta publicada:
echo   %CD%
echo.
echo   Este e o unico botao de publicacao deste repositorio.
echo   Ele confere o GitHub antes, mostra o que vai mudar e so
echo   publica depois de duas confirmacoes quando houver exclusoes.
echo.

where git >nul 2>&1
if errorlevel 1 (
  set "MOTIVO=O GIT NAO FOI ENCONTRADO NESTE WINDOWS."
  goto ERRO
)

if not exist ".git" (
  set "MOTIVO=ESTA PASTA NAO E O CLONE PRINCIPAL DO REPOSITORIO."
  goto ERRO
)

for /f "delims=" %%R in ('git remote get-url origin 2^>nul') do set "REPO_ATUAL=%%R"
if /I not "!REPO_ATUAL!"=="%REPO_ESPERADO%" (
  echo   Esperado: %REPO_ESPERADO%
  echo   Encontrado: !REPO_ATUAL!
  set "MOTIVO=O ORIGIN NAO E O GITHUB OFICIAL ESPERADO."
  goto ERRO
)
echo   ok: repositorio GitHub correto

for /f "delims=" %%B in ('git branch --show-current 2^>nul') do set "BRANCH=%%B"
if /I not "!BRANCH!"=="main" (
  echo   Branch encontrada: !BRANCH!
  set "MOTIVO=A PUBLICACAO SO E PERMITIDA NA BRANCH MAIN."
  goto ERRO
)
echo   ok: branch main

if not exist ".gitignore" (
  set "MOTIVO=NAO ACHEI O .GITIGNORE. NADA FOI PREPARADO."
  goto ERRO
)
findstr /C:"config.txt" ".gitignore" >nul 2>&1
if errorlevel 1 (
  set "MOTIVO=O .GITIGNORE NAO PROTEGE CONFIG.TXT."
  goto ERRO
)
findstr /C:".env" ".gitignore" >nul 2>&1
if errorlevel 1 (
  set "MOTIVO=O .GITIGNORE NAO PROTEGE ARQUIVOS .ENV."
  goto ERRO
)
findstr /C:"*.key" ".gitignore" >nul 2>&1
if errorlevel 1 (
  set "MOTIVO=O .GITIGNORE NAO PROTEGE ARQUIVOS DE CHAVE."
  goto ERRO
)
echo   ok: configuracoes e chaves locais protegidas

echo   ---- conferindo o limite de tamanho do GitHub...
set "CF_LARGE_FILE=!LARGE_FILE!"
powershell -NoProfile -Command "$large=[System.Collections.Generic.List[string]]::new(); foreach($item in @(git ls-files --cached --others --exclude-standard)){ if(Test-Path -LiteralPath $item -PathType Leaf){ $file=Get-Item -LiteralPath $item; if($file.Length -ge 95MB){ $large.Add(('{0} - {1:N2} MB' -f $item,($file.Length/1MB))) } } }; [System.IO.File]::WriteAllLines($env:CF_LARGE_FILE,[string[]]$large); if($large.Count -gt 0){exit 2}" >>"%LOG%" 2>&1
set "LARGE_SCAN_RESULT=!errorlevel!"
set "CF_LARGE_FILE="
if "!LARGE_SCAN_RESULT!"=="2" (
  echo.
  echo   PAREI: estes arquivos ultrapassam o limite seguro do GitHub:
  type "!LARGE_FILE!"
  set "MOTIVO=RETIRE OS ARQUIVOS DE 95 MB OU MAIS DA PUBLICACAO. NADA FOI PREPARADO."
  goto ERRO
)
if not "!LARGE_SCAN_RESULT!"=="0" (
  set "MOTIVO=NAO CONSEGUI CONFERIR O TAMANHO DOS ARQUIVOS. NADA FOI PREPARADO."
  goto ERRO
)
echo   ok: nenhum arquivo publicavel ultrapassa 95 MB

echo   ---- conferindo o GitHub sem alterar seus arquivos...
git fetch --quiet --prune origin main >>"%LOG%" 2>&1
if errorlevel 1 (
  set "MOTIVO=NAO CONSEGUI CONFERIR A BRANCH MAIN NO GITHUB."
  goto ERRO
)

for /f "tokens=1,2" %%A in ('git rev-list --left-right --count HEAD...origin/main 2^>nul') do (
  set "LOCAL_AHEAD=%%A"
  set "REMOTE_AHEAD=%%B"
)
if not "!REMOTE_AHEAD!"=="0" (
  echo   O GitHub possui !REMOTE_AHEAD! commit^(s^) que nao estao nesta pasta.
  set "MOTIVO=PAREI PARA NAO PUBLICAR POR CIMA DE UMA VERSAO MAIS NOVA."
  goto ERRO
)
echo   ok: o GitHub nao esta a frente desta pasta
if not "!LOCAL_AHEAD!"=="0" echo   aviso: existem !LOCAL_AHEAD! commit^(s^) locais ainda nao enviados

git status --porcelain=v1 --untracked-files=all >"%STATUS_FILE%"
git -c core.quotepath=false diff --name-status --diff-filter=D HEAD >"%DELETED_FILE%" 2>>"%LOG%"
git -c core.quotepath=false ls-files --others --exclude-standard >"%UNTRACKED_FILE%"

for /f %%N in ('find /v /c "" ^< "%STATUS_FILE%"') do set "TOTAL=%%N"
for /f %%N in ('find /v /c "" ^< "%DELETED_FILE%"') do set "DELETED=%%N"
for /f %%N in ('find /v /c "" ^< "%UNTRACKED_FILE%"') do set "UNTRACKED=%%N"

echo.
echo   RESUMO DA PUBLICACAO
echo   ------------------------------------------------------------
echo   alteracoes locais encontradas: !TOTAL!
echo   arquivos novos ainda nao versionados: !UNTRACKED!
echo   arquivos marcados como excluidos: !DELETED!
echo   commits locais ainda nao enviados: !LOCAL_AHEAD!
echo   ------------------------------------------------------------

>>"%LOG%" echo.
>>"%LOG%" echo ---- estado completo antes da publicacao
git -c core.quotepath=false status --short >>"%LOG%" 2>&1

if not "!DELETED!"=="0" (
  echo.
  echo   ATENCAO: estes arquivos seriam removidos do GitHub:
  type "%DELETED_FILE%"
  echo.
)

if "!TOTAL!"=="0" if "!LOCAL_AHEAD!"=="0" (
  echo   Nao ha nada novo para publicar.
  goto SUCESSO_SEM_PUBLICAR
)

if "!MODO_VERIFICAR!"=="1" (
  echo.
  echo  ============================================================
  echo   VERIFICACAO CONCLUIDA - NADA FOI GRAVADO OU ENVIADO
  echo  ============================================================
  goto LIMPAR_E_SAIR
)

echo.
echo   Pressione S para publicar TODAS as alteracoes acima.
echo   Pressione N para cancelar sem alterar nada.
>>"%LOG%" echo ---- aguardando confirmacao S ou N para publicar tudo
choice /C SN /N /M "  Confirmacao [S/N]: "
set "CONFIRMACAO_PUBLICAR=!errorlevel!"
if not "!CONFIRMACAO_PUBLICAR!"=="1" (
  echo.
  echo   Cancelado. Nenhum arquivo foi preparado, gravado ou enviado.
  >>"%LOG%" echo ---- publicacao cancelada antes de preparar arquivos
  goto LIMPAR_E_SAIR
)

if not "!DELETED!"=="0" (
  echo.
  echo   Existem !DELETED! exclusoes.
  echo   Pressione S para confirmar tambem essas exclusoes.
  echo   Pressione N para cancelar sem alterar nada.
  >>"%LOG%" echo ---- aguardando segunda confirmacao S ou N para exclusoes
  choice /C SN /N /M "  Confirmar exclusoes [S/N]: "
  set "CONFIRMACAO_EXCLUSOES=!errorlevel!"
  if not "!CONFIRMACAO_EXCLUSOES!"=="1" (
    echo.
    echo   Cancelado. As exclusoes nao foram publicadas.
    >>"%LOG%" echo ---- publicacao cancelada na confirmacao das exclusoes
    goto LIMPAR_E_SAIR
  )
)

for /f "delims=" %%T in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set "STAMP=%%T"
for %%P in ("%~dp0..") do set "PASTA_PAI=%%~fP"
set "BACKUP_ROOT=!PASTA_PAI!\_BACKUPS-ANTES-GITHUB"
set "BACKUP_DIR=!BACKUP_ROOT!\ClubEFootball--main-!STAMP!"

echo.
echo   ---- conferindo espaco para o backup fisico completo...
powershell -NoProfile -Command "$p=(Get-Location).Path; $m=Get-ChildItem -LiteralPath $p -Recurse -Force -File -ErrorAction SilentlyContinue ^| Measure-Object -Property Length -Sum; $size=[int64]$m.Sum; $free=[int64](Get-Item -LiteralPath $p).PSDrive.Free; Write-Host ('  tamanho da pasta: {0:N2} GB' -f ($size/1GB)); Write-Host ('  espaco livre: {0:N2} GB' -f ($free/1GB)); if($free -lt ($size + 2GB)){exit 2}" >>"%LOG%" 2>&1
if errorlevel 2 (
  set "MOTIVO=NAO HA ESPACO LIVRE SUFICIENTE PARA O BACKUP COMPLETO."
  goto ERRO
)
if errorlevel 1 (
  set "MOTIVO=NAO CONSEGUI MEDIR O ESPACO PARA O BACKUP."
  goto ERRO
)

if not exist "!BACKUP_ROOT!" mkdir "!BACKUP_ROOT!" >>"%LOG%" 2>&1
if errorlevel 1 (
  set "MOTIVO=NAO CONSEGUI CRIAR A PASTA EXTERNA DE BACKUP."
  goto ERRO
)

echo   ---- criando backup fisico completo antes de publicar...
echo   Destino: !BACKUP_DIR!
echo   A pasta atual possui muitos arquivos; esta etapa pode demorar.
>>"%LOG%" echo.
>>"%LOG%" echo ---- backup fisico completo
>>"%LOG%" echo destino: !BACKUP_DIR!
robocopy "%CD%" "!BACKUP_DIR!" /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /XJ /NP /NFL /NDL >>"%LOG%" 2>&1
set "ROBOCOPY_RESULT=!errorlevel!"
if !ROBOCOPY_RESULT! GEQ 8 (
  echo   Copia parcial preservada em: !BACKUP_DIR!
  set "MOTIVO=O BACKUP FISICO FALHOU. NADA FOI PREPARADO OU ENVIADO."
  goto ERRO
)

echo   ---- conferindo se origem e backup estao iguais...
robocopy "%CD%" "!BACKUP_DIR!" /E /L /COPY:DAT /DCOPY:DAT /R:0 /W:0 /XJ /NP /NFL /NDL /NJH /NJS >>"%LOG%" 2>&1
set "BACKUP_VERIFY_RESULT=!errorlevel!"
if not "!BACKUP_VERIFY_RESULT!"=="0" (
  echo   Backup mantido para conferencia em: !BACKUP_DIR!
  set "MOTIVO=A CONFERENCIA DO BACKUP ENCONTROU DIFERENCAS. NADA FOI ENVIADO."
  goto ERRO
)
if not exist "!BACKUP_DIR!\.git\HEAD" (
  set "MOTIVO=O BACKUP NAO CONTEM O REPOSITORIO GIT COMPLETO. NADA FOI ENVIADO."
  goto ERRO
)
if not exist "!BACKUP_DIR!\3-ATUALIZAR-O-GITHUB.bat" (
  set "MOTIVO=O BACKUP NAO CONTEM O BOTAO CENTRAL. NADA FOI ENVIADO."
  goto ERRO
)
echo   ok: backup fisico completo criado e conferido

for /f "delims=" %%H in ('git rev-parse HEAD 2^>nul') do set "COMMIT_ANTERIOR=%%H"
set "TAG_RECUPERACAO=recuperacao-antes-publicar-!STAMP!"

git tag "!TAG_RECUPERACAO!" "!COMMIT_ANTERIOR!" >>"%LOG%" 2>&1
if errorlevel 1 (
  set "MOTIVO=NAO CONSEGUI CRIAR O PONTO LOCAL DE RECUPERACAO."
  goto ERRO
)
echo   ok: ponto de recuperacao criado: !TAG_RECUPERACAO!

echo   ---- preparando todos os arquivos...
git add -A >>"%LOG%" 2>&1
if errorlevel 1 (
  set "MOTIVO=O GIT NAO CONSEGUIU PREPARAR TODOS OS ARQUIVOS."
  goto ERRO
)

set "ARQUIVO_SENSIVEL="
for /f "delims=" %%F in ('git diff --cached --name-only --diff-filter=ACMR -- "config.txt" ".env" ".env.*" "*.key" "*.pem" "*.secret" "*.secrets" "credenciais.local.*" "configuracao.local.*"') do (
  if /I not "%%~nxF"==".env.example" set "ARQUIVO_SENSIVEL=%%F"
)
if defined ARQUIVO_SENSIVEL (
  git reset --mixed HEAD >nul 2>&1
  echo   Arquivo detectado: !ARQUIVO_SENSIVEL!
  set "MOTIVO=UM ARQUIVO SENSIVEL ENTROU NA LISTA. NADA FOI GRAVADO."
  goto ERRO
)
echo   ok: nenhum arquivo sensivel entrou na publicacao

git diff --cached --quiet
if not errorlevel 1 goto SEM_NOVO_COMMIT

echo   ---- criando o commit com todas as alteracoes...
git -c user.name="Luis Fernando" -c user.email="luis.soares.177@gmail.com" commit -m "Atualizar todos os arquivos locais - !STAMP!" >>"%LOG%" 2>&1
if errorlevel 1 (
  set "MOTIVO=O GIT NAO CONSEGUIU CRIAR O COMMIT. NADA FOI ENVIADO."
  goto ERRO
)

:SEM_NOVO_COMMIT
for /f "delims=" %%H in ('git rev-parse HEAD 2^>nul') do set "COMMIT_PUBLICADO=%%H"
echo   ---- enviando o commit !COMMIT_PUBLICADO! ...
git push origin main >>"%LOG%" 2>&1
if errorlevel 1 (
  echo   O commit continua salvo nesta maquina: !COMMIT_PUBLICADO!
  echo   Ponto anterior de recuperacao: !TAG_RECUPERACAO!
  echo   Backup fisico: !BACKUP_DIR!
  set "MOTIVO=O PUSH FALHOU. NENHUM ARQUIVO LOCAL FOI PERDIDO."
  goto ERRO
)

set "COMMIT_REMOTO="
for /f "tokens=1" %%H in ('git ls-remote origin refs/heads/main 2^>nul') do set "COMMIT_REMOTO=%%H"
if /I not "!COMMIT_REMOTO!"=="!COMMIT_PUBLICADO!" (
  echo   Commit local:  !COMMIT_PUBLICADO!
  echo   Commit remoto: !COMMIT_REMOTO!
  set "MOTIVO=O PUSH TERMINOU, MAS O GITHUB NAO CONFIRMOU O MESMO COMMIT."
  goto ERRO
)

echo.
echo  ============================================================
echo   SUBIU E FOI CONFERIDO NO GITHUB
echo  ============================================================
echo   Commit confirmado: !COMMIT_PUBLICADO!
echo   Recuperacao local: !TAG_RECUPERACAO!
echo   Backup fisico: !BACKUP_DIR!
echo   Repositorio: github.com/luisferps/ClubEFootball-
echo.

git status --porcelain=v1 --untracked-files=all >"%STATUS_FILE%"
for /f %%N in ('find /v /c "" ^< "%STATUS_FILE%"') do set "RESTANTES=%%N"
if not "!RESTANTES!"=="0" (
  echo   AVISO: surgiram !RESTANTES! novas alteracoes durante o envio.
  echo   Elas nao foram perdidas, mas ainda nao estao no GitHub.
  echo   Rode este mesmo botao novamente depois de conferir.
)
goto SUCESSO

:SUCESSO_SEM_PUBLICAR
echo.
echo  ============================================================
echo   TUDO JA ESTAVA ATUALIZADO
echo  ============================================================
goto SUCESSO

:ERRO
echo.
echo  ============================================================
echo   PAREI COM SEGURANCA
echo  ============================================================
echo   !MOTIVO!
echo   Nenhum comando de apagar ou substituir arquivos foi usado.
echo   Log: %LOG%
echo.
if "!MODO_VERIFICAR!"=="0" pause
call :LIMPAR_TEMP
exit /b 1

:SUCESSO
if "!MODO_VERIFICAR!"=="0" pause

:LIMPAR_E_SAIR
if "!MODO_VERIFICAR!"=="0" (
  echo.
  echo   A janela ficara aberta para voce conferir o resultado.
  pause
)
call :LIMPAR_TEMP
exit /b 0

:LIMPAR_TEMP
del /f /q "%STATUS_FILE%" >nul 2>&1
del /f /q "%DELETED_FILE%" >nul 2>&1
del /f /q "%UNTRACKED_FILE%" >nul 2>&1
del /f /q "%LARGE_FILE%" >nul 2>&1
exit /b 0
