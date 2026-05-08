"""Transcribe Serbian audio with faster-whisper, including word timestamps."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterator


@dataclass
class Word:
    start: float
    end: float
    text: str


@dataclass
class Segment:
    start: float
    end: float
    text: str
    words: list[Word]

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


def transcribe(
    audio: Path,
    model_size: str = "medium",
    language: str = "sr",
    progress: bool = True,
    on_segment=None,
) -> list[Segment]:
    """Run faster-whisper, return segments with word-level timestamps.

    int8 on CPU is the slowest-but-works path. The first call after a
    fresh install downloads the model to the HF cache; later calls are
    fully offline.

    on_segment(segment) is called for each segment as soon as it's
    decoded — used by the web UI to stream live progress to the
    browser. The CLI uses progress=True to print the same info.
    """
    from faster_whisper import WhisperModel

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments_iter, info = model.transcribe(
        str(audio),
        language=language,
        word_timestamps=True,
        vad_filter=True,
        beam_size=5,
    )

    out: list[Segment] = []
    for seg in segments_iter:
        words = [
            Word(start=w.start, end=w.end, text=w.word.strip())
            for w in (seg.words or [])
            if w.start is not None and w.end is not None
        ]
        segment = Segment(
            start=seg.start,
            end=seg.end,
            text=seg.text.strip(),
            words=words,
        )
        out.append(segment)
        if on_segment is not None:
            on_segment(segment)
        if progress:
            mins = int(seg.end // 60)
            secs = int(seg.end % 60)
            print(f"  [{mins:02d}:{secs:02d}] {seg.text.strip()}")

    return out


def iter_words(segments: list[Segment]) -> Iterator[Word]:
    for seg in segments:
        yield from seg.words
