"""Build an ASS subtitle file with word-by-word karaoke highlight.

Approach: chunk each segment into short phrase-lines (max N words),
and within each phrase use ASS \\k karaoke tags so the active word
flips from secondary to primary colour as it's spoken.

Style is derived from the video's actual (width, height) so the same
code looks right on horizontal 1080p, vertical Shorts, 4K, etc. The
ASS PlayRes is set to the real video size, which means font sizes
and margins are in literal pixels — no implicit scaling by the
subtitles filter.

Font, colours, and the box opacity can be overridden by the caller
(the web UI surfaces them as user controls).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .transcribe import Segment, Word


# Timing constants — independent of resolution.
MIN_DURATION = 0.4        # seconds; pad if shorter so it's readable
FADE_MS = 150             # fade in at segment start, fade out at segment end

# Defaults used by Style.for_video when the caller doesn't override.
DEFAULT_FONT = "Arial"
DEFAULT_HIGHLIGHT_HEX = "#FFEE00"  # active word: warm yellow
DEFAULT_TEXT_HEX = "#FFFFFF"       # inactive: white
DEFAULT_BOX_OPACITY = 50           # 0..100; 50 = half-transparent black box


def hex_to_ass(hex_color: str, alpha_pct: int = 100) -> str:
    """Convert "#RRGGBB" + opacity-percent to an ASS &HAABBGGRR token.

    ASS uses BGR (not RGB) and an inverted alpha (00 = opaque,
    FF = invisible). alpha_pct is opacity in human terms — 100% is
    fully visible, 0% is invisible.
    """
    h = hex_color.lstrip("#")
    if len(h) != 6:
        raise ValueError(f"expected #RRGGBB, got {hex_color!r}")
    rr, gg, bb = h[0:2], h[2:4], h[4:6]
    alpha_pct = max(0, min(100, alpha_pct))
    aa = format(round((100 - alpha_pct) / 100 * 255), "02X")
    return f"&H{aa}{bb.upper()}{gg.upper()}{rr.upper()}"


@dataclass(frozen=True)
class Style:
    """Per-render values derived from the video's pixel dimensions and
    the user's chosen font / colours / opacity. All sizes are in
    literal pixels of the source video (we set ASS PlayRes to (width,
    height), so 1 ASS unit == 1 video pixel).
    """
    width: int
    height: int
    font_size: int
    outline: int
    margin_v: int
    margin_side: int
    max_words_per_line: int
    font: str
    primary_colour: str    # ASS &H token, used for the active word
    secondary_colour: str  # ASS &H token, used for inactive words
    outline_colour: str    # ASS &H token, around glyphs
    back_colour: str       # ASS &H token; alpha controls box opacity

    @classmethod
    def for_video(
        cls,
        width: int,
        height: int,
        *,
        font: str = DEFAULT_FONT,
        highlight_hex: str = DEFAULT_HIGHLIGHT_HEX,
        text_hex: str = DEFAULT_TEXT_HEX,
        box_opacity: int = DEFAULT_BOX_OPACITY,
    ) -> "Style":
        # Font size: ~4.5% of the shorter dimension. Keeps Shorts (1080w)
        # and horizontal 1080p (1080h) at the same readable size, and
        # scales 4K up appropriately.
        short = min(width, height)
        font_size = max(20, round(short * 0.045))

        # How many words fit horizontally. Empirical: an average
        # Cyrillic/Latin word + space takes ~5x font_size in width.
        # Cap at 6 to keep lines short for readability.
        usable_w = width * 0.92
        max_words = max(2, min(6, int(usable_w // (font_size * 5))))

        outline = max(2, round(font_size / 12))
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
            font=font,
            primary_colour=hex_to_ass(highlight_hex, 100),
            secondary_colour=hex_to_ass(text_hex, 100),
            outline_colour=hex_to_ass("#000000", 100),
            back_colour=hex_to_ass("#000000", box_opacity),
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
Style: Default,{s.font},{s.font_size},{s.primary_colour},{s.secondary_colour},{s.outline_colour},{s.back_colour},-1,0,0,0,100,100,0,0,3,{s.outline},0,2,{s.margin_side},{s.margin_side},{s.margin_v},1

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
