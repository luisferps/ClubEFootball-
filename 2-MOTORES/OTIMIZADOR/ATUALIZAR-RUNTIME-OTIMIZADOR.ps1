param([string]$Destino)
$ErrorActionPreference = 'Stop'
$pacoteRaiz = $PSScriptRoot
$fonteRaiz = Join-Path $pacoteRaiz 'RUNTIME'
$manifesto = Get-Content -LiteralPath (Join-Path $pacoteRaiz 'MANIFESTO-ATUALIZACAO.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ($manifesto.contrato -ne 'atualizacao_runtime_otimizador_v1') { throw 'Manifesto de atualizacao invalido.' }
if (Get-Process -Name OperacaoLocalJson -ErrorAction SilentlyContinue) {
    throw 'Feche o processamento e o enviador pelo Ctrl+C antes de atualizar. Nenhum processo foi encerrado.'
}
function HashArquivo([string]$Caminho) {
    $fluxo = [IO.File]::OpenRead($Caminho)
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return [BitConverter]::ToString($sha.ComputeHash($fluxo)).Replace('-','').ToLowerInvariant() }
    finally { $sha.Dispose(); $fluxo.Dispose() }
}
function CaminhoDentro([string]$Base, [string]$Relativo) {
    if ([IO.Path]::IsPathRooted($Relativo) -or $Relativo -match '(^|[\\/])\.\.([\\/]|$)') { throw 'Caminho relativo invalido.' }
    $baseFinal = [IO.Path]::GetFullPath($Base).TrimEnd('\') + '\'
    $final = [IO.Path]::GetFullPath((Join-Path $Base $Relativo))
    if (-not $final.StartsWith($baseFinal,[StringComparison]::OrdinalIgnoreCase)) { throw 'Caminho fora da pasta selecionada.' }
    $verificar = $final
    while ($verificar -and $verificar.Length -ge $baseFinal.TrimEnd('\').Length) {
        if (Test-Path -LiteralPath $verificar) {
            $item = Get-Item -LiteralPath $verificar -Force
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Atualizacao recusada em link ou juncao de pastas.' }
        }
        $verificar = Split-Path -Parent $verificar
    }
    return $final
}
if (-not $Destino) {
    Add-Type -AssemblyName System.Windows.Forms
    $dialogo = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialogo.Description = 'Selecione a pasta onde voce abre PROCESSAR-FILA.bat (OPERACAO-LOCAL-JSON).'
    $dialogo.ShowNewFolderButton = $false
    if ($dialogo.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { Write-Host 'Atualizacao cancelada.'; exit 0 }
    $Destino = $dialogo.SelectedPath
}
$Destino = [IO.Path]::GetFullPath($Destino)
if (-not (Test-Path -LiteralPath (Join-Path $Destino 'PROCESSAR-FILA.bat')) -or
    -not (Test-Path -LiteralPath (Join-Path $Destino 'bin\OperacaoLocalJson.exe'))) {
    throw 'Selecione a pasta existente que contem PROCESSAR-FILA.bat e bin\OperacaoLocalJson.exe.'
}
$arquivos = @($manifesto.arquivos)
if ($arquivos.Count -eq 0 -or @($arquivos | Group-Object caminho | Where-Object Count -gt 1).Count -gt 0) {
    throw 'Lista de arquivos vazia ou repetida.'
}
foreach ($arquivo in $arquivos) {
    if ($arquivo.caminho -match '(^|[\\/])(config\.txt|RESULTADOS-JSON|runtime)([\\/]|$)') {
        throw 'Pacote tentou substituir configuracao local ou historico.'
    }
    $fonte = CaminhoDentro $fonteRaiz $arquivo.caminho
    $alvo = CaminhoDentro $Destino $arquivo.caminho
    if (-not (Test-Path -LiteralPath $fonte -PathType Leaf) -or
        (HashArquivo $fonte) -ne $arquivo.sha256) {
        throw ('Arquivo ausente ou corrompido no ZIP: ' + $arquivo.caminho)
    }
}
$backupRelativo = 'ATUALIZACOES\backup-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N')
$backup = CaminhoDentro $Destino $backupRelativo
New-Item -ItemType Directory -Path $backup -Force | Out-Null
$aplicados = New-Object System.Collections.Generic.List[object]
try {
    # A selecao de fila so passa a apontar aos novos pacotes no fim.
    foreach ($arquivo in ($arquivos | Sort-Object @{Expression={ if ($_.caminho -eq 'FILA-ATIVA.json') {1} else {0} }},caminho)) {
        $fonte = CaminhoDentro $fonteRaiz $arquivo.caminho
        $alvo = CaminhoDentro $Destino $arquivo.caminho
        $anterior = CaminhoDentro $backup $arquivo.caminho
        $existia = Test-Path -LiteralPath $alvo
        if ($existia) {
            New-Item -ItemType Directory -Path (Split-Path -Parent $anterior) -Force | Out-Null
            Copy-Item -LiteralPath $alvo -Destination $anterior -Force
        }
        $aplicados.Add([pscustomobject]@{caminho=$arquivo.caminho; existia=$existia})
        New-Item -ItemType Directory -Path (Split-Path -Parent $alvo) -Force | Out-Null
        Copy-Item -LiteralPath $fonte -Destination $alvo -Force
        if ((HashArquivo $alvo) -ne $arquivo.sha256) {
            throw ('Conferencia falhou: ' + $arquivo.caminho)
        }
    }
    Copy-Item -LiteralPath (Join-Path $pacoteRaiz 'MANIFESTO-ATUALIZACAO.json') -Destination (Join-Path $backup 'APLICADO.json')
} catch {
    for ($indice=$aplicados.Count-1; $indice -ge 0; $indice--) {
        $item=$aplicados[$indice]
        $alvo=CaminhoDentro $Destino $item.caminho
        if ($item.existia) {
            Copy-Item -LiteralPath (CaminhoDentro $backup $item.caminho) -Destination $alvo -Force
        } elseif (Test-Path -LiteralPath $alvo) {
            Remove-Item -LiteralPath $alvo -Force
        }
    }
    throw
}
Write-Host ''
Write-Host 'ATUALIZADO E CONFERIDO. Nenhum processamento foi iniciado.' -ForegroundColor Green
Write-Host ('Destino: ' + $Destino)
Write-Host ('Backup: ' + $backup)
Write-Host 'config.txt e RESULTADOS-JSON foram preservados.'
Write-Host 'Use os atalhos habituais somente quando decidir retomar o Otimizador.'
