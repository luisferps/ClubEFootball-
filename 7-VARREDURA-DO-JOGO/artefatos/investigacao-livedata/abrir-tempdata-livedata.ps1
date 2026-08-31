[CmdletBinding()]
param(
    [Parameter()]
    [string]$InputDirectory = 'C:\ProgramData\KONAMI\eFootball\ST\TempData\Download',

    [Parameter()]
    [string]$OutputDirectory = (Join-Path $PSScriptRoot 'pngs-20260831'),

    [Parameter()]
    [switch]$InspectOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Esta chave de 32 bytes foi reconstruida estaticamente do eFootball.exe local.
# O jogo nao e iniciado e nenhum arquivo de origem e alterado por este script.
$AesKeyHex = '43740981523cdc171e71de2ccab1a5a9b86f4b833196c55facd4bd25846c33f5'

function ConvertFrom-HexString {
    param([Parameter(Mandatory)][string]$Hex)

    if (($Hex.Length % 2) -ne 0 -or $Hex -notmatch '^[0-9a-fA-F]+$') {
        throw "Texto hexadecimal invalido."
    }

    $bytes = [byte[]]::new($Hex.Length / 2)
    for ($i = 0; $i -lt $bytes.Length; $i++) {
        $bytes[$i] = [Convert]::ToByte($Hex.Substring($i * 2, 2), 16)
    }
    return $bytes
}

function ConvertTo-HexString {
    param([Parameter(Mandatory)][byte[]]$Bytes)
    return ([Convert]::ToHexString($Bytes)).ToLowerInvariant()
}

function Get-Sha256Hex {
    param([Parameter(Mandatory)][byte[]]$Bytes)

    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        return (ConvertTo-HexString -Bytes ($sha.ComputeHash($Bytes)))
    }
    finally {
        $sha.Dispose()
    }
}

function Read-UInt32BigEndian {
    param(
        [Parameter(Mandatory)][byte[]]$Bytes,
        [Parameter(Mandatory)][int]$Offset
    )

    if ($Offset -lt 0 -or ($Offset + 4) -gt $Bytes.Length) {
        throw "Leitura fora do limite no deslocamento $Offset."
    }

    return [uint32]((([uint32]$Bytes[$Offset]) -shl 24) -bor
        (([uint32]$Bytes[$Offset + 1]) -shl 16) -bor
        (([uint32]$Bytes[$Offset + 2]) -shl 8) -bor
        ([uint32]$Bytes[$Offset + 3]))
}

function Test-PngStructure {
    param([Parameter(Mandatory)][byte[]]$Bytes)

    $signature = [byte[]](0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a)
    if ($Bytes.Length -lt 33) {
        return [pscustomobject]@{ Valid = $false; Width = $null; Height = $null; Reason = 'arquivo curto demais' }
    }
    for ($i = 0; $i -lt $signature.Length; $i++) {
        if ($Bytes[$i] -ne $signature[$i]) {
            return [pscustomobject]@{ Valid = $false; Width = $null; Height = $null; Reason = 'assinatura PNG ausente' }
        }
    }

    $position = 8
    $width = $null
    $height = $null
    $foundIhdr = $false
    $foundIend = $false

    while (($position + 12) -le $Bytes.Length) {
        $chunkLength = [uint64](Read-UInt32BigEndian -Bytes $Bytes -Offset $position)
        $chunkEnd = [uint64]$position + 12 + $chunkLength
        if ($chunkEnd -gt [uint64]$Bytes.Length) {
            return [pscustomobject]@{ Valid = $false; Width = $width; Height = $height; Reason = 'bloco PNG ultrapassa o fim do arquivo' }
        }

        $chunkType = [Text.Encoding]::ASCII.GetString($Bytes, $position + 4, 4)
        if ($chunkType -eq 'IHDR') {
            if ($position -ne 8 -or $chunkLength -ne 13) {
                return [pscustomobject]@{ Valid = $false; Width = $null; Height = $null; Reason = 'IHDR invalido' }
            }
            $width = Read-UInt32BigEndian -Bytes $Bytes -Offset ($position + 8)
            $height = Read-UInt32BigEndian -Bytes $Bytes -Offset ($position + 12)
            $foundIhdr = $true
        }
        elseif ($chunkType -eq 'IEND') {
            if ($chunkLength -ne 0) {
                return [pscustomobject]@{ Valid = $false; Width = $width; Height = $height; Reason = 'IEND invalido' }
            }
            $foundIend = $true
            if ($chunkEnd -ne [uint64]$Bytes.Length) {
                return [pscustomobject]@{ Valid = $false; Width = $width; Height = $height; Reason = 'bytes inesperados depois de IEND' }
            }
            break
        }

        $position = [int]$chunkEnd
    }

    if (-not $foundIhdr -or -not $foundIend) {
        return [pscustomobject]@{ Valid = $false; Width = $width; Height = $height; Reason = 'IHDR ou IEND ausente' }
    }

    return [pscustomobject]@{ Valid = $true; Width = $width; Height = $height; Reason = 'assinatura, IHDR e IEND validos' }
}

$resolvedInput = (Resolve-Path -LiteralPath $InputDirectory).Path
$sourceFiles = @(
    Get-ChildItem -LiteralPath $resolvedInput -File |
        Where-Object { $_.Name -match '^[0-9a-fA-F]{64}\.[0-9]+$' } |
        Sort-Object Name
)

