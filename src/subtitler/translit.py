"""Serbian Latin -> Cyrillic transliteration.

Lossless because Serbian Latin (gajica) and Cyrillic (vukovica) are
1:1 except for three digraphs (lj, nj, dž) which each map to a single
Cyrillic letter.

We process longest-match first to handle the digraphs, and respect
case (LJ vs Lj vs lj).
"""

from __future__ import annotations

from .transcribe import Segment, Word


_DIGRAPHS = [
    ("Lj", "Љ"), ("LJ", "Љ"), ("lj", "љ"),
    ("Nj", "Њ"), ("NJ", "Њ"), ("nj", "њ"),
    ("Dž", "Џ"), ("DŽ", "Џ"), ("dž", "џ"),
]

_SINGLE = {
    "A": "А", "B": "Б", "V": "В", "G": "Г", "D": "Д", "Đ": "Ђ",
    "E": "Е", "Ž": "Ж", "Z": "З", "I": "И", "J": "Ј", "K": "К",
    "L": "Л", "M": "М", "N": "Н", "O": "О", "P": "П", "R": "Р",
    "S": "С", "T": "Т", "Ć": "Ћ", "U": "У", "F": "Ф", "H": "Х",
    "C": "Ц", "Č": "Ч", "Š": "Ш",
    "a": "а", "b": "б", "v": "в", "g": "г", "d": "д", "đ": "ђ",
    "e": "е", "ž": "ж", "z": "з", "i": "и", "j": "ј", "k": "к",
    "l": "л", "m": "м", "n": "н", "o": "о", "p": "п", "r": "р",
    "s": "с", "t": "т", "ć": "ћ", "u": "у", "f": "ф", "h": "х",
    "c": "ц", "č": "ч", "š": "ш",
}


def latin_to_cyrillic(text: str) -> str:
    out: list[str] = []
    i = 0
    while i < len(text):
        # Try digraphs first
        matched = False
        for src, dst in _DIGRAPHS:
            if text.startswith(src, i):
                out.append(dst)
                i += len(src)
                matched = True
                break
        if matched:
            continue
        ch = text[i]
        out.append(_SINGLE.get(ch, ch))
        i += 1
    return "".join(out)


def latin_to_cyrillic_segments(segments: list[Segment]) -> list[Segment]:
    out: list[Segment] = []
    for s in segments:
        words = [
            Word(start=w.start, end=w.end, text=latin_to_cyrillic(w.text))
            for w in s.words
        ]
        out.append(
            Segment(
                start=s.start,
                end=s.end,
                text=latin_to_cyrillic(s.text),
                words=words,
            )
        )
    return out
