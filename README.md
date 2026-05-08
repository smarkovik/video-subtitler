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
