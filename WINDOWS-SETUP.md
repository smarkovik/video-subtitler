# Windows setup — what to download and where

This is a complete walkthrough for a non-developer on Windows. Two
paths are documented:

- **Easy path** (recommended): one download from GitHub, then
  double-click `setup.bat` and it installs everything else for you.
- **Manual path** (fallback if the easy path fails): three downloads
  you install yourself, in order.

You only do this once. After it's done, subtitling a video is a
drag-and-drop.

---

## Before you start — quick check

Press the Windows key, type `winver`, hit Enter. A small window
shows your Windows version.

- **Windows 11 — anything**: ✅ ready, follow the easy path.
- **Windows 10 build 19041 or newer** (about mid-2020 onwards):
  ✅ ready, follow the easy path.
- **Windows 10 older than build 19041**: skip to the [manual
  path](#manual-path) — `winget` won't be available to you.
- **Windows 8 or 7**: not supported. Sorry.

You also need about **3 GB of free disk space** for Python, ffmpeg,
and the speech-recognition model.

---

## Easy path

### Download #1 — the tool itself

Go to:

> <https://github.com/smarkovik/video-subtitler>

Click the green **Code** button (top-right of the file list) →
**Download ZIP**.

You'll get a file named `video-subtitler-main.zip` (a few hundred
KB) in your `Downloads` folder.

