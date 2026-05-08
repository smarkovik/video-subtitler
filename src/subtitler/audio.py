"""Extract Whisper-friendly audio from a video file."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class FFmpegMissing(RuntimeError):
    pass


class FFmpegFailed(RuntimeError):
    pass


def ensure_ffmpeg() -> str:
    path = shutil.which("ffmpeg")
    if not path:
        raise FFmpegMissing(
            "ffmpeg not found on PATH. See docs/setup-windows.md."
        )
    return path


def extract_audio(video: Path, out_wav: Path) -> Path:
    """Extract mono 16kHz PCM WAV. Whisper expects this format."""
    ensure_ffmpeg()
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video),
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-c:a", "pcm_s16le",
        str(out_wav),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise FFmpegFailed(
            f"ffmpeg failed extracting audio:\n{proc.stderr[-2000:]}"
        )
    return out_wav
