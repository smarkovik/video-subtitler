# video-subtitler

Fully offline subtitle generator for Serbian-language YouTube videos.

Drop a video in, get back the same video with burned-in word-by-word
subtitles plus a standalone `.srt` file. Runs locally on a modest
Windows laptop with no GPU and no internet (after a one-time model
download).

## Status

Early development. See [docs/ideation.md](docs/ideation.md) for the
problem statement and design decisions, and the commit log for build
progress.

## Quick start (macOS / Linux)

```bash
make setup                              # venv + deps + ffmpeg sanity check
make model                              # one-time, needs internet
make transcribe VIDEO=path/to/video.mov # produces video.srt for review
# ... open video.srt in your editor, fix names/slang, save ...
make encode VIDEO=path/to/video.mov     # produces video.subbed.mp4
```

Optional flags via `FLAGS=`:

```bash
make encode VIDEO=v.mov FLAGS="--clean"     # strip filler words
make encode VIDEO=v.mov FLAGS="--cyrillic"  # transliterate Latin -> Cyrillic
```

`make clean VIDEO=v.mov` removes the generated `.wav`, `.srt`,
`.words.json`, `.ass`, and `.subbed.mp4` (keeps the source video).
`make help` lists all targets.

## Quick start (Windows, non-developer)

1. Download the repo as a ZIP and extract it.
2. Double-click `setup.bat`. It installs Python, ffmpeg, and the
   speech model for you. Wait for "Setup complete."
3. Drag a video onto `run.bat` to transcribe.
4. Edit the generated `.srt` in Notepad to fix any misheard words.
5. Drag the same video onto `run.bat` again to burn in the subtitles.

Full walkthrough — including specific download URLs and a manual
fallback path — in [WINDOWS-SETUP.md](WINDOWS-SETUP.md).

## Pipeline

```
video.mp4
   │
   ├─► extract audio (ffmpeg)
   │
   ├─► transcribe (faster-whisper, medium, sr)
   │       └─► video.srt        ← user edits names/slang here
   │       └─► video.words.json
   │
   ├─► [pause for review]
   │
   ├─► render ASS with per-word highlight
   │
   └─► burn into video.subbed.mp4 (ffmpeg)
```

## Goals

- 100% offline after first-run model download
- Serbian transcription, Latin or Cyrillic output
- Burned-in karaoke-style subtitles (Arial bold, white on black)
- Manual review step before the final render
- Drag-and-drop on Windows; CLI everywhere else

## Non-goals

- Real-time transcription
- Batch processing
- Cloud anything
- Pretty UI (the video is the product, not the app)
