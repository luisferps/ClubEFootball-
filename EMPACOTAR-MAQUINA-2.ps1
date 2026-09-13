param([string]$Destino)
$ErrorActionPreference='Stop'
$origem=[IO.Path]::GetFullPath($PSScriptRoot).TrimEnd('\')
if(-not $Destino){$Destino=Join-Path ([Environment]::GetFolderPath('Desktop')) ('ClubEfootball-Maquina-2-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))}
$destinoAbsoluto=[IO.Path]::GetFullPath($Destino).TrimEnd('\')
if($destinoAbsoluto.StartsWith($origem+'\',[StringComparison]::OrdinalIgnoreCase) -or $destinoAbsoluto -eq $origem){throw 'Destino deve ficar fora da pasta de origem.'}
if(Test-Path -LiteralPath $destinoAbsoluto){throw 'Destino ja existe. Escolha uma pasta nova para evitar mistura de versoes.'}
$operacao=Join-Path $origem '2-MOTORES\OTIMIZADOR\OPERACAO-LOCAL-JSON'
$ativa=Get-Content -Raw -LiteralPath (Join-Path $operacao 'FILA-ATIVA.json') | ConvertFrom-Json
if(@($ativa.lotes).Count -ne 1 -or $ativa.lotes[0] -ne '39da8ff4-7a4a-4ec7-8641-e81b5677ad4c'){throw 'Baixe e confira a fila v6 antes de empacotar.'}
$ignorar=@(
 '^7-VARREDURA-DO-JOGO/(artefatos|logs|ANALISE-LIVEDATA|RESULTADOS-E-VALIDACOES)/',
 '^2-MOTORES/OTIMIZADOR/(PACOTE-FILA-INTEGRAL|runtime|teste-100)/',
 '^2-MOTORES/OTIMIZADOR/OPERACAO-LOCAL-JSON/(RENOVACOES|RESULTADOS-JSON|HISTORICO-RENOVACOES)/',
 '^2-MOTORES/OTIMIZADOR/OPERACAO-LOCAL-JSON/TESTE-',
 '^2-MOTORES/OTIMIZADOR/OPERACAO-LOCAL-JSON/bin/anteriores/',
 '^2-MOTORES/BONIFICADOR/(fila-local|interface/runtime)/',
 '(^|/)(__pycache__|\.git|\.pytest_cache)/',
 '\.(pyc|lock|zip|bak)$',
 '(^|/)ESTADO-(PROCESSAMENTO|ENVIO).*\.json$',
 '^2-MOTORES/BONIFICADOR/(LEIA-ME|MANIFESTO)-ATUALIZACAO-MAQUINA-2-V12\.',
 '(^|/)\.env($|\.)'
)
New-Item -ItemType Directory -Path $destinoAbsoluto | Out-Null
$manifesto=[Collections.Generic.List[object]]::new()
foreach($arquivo in Get-ChildItem -LiteralPath $origem -Recurse -File -Force){
 $rel=$arquivo.FullName.Substring($origem.Length+1).Replace('\','/')
 if(@($ignorar | Where-Object {$rel -match $_}).Count){continue}
 $alvo=Join-Path $destinoAbsoluto $rel
 New-Item -ItemType Directory -Path (Split-Path -Parent $alvo) -Force | Out-Null
 Copy-Item -LiteralPath $arquivo.FullName -Destination $alvo
 $hash=(Get-FileHash -LiteralPath $arquivo.FullName -Algorithm SHA256).Hash
 if((Get-FileHash -LiteralPath $alvo -Algorithm SHA256).Hash -ne $hash){throw "Copia divergente: $rel"}
 $manifesto.Add([pscustomobject]@{Arquivo=$rel;Bytes=$arquivo.Length;SHA256=$hash})
}
$manifesto | Export-Csv -LiteralPath (Join-Path $destinoAbsoluto 'MANIFESTO-ENTREGA.csv') -NoTypeInformation -Encoding UTF8
Write-Output "Pasta completa: $destinoAbsoluto"
Write-Output "Arquivos copiados e conferidos: $($manifesto.Count)"