**Right-click that zip → Extract All... → choose Desktop** (or
anywhere you'll remember).

You should now have a folder called `video-subtitler-main` containing
files like `setup.bat`, `run.bat`, `README.md`, `Makefile`, and
folders called `src`, `docs`.

### Run setup.bat

**Double-click `setup.bat`** inside that folder.

A black window opens. It will:

1. Check that `winget` is available. (If not, see [What if winget is
   missing](#what-if-winget-is-missing) below.)
2. **Install Python 3.13** automatically. Windows may show a popup
   asking permission — click **Yes**. About 30 seconds.
3. **Install ffmpeg** automatically. Same — say Yes if asked. About
   1 minute.
4. Create a small Python environment inside the project folder
   (called `.venv`).
5. **Download the speech-recognition model.** This is ~1.5 GB and
   takes 5–15 minutes depending on your internet. Grab a coffee.

When you see **"Setup complete."**, you can close the window. You're
done with setup forever.

### What if winget is missing

If `setup.bat` says *"winget is missing"*:

1. Open the **Microsoft Store** (search for it from the Start menu).
2. Search for **"App Installer"** (publisher: *Microsoft Corporation*).
3. Click **Get** / **Update**.
4. Direct link: <https://apps.microsoft.com/detail/9NBLGGH4NNS1>

Once App Installer is installed/updated, run `setup.bat` again.

If it still doesn't work, follow the [manual path](#manual-path).

---

## Using it (after setup is done)

1. **Drag your video onto `run.bat`.** A black window opens and
   transcribes the audio. On a laptop, expect roughly the same time
   as the video itself (a 10-minute video → ~10 minutes).

2. When it finishes, look in the **same folder as your video**.
   There's a new file with the same name but ending in `.srt`. For
   example, if your video is `vacation.mp4`, you'll see
   `vacation.srt`.

3. **Open the `.srt` file in Notepad** (right-click → Open With →
   Notepad). It looks like this:

   ```
   1
   00:00:00,500 --> 00:00:03,200
   Добар дан, ja сам Марко.

   2
   00:00:03,500 --> 00:00:07,000
   Данас идемо да прочамо о Антибу.
   ```

   Read through. Fix any names, slang, or technical terms that the
   computer misheard. **Don't change the timestamp lines** (the ones
   with `-->`) — those tell the tool when each subtitle should
   appear. Save the file (Ctrl+S).

4. **Drag the same video onto `run.bat` again.** This time it
   builds the final video with the subtitles burned in. About the
   same speed as the video itself.

5. When it's done, look for `<your-video>.subbed.mp4` next to the
   original. **That's the file you upload to YouTube.**

After step 5 you can disconnect from the internet. Everything from
here on runs locally on your laptop.

---

## Manual path

Follow this if the easy path didn't work, or if you'd rather install
each piece yourself.

### Download #1 — Python 3.13

> <https://www.python.org/downloads/windows/>

Click **"Latest Python 3.13 Release"**, then on that page scroll
down to **"Files"** and download:

> **Windows installer (64-bit)** — `python-3.13.X-amd64.exe`

Run the downloaded `.exe`.

⚠️ **On the first installer screen, tick the box that says "Add
python.exe to PATH"** (bottom of the window). This is the most
important step — without it, nothing else works.

Then click **Install Now** and wait.

To verify: press Windows key, type `cmd`, hit Enter. In the black
window, type `python --version` and press Enter. You should see
`Python 3.13.something`.

### Download #2 — ffmpeg

> <https://www.gyan.dev/ffmpeg/builds/>

Scroll down to **"release builds"** and download:

> **`ffmpeg-release-essentials.zip`**

(File size ~80 MB.)

You need to extract this and put `ffmpeg.exe` somewhere on your PATH:

1. Right-click the downloaded zip → **Extract All...** → extract to
   `C:\` so you end up with a folder like
   `C:\ffmpeg-7.X-essentials_build`.
2. Rename that folder to just `C:\ffmpeg` (so the path is short and
   memorable).
3. Inside `C:\ffmpeg\bin` you should see `ffmpeg.exe`.
4. Add `C:\ffmpeg\bin` to your `Path` environment variable:
   - Press Windows key, type **"environment"**, click **"Edit the
     system environment variables"**.
   - Click **"Environment Variables..."** at the bottom.
   - Under **"User variables for ..."**, find the variable named
     `Path`, select it, click **Edit...**.
   - Click **New**, paste `C:\ffmpeg\bin`, click **OK** on every
     window.

To verify: open a **new** Command Prompt window (any old ones won't
see the change), type `ffmpeg -version` and press Enter. You should
see ffmpeg's version banner.

### Download #3 — the tool

Same as the easy path:

> <https://github.com/smarkovik/video-subtitler>

Green **Code** button → **Download ZIP** → extract to your Desktop.

### Run setup.bat

Once Python and ffmpeg are both installed and on your PATH, you can
still use `setup.bat` — it will see they're already installed,
skip them, and just create the venv, install Python deps, and
download the speech model.

If `setup.bat` still fails for some reason, you can run setup
yourself by opening Command Prompt **inside the project folder**
(Shift + right-click in the folder → "Open in Terminal" or "Open
PowerShell window here") and typing:

```
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt
set PYTHONPATH=src
.venv\Scripts\python -m subtitler --download-model
```

The last command downloads the speech model and is the slow one.

After that, `run.bat` works the same as in the easy path.

---

## Troubleshooting

**`setup.bat` opens and closes immediately.** It's pausing on a
"press any key" line — the window is just hidden. Bring it forward
or check the taskbar.

**"`python` is not recognized as an internal or external command."**
You ran the manual installer but didn't tick "Add python.exe to
PATH". Re-run the Python installer, choose **Modify**, and add it to
PATH. Or uninstall and reinstall, this time ticking the box.

**"`ffmpeg is missing the subtitles filter`"** during setup. The
ffmpeg you have installed was built without subtitle-rendering
support (libass). Uninstall it (Settings → Apps), then run
`setup.bat` again — it'll install the right one (`Gyan.FFmpeg`).
Or use the manual path with `ffmpeg-release-essentials.zip` from
gyan.dev, which includes libass.

**Model download fails halfway.** Hugging Face occasionally
rate-limits or your internet hiccups. Just run `setup.bat` again —
it will resume from where it left off. The download is cached at
`%USERPROFILE%\.cache\huggingface\hub`.

**Transcription runs but produces nonsense.** Double-check your
video actually has audio and that someone is speaking Serbian. If
the audio is very quiet or noisy, expect lower accuracy — that's
why there's a review step.

**Transcription is impossibly slow** (more than ~3× the video
length). Either (a) your laptop is too old for the `medium` model —
ask whoever sent you this tool to switch you to `small`, or (b) some
other heavy program is running. Close other apps and try again.

**"`run.bat` says `.venv` is missing".** You haven't run `setup.bat`
yet, or the venv folder got deleted. Run `setup.bat` again — it's
safe to re-run.
