param(
  [ValidateSet('Menu', 'Status', 'Configurar', 'Iniciar', 'Pausar', 'Retomar', 'Parar', 'Verificar')]
  [string]$Acao = 'Menu'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$PastaFerramenta = Split-Path -Parent $MyInvocation.MyCommand.Path
$Worker = Join-Path $PastaFerramenta 'photo-batch-worker.mjs'
$Extrator = Join-Path $PastaFerramenta 'card-image-extractor.mjs'
$Manifesto = Join-Path $PastaFerramenta 'photo-manifest.mjs'
$Output = Join-Path $PastaFerramenta 'output'
$PastaOperador = Join-Path $Output 'operador'
$PastaControle = Join-Path $PastaOperador 'controle'
$EstadoPath = Join-Path $PastaOperador 'estado.json'
$CredenciaisPath = Join-Path $Output 'state\credentials.windows-dpapi.json'
$PausarPath = Join-Path $PastaControle 'pausar.solicitado.json'
$PararPath = Join-Path $PastaControle 'parar.solicitado.json'
$PackagePg = Join-Path $PastaFerramenta 'node_modules\pg\package.json'

function Escrever-Titulo {
  Write-Host ''
  Write-Host '============================================================' -ForegroundColor DarkCyan
  Write-Host 'EXTRATOR DE FOTOS - CONTROLE OPERACIONAL' -ForegroundColor Cyan
  Write-Host '============================================================' -ForegroundColor DarkCyan
}

function Ler-JsonSeguro([string]$Caminho) {
  if (-not (Test-Path -LiteralPath $Caminho)) { return $null }
  try { return Get-Content -LiteralPath $Caminho -Raw -Encoding UTF8 | ConvertFrom-Json }
  catch { return $null }
}

function Obter-Estado { return Ler-JsonSeguro -Caminho $EstadoPath }

function Processo-Do-Worker-Ativo($Estado) {
  if ($null -eq $Estado -or $null -eq $Estado.pid) { return $false }
  $pidWorker = 0
  if (-not [int]::TryParse([string]$Estado.pid, [ref]$pidWorker) -or $pidWorker -le 0) { return $false }
  try {
    $processo = Get-CimInstance Win32_Process -Filter "ProcessId = $pidWorker" -ErrorAction Stop
    if ($null -eq $processo) { return $false }
    return [string]$processo.CommandLine -like '*photo-batch-worker.mjs*'
  } catch {
    try { return $null -ne (Get-Process -Id $pidWorker -ErrorAction Stop) }
    catch { return $false }
  }
}

function Processo-Legado-Ativo {
  $pastaLegado = $PastaFerramenta + ' - LEGADO'
  try {
    return @(
      Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {
        [string]$_.CommandLine -like ('*' + $pastaLegado + '*') -and
        [string]$_.CommandLine -match 'interface-local-server\.mjs|card-image-extractor\.mjs|abrir-interface\.ps1'
      }
    ).Count -gt 0
  } catch { return $false }
}

function Converter-Seguro-Para-Texto([Security.SecureString]$Seguro) {
  $ponteiro = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($Seguro)
  try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ponteiro) }
  finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ponteiro) }
}

function Validar-Credenciais-Objeto($Credenciais) {
  $key = [string]$Credenciais.cloudinaryApiKey
  $secret = [string]$Credenciais.cloudinaryApiSecret
  $dbUrl = [string]$Credenciais.supabaseDbUrl
  if ([string]::IsNullOrWhiteSpace($key) -or [string]::IsNullOrWhiteSpace($secret) -or [string]::IsNullOrWhiteSpace($dbUrl)) { throw 'As três credenciais são obrigatórias.' }
  if ($key.Length -gt 8192 -or $secret.Length -gt 8192 -or $dbUrl.Length -gt 8192 -or $key -match "[\r\n]" -or $secret -match "[\r\n]" -or $dbUrl -match "[\r\n]") { throw 'Uma credencial possui formato inválido.' }
  $uri = $null
  if (-not [Uri]::TryCreate($dbUrl, [UriKind]::Absolute, [ref]$uri) -or $uri.Scheme -notin @('postgres', 'postgresql') -or [string]::IsNullOrWhiteSpace($uri.Host)) { throw 'A Supabase Database URL precisa ser uma conexão PostgreSQL válida.' }
  if ($uri.Port -eq 6543) { throw 'Essa URL usa Transaction pooler 6543. No Supabase, copie Session pooler na porta 5432.' }
}

