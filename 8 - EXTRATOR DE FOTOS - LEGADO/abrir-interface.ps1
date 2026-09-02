$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$pastaFerramenta = Split-Path -Parent $MyInvocation.MyCommand.Path
$servidor = Join-Path $pastaFerramenta 'interface-local-server.mjs'
. (Join-Path $pastaFerramenta 'bootstrap-node.ps1')

function Garantir-Dependencias([string]$Node, [string]$Pasta) {
  $pg = Join-Path $Pasta 'node_modules\pg\package.json'
  if (Test-Path -LiteralPath $pg) { return }
  $npm = Join-Path (Split-Path -Parent $Node) 'npm.cmd'
  if (-not (Test-Path -LiteralPath $npm)) {
    $npmComando = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if ($npmComando) { $npm = $npmComando.Source }
  }
  if (-not (Test-Path -LiteralPath $npm)) { throw 'npm.cmd não foi encontrado para instalar a dependência fixada no package-lock.json.' }
  Write-Host 'Preparando as dependências verificadas na primeira utilização...'
  & $npm ci --ignore-scripts --no-audit --no-fund --omit=dev --prefix $Pasta
  if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $pg)) { throw 'As dependências não passaram pela instalação verificada.' }
}

try {
  $node = Obter-Node -PastaFerramenta $pastaFerramenta
  Garantir-Dependencias -Node $node -Pasta $pastaFerramenta
  Write-Host 'Abrindo a interface local do Extrator de Fotos...'
  Write-Host 'Cole as chaves somente na página local que será aberta.'
  Write-Host 'Esta janela mantém o aplicativo ativo somente em 127.0.0.1.'
  & $node $servidor
  if ($LASTEXITCODE -ne 0) { throw "A interface local terminou com o código $LASTEXITCODE." }
} catch {
  Write-Host ''
  Write-Host 'Não foi possível abrir a interface local.' -ForegroundColor Red
  Write-Host $_.Exception.Message -ForegroundColor Red
  exit 1
}
