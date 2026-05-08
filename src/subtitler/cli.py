"""Command-line entry point.

Two-stage workflow:

  1. python -m subtitler video.mp4
     -> extracts audio, transcribes, writes video.srt + video.words.json
     -> tells the user to edit video.srt and rerun with --render

  2. python -m subtitler video.mp4 --render
     -> re-reads edited SRT, realigns word timings, builds ASS, burns

Pass --download-model on the very first run with internet to cache
the Whisper weights, then never need internet again.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .audio import extract_audio, FFmpegMissing, FFmpegFailed
from .transcribe import transcribe
from .srt import write_srt, read_srt
from .store import write_words_json, read_words_json
from .ass import write_ass
from .burn import burn
from .realign import realign


def _paths(video: Path) -> dict[str, Path]:
    stem = video.with_suffix("")
    return {
        "audio": stem.with_suffix(".wav"),
        "srt": stem.with_suffix(".srt"),
        "words": Path(str(stem) + ".words.json"),
        "ass": stem.with_suffix(".ass"),
        "out": Path(str(stem) + ".subbed.mp4"),
    }


def _stage_transcribe(video: Path, model: str) -> int:
    p = _paths(video)
    print(f"[1/3] Extracting audio -> {p['audio'].name}")
    try:
        extract_audio(video, p["audio"])
    except (FFmpegMissing, FFmpegFailed) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    print(f"[2/3] Transcribing with whisper-{model} (cpu, int8)...")
    print("      First run downloads the model; later runs are offline.")
    segments = transcribe(p["audio"], model_size=model, language="sr")

    print(f"[3/3] Writing {p['srt'].name} and {p['words'].name}")
    write_srt(segments, p["srt"])
    write_words_json(segments, p["words"])

    print()
    print("Transcription complete.")
    print(f"  1. Open {p['srt'].name} in a text editor.")
    print("  2. Fix any misheard names, slang, or technical terms.")
    print("  3. Save, then rerun with --render to burn the subtitles in.")
    return 0


def _stage_render(video: Path, cyrillic: bool, clean: bool) -> int:
    p = _paths(video)
    if not p["srt"].exists() or not p["words"].exists():
        print(
            f"error: missing {p['srt'].name} or {p['words'].name}.\n"
            "Run without --render first to generate them.",
            file=sys.stderr,
        )
        return 2

    print(f"[1/3] Reading edited {p['srt'].name} and reattaching word timings")
    edited = read_srt(p["srt"])
    original = read_words_json(p["words"])
    segments = realign(edited, original)

    if clean:
        from .cleanup import strip_fillers
        segments = strip_fillers(segments)
        print("      filler-word cleanup applied")

    if cyrillic:
        from .translit import latin_to_cyrillic_segments
        segments = latin_to_cyrillic_segments(segments)
        print("      transliterated to Cyrillic")

    print(f"[2/3] Building ASS -> {p['ass'].name}")
    write_ass(segments, p["ass"])

    print(f"[3/3] Burning into {p['out'].name} (this is the slow part)")
    try:
        burn(video, p["ass"], p["out"])
    except (FFmpegMissing, FFmpegFailed) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    print()
    print(f"Done. Final video: {p['out']}")
    return 0


def _download_model(model: str) -> int:
    print(f"Downloading whisper-{model} weights to HF cache...")
    from faster_whisper import WhisperModel
    WhisperModel(model, device="cpu", compute_type="int8")
    print("Done. You can disconnect from the internet now.")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="subtitler",
        description="Offline Serbian video subtitler.",
    )
    p.add_argument("video", nargs="?", type=Path, help="path to the video file")
    p.add_argument("--render", action="store_true",
                   help="render final video from edited SRT (run after editing)")
    p.add_argument("--cyrillic", action="store_true",
                   help="transliterate Latin output to Cyrillic before render")
    p.add_argument("--clean", action="store_true",
                   help="strip filler words before render")
    p.add_argument("--model", default="medium",
                   help="whisper model size (default: medium)")
    p.add_argument("--download-model", action="store_true",
                   help="download model weights and exit (one-time, needs internet)")
    args = p.parse_args(argv)

    if args.download_model:
        return _download_model(args.model)

    if not args.video:
        p.error("video path required (unless using --download-model)")

    video = args.video.expanduser().resolve()
    if not video.exists():
        print(f"error: {video} not found", file=sys.stderr)
        return 2

    if args.render:
        return _stage_render(video, cyrillic=args.cyrillic, clean=args.clean)
    return _stage_transcribe(video, model=args.model)


if __name__ == "__main__":
    sys.exit(main())
