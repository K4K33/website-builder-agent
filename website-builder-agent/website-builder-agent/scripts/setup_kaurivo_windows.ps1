# Kaurivo first-time Windows setup. Installs ONLY into the local user's
# existing checkout; no paid AI, new cloud services or background processes
# are created without explicit confirmation.
param([switch]$Codex)
$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $root
Write-Host "Kaurivo – Windows-rakentajan ensiasennus"
if (!(Get-Command git -ErrorAction SilentlyContinue)) {
  throw "Git for Windows puuttuu. Asenna Git: https://git-scm.com/download/win"
}
if (!(Get-Command py -ErrorAction SilentlyContinue)) {
  throw "Python Launcher puuttuu. Asenna Python 3.11: https://www.python.org/downloads/windows/"
}
& py -3.11 --version
if ($LASTEXITCODE -ne 0) { throw "Python 3.11 puuttuu. Asenna se ensin." }
if (!(Test-Path ".venv\Scripts\python.exe")) {
  & py -3.11 -m venv .venv
  if ($LASTEXITCODE -ne 0) { throw "Python-ympäristöä ei voitu luoda." }
}
$python = Join-Path $root ".venv\Scripts\python.exe"
& $python -m pip install --disable-pip-version-check -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Python-riippuvuuksien asennus epäonnistui." }
& $python -m playwright install chromium
if ($LASTEXITCODE -ne 0) { throw "Chromiumin asennus epäonnistui." }
if ($Codex) {
  if (!(Get-Command codex -ErrorAction SilentlyContinue)) {
    throw "Asenna ensin Codex CLI. Ohje: https://developers.openai.com/codex/cli"
  }
  Write-Host "Kirjaudu Codexiin ChatGPT-tililläsi selaimessa."
  & codex login
  if ($LASTEXITCODE -ne 0) { throw "Codex-kirjautuminen epäonnistui." }
  Write-Host "Tarkistetaan Codexin rakennusmalli ja kuvallinen laaduntarkistus."
  & $python -m utils.codex_ai --verify
  if ($LASTEXITCODE -ne 0) { throw "Codexin mallikoe epäonnistui. Rakentajaa ei käynnistetty." }
} else {
  if (!(Get-Command ollama -ErrorAction SilentlyContinue)) {
    throw "Ollama puuttuu. Asenna ilmainen Ollama: https://ollama.com/download/windows"
  }
  $allow = Read-Host "Asennetaanko paikalliset tekoälymallit? (n. 9–12 GB levytilaa, kyllä/ei)"
  if ($allow -notin @("kyllä","k","yes","y")) {
    Write-Host "Voit myöhemmin suorittaa: ollama pull qwen2.5-coder:7b ja ollama pull llava:7b"
  } else {
    & ollama pull qwen2.5-coder:7b
    if ($LASTEXITCODE -ne 0) { throw "Koodimallin asennus epäonnistui." }
    & ollama pull llava:7b
    if ($LASTEXITCODE -ne 0) { throw "Kuvia ymmärtävän QA-mallin asennus epäonnistui." }
  }
}

$folder=Join-Path $env:LOCALAPPDATA "Kaurivo"
New-Item -ItemType Directory -Force -Path $folder | Out-Null
Write-Host "Avaa Kaurivon hallinnasta Demot ja paina 'Luo Windows-rakentajan avain'."
$secure=Read-Host "Liitä avain tähän (ei näy ruudulla)" -AsSecureString
$plain=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try {
  $value=[Runtime.InteropServices.Marshal]::PtrToStringBSTR($plain)
  if ($value -notmatch '^kvl_[0-9a-f]{64}$') {
    throw "Avaimen muoto ei täsmää. Luo uusi avain Kaurivon hallinnassa."
  }
} finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($plain) }
$dest=Join-Path $folder "worker.token.dpapi"
$secure | ConvertFrom-SecureString | Set-Content -Encoding ascii -Path $dest
$backend = if ($Codex) { "codex" } else { "ollama" }
Set-Content -Encoding ascii -Path (Join-Path $folder "worker.backend") -Value $backend
Write-Host "Avain tallennettiin nykyisen Windows-käyttäjän DPAPI-suojattuna."
Write-Host "Huomio: GitHubin sisäisen demon julkaisu tarvitsee Git Credential Managerissa hyväksytyn sisäänkirjautumisen, jolla on Contents:write."
$auto=Read-Host "Käynnistetäänkö Windows-rakentaja automaattisesti sisäänkirjautumisen yhteydessä? (k/e)"
if ($auto -in @("k","kyllä","y","yes")) {
  $start=Join-Path $PSScriptRoot "start_kaurivo_worker.ps1"
  $action=New-ScheduledTaskAction -Execute "powershell.exe" -Argument ('-NoProfile -ExecutionPolicy Bypass -File "'+$start+'"') -WorkingDirectory $root
  $trigger=New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
  $opts=New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
  try {
    Register-ScheduledTask -TaskName "Kaurivo Windows Builder" -Action $action -Trigger $trigger -Settings $opts -Description "Private Kaurivo website demo builder" -Force | Out-Null
    Write-Host "Automaattinen käynnistys rekisteröity. Työ vaatii aktiivisen Windows-istunnon."
  } catch {
    Write-Warning "Ajastettua käynnistystä ei voitu tehdä. Voit käynnistää start_kaurivo_worker.ps1 käsin."
  }
}
if ($Codex) {
  Write-Host "Asennus valmis. Codex-rakentaja käynnistyy tähän ikkunaan."
  & (Join-Path $PSScriptRoot "start_kaurivo_worker.ps1")
  exit $LASTEXITCODE
}
Write-Host "Asennus valmis. Avaa uusi PowerShell ja suorita:"
Write-Host ('powershell -ExecutionPolicy Bypass -File "' + (Join-Path $PSScriptRoot "start_kaurivo_worker.ps1") + '"')
