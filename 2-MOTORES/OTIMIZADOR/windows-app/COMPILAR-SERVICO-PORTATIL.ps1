$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$source = Join-Path $root 'servico_portatil.py'
$runtime = Join-Path $root 'runtime'
$output = Join-Path $runtime 'OtimizadorServico.exe'
$dependencias = Join-Path $runtime '_internal'
$pythonCandidatos = @(
    (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'),
    (Get-Command py.exe -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Source)
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }
$python = $pythonCandidatos | Select-Object -First 1
if (-not $python) { throw 'Python de compilação não encontrado nesta máquina de desenvolvimento.' }
if (-not (Test-Path -LiteralPath $source)) { throw 'servico_portatil.py não encontrado.' }

$entradas = @(
    $source,
    (Join-Path $root 'interface\servidor.py'),
    (Join-Path $root 'equacao.py'),
    (Join-Path $root 'motor.py'),
    (Join-Path $root 'fonte_unica.py'),
    (Join-Path $root 'roda_lote_v6.py'),
    (Join-Path $root 'regua.py'),
    (Join-Path $root 'travas.py'),
    (Join-Path $root 'fila_producao_v3.py'),
    (Join-Path $root 'fila_local_v1.py'),
    (Join-Path $root 'preparo_fila_integral_v5.py')
)
$precisaCompilar = -not (Test-Path -LiteralPath $output) -or -not (Test-Path -LiteralPath $dependencias)
if (-not $precisaCompilar) {
    $geradoEm = (Get-Item -LiteralPath $output).LastWriteTimeUtc
    $precisaCompilar = @($entradas | Where-Object { Test-Path -LiteralPath $_ } | Where-Object { (Get-Item -LiteralPath $_).LastWriteTimeUtc -gt $geradoEm }).Count -gt 0
}
if (-not $precisaCompilar) {
    Get-Item -LiteralPath $output | Select-Object FullName,Length,LastWriteTime
    return
}

& $python -c "import PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
    & $python -m pip install --disable-pip-version-check --quiet PyInstaller
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível instalar a ferramenta de empacotamento do serviço portátil.' }
}

$temporario = Join-Path $root 'windows-app\_empacotamento-servico-portatil'
if (Test-Path -LiteralPath $temporario) { Remove-Item -LiteralPath $temporario -Recurse -Force }
New-Item -ItemType Directory -Path $temporario -Force | Out-Null
New-Item -ItemType Directory -Path $runtime -Force | Out-Null
try {
    # onedir evita a descompressão de todo o NumPy a cada clique. O usuário
    # copia a pasta runtime inteira junto do Otimizador e o painel abre sem
    # depender de Python instalado nem de uma extração temporária lenta.
    & $python -m PyInstaller --noconfirm --clean --onedir --name 'OtimizadorServico' `
        --paths (Join-Path $root 'interface') --hidden-import numpy `
        --collect-all psycopg --collect-all psycopg_binary `
        --workpath (Join-Path $temporario 'build') --distpath (Join-Path $temporario 'dist') `
        --specpath $temporario $source
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao empacotar o serviço portátil do Otimizador.' }
    $pastaGerada = Join-Path $temporario 'dist\OtimizadorServico'
    $gerado = Join-Path $pastaGerada 'OtimizadorServico.exe'
    if (-not (Test-Path -LiteralPath $gerado)) { throw 'O empacotamento não gerou OtimizadorServico.exe.' }
    # O runtime anterior já foi preservado no snapshot de recuperação antes
    # do build. Copiar o conteúdo por cima mantém o caminho estável usado pelo
    # lançador e instala também _internal, obrigatório para abrir em qualquer
    # computador sem Python.
    Copy-Item -Path (Join-Path $pastaGerada '*') -Destination $runtime -Recurse -Force
} finally {
    if (Test-Path -LiteralPath $temporario) { Remove-Item -LiteralPath $temporario -Recurse -Force }
}
Get-Item -LiteralPath $output | Select-Object FullName,Length,LastWriteTime
