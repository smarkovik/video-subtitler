"""SRT (SubRip) read and write."""

from __future__ import annotations

import re
from pathlib import Path

from .transcribe import Segment, Word


def _fmt_time(t: float) -> str:
    if t < 0:
        t = 0.0
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int(round((t - int(t)) * 1000))
    if ms == 1000:
        ms = 0
        s += 1
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _parse_time(s: str) -> float:
    h, m, rest = s.split(":")
    sec, ms = rest.split(",")
    return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000.0


def write_srt(segments: list[Segment], path: Path) -> None:
    lines: list[str] = []
    for i, seg in enumerate(segments, 1):
        lines.append(str(i))
        lines.append(f"{_fmt_time(seg.start)} --> {_fmt_time(seg.end)}")
        lines.append(seg.text)
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


_BLOCK = re.compile(
    r"(\d+)\s*\n([\d:,]+)\s*-->\s*([\d:,]+)\s*\n(.*?)(?=\n\s*\n|\Z)",
    re.DOTALL,
)


def read_srt(path: Path) -> list[Segment]:
    """Read an edited SRT back. Words list comes back empty here; the
    caller re-attaches word timings from words.json."""
    text = path.read_text(encoding="utf-8")
    out: list[Segment] = []
    for m in _BLOCK.finditer(text):
        out.append(
            Segment(
                start=_parse_time(m.group(2)),
                end=_parse_time(m.group(3)),
                text=m.group(4).strip(),
                words=[],
            )
        )
    return out
