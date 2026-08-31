$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$source = Join-Path $root 'windows-app\ClubEfootballOtimizadorLauncher.cs'
$icon = Join-Path $root 'windows-app\assets\icone-otimizador-clubefootball.ico'
$output = Join-Path $root 'Otimizador ClubEfootball.exe'
$compilarServico = Join-Path $root 'windows-app\COMPILAR-SERVICO-PORTATIL.ps1'
$compiler64 = 'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$compiler32 = 'C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe'
$compiler = if (Test-Path -LiteralPath $compiler64) { $compiler64 } elseif (Test-Path -LiteralPath $compiler32) { $compiler32 } else { $null }
if (-not $compiler) { throw 'Compilador .NET do Windows não encontrado.' }
if (-not (Test-Path -LiteralPath $icon)) { throw 'Ícone do aplicativo não encontrado.' }
if (-not (Test-Path -LiteralPath $compilarServico)) { throw 'Compilador do serviço portátil não encontrado.' }
& $compilarServico
if (-not $?) { throw 'Falha ao preparar o serviço portátil do Otimizador.' }
$precisaCompilar = -not (Test-Path -LiteralPath $output)
if (-not $precisaCompilar) {
    $exeData = (Get-Item -LiteralPath $output).LastWriteTimeUtc
    $precisaCompilar = (Get-Item -LiteralPath $source).LastWriteTimeUtc -gt $exeData -or
                       (Get-Item -LiteralPath $icon).LastWriteTimeUtc -gt $exeData
}
if (-not $precisaCompilar) {
    Get-Item -LiteralPath $output | Select-Object FullName,Length,LastWriteTime
    return
}
& $compiler /nologo /target:winexe /optimize+ /platform:anycpu /reference:System.dll /reference:System.Windows.Forms.dll "/win32icon:$icon" "/out:$output" $source
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $output)) { throw 'Falha ao compilar o aplicativo Windows.' }
Get-Item -LiteralPath $output | Select-Object FullName,Length,LastWriteTime
