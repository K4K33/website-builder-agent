# Switch an already enrolled Windows worker to local-only inference.
# Keeps the existing DPAPI token, queue jobs, quality gates and checkpoints.
# Model downloads require explicit permission; Codex is never invoked.
$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$settings = Join-Path $env:LOCALAPPDATA "Kaurivo"
$venv = Join-Path $root ".venv\Scripts\python.exe"
$token = Join-Path $settings "worker.token.dpapi"
$backend = Join-Path $settings "worker.backend"
if (!(Test-Path $venv)) { throw "Python puuttuu. Suorita setup_kaurivo_windows.ps1 ensin." }
if (!(Test-Path $token)) { throw "Rakentajan avain puuttuu. Suorita setup_kaurivo_windows.ps1 ensin." }
if (!(Get-Command ollama -ErrorAction SilentlyContinue)) {
  throw "Ollama puuttuu. Asenna ilmainen Ollama osoitteesta https://ollama.com/download/windows ja suorita tämä uudelleen."
}
Write-Host "Tarkistetaan paikalliset, maksuttomat AI-mallit. Codexia ei käynnistetä."
$models = @("qwen2.5-coder:7b", "llava:7b")
$catalog = @(& ollama list)
if ($LASTEXITCODE -ne 0) {
  throw "Ollama ei vastaa. Käynnistä Ollama-sovellus ja suorita tämä uudelleen."
}
$missing = @()
foreach ($model in $models) {
  $found = $false
  foreach ($line in $catalog) {
    if ($line -match ('^' + [Regex]::Escape($model) + '\s')) { $found = $true; break }
  }
  if (!$found) { $missing += $model }
}
if ($missing.Count -gt 0) {
  Write-Host ("Puuttuvat mallit: " + ($missing -join ", "))
  $allow = Read-Host "Ladataanko ilmaiset paikalliset mallit (noin 9-12 GB levytilaa)? (k/e)"
  if ($allow -notin @("k", "kyllä", "y", "yes")) {
    throw "Mallien lataus peruutettiin. Kaurivon AI-asetusta ei muutettu."
  }
  foreach ($model in $missing) {
    & ollama pull $model
    if ($LASTEXITCODE -ne 0) { throw ("Mallin lataus epäonnistui: " + $model) }
  }
}
# Model readiness is verified BEFORE changing the saved engine. No credentials
# or Supabase database settings are touched by this script.
Push-Location $root
try {
  $env:KAURIVO_WINDOWS_BACKEND = "ollama"
  $env:OLLAMA_RESEARCH_MODEL = "qwen2.5-coder:7b"
  $env:OLLAMA_BUILDER_MODEL = "qwen2.5-coder:7b"
  $env:OLLAMA_QA_MODEL = "llava:7b"
  & $venv -m scripts.check_local_models
  if ($LASTEXITCODE -ne 0) {
    throw "Paikalliset mallit eivät läpäisseet tarkistusta. Asetusta ei vaihdettu."
  }
} finally {
  Pop-Location
}
New-Item -ItemType Directory -Force -Path $settings | Out-Null
Set-Content -Encoding ascii -Path $backend -Value "ollama"
Write-Host "Kaurivon Windows-rakentaja on nyt offline-AI-tilassa (ei Codex-kiintiötä)."
Write-Host "Sulje aiempi Kaurivo-rakentaja painamalla sen ikkunassa Ctrl+C."
Write-Host "Käynnistä sitten: powershell -NoProfile -ExecutionPolicy Bypass -File .\start_kaurivo_worker.ps1"
Write-Host "Huom. Todellinen verkkosivulaatu pitää edelleen todentaa oikealla demolla."
