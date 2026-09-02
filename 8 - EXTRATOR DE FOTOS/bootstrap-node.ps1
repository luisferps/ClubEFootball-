function Obter-Node {
  param([Parameter(Mandatory = $true)][string]$PastaFerramenta)

  $nodeCodex = 'C:\Users\Luis Fernando\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
  $npmCodex = Join-Path (Split-Path -Parent $nodeCodex) 'npm.cmd'
  if ((Test-Path -LiteralPath $nodeCodex) -and (Test-Path -LiteralPath $npmCodex)) { return $nodeCodex }

  $nodeSistema = Get-Command node -ErrorAction SilentlyContinue
  if ($nodeSistema) {
    $versao = & $nodeSistema.Source --version 2>$null
    $npmSistema = Join-Path (Split-Path -Parent $nodeSistema.Source) 'npm.cmd'
    if ($versao -match '^v(\d+)' -and [int]$Matches[1] -ge 20 -and (Test-Path -LiteralPath $npmSistema)) { return $nodeSistema.Source }
  }

  $versaoNode = '24.20.0'
  $arquitetura = [Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString().ToLowerInvariant()
  if ($arquitetura -eq 'x64') {
    $pacote = "node-v$versaoNode-win-x64.zip"
    $hashEsperado = '6cac9ffbca8f6a47091e4b5c772e0606049c3871cb67d900c0cedde630e545ba'
  } elseif ($arquitetura -eq 'arm64') {
    $pacote = "node-v$versaoNode-win-arm64.zip"
    $hashEsperado = '31c6799744de8a54601643098040c68c3697e56c94e407d61d0e5fa5f34191d7'
  } else {
    throw "Windows não suportado pelo iniciador: $arquitetura"
  }

  $pastaRuntime = Join-Path $PastaFerramenta '.runtime'
  $pastaNode = Join-Path $pastaRuntime ([IO.Path]::GetFileNameWithoutExtension($pacote))
  $nodePortatil = Join-Path $pastaNode 'node.exe'
  if (Test-Path -LiteralPath $nodePortatil) { return $nodePortatil }

  New-Item -ItemType Directory -Path $pastaRuntime -Force | Out-Null
  $arquivoZip = Join-Path $pastaRuntime $pacote
  $url = "https://nodejs.org/download/release/v$versaoNode/$pacote"

  if (-not (Test-Path -LiteralPath $arquivoZip)) {
    Write-Host 'Preparando o executor seguro na primeira utilização...'
    Invoke-WebRequest -Uri $url -OutFile $arquivoZip -UseBasicParsing -TimeoutSec 180
  }

  $hashReal = (Get-FileHash -LiteralPath $arquivoZip -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($hashReal -ne $hashEsperado) {
    throw 'O executor baixado não passou na verificação SHA-256. Nada será executado.'
  }

  Expand-Archive -LiteralPath $arquivoZip -DestinationPath $pastaRuntime -Force
  if (-not (Test-Path -LiteralPath $nodePortatil)) {
    throw 'O executor seguro não foi encontrado depois da descompactação.'
  }
  return $nodePortatil
}
