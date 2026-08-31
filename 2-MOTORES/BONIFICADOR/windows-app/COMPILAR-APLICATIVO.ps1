$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$source = Join-Path $root 'windows-app\ClubEfootballBonificadorLauncher.cs'
$icon = Join-Path $root 'windows-app\assets\icone-bonificador-clubefootball.ico'
$output = Join-Path $root 'Bonificador ClubEfootball.exe'
$component = Join-Path $root 'windows-app\assets\BonificadorComponente.bin'
$compiler64 = 'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$compiler32 = 'C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe'
$compiler = if (Test-Path -LiteralPath $compiler64) { $compiler64 } elseif (Test-Path -LiteralPath $compiler32) { $compiler32 } else { $null }
if (-not $compiler) { throw 'Compilador .NET do Windows não encontrado.' }
if (-not (Test-Path -LiteralPath $source)) { throw 'Fonte do lançador não encontrada.' }
if (-not (Test-Path -LiteralPath $icon)) { throw 'Ícone do aplicativo não encontrado.' }
if (-not (Test-Path -LiteralPath $component)) { throw 'Payload interno do componente não encontrado.' }

& $compiler /nologo /target:winexe /optimize+ /platform:anycpu /reference:System.dll /reference:System.Drawing.dll /reference:System.Windows.Forms.dll /reference:System.Web.Extensions.dll "/win32icon:$icon" "/resource:$component,BonificadorComponente" "/out:$output" $source
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $output)) { throw 'Falha ao compilar o aplicativo Windows.' }
Get-Item -LiteralPath $output | Select-Object FullName,Length,LastWriteTime
