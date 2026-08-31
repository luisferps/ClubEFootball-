$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$source = Join-Path $root 'windows-app\ClubEfootballExtractorLauncher.cs'
$icon = Join-Path $root 'windows-app\assets\icone-extrator-clubefootball.ico'
$output = Join-Path $root 'Extrator eFootball.exe'
$staging = Join-Path $root 'Extrator eFootball.novo.exe'
$compiler64 = 'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$compiler32 = 'C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe'
$compiler = if (Test-Path -LiteralPath $compiler64) { $compiler64 } elseif (Test-Path -LiteralPath $compiler32) { $compiler32 } else { $null }

if (-not $compiler) { throw 'Compilador .NET do Windows não encontrado.' }
if (-not (Test-Path -LiteralPath $icon)) { throw 'Ícone do aplicativo não encontrado.' }
if (-not (Test-Path -LiteralPath $source)) { throw 'Código-fonte do launcher não encontrado.' }

# Compila primeiro em um arquivo separado. Assim, a compilação não falha só
# porque uma versão anterior do Extrator ainda está aberta no Windows.
if (Test-Path -LiteralPath $staging) {
    Remove-Item -LiteralPath $staging -Force -ErrorAction SilentlyContinue
}

& $compiler /nologo /target:winexe /optimize+ /platform:anycpu /reference:System.dll /reference:System.Security.dll /reference:System.Drawing.dll /reference:System.Windows.Forms.dll /reference:System.Web.Extensions.dll "/win32icon:$icon" "/out:$staging" $source
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $staging)) {
    throw 'Falha ao compilar o aplicativo Windows.'
}

# Encerra somente o processo cujo executável é exatamente o Extrator desta
# pasta. Nenhum navegador, Python ou outro programa é finalizado aqui.
$targetPath = [System.IO.Path]::GetFullPath($output)
$runningExtractors = Get-Process -ErrorAction SilentlyContinue | Where-Object {
    try {
        $_.Path -and ([System.IO.Path]::GetFullPath($_.Path) -ieq $targetPath)
    }
    catch {
        $false
    }
}

if ($runningExtractors) {
    Write-Host 'Fechando o Extrator antigo para instalar a versão nova...'
    $runningExtractors | Stop-Process -Force -ErrorAction SilentlyContinue
    foreach ($process in $runningExtractors) {
        try { $process.WaitForExit(5000) | Out-Null } catch { }
    }
}

# Espera até 15 segundos caso o Windows ou o antivírus ainda esteja liberando
# o arquivo antigo. Depois substitui o EXE de uma só vez.
$deadline = (Get-Date).AddSeconds(15)
$unlocked = $false
while ((Get-Date) -lt $deadline) {
    try {
        if (Test-Path -LiteralPath $output) {
            $stream = [System.IO.File]::Open(
                $output,
                [System.IO.FileMode]::Open,
                [System.IO.FileAccess]::ReadWrite,
                [System.IO.FileShare]::None
            )
            $stream.Dispose()
        }
        $unlocked = $true
        break
    }
    catch {
        Start-Sleep -Milliseconds 250
    }
}

if (-not $unlocked) {
    Remove-Item -LiteralPath $staging -Force -ErrorAction SilentlyContinue
    throw 'O Extrator antigo continuou em uso. Feche a janela do Extrator e execute o botão 4 novamente.'
}

Move-Item -LiteralPath $staging -Destination $output -Force
if (-not (Test-Path -LiteralPath $output)) {
    throw 'O novo executável foi compilado, mas não pôde ser instalado.'
}

Get-Item -LiteralPath $output | Select-Object FullName,Length,LastWriteTime