function Abrir-Cofre {
  $documento = Ler-JsonSeguro -Caminho $CredenciaisPath
  if ($null -eq $documento -or $documento.format -ne 'clubefutebol-photo-credentials-windows-dpapi-v2' -or [string]$documento.ciphertext -notmatch '^[A-Za-z0-9+/=]+$') { throw 'O cofre local ainda não foi configurado ou está inválido.' }
  Add-Type -AssemblyName System.Security
  $selado = $null
  $bytes = $null
  $texto = $null
  $credenciais = $null
  try {
    $selado = [Convert]::FromBase64String([string]$documento.ciphertext)
    $bytes = [Security.Cryptography.ProtectedData]::Unprotect($selado, $null, [Security.Cryptography.DataProtectionScope]::CurrentUser)
    $texto = [Text.Encoding]::UTF8.GetString($bytes)
    $credenciais = $texto | ConvertFrom-Json
    Validar-Credenciais-Objeto -Credenciais $credenciais
    return $true
  } finally {
    if ($selado) { [Array]::Clear($selado, 0, $selado.Length) }
    if ($bytes) { [Array]::Clear($bytes, 0, $bytes.Length) }
    $texto = $null
    $credenciais = $null
    if ($documento) { $documento.ciphertext = '' }
  }
}

function Cofre-Configurado {
  try { return [bool](Abrir-Cofre) }
  catch { return $false }
}

function Salvar-Cofre {
  Escrever-Titulo
  Write-Host 'CONFIGURAÇÃO LOCAL DAS TRÊS CREDENCIAIS' -ForegroundColor Yellow
  Write-Host 'Elas não aparecem na tela e ficam protegidas pelo Windows DPAPI.'
  Write-Host 'Use a URL do Supabase Session pooler, porta 5432.'
  Write-Host ''
  $keySeguro = Read-Host 'Cole a Cloudinary API Key' -AsSecureString
  $secretSeguro = Read-Host 'Cole a Cloudinary API Secret' -AsSecureString
  $dbSeguro = Read-Host 'Cole a Supabase Database URL completa' -AsSecureString
  $key = $null
  $secret = $null
  $dbUrl = $null
  $texto = $null
  $bytes = $null
  $selado = $null
  try {
    $key = Converter-Seguro-Para-Texto $keySeguro
    $secret = Converter-Seguro-Para-Texto $secretSeguro
    $dbUrl = Converter-Seguro-Para-Texto $dbSeguro
    $credenciais = [ordered]@{ cloudinaryApiKey = $key.Trim(); cloudinaryApiSecret = $secret.Trim(); supabaseDbUrl = $dbUrl.Trim() }
    Validar-Credenciais-Objeto -Credenciais $credenciais
    $texto = $credenciais | ConvertTo-Json -Compress
    Add-Type -AssemblyName System.Security
    $bytes = [Text.Encoding]::UTF8.GetBytes($texto)
    $selado = [Security.Cryptography.ProtectedData]::Protect($bytes, $null, [Security.Cryptography.DataProtectionScope]::CurrentUser)
    $documento = [ordered]@{ format = 'clubefutebol-photo-credentials-windows-dpapi-v2'; protection = 'Windows DPAPI CurrentUser'; ciphertext = [Convert]::ToBase64String($selado) }
    $pastaEstado = Split-Path -Parent $CredenciaisPath
    New-Item -ItemType Directory -Path $pastaEstado -Force | Out-Null
    [IO.File]::WriteAllText($CredenciaisPath, (($documento | ConvertTo-Json) + [Environment]::NewLine), (New-Object Text.UTF8Encoding($false)))
    Write-Host ''
    Write-Host 'OK: credenciais salvas somente nesta conta do Windows.' -ForegroundColor Green
    Write-Host 'Nenhuma consulta, imagem ou alteração de banco foi executada.' -ForegroundColor Green
  } finally {
    if ($bytes) { [Array]::Clear($bytes, 0, $bytes.Length) }
    if ($selado) { [Array]::Clear($selado, 0, $selado.Length) }
    $key = $null; $secret = $null; $dbUrl = $null; $texto = $null
    $keySeguro = $null; $secretSeguro = $null; $dbSeguro = $null
  }
}

