# Ideation

Captured at project start. This is the "why" and "what" — the "how"
lives in [architecture.md](architecture.md).

## Who it's for

A Serbian-speaking YouTuber. He records videos in Serbian, mostly
talking-head style, between 30 seconds and 30 minutes long. He wants
subtitles on every video without paying for a cloud service or sending
his footage anywhere.

## The job

Take one video file. Produce two things:

1. The same video with subtitles burned into the picture.
2. A standalone `.srt` file (so YouTube viewers can toggle them off,
   and so future tools can re-use the timing).

## Hard constraints

- **Offline.** Runs on his machine, no network calls. One-time model
  download during setup is fine; after that, airplane mode works.
- **Modest hardware.** Windows ThinkPad laptop, no discrete GPU. Slow
  is acceptable; broken is not.
- **Serbian language.** Output script is Latin by default, Cyrillic
  optional via a flag.

## Soft preferences

- **Cleaned-up text** over literal transcription. Filler words like
  *ovaj*, *znači*, *pa* should be removable.
- **Word-by-word highlight** (TikTok / karaoke style) on the burned-in
  track. The `.srt` stays standard 1–2 line blocks.
- **Style.** Arial bold, white text on a solid black background, size
  ~11. We'll polish later — the video is the product, not the app.
- **Review step.** Whisper will mishear names, slang, and technical
  terms. He gets to edit the `.srt` before the final render.

## Workflow he wants

1. Drag video onto the tool.
2. Wait. Get back a `.srt`.
3. Open it in Notepad, fix mistakes, save.
4. Run again to render the final video.

CLI is acceptable for v1. A drag-and-drop `.bat` wrapper comes after
the pipeline works.

## What we're explicitly not building

- Real-time / live transcription.
- Batch processing — one video at a time is fine.
- A polished GUI. Maybe later, if the CLI proves annoying.
- Translation. Serbian in, Serbian out.

## Decisions made up front

| Question | Answer | Why |
|---|---|---|
| Transcription engine | `faster-whisper` (CTranslate2, int8) | Best CPU performance for Whisper; supports word timestamps natively. |
| Model size | `medium` | Good Serbian accuracy; fits the "slow but works" budget on a CPU laptop. |
| Subtitle format for burn-in | ASS (Advanced SubStation Alpha) | Required for per-word styling; ffmpeg burns it in directly. |
| Subtitle format for delivery | SRT | What YouTube and editors expect. |
| Burn-in tool | `ffmpeg` with `subtitles` filter | Standard, offline, scriptable. |
| Default output script | Latin | What the user defaults to. |
| Cyrillic | Post-transcription transliteration via `--cyrillic` | Lossless for Serbian; avoids retraining. |

## Open questions (deferred)

- Filler-word list — start with a small handful (`ovaj`, `znači`,
  `pa`, `ono`), iterate based on his actual videos.
- Exact subtitle styling (font size, padding, position) — get
  something reasonable working, then tune from a real render.
- Whether to ship a GUI later. Decide after he's used the CLI for a
  few videos.
