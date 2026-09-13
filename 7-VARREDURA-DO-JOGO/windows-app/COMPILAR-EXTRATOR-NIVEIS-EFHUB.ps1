$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$source = Join-Path $root 'windows-app\ClubEfootballEfhubLevelsLauncher.cs'
$icon = Join-Path $root 'windows-app\assets\icone-extrator-clubefootball.ico'
$output = Join-Path $root 'Extrator Niveis eFHUB.exe'
$staging = Join-Path $root 'Extrator Niveis eFHUB.novo.exe'
$compiler64 = 'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$compiler32 = 'C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe'
$compiler = if (Test-Path -LiteralPath $compiler64) { $compiler64 } elseif (Test-Path -LiteralPath $compiler32) { $compiler32 } else { $null }

if (-not $compiler) { throw 'Compilador .NET do Windows não encontrado.' }
if (-not (Test-Path -LiteralPath $icon)) { throw 'Ícone do aplicativo não encontrado.' }

if (Test-Path -LiteralPath $staging) { Remove-Item -LiteralPath $staging -Force }
& $compiler /nologo /target:winexe /optimize+ /platform:anycpu /reference:System.dll /reference:System.Security.dll /reference:System.Drawing.dll /reference:System.Windows.Forms.dll /reference:System.Web.Extensions.dll "/win32icon:$icon" "/out:$staging" $source
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $staging)) { throw 'Falha ao compilar o Extrator de Níveis eFHUB.' }

$targetPath = [System.IO.Path]::GetFullPath($output)
$running = Get-Process -ErrorAction SilentlyContinue | Where-Object {
    try { $_.Path -and ([System.IO.Path]::GetFullPath($_.Path) -ieq $targetPath) } catch { $false }
}
if ($running) { $running | Stop-Process -Force; foreach ($process in $running) { try { $process.WaitForExit(5000) | Out-Null } catch { } } }
Move-Item -LiteralPath $staging -Destination $output -Force
Get-Item -LiteralPath $output | Select-Object FullName,Length,LastWriteTime