function Garantir-Dependencias {
  . (Join-Path $PastaFerramenta 'bootstrap-node.ps1')
  $node = Obter-Node -PastaFerramenta $PastaFerramenta
  if (-not (Test-Path -LiteralPath $PackagePg)) {
    $npm = Join-Path (Split-Path -Parent $node) 'npm.cmd'
    if (-not (Test-Path -LiteralPath $npm)) {
      $npmComando = Get-Command npm.cmd -ErrorAction SilentlyContinue
      if ($npmComando) { $npm = $npmComando.Source }
    }
    if (-not (Test-Path -LiteralPath $npm)) { throw 'npm.cmd não foi encontrado para preparar a dependência verificada.' }
    Write-Host 'Preparando a dependência verificada na primeira utilização...'
    & $npm ci --ignore-scripts --no-audit --no-fund --omit=dev --prefix $PastaFerramenta
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $PackagePg)) { throw 'A dependência não passou pela instalação verificada.' }
  }
  return $node
}

function Mostrar-Status {
  Escrever-Titulo
  $estado = Obter-Estado
  $ativo = Processo-Do-Worker-Ativo -Estado $estado
  $legadoAtivo = Processo-Legado-Ativo
  $cofre = Cofre-Configurado
  Write-Host ('Credenciais locais: ' + $(if ($cofre) { 'CONFIGURADAS' } else { 'NÃO CONFIGURADAS' })) -ForegroundColor $(if ($cofre) { 'Green' } else { 'Yellow' })
  if ($legadoAtivo) { Write-Host 'ATENÇÃO: existe um processo do Extrator LEGADO ativo. Não inicie o batch.' -ForegroundColor Red }
  if ($null -eq $estado) {
    Write-Host 'Execução: ainda não há execução operacional nesta máquina.'
    Write-Host ('Estado esperado em: ' + $EstadoPath)
    return
  }
  $statusVisivel = [string]$estado.status
  if ($ativo -and (Test-Path -LiteralPath $PararPath)) { $statusVisivel = 'PARADA SOLICITADA - aguardando ponto seguro' }
  elseif ($ativo -and (Test-Path -LiteralPath $PausarPath)) { $statusVisivel = 'PAUSA SOLICITADA/ATIVA' }
  elseif (-not $ativo -and $estado.status -in @('running', 'starting', 'paused')) { $statusVisivel = 'INTERROMPIDA - processo não está ativo' }
  Write-Host ('Execução: ' + $statusVisivel) -ForegroundColor $(if ($ativo) { 'Cyan' } elseif ($estado.status -eq 'completed') { 'Green' } else { 'Yellow' })
  Write-Host ('Fase: ' + [string]$estado.phase)
  Write-Host ('Fila desta consulta: {0} de {1}' -f [int]$estado.queue_completed, [int]$estado.queue_total)
  if ($estado.PSObject.Properties.Name -contains 'current_card_progress' -and $null -ne $estado.current_card_progress) {
    Write-Host ('Progresso dentro do lote: {0} de {1}' -f [int]$estado.current_card_progress, [int]$estado.current_card_total)
  }
  Write-Host ('Lotes seguros fechados: {0}' -f [int]$estado.safe_batches)
  Write-Host ('Links gravados e relidos: {0}' -f [int]$estado.updated)
  Write-Host ('Conflitos: {0}' -f [int]$estado.conflicts)
  if ($null -ne $estado.final_missing) { Write-Host ('Pendências na última leitura: {0}' -f [int]$estado.final_missing) }
  if ($estado.PSObject.Properties.Name -contains 'last_safe_batch' -and $null -ne $estado.last_safe_batch) { Write-Host ('Último lote seguro: {0}' -f [int]$estado.last_safe_batch) }
  if ($estado.PSObject.Properties.Name -contains 'message' -and -not [string]::IsNullOrWhiteSpace([string]$estado.message)) { Write-Host ('Mensagem: ' + [string]$estado.message) -ForegroundColor Green }
  if ($estado.PSObject.Properties.Name -contains 'error' -and -not [string]::IsNullOrWhiteSpace([string]$estado.error)) { Write-Host ('Erro: ' + [string]$estado.error) -ForegroundColor Red }
  Write-Host ('Log: ' + [string]$estado.log_file)
  Write-Host ('Resumo: ' + [string]$estado.summary_file)
}

