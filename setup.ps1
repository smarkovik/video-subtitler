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

function Run-Native($block) {
    # Run a native command (winget, ffmpeg, python, pip...) without
    # tripping ErrorActionPreference='Stop' on stderr writes.
    #
    # Windows PowerShell 5.1 raises a NativeCommandError when a native
    # command emits anything to stderr while the strict preference is
    # active — even harmless warnings ("set HF_TOKEN", ffmpeg's
    # version banner, pip deprecation notices, etc.). Wrapping the
    # call here flips the preference locally so stderr is just
    # printed, not promoted to a fatal error. Returns $LASTEXITCODE.
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & $block
        return $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $prev
    }
}

function Find-Real-Python {
    # Return the path to a *real* python.exe, or $null.
    #
    # Windows 10/11 ships with an "App Execution Alias" stub at
    # %LOCALAPPDATA%\Microsoft\WindowsApps\python.exe (and python3.exe).
    # The stub is on PATH by default and pretends Python is installed,
    # but when you actually run it, it just prints "Python was not found"
    # and offers to send you to the Microsoft Store. We have to skip
    # past it to find a real Python.
    $names = @('python', 'python3', 'py')
    foreach ($name in $names) {
        $candidates = @(Get-Command $name -All -ErrorAction SilentlyContinue)
        foreach ($c in $candidates) {
            $path = $c.Source
            if ($path -and ($path -notlike '*\Microsoft\WindowsApps\*')) {
                return $path
            }
        }
    }
    return $null
}

function Install-Via-Winget($displayName, $wingetId, $cmdToCheck) {
    if (Has-Cmd $cmdToCheck) {
        Ok "$displayName already installed ($(Get-Command $cmdToCheck | Select-Object -First 1 -ExpandProperty Source))"
        return
    }
    Info "installing $displayName via winget ($wingetId)..."
    Run-Native { winget install --id $wingetId --silent --accept-package-agreements --accept-source-agreements --scope user 2>&1 | Out-Host } | Out-Null
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

# Python: don't use Has-Cmd because the Windows Store python.exe stub
# fakes the answer. Use Find-Real-Python instead.
$realPython = Find-Real-Python
if ($realPython) {
    Ok "Python already installed ($realPython)"
} else {
    Info "installing Python 3.13 via winget (Python.Python.3.13)..."
    Run-Native { winget install --id 'Python.Python.3.13' --silent --accept-package-agreements --accept-source-agreements --scope user 2>&1 | Out-Host } | Out-Null
    Refresh-Path
    $realPython = Find-Real-Python
    if (-not $realPython) {
        Fail "Python installed but is still not reachable on PATH."
        Write-Host ""
        Write-Host "    Most common cause: a Windows Store stub is intercepting 'python'."
        Write-Host "    To fix it:"
        Write-Host ""
        Write-Host "      1. Press Windows key, search for 'Manage app execution aliases'"
        Write-Host "         and open it. (Settings > Apps > Advanced app settings >"
        Write-Host "         App execution aliases on newer Windows.)"
        Write-Host "      2. Turn OFF the toggles next to 'python.exe' and 'python3.exe'."
        Write-Host "      3. Close this window and double-click setup.bat again."
        Write-Host ""
        exit 1
    }
    Ok "Python installed ($realPython)"
}

Install-Via-Winget 'ffmpeg' 'Gyan.FFmpeg' 'ffmpeg'

# --- Step 3: verify ffmpeg has libass ----------------------------------------

Section "Verifying ffmpeg has subtitle support"

# ffmpeg writes its version banner to stderr; Run-Native keeps that
# from triggering NativeCommandError. Capture filter list as a string.
$filters = ""
$ffmpegRc = Run-Native {
    $script:__filtersOut = (& ffmpeg -filters 2>&1) -join "`n"
}
$filters = $script:__filtersOut

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
    Info "creating .venv with $realPython ..."
    $rc = Run-Native { & $realPython -m venv .venv 2>&1 | Out-Host }
    if ($rc -ne 0 -or -not (Test-Path '.venv\Scripts\python.exe')) {
        throw "venv creation failed (exit $rc). Check the messages above."
    }
} else {
    Ok ".venv already exists"
}

$venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'

# --- Step 5: install Python deps ---------------------------------------------

Section "Installing Python dependencies"

$rc = Run-Native { & $venvPython -m pip install --upgrade pip 2>&1 | Out-Host }
if ($rc -ne 0) { throw "pip self-upgrade failed (exit $rc). Scroll up to see the error." }

$rc = Run-Native { & $venvPython -m pip install -r requirements.txt 2>&1 | Out-Host }
if ($rc -ne 0) { throw "pip install failed (exit $rc). Scroll up to see the error." }

Ok "Python deps installed"

# --- Step 6: download Whisper model ------------------------------------------

Section "Downloading Whisper-medium speech model (~1.5 GB)"
Info "this only happens the first time. Grab a coffee."

$env:PYTHONPATH = (Join-Path $PSScriptRoot 'src')
$rc = Run-Native { & $venvPython -m subtitler --download-model 2>&1 | Out-Host }
if ($rc -ne 0) {
    throw "Model download failed (exit $rc). Check your internet connection and re-run setup.bat."
}
Ok "model cached"

# --- Done --------------------------------------------------------------------

Write-Host ""
Write-Host "All done." -ForegroundColor Green
Write-Host ""
Write-Host "Drop a video onto run.bat to subtitle it."
exit 0
