"""Strip Serbian filler words from segments.

Conservative starter list. Easy to extend after seeing real videos.
Matches whole tokens only, case-insensitive, ignoring trailing
punctuation. Both segment text and word lists are cleaned.
"""

from __future__ import annotations

import re

from .transcribe import Segment, Word


FILLERS: set[str] = {
    "ovaj",
    "ovaj,",
    "znači",
    "znaci",
    "pa",
    "ono",
    "kao",
    "tipa",
    "u stvari",
}


_PUNCT_RE = re.compile(r"[.,!?;:…]+$")


def _norm(token: str) -> str:
    return _PUNCT_RE.sub("", token).strip().lower()


def _is_filler(token: str) -> bool:
    return _norm(token) in {_norm(f) for f in FILLERS}


def strip_fillers_text(text: str) -> str:
    tokens = text.split()
    kept = [t for t in tokens if not _is_filler(t)]
    return " ".join(kept)


def strip_fillers(segments: list[Segment]) -> list[Segment]:
    out: list[Segment] = []
    for s in segments:
        kept_words = [w for w in s.words if not _is_filler(w.text)]
        new_text = strip_fillers_text(s.text)
        if not new_text:
            # Skip segments that became empty.
            continue
        out.append(
            Segment(
                start=s.start,
                end=s.end,
                text=new_text,
                words=kept_words,
            )
        )
    return out