function Confirmar-Inicio {
  Write-Host ''
  Write-Host 'A execução irá:' -ForegroundColor Yellow
  Write-Host '- consultar no Supabase somente cards com foto_url_cloudinary NULL;'
  Write-Host '- preparar lotes de até 100 imagens;'
  Write-Host '- aplicar cada manifesto somente após validação;'
  Write-Host '- nunca substituir link já existente;'
  Write-Host '- reler o banco após cada APPLY.'
  Write-Host ''
  & choice.exe /C SN /N /M 'Deseja INICIAR/RETOMAR agora? [S/N] '
  return $LASTEXITCODE -eq 1
}

function Esperar-Estado-Inicial([string]$RunId, $Processo, [string]$StderrPath) {
  for ($tentativa = 0; $tentativa -lt 50; $tentativa++) {
    Start-Sleep -Milliseconds 200
    $Processo.Refresh()
    $estado = Obter-Estado
    if ($null -ne $estado -and [string]$estado.run_id -eq $RunId) {
      if ([string]$estado.status -eq 'failed') {
        Write-Host ('FALHA AO INICIAR: ' + [string]$estado.error) -ForegroundColor Red
        Write-Host ('Log: ' + [string]$estado.log_file)
        return 'failed'
      }
      if ([string]$estado.status -eq 'completed') {
        Write-Host ('CONCLUÍDO: ' + [string]$estado.message) -ForegroundColor Green
        Write-Host ('Log: ' + [string]$estado.log_file)
        return 'completed'
      }
      if ([string]$estado.status -in @('paused', 'stopped_safe')) { return [string]$estado.status }
      if ([string]$estado.status -eq 'running' -and [string]$estado.phase -notin @('starting', 'discovering')) { return 'running' }
    }
    if ($Processo.HasExited) { break }
  }
  $Processo.Refresh()
  if ($Processo.HasExited) {
    $erroLancador = if (Test-Path -LiteralPath $StderrPath) { (Get-Content -LiteralPath $StderrPath -Raw -ErrorAction SilentlyContinue).Trim() } else { '' }
    if ([string]::IsNullOrWhiteSpace($erroLancador)) { $erroLancador = 'O worker fechou antes de publicar o estado inicial.' }
    Write-Host ('FALHA AO INICIAR: ' + $erroLancador) -ForegroundColor Red
    Write-Host ('Log técnico do iniciador: ' + $StderrPath)
    return 'failed'
  }
  $estadoAtual = Obter-Estado
  if ($null -ne $estadoAtual -and [string]$estadoAtual.run_id -eq $RunId -and [string]$estadoAtual.phase -eq 'discovering') {
    Write-Host 'PROCESSO ATIVO: a consulta inicial da fila ainda está em andamento.' -ForegroundColor Cyan
    Write-Host ('Log: ' + [string]$estadoAtual.log_file)
    return 'consulting'
  }
  Write-Host 'PROCESSO ATIVO: o estado inicial ainda não ficou disponível.' -ForegroundColor Yellow
  Write-Host ('Estado esperado em: ' + $EstadoPath)
  return 'running'
}

