# Windows setup

One-time setup for a Windows ThinkPad. After this, the tool runs
fully offline.

## 1. Install Python 3.11

Grab the installer from <https://www.python.org/downloads/windows/>.
**Tick "Add Python to PATH"** during install.

Verify in a fresh PowerShell window:

```powershell
python --version
```

Should print `Python 3.11.x`.

## 2. Install ffmpeg

Easiest way: install the [Gyan.dev essentials build](https://www.gyan.dev/ffmpeg/builds/).

1. Download the "release essentials" zip.
2. Unzip to `C:\ffmpeg`.
3. Add `C:\ffmpeg\bin` to your `Path` (System Properties → Environment Variables → Path → Edit → New).

Verify:

```powershell
ffmpeg -version
```

## 3. Clone and install this project

```powershell
git clone <repo-url> video-subtitler
cd video-subtitler

python -m venv .venv
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

If PowerShell refuses to run `Activate.ps1`, run this once as
Administrator and retry:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## 4. First run (downloads the model)

The Whisper `medium` model (~1.5 GB) downloads on first use and is
cached at `%USERPROFILE%\.cache\huggingface\hub`. Run this once with
internet:

```powershell
python -m subtitler --download-model
```

After this completes, you can disconnect from the internet entirely.

## 5. Use it

```powershell
python -m subtitler "C:\path\to\video.mp4"
```

This produces `video.srt` and `video.words.json` next to the source.

Open `video.srt` in Notepad, fix any misheard names or words, save.

Then render:

```powershell
python -m subtitler "C:\path\to\video.mp4" --render
```

This produces `video.subbed.mp4`.

Drag-and-drop wrapper (`run.bat`) is documented separately once it
ships.

## Troubleshooting

**"ffmpeg is not recognized"** — `Path` change didn't take effect.
Close and reopen PowerShell, or sign out and back in.

**Model download stalls** — Hugging Face occasionally rate-limits.
Retry after a minute, or set `HF_HUB_ENABLE_HF_TRANSFER=0`.

**Transcription is impossibly slow** — confirm you're on the `medium`
model, not `large-v3`. Drop to `small` with `--model small` if your
laptop is older than 2018.
