# Start Kaurivo's private, free-only Windows worker under the CURRENT user.
# The secret is stored only as a Windows DPAPI user-protected blob.
$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$settings = Join-Path $env:LOCALAPPDATA "Kaurivo"
$secretFile = Join-Path $settings "worker.token.dpapi"
$venv = Join-Path $root ".venv\Scripts\python.exe"
if (!(Test-Path $venv)) { throw "Kaurivo Python environment missing. Run setup_kaurivo_windows.ps1." }
if (!(Test-Path $secretFile)) { throw "Kaurivo key missing. Run setup_kaurivo_windows.ps1." }
$encrypted = Get-Content -Raw -Path $secretFile
$secure = ConvertTo-SecureString $encrypted.Trim()
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try {
  $env:KAURIVO_LOCAL_WORKER_TOKEN = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
} finally {
  [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
}
$env:PYTHONUNBUFFERED = "1"
$env:FREE_ONLY = "1"
$backendFile = Join-Path $settings "worker.backend"
$env:KAURIVO_WINDOWS_BACKEND = "ollama"
if (Test-Path $backendFile) {
  $env:KAURIVO_WINDOWS_BACKEND = (Get-Content -Raw -Path $backendFile).Trim()
}
if ($env:KAURIVO_WINDOWS_BACKEND -notin @("codex", "ollama")) {
  throw "Tuntematon Kaurivon AI-asetus. Suorita asennus uudelleen."
}
$env:OLLAMA_RESEARCH_MODEL = "qwen2.5-coder:7b"
$env:OLLAMA_BUILDER_MODEL = "qwen2.5-coder:7b"
$env:OLLAMA_QA_MODEL = "llava:7b"
$env:KAURIVO_BROWSER_SOURCE_FALLBACK = "1"
Write-Host "Kaurivo Windows builder: starting (Ctrl+C stops this terminal only)."
Push-Location $root
try {
  & $venv -m scripts.kaurivo_local_worker
} finally {
  $env:KAURIVO_LOCAL_WORKER_TOKEN = ""
  Pop-Location
}
