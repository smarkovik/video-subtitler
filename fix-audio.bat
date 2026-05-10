@echo off
REM Drag a .subbed.mp4 onto this .bat to re-encode the audio to AAC.
REM
REM Useful when the original video had PCM audio (DaVinci Resolve
REM exports, some screen recorders) — the rendered .subbed.mp4
REM technically plays, but Windows Media Player and most phones
REM reject the audio. Re-encoding to AAC makes it universally
REM playable. Video is copied untouched — no quality loss, runs
REM in seconds even on long videos.

setlocal
title video-subtitler — fix audio
cd /d "%~dp0"

if "%~1"=="" (
    echo Usage: drag a video file onto this .bat
    pause
    exit /b 1
)

set "INPUT=%~1"
set "OUTPUT=%~dpn1.fixed.mp4"

echo Re-encoding audio in:
echo   %INPUT%
echo to:
echo   %OUTPUT%
echo.

ffmpeg -y -i "%INPUT%" -c:v copy -c:a aac -b:a 192k "%OUTPUT%"
set "RC=%ERRORLEVEL%"

echo.
if "%RC%"=="0" (
    echo Done. Open %OUTPUT% — audio should now play in any player.
) else (
    echo ffmpeg failed with code %RC%. Scroll up for details.
)
pause
