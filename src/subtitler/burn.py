"""Burn an ASS subtitle file into a video using ffmpeg."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .audio import ensure_ffmpeg, FFmpegFailed


def _escape_for_filter(p: Path) -> str:
    """ffmpeg's filter-graph parser uses : as option separator and \\
    as the escape char. On Windows, drive-letter colons and path
    backslashes both blow up if not escaped.

    Reference: https://ffmpeg.org/ffmpeg-filters.html#Notes-on-filtergraph-escaping
    """
    s = str(p)
    s = s.replace("\\", "\\\\")  # backslash escape (Windows paths)
    s = s.replace(":", "\\:")    # colon escape (drive letters, etc)
    s = s.replace("'", "\\'")
    return s


def burn(video: Path, ass_file: Path, out: Path) -> Path:
    ensure_ffmpeg()
    out.parent.mkdir(parents=True, exist_ok=True)
    filter_path = _escape_for_filter(ass_file)
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video),
        "-vf", f"subtitles=filename={filter_path}",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        "-c:a", "copy",
        str(out),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise FFmpegFailed(
            f"ffmpeg failed burning subtitles:\n{proc.stderr[-2000:]}"
        )
    return out
