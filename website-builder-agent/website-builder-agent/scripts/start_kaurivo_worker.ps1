# Start Kaurivo's private, free-only Windows worker under the CURRENT user.
# The secret is stored only as a Windows DPAPI user-protected blob.
$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$settings = Join-Path $env:LOCALAPPDATA "Kaurivo"
$secretFile = Join-Path $settings "worker.token.dpapi"
$venv = Join-Path $root ".venv\Scripts\python.exe"
if (!(Test-Path $venv)) { throw "Kaurivo Python environment missing. Run setup_kaurivo_windows.ps1." }
if (!(Test-Path $secretFile)) { throw "Kaurivo key missing. Run setup_kaurivo_windows.ps1." }
$backendFile = Join-Path $settings "worker.backend"
# Codex is deliberately disabled for this Windows worker. Never silently
# consume the owner's ChatGPT/Codex quota, even if an older setup selected it.
if (!(Test-Path $backendFile) -or
    (Get-Content -Raw -Path $backendFile).Trim() -ne "ollama") {
  throw "Codex on poistettu Kaurivon Windows-rakentajasta. Suorita ensin .\switch_kaurivo_to_offline.ps1 (maksuton Ollama)."
}
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
$env:KAURIVO_WINDOWS_BACKEND = "ollama"
$env:OLLAMA_RESEARCH_MODEL = "qwen2.5-coder:7b"
$env:OLLAMA_BUILDER_MODEL = "qwen2.5-coder:7b"
$env:OLLAMA_QA_MODEL = "llava:7b"
# Local inference can be slower than a cloud model; it still fails QA closed.
$env:OLLAMA_TIMEOUT_SECONDS = "1200"
$env:OLLAMA_NUM_CTX = "8192"
$env:KAURIVO_BROWSER_SOURCE_FALLBACK = "1"
Write-Host "Kaurivo Windows builder: starting (Ctrl+C stops this terminal only)."
Push-Location $root
try {
  & $venv -m scripts.kaurivo_local_worker
} finally {
  $env:KAURIVO_LOCAL_WORKER_TOKEN = ""
  Pop-Location
}
