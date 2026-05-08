"""Build an ASS subtitle file with word-by-word karaoke highlight.

Approach: chunk each segment into short phrase-lines (max N words),
and within each phrase use ASS \\k karaoke tags so the active word
flips from secondary to primary colour as it's spoken.

Style: Arial bold, white text, semi-opaque black box behind text
(BorderStyle 3). Active word turns yellow.
"""

from __future__ import annotations

from pathlib import Path

from .transcribe import Segment, Word


# Style constants
FONT = "Arial"
FONT_SIZE = 72            # pt at 1920x1080 reference; ffmpeg scales it
PRIMARY = "&H0000FFFF"    # active word: yellow (BGR + alpha 00)
SECONDARY = "&H00FFFFFF"  # inactive: white
OUTLINE = "&H00000000"    # black outline
BACK = "&H80000000"       # 50% black box behind text
MARGIN_V = 80             # pixels from bottom

MAX_WORDS_PER_LINE = 6
MIN_DURATION = 0.4        # seconds; pad if shorter so it's readable


def _fmt_time(t: float) -> str:
    if t < 0:
        t = 0.0
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t - h * 3600 - m * 60
    cs = int(round(s * 100))
    if cs >= 6000:  # carry
        cs = 0
        m += 1
    return f"{h:d}:{m:02d}:{cs // 100:02d}.{cs % 100:02d}"


def _ass_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def _chunk(words: list[Word], n: int) -> list[list[Word]]:
    return [words[i : i + n] for i in range(0, len(words), n)]


def _build_karaoke_text(words: list[Word]) -> str:
    """Each \\k value is the duration of that word in centiseconds.

    Default \\k behaviour: word starts in SecondaryColour, flips to
    PrimaryColour when its time arrives. Result: text is white, active
    word is yellow.
    """
    parts: list[str] = []
    for w in words:
        dur_cs = max(1, int(round((w.end - w.start) * 100)))
        parts.append(f"{{\\k{dur_cs}}}{_ass_escape(w.text)}")
    return " ".join(parts)


def _header() -> str:
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{FONT},{FONT_SIZE},{PRIMARY},{SECONDARY},{OUTLINE},{BACK},-1,0,0,0,100,100,0,0,3,4,0,2,40,40,{MARGIN_V},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _event(start: float, end: float, text: str) -> str:
    return f"Dialogue: 0,{_fmt_time(start)},{_fmt_time(end)},Default,,0,0,0,,{text}"


def build_ass(segments: list[Segment], max_words: int = MAX_WORDS_PER_LINE) -> str:
    events: list[str] = []
    for seg in segments:
        if not seg.words:
            # No word timestamps (e.g. user inserted a fresh line);
            # fall back to a plain block.
            end = max(seg.end, seg.start + MIN_DURATION)
            events.append(_event(seg.start, end, _ass_escape(seg.text)))
            continue
        for chunk in _chunk(seg.words, max_words):
            start = chunk[0].start
            end = chunk[-1].end
            if end - start < MIN_DURATION:
                end = start + MIN_DURATION
            events.append(_event(start, end, _build_karaoke_text(chunk)))
    return _header() + "\n".join(events) + "\n"


def write_ass(segments: list[Segment], path: Path) -> None:
    path.write_text(build_ass(segments), encoding="utf-8")
