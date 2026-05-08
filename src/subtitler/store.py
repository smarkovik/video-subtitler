"""Persist and reload word-level timestamps as JSON sidecars."""

from __future__ import annotations

import json
from pathlib import Path

from .transcribe import Segment, Word


def write_words_json(segments: list[Segment], path: Path) -> None:
    data = [seg.to_dict() for seg in segments]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_words_json(path: Path) -> list[Segment]:
    data = json.loads(path.read_text(encoding="utf-8"))
    out: list[Segment] = []
    for d in data:
        words = [Word(**w) for w in d.get("words", [])]
        out.append(Segment(start=d["start"], end=d["end"], text=d["text"], words=words))
    return out
