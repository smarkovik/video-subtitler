@echo off
REM Drag a video file onto this .bat to subtitle it.
REM
REM First drop: transcribes and writes <name>.srt next to the video.
REM Edit the .srt in Notepad, then drop the SAME video on this .bat
REM again to render the final video with burned-in subtitles.

setlocal

if "%~1"=="" (
    echo Usage: drag a video file onto this .bat
    pause
    exit /b 1
)

set "VIDEO=%~1"
set "STEM=%~dpn1"
set "SRT=%STEM%.srt"

REM Activate venv if present
if exist "%~dp0.venv\Scripts\activate.bat" (
    call "%~dp0.venv\Scripts\activate.bat"
)

if exist "%SRT%" (
    echo Found %SRT% — running render stage.
    python -m subtitler "%VIDEO%" --render --clean
) else (
    python -m subtitler "%VIDEO%"
)

echo.
pause
