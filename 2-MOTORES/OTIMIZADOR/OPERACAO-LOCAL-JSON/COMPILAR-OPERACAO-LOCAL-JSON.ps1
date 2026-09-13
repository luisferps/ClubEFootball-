$ErrorActionPreference = 'Stop'

$operacao = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $operacao
$source = Join-Path $operacao 'programas\operacao_local_json.py'
$bin = Join-Path $operacao 'bin'
$output = Join-Path $bin 'OperacaoLocalJson.exe'
$pythonCandidatos = @(
    (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'),
    (Get-Command py.exe -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Source)
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }
$python = $pythonCandidatos | Select-Object -First 1
if (-not $python) { throw 'Python de compilacao nao encontrado nesta maquina de desenvolvimento.' }
if (-not (Test-Path -LiteralPath $source)) { throw 'Fonte da operacao local nao encontrada.' }

& $python -c "import PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
    & $python -m pip install --disable-pip-version-check --quiet PyInstaller
    if ($LASTEXITCODE -ne 0) { throw 'Nao foi possivel instalar o empacotador.' }
}

$temporario = Join-Path $operacao '_empacotamento'
$temporarioAbsoluto = [System.IO.Path]::GetFullPath($temporario)
$operacaoAbsoluta = [System.IO.Path]::GetFullPath($operacao).TrimEnd('\') + '\'
if (-not $temporarioAbsoluto.StartsWith($operacaoAbsoluta, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'Diretorio temporario fora da operacao local.'
}
if (Test-Path -LiteralPath $temporario) { Remove-Item -LiteralPath $temporario -Recurse -Force }
New-Item -ItemType Directory -Path $temporario -Force | Out-Null
try {
    & $python -m PyInstaller --noconfirm --clean --onefile --name 'OperacaoLocalJson' `
        --paths $root --hidden-import numpy `
        --add-data "$root\equacao.py;." `
        --add-data "$root\motor.py;." `
        --add-data "$root\regua.py;." `
        --add-data "$root\fonte_unica.py;." `
        --add-data "$root\roda_lote_v6.py;." `
        --workpath (Join-Path $temporario 'build') --distpath (Join-Path $temporario 'dist') `
        --specpath $temporario $source
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao empacotar a operacao local.' }
    $gerado = Join-Path $temporario 'dist\OperacaoLocalJson.exe'
    if (-not (Test-Path -LiteralPath $gerado)) { throw 'O empacotamento nao gerou OperacaoLocalJson.exe.' }
    New-Item -ItemType Directory -Path $bin -Force | Out-Null
    if (Test-Path -LiteralPath $output) {
        $hashAnterior = (Get-FileHash -LiteralPath $output -Algorithm SHA256).Hash.ToLowerInvariant()
        $anteriores = Join-Path $bin 'anteriores'
        New-Item -ItemType Directory -Path $anteriores -Force | Out-Null
        Copy-Item -LiteralPath $output -Destination (Join-Path $anteriores ("OperacaoLocalJson-" + $hashAnterior + ".exe")) -Force
    }
    Copy-Item -LiteralPath $gerado -Destination $output -Force
} finally {
    if (Test-Path -LiteralPath $temporario) { Remove-Item -LiteralPath $temporario -Recurse -Force }
}
Get-Item -LiteralPath $output | Select-Object FullName,Length,LastWriteTime
