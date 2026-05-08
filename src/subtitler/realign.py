"""Re-attach original word timings to user-edited segment text.

After the user edits the SRT, we have new text but no per-word
timestamps for it. We zip the edited tokens onto the original word
timings; if counts diverge, fall back to even time distribution
across the segment so the karaoke effect still looks plausible.
"""

from __future__ import annotations

from .transcribe import Segment, Word


def _tokenize(text: str) -> list[str]:
    # Subtitles often span 1-2 lines; flatten to single space-separated tokens.
    return [t for t in text.replace("\n", " ").split() if t]


def realign_segment(edited: Segment, original: Segment) -> Segment:
    tokens = _tokenize(edited.text)
    if not tokens:
        return Segment(edited.start, edited.end, edited.text, [])

    if original.words and len(tokens) == len(original.words):
        words = [
            Word(start=ow.start, end=ow.end, text=tok)
            for tok, ow in zip(tokens, original.words)
        ]
        return Segment(edited.start, edited.end, edited.text, words)

    # Fallback: distribute tokens evenly across the segment.
    duration = max(0.1, edited.end - edited.start)
    step = duration / len(tokens)
    words = [
        Word(
            start=edited.start + i * step,
            end=edited.start + (i + 1) * step,
            text=tok,
        )
        for i, tok in enumerate(tokens)
    ]
    return Segment(edited.start, edited.end, edited.text, words)


def realign(edited: list[Segment], original: list[Segment]) -> list[Segment]:
    """Pair edited segments with originals by index. Counts can diverge
    if the user merged or split lines; we walk the shorter list and
    pass the rest through with even distribution."""
    out: list[Segment] = []
    for i, e in enumerate(edited):
        o = original[i] if i < len(original) else Segment(e.start, e.end, e.text, [])
        out.append(realign_segment(e, o))
    return out
