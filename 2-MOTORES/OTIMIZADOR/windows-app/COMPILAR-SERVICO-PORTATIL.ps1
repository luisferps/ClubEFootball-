$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$source = Join-Path $root 'servico_portatil.py'
$runtime = Join-Path $root 'runtime'
$output = Join-Path $runtime 'OtimizadorServico.exe'
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
    (Join-Path $root 'fila_producao_v3.py'),
    (Join-Path $root 'preparo_fila_integral_v5.py')
)
$precisaCompilar = -not (Test-Path -LiteralPath $output)
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
    & $python -m PyInstaller --noconfirm --clean --onefile --name 'OtimizadorServico' `
        --paths (Join-Path $root 'interface') --hidden-import numpy --collect-all numpy `
        --workpath (Join-Path $temporario 'build') --distpath (Join-Path $temporario 'dist') `
        --specpath $temporario $source
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao empacotar o serviço portátil do Otimizador.' }
    $gerado = Join-Path $temporario 'dist\OtimizadorServico.exe'
    if (-not (Test-Path -LiteralPath $gerado)) { throw 'O empacotamento não gerou OtimizadorServico.exe.' }
    Copy-Item -LiteralPath $gerado -Destination $output -Force
} finally {
    if (Test-Path -LiteralPath $temporario) { Remove-Item -LiteralPath $temporario -Recurse -Force }
}
Get-Item -LiteralPath $output | Select-Object FullName,Length,LastWriteTime
