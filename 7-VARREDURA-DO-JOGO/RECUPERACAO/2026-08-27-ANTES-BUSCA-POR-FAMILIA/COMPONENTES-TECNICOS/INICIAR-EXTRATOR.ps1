$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$bundledPython = 'C:\Users\Luis Fernando\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$python = $null

if (Get-Command py -ErrorAction SilentlyContinue) {
  $python = 'py'
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
  $python = 'python'
} elseif (Test-Path -LiteralPath $bundledPython) {
  $python = $bundledPython
} else {
  throw 'Python 3 não encontrado. Instale Python 3 e execute INSTALAR-DEPENDENCIAS.cmd.'
}

$vendor = Join-Path $root 'executor\vendor'
if (Test-Path -LiteralPath $vendor) {
  $env:PYTHONPATH = $vendor
}

if (-not $env:CLUBEF_SUPABASE_DB_URL) {
  $connect = Read-Host 'Conectar ao Supabase para validar/aplicar depois? Digite S ou N'
  if ($connect.Trim().ToUpperInvariant() -eq 'S') {
    $secureDsn = Read-Host 'Cole a connection string PostgreSQL completa (ela não será salva)' -AsSecureString
    $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureDsn)
    try {
      $env:CLUBEF_SUPABASE_DB_URL = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
    } finally {
      [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
    }
  }
}

Push-Location $root
try {
  if ($python -eq 'py') {
    & py -3 'executor\executor_local.py'
  } else {
    & $python 'executor\executor_local.py'
  }
} finally {
  Pop-Location
}
