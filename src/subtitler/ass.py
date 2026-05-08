"""Build an ASS subtitle file with word-by-word karaoke highlight.

Two rendering modes, picked by Style.full_strip:

  full_strip = False (default):
      BorderStyle 3 — libass paints an opaque box behind every glyph
      using BackColour. The "boxes hug the text" look.

  full_strip = True:
      BorderStyle 1 — outline + shadow only, no per-glyph box. We
      emit an extra Dialogue per chunk on layer 0 that draws a
      single rounded rectangle (ASS \\p1 path) spanning the screen
      width, and the karaoke text rides on layer 1 over the top.

Three positions (top / middle / bottom) map to ASS Alignment 8 / 5
/ 2. In full-strip mode, both the strip and the text are positioned
explicitly via \\pos so the text lands precisely centred on the
strip regardless of margins.

Style is derived from the video's actual (width, height); the ASS
PlayRes matches the video, so all sizes are literal source pixels
with no implicit scaling.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .transcribe import Segment, Word


# Timing constants — independent of resolution.
MIN_DURATION = 0.4
FADE_MS = 150

# Style defaults
DEFAULT_FONT = "Arial"
DEFAULT_HIGHLIGHT_HEX = "#FFEE00"
DEFAULT_TEXT_HEX = "#FFFFFF"
DEFAULT_BOX_OPACITY = 50
DEFAULT_FULL_STRIP = False
DEFAULT_RADIUS = 0
DEFAULT_POSITION = "bottom"

# Strip height as a multiple of font_size (~vertical padding).
STRIP_HEIGHT_RATIO = 1.6


def hex_to_ass(hex_color: str, alpha_pct: int = 100) -> str:
    """Convert "#RRGGBB" + opacity-percent to an ASS &HAABBGGRR token."""
    h = hex_color.lstrip("#")
    if len(h) != 6:
        raise ValueError(f"expected #RRGGBB, got {hex_color!r}")
    rr, gg, bb = h[0:2], h[2:4], h[4:6]
    alpha_pct = max(0, min(100, alpha_pct))
    aa = format(round((100 - alpha_pct) / 100 * 255), "02X")
    return f"&H{aa}{bb.upper()}{gg.upper()}{rr.upper()}"


def _split_back(ass_token: str) -> tuple[str, str]:
    """Split &HAABBGGRR into (BBGGRR, AA) for use in inline overrides."""
    h = ass_token.lstrip("&H").rstrip("&")
    return h[2:], h[:2]


def _alignment(position: str) -> int:
    return {"top": 8, "middle": 5, "bottom": 2}.get(position, 2)


@dataclass(frozen=True)
class Style:
    width: int
    height: int
    font_size: int
    outline: int
    margin_v: int
    margin_side: int
    max_words_per_line: int
    font: str
    primary_colour: str
    secondary_colour: str
    outline_colour: str
    back_colour: str
    full_strip: bool
    radius: int
    position: str  # "top" | "middle" | "bottom"

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
        full_strip: bool = DEFAULT_FULL_STRIP,
        radius: int = DEFAULT_RADIUS,
        position: str = DEFAULT_POSITION,
    ) -> "Style":
        short = min(width, height)
        font_size = max(20, round(short * 0.045))
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
            full_strip=full_strip,
            radius=max(0, int(radius)),
            position=position if position in ("top", "middle", "bottom") else "bottom",
        )


# ---- helpers ----------------------------------------------------------------

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


def _strip_rect(s: Style) -> tuple[int, int, int, int]:
    """Return (left, top, w, h) of the full strip in source pixels."""
    h = round(s.font_size * STRIP_HEIGHT_RATIO)
    left = s.margin_side
    w = s.width - 2 * s.margin_side
    if s.position == "top":
        top = s.margin_v
    elif s.position == "middle":
        top = (s.height - h) // 2
    else:  # bottom
        top = s.height - s.margin_v - h
    return left, top, w, h


def _rounded_rect_path(w: int, h: int, r: int) -> str:
    """ASS \\p1 path for a rounded rectangle of size (w, h) with corner
    radius r. r is clamped to half the shorter side."""
    r = max(0, min(r, min(w, h) // 2))
    if r == 0:
        return f"m 0 0 l {w} 0 l {w} {h} l 0 {h} l 0 0"
    return (
        f"m {r} 0 "
        f"l {w - r} 0 "
        f"b {w} 0 {w} 0 {w} {r} "
        f"l {w} {h - r} "
        f"b {w} {h} {w} {h} {w - r} {h} "
        f"l {r} {h} "
        f"b 0 {h} 0 {h} 0 {h - r} "
        f"l 0 {r} "
        f"b 0 0 0 0 {r} 0"
    )


# ---- header -----------------------------------------------------------------

def _header(s: Style) -> str:
    border_style = 1 if s.full_strip else 3
    align = _alignment(s.position)
    # In full-strip mode the BackColour isn't drawn (BorderStyle 1),
    # but the field is still required by ASS — leave it as configured
    # so the file still round-trips cleanly through other tools.
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: {s.width}
PlayResY: {s.height}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{s.font},{s.font_size},{s.primary_colour},{s.secondary_colour},{s.outline_colour},{s.back_colour},-1,0,0,0,100,100,0,0,{border_style},{s.outline},0,{align},{s.margin_side},{s.margin_side},{s.margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _dialogue(layer: int, start: float, end: float, text: str) -> str:
    return f"Dialogue: {layer},{_fmt_time(start)},{_fmt_time(end)},Default,,0,0,0,,{text}"


def _fade_prefix(fade_in: bool, fade_out: bool) -> str:
    if not (fade_in or fade_out):
        return ""
    fi = FADE_MS if fade_in else 0
    fo = FADE_MS if fade_out else 0
    return f"\\fad({fi},{fo})"


# ---- per-mode event builders ------------------------------------------------

def _word_box_text_event(
    start: float, end: float, body: str, fade_in: bool, fade_out: bool
) -> str:
    """BorderStyle-3 word-box mode: just the karaoke text. The
    per-glyph box comes from the Style's BackColour."""
    fade = _fade_prefix(fade_in, fade_out)
    text = f"{{{fade}}}{body}" if fade else body
    return _dialogue(0, start, end, text)