if ($sourceFiles.Count -eq 0) {
    throw "Nenhum arquivo com o padrao esperado foi encontrado em $resolvedInput."
}

$resolvedOutput = $null
if (-not $InspectOnly) {
    if (Test-Path -LiteralPath $OutputDirectory) {
        $existing = @(Get-ChildItem -LiteralPath $OutputDirectory -Force)
        if ($existing.Count -gt 0) {
            throw "A pasta de saida ja existe e nao esta vazia: $OutputDirectory"
        }
    }
    else {
        $null = New-Item -ItemType Directory -Path $OutputDirectory
    }
    $resolvedOutput = (Resolve-Path -LiteralPath $OutputDirectory).Path
}

$key = ConvertFrom-HexString -Hex $AesKeyHex
$results = [Collections.Generic.List[object]]::new()

foreach ($file in $sourceFiles) {
    $before = Get-Item -LiteralPath $file.FullName
    $beforeHash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    $encrypted = [IO.File]::ReadAllBytes($file.FullName)

    if ($encrypted.Length -le 32 -or (($encrypted.Length - 16) % 16) -ne 0) {
        throw "Tamanho cifrado inesperado em $($file.FullName)."
    }

    $iv = [byte[]]::new(16)
    [Array]::Copy($encrypted, 0, $iv, 0, 16)
    $ciphertext = [byte[]]::new($encrypted.Length - 16)
    [Array]::Copy($encrypted, 16, $ciphertext, 0, $ciphertext.Length)

    $aes = [Security.Cryptography.Aes]::Create()
    try {
        $aes.KeySize = 256
        $aes.BlockSize = 128
        $aes.Mode = [Security.Cryptography.CipherMode]::CBC
        $aes.Padding = [Security.Cryptography.PaddingMode]::PKCS7
        $aes.Key = $key
        $aes.IV = $iv
        $decryptor = $aes.CreateDecryptor()
        try {
            # TransformFinalBlock tambem valida e remove o padding PKCS#7.
            $plain = $decryptor.TransformFinalBlock($ciphertext, 0, $ciphertext.Length)
        }
        finally {
            $decryptor.Dispose()
        }
    }
    finally {
        $aes.Dispose()
    }

    $png = Test-PngStructure -Bytes $plain
    if (-not $png.Valid) {
        throw "A decifragem de $($file.Name) nao resultou em PNG valido: $($png.Reason)."
    }

    $plainHash = Get-Sha256Hex -Bytes $plain
    $outputPath = $null
    if (-not $InspectOnly) {
        $outputPath = Join-Path $resolvedOutput ($file.Name + '.png')
        if (Test-Path -LiteralPath $outputPath) {
            throw "O script nao sobrescreve resultado existente: $outputPath"
        }
        [IO.File]::WriteAllBytes($outputPath, $plain)
    }

    $after = Get-Item -LiteralPath $file.FullName
    $afterHash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    $sourceUnchanged = (
        $before.Length -eq $after.Length -and
        $before.LastWriteTimeUtc -eq $after.LastWriteTimeUtc -and
        $beforeHash -eq $afterHash
    )
    if (-not $sourceUnchanged) {
        throw "A verificacao de somente leitura falhou para $($file.FullName)."
    }

    $results.Add([pscustomobject][ordered]@{
        arquivo_origem = $file.FullName
        nome_origem = $file.Name
        tamanho_cifrado_bytes = [int64]$encrypted.Length
        sha256_arquivo_cifrado = $beforeHash
        iv_hex = ConvertTo-HexString -Bytes $iv
        metodo = 'AES-256-CBC; IV nos 16 primeiros bytes; PKCS#7'
        padding_pkcs7_valido = $true
        formato_decifrado = 'PNG'
        validacao_png = $png.Reason
        largura = [uint32]$png.Width
        altura = [uint32]$png.Height
        tamanho_png_bytes = [int64]$plain.Length
        sha256_png = $plainHash
        arquivo_png = $outputPath
        origem_permaneceu_inalterada = $sourceUnchanged
    })
}

$manifest = [pscustomobject][ordered]@{
    gerado_em_utc = [DateTime]::UtcNow.ToString('o')
    ferramenta = $MyInvocation.MyCommand.Path
    somente_leitura_na_origem = $true
    pasta_origem = $resolvedInput
    total_arquivos = $results.Count
    derivacao_chave = '32 bytes reconstruidos estaticamente do eFootball.exe local; objeto em RVA 0x6E6FA70, inicializacao em RVA 0x46E28B7, consumo pelo OnlineSystemHttpAes em RVA 0x480DA10'
    metodo = 'AES-256-CBC; IV nos 16 primeiros bytes; dados cifrados a partir do byte 16; padding PKCS#7'
    itens = $results
}

if ($InspectOnly) {
    $manifest | ConvertTo-Json -Depth 5
}
else {
    $jsonPath = Join-Path $resolvedOutput 'manifesto.json'
    $csvPath = Join-Path $resolvedOutput 'manifesto.csv'
    $manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $jsonPath -Encoding utf8
    $results | Export-Csv -LiteralPath $csvPath -NoTypeInformation -Encoding utf8
    $manifest | ConvertTo-Json -Depth 5
}
