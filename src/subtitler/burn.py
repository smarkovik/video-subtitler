"""Burn an ASS subtitle file into a video using ffmpeg."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Callable, Optional

from .audio import ensure_ffmpeg, FFmpegFailed


_TIME_RE = re.compile(r"time=(\d+):(\d+):(\d+(?:\.\d+)?)")


def _escape_for_filter(p: Path) -> str:
    """ffmpeg's filter-graph parser uses : as option separator and \\
    as the escape char. On Windows, drive-letter colons and path
    backslashes both blow up if not escaped.

    Reference: https://ffmpeg.org/ffmpeg-filters.html#Notes-on-filtergraph-escaping
    """
    s = str(p)
    s = s.replace("\\", "\\\\")
    s = s.replace(":", "\\:")
    s = s.replace("'", "\\'")
    return s


def burn(
    video: Path,
    ass_file: Path,
    out: Path,
    on_progress: Optional[Callable[[float], None]] = None,
) -> Path:
    """Burn the ASS file into video, writing out as H.264 mp4.

    on_progress(seconds_processed) is called whenever ffmpeg emits a
    new "time=" line on stderr (roughly every couple of frames). The
    caller can divide by total duration to get a percentage.
    """
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

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    last_lines: list[str] = []
    assert proc.stderr is not None
    for raw in proc.stderr:
        line = raw.rstrip("\n")
        # Keep a sliding window for error messages on failure.
        last_lines.append(line)
        if len(last_lines) > 80:
            last_lines.pop(0)
        if on_progress is None:
            continue
        m = _TIME_RE.search(line)
        if m:
            t = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
            on_progress(t)

    rc = proc.wait()
    if rc != 0:
        tail = "\n".join(last_lines[-30:])
        raise FFmpegFailed(f"ffmpeg failed burning subtitles:\n{tail}")
    return out
