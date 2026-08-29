$ErrorActionPreference = 'Stop'

$raiz = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)))
$alvos = @(
    (Join-Path $raiz '2-MOTORES\BONIFICADOR\RODAR-INTERFACE-BONIFICADOR.bat'),
    (Join-Path $raiz '2-MOTORES\BONIFICADOR\Bonificador ClubEfootball.exe'),
    (Join-Path $raiz '2-MOTORES\BONIFICADOR\windows-app'),
    (Join-Path $raiz '2-MOTORES\BONIFICADOR\interface')
)

foreach ($alvo in $alvos) {
    if (-not (Test-Path -LiteralPath $alvo)) {
        throw "Rollback interrompido: alvo ausente $alvo"
    }
}

Remove-Item -LiteralPath $alvos[0] -Force
Remove-Item -LiteralPath $alvos[1] -Force
Remove-Item -LiteralPath $alvos[2] -Recurse -Force
Remove-Item -LiteralPath $alvos[3] -Recurse -Force
Write-Host 'Interface local do Bonificador removida; motor e contratos permaneceram intactos.'