function Iniciar-Worker {
  Escrever-Titulo
  $estado = Obter-Estado
  if (Processo-Do-Worker-Ativo -Estado $estado) {
    Write-Host 'Já existe uma execução ativa. Use STATUS, PAUSAR ou PARAR.' -ForegroundColor Yellow
    return
  }
  if (Processo-Legado-Ativo) {
    Write-Host 'Existe um processo do Extrator LEGADO ativo.' -ForegroundColor Red
    Write-Host 'Feche a execução antiga antes de iniciar o batch novo.' -ForegroundColor Red
    return
  }
  if (-not (Cofre-Configurado)) {
    Write-Host 'As credenciais locais ainda não estão configuradas nesta conta do Windows.' -ForegroundColor Yellow
    Write-Host 'Use a opção 6 antes de iniciar.'
    return
  }
  if (-not (Confirmar-Inicio)) {
    Write-Host ''
    Write-Host 'Cancelado. Nada foi iniciado e o banco não foi alterado.' -ForegroundColor Yellow
    return
  }
  $node = Garantir-Dependencias
  New-Item -ItemType Directory -Path $PastaControle -Force | Out-Null
  Remove-Item -LiteralPath $PausarPath -Force -ErrorAction SilentlyContinue
  Remove-Item -LiteralPath $PararPath -Force -ErrorAction SilentlyContinue
  $runId = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH-mm-ss-fffZ')
  $pastaRun = Join-Path $PastaOperador ('runs\' + $runId)
  New-Item -ItemType Directory -Path $pastaRun -Force | Out-Null
  $stdout = Join-Path $pastaRun 'lancador.stdout.log'
  $stderr = Join-Path $pastaRun 'lancador.stderr.log'
  $argumentos = '"{0}" --run-id {1}' -f $Worker, $runId
  $processo = Start-Process -FilePath $node -ArgumentList $argumentos -WorkingDirectory $PastaFerramenta -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
  Write-Host ''
  Write-Host 'Aguardando o worker publicar o estado inicial...' -ForegroundColor Cyan
  $resultadoInicial = Esperar-Estado-Inicial -RunId $runId -Processo $processo -StderrPath $stderr
  if ($resultadoInicial -in @('running', 'consulting')) {
    Write-Host ('OK: executor ativo em segundo plano. PID {0}.' -f $processo.Id) -ForegroundColor Green
    Write-Host 'Agora ele está consultando a fila; use a opção 2 para acompanhar.'
    Write-Host 'Você pode fechar esta janela sem encerrar o worker.'
    Write-Host ('Pasta desta execução: ' + $pastaRun)
  } elseif ($resultadoInicial -eq 'paused') {
    Write-Host 'O executor iniciou e está pausado no ponto seguro.' -ForegroundColor Yellow
  } elseif ($resultadoInicial -eq 'stopped_safe') {
    Write-Host 'O executor atendeu uma parada segura antes de processar novo lote.' -ForegroundColor Yellow
  }
}

function Escrever-Solicitacao([string]$Caminho, [string]$AcaoSolicitada) {
  $estado = Obter-Estado
  if (-not (Processo-Do-Worker-Ativo -Estado $estado)) { Write-Host 'Não existe execução ativa nesta máquina.' -ForegroundColor Yellow; return $false }
  New-Item -ItemType Directory -Path $PastaControle -Force | Out-Null
  $payload = [ordered]@{ action = $AcaoSolicitada; requested_at_utc = [DateTime]::UtcNow.ToString('o') }
  [IO.File]::WriteAllText($Caminho, (($payload | ConvertTo-Json) + [Environment]::NewLine), (New-Object Text.UTF8Encoding($false)))
  return $true
}

function Pausar-Worker {
  Escrever-Titulo
  if (Escrever-Solicitacao -Caminho $PausarPath -AcaoSolicitada 'pause') { Write-Host 'Pausa solicitada. O executor vai parar no próximo ponto seguro.' -ForegroundColor Green }
}

function Retomar-Worker {
  Escrever-Titulo
  $estado = Obter-Estado
  if (-not (Processo-Do-Worker-Ativo -Estado $estado)) { Write-Host 'A execução não está ativa. Use a opção 1 para criar uma nova execução segura.' -ForegroundColor Yellow; return }
  Remove-Item -LiteralPath $PausarPath -Force -ErrorAction SilentlyContinue
  Write-Host 'Continuação liberada. O executor retomará do ponto seguro.' -ForegroundColor Green
}

function Parar-Worker {
  Escrever-Titulo
  if (Escrever-Solicitacao -Caminho $PararPath -AcaoSolicitada 'stop') {
    Write-Host 'Parada segura solicitada.' -ForegroundColor Green
    Write-Host 'O processo não será morto: ele fechará a etapa atual e preservará manifesto/logs.'
  }
}

function Verificar-Arquivos {
  Escrever-Titulo
  $obrigatorios = @($Worker, $Extrator, $Manifesto, (Join-Path $PastaFerramenta 'package-lock.json'), (Join-Path $PastaFerramenta 'bootstrap-node.ps1'))
  $faltando = @($obrigatorios | Where-Object { -not (Test-Path -LiteralPath $_ -PathType Leaf) })
  if ($faltando.Count -gt 0) { throw ('Arquivos obrigatórios ausentes: ' + ($faltando -join ', ')) }
  Write-Host 'OK: estrutura operacional íntegra.' -ForegroundColor Green
  Write-Host 'Esta verificação não consulta Cloudinary, Supabase nem altera o banco.'
  Mostrar-Status
}

function Executar-Acao([string]$Nome) {
  switch ($Nome) {
    'Status' { Mostrar-Status }
    'Configurar' { Salvar-Cofre }
    'Iniciar' { Iniciar-Worker }
    'Pausar' { Pausar-Worker }
    'Retomar' { Retomar-Worker }
    'Parar' { Parar-Worker }
    'Verificar' { Verificar-Arquivos }
    default { throw "Ação inválida: $Nome" }
  }
}

try {
  if ($Acao -ne 'Menu') { Executar-Acao -Nome $Acao; exit 0 }
  do {
    Clear-Host
    Mostrar-Status
    Write-Host ''
    Write-Host '1 - INICIAR/RETOMAR fila persistida'
    Write-Host '2 - STATUS'
    Write-Host '3 - PAUSAR no próximo ponto seguro'
    Write-Host '4 - CONTINUAR uma execução pausada'
    Write-Host '5 - PARAR com segurança'
    Write-Host '6 - CONFIGURAR/ATUALIZAR as três credenciais locais'
    Write-Host '7 - VERIFICAR arquivos e status (somente leitura)'
    Write-Host '0 - SAIR'
    Write-Host ''
    $opcao = (Read-Host 'Escolha').Trim()
    switch ($opcao) {
      '1' { Executar-Acao -Nome 'Iniciar' }
      '2' { Executar-Acao -Nome 'Status' }
      '3' { Executar-Acao -Nome 'Pausar' }
      '4' { Executar-Acao -Nome 'Retomar' }
      '5' { Executar-Acao -Nome 'Parar' }
      '6' { Executar-Acao -Nome 'Configurar' }
      '7' { Executar-Acao -Nome 'Verificar' }
      '0' { break }
      default { Write-Host 'Opção inválida.' -ForegroundColor Yellow }
    }
    if ($opcao -ne '0') {
      Write-Host ''
      [void](Read-Host 'Pressione ENTER para voltar ao menu')
    }
  } while ($opcao -ne '0')
} catch {
  Write-Host ''
  Write-Host 'A operação não pôde ser concluída:' -ForegroundColor Red
  Write-Host $_.Exception.Message -ForegroundColor Red
  exit 1
}
