$ErrorActionPreference = 'Stop'
$root = 'C:\Users\Luis Fernando\Downloads\Clubefootball V4\7-VARREDURA-DO-JOGO'
$snapshot = Join-Path $root 'RECUPERACAO\2026-08-28-ANTES-IMPETOS-OPERACIONAL'
Copy-Item -LiteralPath (Join-Path $snapshot 'app\extrator-core.js') -Destination (Join-Path $root 'app\extrator-core.js') -Force
Copy-Item -LiteralPath (Join-Path $snapshot 'executor\executor_local.py') -Destination (Join-Path $root 'executor\executor_local.py') -Force
Copy-Item -LiteralPath (Join-Path $snapshot 'DOCUMENTACAO\MANUAL-DO-EXTRATOR.md') -Destination (Join-Path $root 'DOCUMENTACAO\MANUAL-DO-EXTRATOR.md') -Force
Remove-Item -LiteralPath (Join-Path $root 'executor\impetos.py') -Force
Remove-Item -LiteralPath (Join-Path $root 'RESULTADOS-E-VALIDACOES\TESTES\teste-impetos-fisicos.js') -Force
Remove-Item -LiteralPath (Join-Path $root 'RESULTADOS-E-VALIDACOES\TESTES\gerar-snapshot-impetos.js') -Force
Remove-Item -LiteralPath (Join-Path $root 'RESULTADOS-E-VALIDACOES\TESTES\teste-impetos-banco-readonly.py') -Force
Write-Output 'Rollback local de Ímpetos concluído. Banco não exige rollback: integração e testes foram somente leitura.'
