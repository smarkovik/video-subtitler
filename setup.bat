@echo off
REM Double-click this file to install everything you need.
REM
REM This script just hands off to setup.ps1 with PowerShell's
REM execution policy bypassed so the user doesn't have to mess with
REM Windows security settings.

title video-subtitler — first-time setup
cd /d "%~dp0"

echo.
echo  ============================================================
echo    video-subtitler — first-time setup
echo  ============================================================
echo.
echo   This will install:
echo     * Python 3.13         (if missing)
echo     * ffmpeg              (if missing)
echo     * the Whisper speech-recognition model (~1.5 GB, one-time)
echo.
echo   You only need to do this once. After it finishes you can
echo   subtitle videos by dragging them onto run.bat.
echo.
echo   You may see a Windows popup asking permission to install
echo   software — click Yes.
echo.
pause

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"
set "RC=%ERRORLEVEL%"

echo.
if "%RC%"=="0" (
    echo  ============================================================
    echo    Setup complete. You can close this window.
    echo.
    echo    To subtitle a video: drag it onto run.bat
    echo  ============================================================
) else (
    echo  ============================================================
    echo    Setup failed. Scroll up to see what went wrong.
    echo    If you're stuck, share the messages above with whoever
    echo    sent you this tool.
    echo  ============================================================
)
echo.
pause
