@echo off
REM Double-click to open the video-subtitler UI in your browser.
REM
REM Run setup.bat first if you haven't already.

setlocal
title video-subtitler UI
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo .venv is missing. Double-click setup.bat first.
    pause
    exit /b 1
)

set "PYTHONPATH=%~dp0src"
set "PY=%~dp0.venv\Scripts\python.exe"

REM Force UTF-8 for Python's stdio so Cyrillic transcript progress
REM doesn't crash with UnicodeEncodeError on a cp1252/cp1251 console.
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

echo Starting the video-subtitler UI...
echo Your browser should open in a moment.
echo Leave this window open while you work. Close it to stop the server.
echo.

"%PY%" -m subtitler.server

echo.
pause
