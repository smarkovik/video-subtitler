# setup.ps1 — install everything video-subtitler needs.
#
# Driven by setup.bat (which sets ExecutionPolicy Bypass for this run
# only — nothing global is changed). Safe to re-run.

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

function Section($msg) {
    Write-Host ""
    Write-Host "==> $msg" -ForegroundColor Cyan
}

function Ok($msg)   { Write-Host "    [ok]   $msg" -ForegroundColor Green }
function Info($msg) { Write-Host "    [..]   $msg" -ForegroundColor Yellow }
function Fail($msg) { Write-Host "    [fail] $msg" -ForegroundColor Red }

function Refresh-Path {
    # winget installs add to PATH at the system or user level, but
    # the current process inherits PATH at start. Rebuild it from
    # the registry so freshly-installed tools are visible.
    $machine = [System.Environment]::GetEnvironmentVariable('Path', 'Machine')
    $user    = [System.Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = "$machine;$user"
}

function Has-Cmd($name) {
    $null -ne (Get-Command $name -ErrorAction SilentlyContinue)
}

function Install-Via-Winget($displayName, $wingetId, $cmdToCheck) {
    if (Has-Cmd $cmdToCheck) {
        Ok "$displayName already installed ($(Get-Command $cmdToCheck | Select-Object -First 1 -ExpandProperty Source))"
        return
    }
    Info "installing $displayName via winget ($wingetId)..."
    winget install --id $wingetId --silent --accept-package-agreements --accept-source-agreements --scope user 2>&1 | Out-Host
    Refresh-Path
    if (-not (Has-Cmd $cmdToCheck)) {
        throw "$displayName installed but '$cmdToCheck' is still not on PATH. Try closing this window and double-clicking setup.bat again."
    }
    Ok "$displayName installed"
}

# --- Step 1: prerequisites ---------------------------------------------------

Section "Checking prerequisites"

if (-not (Has-Cmd 'winget')) {
    Fail "winget is missing."
    Write-Host ""
    Write-Host "    winget ships with Windows 10 (build 1809+) and Windows 11."
    Write-Host "    To install it: open the Microsoft Store, search for"
    Write-Host "    'App Installer' from Microsoft, and click Update / Install."
    Write-Host "    Then run setup.bat again."
    exit 1
}
Ok "winget found"

# --- Step 2: install Python and ffmpeg ---------------------------------------

Section "Installing Python and ffmpeg"

Install-Via-Winget 'Python 3.13' 'Python.Python.3.13' 'python'
Install-Via-Winget 'ffmpeg'      'Gyan.FFmpeg'        'ffmpeg'

# Some winget Python installs land in a "py" launcher only — make sure
# `python` itself works.
if (-not (Has-Cmd 'python')) {
    if (Has-Cmd 'py') {
        Info "using 'py' launcher in place of 'python'"
        Set-Alias -Name python -Value py -Scope Script
    } else {
        throw "Python installed but neither 'python' nor 'py' is on PATH."
    }
}

# --- Step 3: verify ffmpeg has libass ----------------------------------------

Section "Verifying ffmpeg has subtitle support"

# ffmpeg writes its version banner to stderr (always), and Windows
# PowerShell 5.1 turns any stderr from a native command into a
# NativeCommandError when $ErrorActionPreference is 'Stop'. Merge
# streams via 2>&1 and relax the preference locally so the call can
# complete and we can actually inspect the filter list.
$prevPref = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
try {
    $filters = (& ffmpeg -filters 2>&1) -join "`n"
    $ffmpegRc = $LASTEXITCODE
} finally {
    $ErrorActionPreference = $prevPref
}

if ($ffmpegRc -ne 0) {
    Fail "ffmpeg failed to run (exit $ffmpegRc)."
    Write-Host "    Try opening a new terminal and running 'ffmpeg -version' manually."
    exit 1
}
if (-not ($filters -match '\bsubtitles\b')) {
    Fail "ffmpeg is missing the 'subtitles' filter (libass)."
    Write-Host "    The Gyan.FFmpeg build normally includes it. Try uninstalling"
    Write-Host "    ffmpeg ('winget uninstall Gyan.FFmpeg') and re-running setup.bat."
    exit 1
}
Ok "subtitles filter present"

# --- Step 4: create venv -----------------------------------------------------

Section "Creating Python virtual environment"

if (-not (Test-Path '.venv\Scripts\python.exe')) {
    Info "creating .venv ..."
    python -m venv .venv
} else {
    Ok ".venv already exists"
}

$venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'

# --- Step 5: install Python deps ---------------------------------------------

Section "Installing Python dependencies"

& $venvPython -m pip install --upgrade pip 2>&1 | Out-Host
& $venvPython -m pip install -r requirements.txt 2>&1 | Out-Host
if ($LASTEXITCODE -ne 0) {
    throw "pip install failed. Scroll up to see the error."
}
Ok "Python deps installed"

# --- Step 6: download Whisper model ------------------------------------------

Section "Downloading Whisper-medium speech model (~1.5 GB)"
Info "this only happens the first time. Grab a coffee."

$env:PYTHONPATH = (Join-Path $PSScriptRoot 'src')
& $venvPython -m subtitler --download-model 2>&1 | Out-Host
if ($LASTEXITCODE -ne 0) {
    throw "Model download failed. Check your internet connection and re-run setup.bat."
}
Ok "model cached"

# --- Done --------------------------------------------------------------------

Write-Host ""
Write-Host "All done." -ForegroundColor Green
Write-Host ""
Write-Host "Drop a video onto run.bat to subtitle it."
exit 0