def _strip_events(
    style: Style, start: float, end: float, body: str, fade_in: bool, fade_out: bool
) -> list[str]:
    """Full-strip mode: emit one rectangle on layer 0 and the text
    on layer 1, both positioned so the text sits centred on the strip."""
    left, top, w, h = _strip_rect(style)
    cx = left + w // 2
    cy = top + h // 2
    bgr, aa = _split_back(style.back_colour)
    fade = _fade_prefix(fade_in, fade_out)

    path = _rounded_rect_path(w, h, style.radius)
    rect_text = (
        f"{{\\an7\\pos({left},{top}){fade}\\bord0\\shad0"
        f"\\1c&H{bgr}&\\1a&H{aa}&\\p1}}{path}{{\\p0}}"
    )

    text_text = f"{{\\an5\\pos({cx},{cy}){fade}}}{body}"

    return [
        _dialogue(0, start, end, rect_text),
        _dialogue(1, start, end, text_text),
    ]


# ---- main builder -----------------------------------------------------------

def build_ass(segments: list[Segment], style: Style) -> str:
    events: list[str] = []
    for seg in segments:
        if not seg.words:
            end = max(seg.end, seg.start + MIN_DURATION)
            body = _ass_escape(seg.text)
            if style.full_strip:
                events.extend(_strip_events(style, seg.start, end, body, True, True))
            else:
                events.append(_word_box_text_event(seg.start, end, body, True, True))
            continue

        chunks = _chunk(seg.words, style.max_words_per_line)
        last = len(chunks) - 1
        for i, chunk in enumerate(chunks):
            start = chunk[0].start
            end = chunk[-1].end
            if end - start < MIN_DURATION:
                end = start + MIN_DURATION
            body = _build_karaoke_text(chunk)
            fi = (i == 0)
            fo = (i == last)
            if style.full_strip:
                events.extend(_strip_events(style, start, end, body, fi, fo))
            else:
                events.append(_word_box_text_event(start, end, body, fi, fo))

    return _header(style) + "\n".join(events) + "\n"


def write_ass(segments: list[Segment], path: Path, style: Style) -> None:
    path.write_text(build_ass(segments, style), encoding="utf-8")
