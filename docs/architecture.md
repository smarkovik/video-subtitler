# Architecture

## Components

```
┌─────────────┐
│   cli.py    │  entry point: parse args, orchestrate
└──────┬──────┘
       │
   ┌───┴────┐
   │ stage  │  decided by file presence:
   │ select │  no .srt yet → transcribe stage
   └───┬────┘  .srt exists → render stage
       │
       ├─── transcribe stage ────────────────────┐
       │                                          │
       │  audio.py    → extract 16kHz mono WAV   │
       │  transcribe  → faster-whisper, sr, word │
       │                timestamps               │
       │  cleanup.py  → strip filler words       │
       │  srt.py      → write video.srt          │
       │  (also writes video.words.json)         │
       │                                          │
       └─── render stage ────────────────────────┤
                                                  │
          read edited video.srt + words.json     │
          translit.py  → optional Cyrillic       │
          ass.py       → ASS with per-word       │
                         karaoke highlight       │
          burn.py      → ffmpeg burn-in →        │
                         video.subbed.mp4        │
                                                  │
                                                  ▼
                                          done
```

## Module responsibilities

| Module | Role |
|---|---|
| `cli.py` | Argument parsing, stage selection, user prompts. |
| `audio.py` | Wrap `ffmpeg` to extract a Whisper-friendly WAV. |
| `transcribe.py` | Wrap `faster-whisper`; return segments with word timestamps. |
| `cleanup.py` | Remove filler words from segments and word lists. |
| `srt.py` | Serialize segments to SubRip format. |
| `translit.py` | Serbian Latin ↔ Cyrillic, lossless. |
| `ass.py` | Build ASS file with karaoke `\k` tags for word highlight. |
| `burn.py` | Wrap `ffmpeg subtitles=` filter to burn ASS into MP4. |

## Data passed between stages

`video.srt` — what the user edits.

`video.words.json` — word-level timestamps the SRT can't carry.
Without this, the render stage would have to re-transcribe.

```json
[
  {
    "start": 0.0,
    "end": 3.2,
    "text": "Dobar dan, ja sam Marko.",
    "words": [
      {"start": 0.0, "end": 0.5, "text": "Dobar"},
      {"start": 0.5, "end": 0.9, "text": "dan,"},
      {"start": 1.2, "end": 1.5, "text": "ja"},
      {"start": 1.5, "end": 1.8, "text": "sam"},
      {"start": 1.8, "end": 3.2, "text": "Marko."}
    ]
  }
]
```

When the user edits the SRT, we re-align the edited text onto the
original word timestamps in the render stage. Simple strategy: split
edited segment text on whitespace and zip with the original word
timings. If word counts diverge, fall back to evenly distributing the
new words across the segment's duration.

## Why faster-whisper over alternatives

| Option | Why not |
|---|---|
| OpenAI `openai-whisper` | Slowest CPU path; no native int8. |
| `whisper.cpp` | Fast on CPU, but Python bindings are awkward and word-timestamp support is less mature. |
| `WhisperX` | Excellent alignment, but pulls in pyannote and adds GPU-leaning dependencies. |
| **`faster-whisper`** | CTranslate2 backend, int8 quantization, native word timestamps, pip-installable, works fine on Windows CPU. |

## Why ASS for burn-in

SRT can only carry plain text and timing. We need:

- Per-word highlight (karaoke `\k`)
- Specific font, size, weight, colors
- Background box behind text
- Predictable positioning across resolutions

ASS is the standard for all of that, and `ffmpeg`'s `subtitles=`
filter renders it natively. The user-facing `.srt` stays plain SRT;
the ASS is an internal render artifact.

## Failure modes to handle

- **ffmpeg missing** → friendly error pointing to WINDOWS-SETUP.md.
- **Model download fails** (first run, no internet) → suggest running once with internet to cache.
- **Edited SRT word count differs from original** → fall back to even time distribution, log a warning.
- **Video has no audio** → ffmpeg returns empty WAV, transcription yields zero segments → emit empty SRT and stop.
