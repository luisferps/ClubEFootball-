param(
  [string]$ArquivoIds,
  [ValidateRange(1, 100)]
  [int]$Limite = 1
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$pastaFerramenta = Split-Path -Parent $MyInvocation.MyCommand.Path
$exemplo = Join-Path $pastaFerramenta 'exemplos\cards-exemplo.txt'
$extrator = Join-Path $pastaFerramenta 'card-image-extractor.mjs'
. (Join-Path $pastaFerramenta 'bootstrap-node.ps1')

function Ler-Segredo([string]$Mensagem) {
  $seguro = Read-Host $Mensagem -AsSecureString
  $ponteiro = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($seguro)
  try {
    return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ponteiro)
  } finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ponteiro)
  }
}

$ArquivoIds = if ([string]::IsNullOrWhiteSpace($ArquivoIds)) { $exemplo } else { $ArquivoIds.Trim('"') }
$arquivoResolvido = (Resolve-Path -LiteralPath $ArquivoIds).Path
if ($Limite -lt 1 -or $Limite -gt 100) { throw 'A quantidade deve ficar entre 1 e 100.' }

$node = Obter-Node -PastaFerramenta $pastaFerramenta

$cloudinaryUrl = Ler-Segredo 'Cole a API Environment variable do Cloudinary (ela não aparecerá)'
$cloudinaryUri = [Uri]$cloudinaryUrl
if ($cloudinaryUri.Scheme -ne 'cloudinary' -or $cloudinaryUri.Host -ne 'demsusjwf') {
  throw 'A API Environment variable não pertence ao Cloudinary esperado (demsusjwf).'
}
$credenciaisCloudinary = $cloudinaryUri.UserInfo.Split(':', 2)
if ($credenciaisCloudinary.Count -ne 2) { throw 'A API Environment variable do Cloudinary está incompleta.' }
$cloudinaryKey = [Uri]::UnescapeDataString($credenciaisCloudinary[0])
$cloudinarySecret = [Uri]::UnescapeDataString($credenciaisCloudinary[1])
if ([string]::IsNullOrWhiteSpace($cloudinaryKey) -or [string]::IsNullOrWhiteSpace($cloudinarySecret)) {
  throw 'A API Environment variable do Cloudinary está incompleta.'
}
$supabaseSecret = Ler-Segredo 'Cole a chave service_role do Supabase (ela não aparecerá)'

try {
  $env:CLOUDINARY_API_KEY = $cloudinaryKey
  $env:CLOUDINARY_API_SECRET = $cloudinarySecret
  $env:CLOUDINARY_CLOUD_NAME = 'demsusjwf'
  $env:CLOUDINARY_UPLOAD_PRESET = 'clubefutebol_cards_no_overwrite'
  $env:SUPABASE_URL = 'https://trqqpsnafpbudtvvicch.supabase.co'
  $env:SUPABASE_SERVICE_ROLE_KEY = $supabaseSecret

  & $node $extrator --input $arquivoResolvido --limit $Limite --apply
  if ($LASTEXITCODE -ne 0) { throw "O extrator terminou com código $LASTEXITCODE." }
} finally {
  Remove-Item Env:CLOUDINARY_API_KEY -ErrorAction SilentlyContinue
  Remove-Item Env:CLOUDINARY_API_SECRET -ErrorAction SilentlyContinue
  Remove-Item Env:CLOUDINARY_CLOUD_NAME -ErrorAction SilentlyContinue
  Remove-Item Env:CLOUDINARY_UPLOAD_PRESET -ErrorAction SilentlyContinue
  Remove-Item Env:SUPABASE_URL -ErrorAction SilentlyContinue
  Remove-Item Env:SUPABASE_SERVICE_ROLE_KEY -ErrorAction SilentlyContinue
  $cloudinaryKey = $null
  $cloudinarySecret = $null
  $cloudinaryUrl = $null
  $cloudinaryUri = $null
  $credenciaisCloudinary = $null
  $supabaseSecret = $null
}

Write-Host ''
Write-Host 'Concluído. Consulte a pasta output\runs para o resumo e o log.' -ForegroundColor Green

