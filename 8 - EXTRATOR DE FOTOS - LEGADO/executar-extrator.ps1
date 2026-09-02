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

$cloudinaryKey = Ler-Segredo 'Cole a API Key do Cloudinary (ela não aparecerá)'
$cloudinarySecret = Ler-Segredo 'Cole a API Secret do Cloudinary (ela não aparecerá)'
if ([string]::IsNullOrWhiteSpace($cloudinaryKey) -or [string]::IsNullOrWhiteSpace($cloudinarySecret)) {
  throw 'A API Key e a API Secret do Cloudinary são obrigatórias.'
}
$cloudinaryUrl = 'cloudinary://{0}:{1}@demsusjwf' -f [Uri]::EscapeDataString($cloudinaryKey), [Uri]::EscapeDataString($cloudinarySecret)
try {
  $env:CLOUDINARY_API_KEY = $cloudinaryKey
  $env:CLOUDINARY_API_SECRET = $cloudinarySecret
  $env:CLOUDINARY_CLOUD_NAME = 'demsusjwf'
  $env:CLOUDINARY_URL = $cloudinaryUrl
  $env:CLOUDINARY_UPLOAD_PRESET = 'clubefutebol_cards_no_overwrite'
  & $node $extrator --input $arquivoResolvido --limit $Limite --upload
  if ($LASTEXITCODE -ne 0) { throw "O extrator terminou com código $LASTEXITCODE." }
} finally {
  Remove-Item Env:CLOUDINARY_API_KEY -ErrorAction SilentlyContinue
  Remove-Item Env:CLOUDINARY_API_SECRET -ErrorAction SilentlyContinue
  Remove-Item Env:CLOUDINARY_CLOUD_NAME -ErrorAction SilentlyContinue
  Remove-Item Env:CLOUDINARY_URL -ErrorAction SilentlyContinue
  Remove-Item Env:CLOUDINARY_UPLOAD_PRESET -ErrorAction SilentlyContinue
  $cloudinaryKey = $null
  $cloudinarySecret = $null
  $cloudinaryUrl = $null
}

Write-Host ''
Write-Host 'Concluído. Consulte output\runs para manifesto, resumo e log. O banco não foi alterado.' -ForegroundColor Green
