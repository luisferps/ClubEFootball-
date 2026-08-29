$ErrorActionPreference = 'Stop'

$raiz = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)))
$origem = Join-Path $raiz '2-MOTORES\BONIFICADOR\motor_bonus.py'
$destino = Join-Path $raiz '2-MOTORES\motor_bonus.py'

if (-not (Test-Path -LiteralPath $origem)) {
    throw "Recuperação interrompida: executável novo não encontrado em $origem"
}
if (Test-Path -LiteralPath $destino) {
    throw "Recuperação interrompida: caminho histórico já existe em $destino"
}

Move-Item -LiteralPath $origem -Destination $destino
Write-Host 'Bonificador restaurado em 2-MOTORES\motor_bonus.py.'
