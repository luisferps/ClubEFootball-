param(
  [Parameter(Mandatory=$true)][string]$Python,
  [Parameter(Mandatory=$true)][string]$PastaTrabalho
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$servidor = Join-Path $root 'interface\servidor.py'
$motor = Join-Path $root 'motor_bonus.py'
$altura = Join-Path $root 'altura_independente.py'
$destino = Join-Path $root 'windows-app\assets\BonificadorComponente.bin'
$dist = Join-Path $PastaTrabalho 'dist'
$build = Join-Path $PastaTrabalho 'build'
$spec = Join-Path $PastaTrabalho 'spec'
foreach ($arquivo in @($Python,$servidor,$motor,$altura)) {
  if (-not (Test-Path -LiteralPath $arquivo -PathType Leaf)) {
    throw "Arquivo obrigatório ausente: $arquivo"
  }
}
New-Item -ItemType Directory -Force -Path $PastaTrabalho,$dist,$build,$spec | Out-Null
& $Python -m PyInstaller --noconfirm --clean --onefile --console `
  --name BonificadorComponente `
  --distpath $dist --workpath $build --specpath $spec `
  --add-data "${motor}:." --add-data "${altura}:." $servidor
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller não concluiu o componente.' }
$gerado = Join-Path $dist 'BonificadorComponente.exe'
if (-not (Test-Path -LiteralPath $gerado -PathType Leaf)) {
  throw 'Componente gerado não foi encontrado.'
}
Copy-Item -LiteralPath $gerado -Destination $destino -Force
Get-FileHash -Algorithm SHA256 -LiteralPath $destino

