"""Build an ASS subtitle file with word-by-word karaoke highlight.

Approach: chunk each segment into short phrase-lines (max N words),
and within each phrase use ASS \\k karaoke tags so the active word
flips from secondary to primary colour as it's spoken.

Style is derived from the video's actual (width, height) so the same
code looks right on horizontal 1080p, vertical Shorts, 4K, etc. The
ASS PlayRes is set to the real video size, which means font sizes
and margins are in literal pixels — no implicit scaling by the
subtitles filter.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .transcribe import Segment, Word


# Colour and timing constants — independent of resolution.
FONT = "Arial"
PRIMARY = "&H0000FFFF"    # active word: yellow (BGR + alpha 00)
SECONDARY = "&H00FFFFFF"  # inactive: white
OUTLINE_COLOUR = "&H00000000"
BACK = "&H80000000"       # 50% black box behind text
MIN_DURATION = 0.4        # seconds; pad if shorter so it's readable
FADE_MS = 150             # fade in at segment start, fade out at segment end


@dataclass(frozen=True)
class Style:
    """Per-render values derived from the video's pixel dimensions.

    All sizes are in literal pixels of the source video (we set ASS
    PlayRes to (width, height), so 1 ASS unit == 1 video pixel).
    """
    width: int
    height: int
    font_size: int
    outline: int
    margin_v: int
    margin_side: int
    max_words_per_line: int

    @classmethod
    def for_video(cls, width: int, height: int) -> "Style":
        # Font: ~4.5% of the shorter dimension. Keeps Shorts (1080w)
        # and horizontal 1080p (1080h) at the same readable size, and
        # scales 4K up appropriately.
        short = min(width, height)
        font_size = max(20, round(short * 0.045))

        # How many words fit horizontally. Empirical: an average
        # Cyrillic/Latin word + space takes ~5x font_size in width.
        # Cap at 6 to keep lines short for readability.
        usable_w = width * 0.92  # leave 4% padding each side
        max_words = max(2, min(6, int(usable_w // (font_size * 5))))

        # Outline scales with font; below ~3px is invisible at 1080w.
        outline = max(2, round(font_size / 12))

        # Bottom margin: 5% of height. Side margins: 4% of width.
        margin_v = max(20, round(height * 0.05))
        margin_side = max(20, round(width * 0.04))

        return cls(
            width=width,
            height=height,
            font_size=font_size,
            outline=outline,
            margin_v=margin_v,
            margin_side=margin_side,
            max_words_per_line=max_words,
        )


def _fmt_time(t: float) -> str:
    if t < 0:
        t = 0.0
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t - h * 3600 - m * 60
    cs = int(round(s * 100))
    if cs >= 6000:
        cs = 0
        m += 1
    return f"{h:d}:{m:02d}:{cs // 100:02d}.{cs % 100:02d}"


def _ass_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def _chunk(words: list[Word], n: int) -> list[list[Word]]:
    return [words[i : i + n] for i in range(0, len(words), n)]


def _build_karaoke_text(words: list[Word]) -> str:
    parts: list[str] = []
    for w in words:
        dur_cs = max(1, int(round((w.end - w.start) * 100)))
        parts.append(f"{{\\k{dur_cs}}}{_ass_escape(w.text)}")
    return " ".join(parts)


def _header(s: Style) -> str:
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: {s.width}
PlayResY: {s.height}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{FONT},{s.font_size},{PRIMARY},{SECONDARY},{OUTLINE_COLOUR},{BACK},-1,0,0,0,100,100,0,0,3,{s.outline},0,2,{s.margin_side},{s.margin_side},{s.margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _event(
    start: float,
    end: float,
    text: str,
    fade_in: bool = False,
    fade_out: bool = False,
) -> str:
    if fade_in or fade_out:
        fi = FADE_MS if fade_in else 0
        fo = FADE_MS if fade_out else 0
        text = f"{{\\fad({fi},{fo})}}{text}"
    return f"Dialogue: 0,{_fmt_time(start)},{_fmt_time(end)},Default,,0,0,0,,{text}"


def build_ass(segments: list[Segment], style: Style) -> str:
    events: list[str] = []
    for seg in segments:
        if not seg.words:
            end = max(seg.end, seg.start + MIN_DURATION)
            events.append(
                _event(seg.start, end, _ass_escape(seg.text),
                       fade_in=True, fade_out=True)
            )
            continue
        chunks = _chunk(seg.words, style.max_words_per_line)
        last = len(chunks) - 1
        for i, chunk in enumerate(chunks):
            start = chunk[0].start
            end = chunk[-1].end
            if end - start < MIN_DURATION:
                end = start + MIN_DURATION
            events.append(
                _event(
                    start, end, _build_karaoke_text(chunk),
                    fade_in=(i == 0),
                    fade_out=(i == last),
                )
            )
    return _header(style) + "\n".join(events) + "\n"


def write_ass(segments: list[Segment], path: Path, style: Style) -> None:
    path.write_text(build_ass(segments, style), encoding="utf-8")
