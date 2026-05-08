@echo off
REM Drag a video file onto this .bat to subtitle it.
REM
REM First drop: transcribes and writes <name>.srt next to the video.
REM Edit the .srt in Notepad, then drop the SAME video on this .bat
REM again to render the final video with burned-in subtitles.
REM
REM If you haven't run setup.bat yet, do that first (one time).

setlocal
title video-subtitler
cd /d "%~dp0"

if "%~1"=="" (
    echo Usage: drag a video file onto this .bat
    echo.
    echo If you haven't already, double-click setup.bat first.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo .venv is missing. Double-click setup.bat first.
    pause
    exit /b 1
)

set "VIDEO=%~1"
set "STEM=%~dpn1"
set "SRT=%STEM%.srt"
set "PYTHONPATH=%~dp0src"
set "PY=%~dp0.venv\Scripts\python.exe"

if exist "%SRT%" (
    echo Found %SRT% — running render stage.
    "%PY%" -m subtitler "%VIDEO%" --render --clean
) else (
    "%PY%" -m subtitler "%VIDEO%"
)

echo.
pause
