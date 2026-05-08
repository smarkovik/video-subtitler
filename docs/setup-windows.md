# Windows setup (plug-and-play)

For non-developers. You'll do this **once**. After that, subtitling
a video is just a drag-and-drop.

## What you need

- A Windows 10 (build 1809 or newer) or Windows 11 PC.
- An internet connection for the first-time setup only.
- About 3 GB of free disk space (Python + ffmpeg + the speech model).

## Step 1 — Get the tool

1. Go to <https://github.com/smarkovik/video-subtitler>.
2. Click the green **Code** button → **Download ZIP**.
3. Right-click the downloaded zip → **Extract All...** → pick a
   folder you'll remember (Desktop is fine).

You should now have a folder called `video-subtitler` with files
inside it including `setup.bat` and `run.bat`.

## Step 2 — Run setup (one time)

**Double-click `setup.bat`** inside the `video-subtitler` folder.

A black window opens and walks through:

1. Installing Python (if you don't have it).
2. Installing ffmpeg (the video tool).
3. Downloading the speech-recognition model (about 1.5 GB — grab a
   coffee, this is the slow part).

Windows will probably show a popup asking permission to install
software. Click **Yes**.

When you see "Setup complete." you can close the window.

## Step 3 — Subtitle a video

1. **Drag your video file onto `run.bat`.**
   A black window opens and starts transcribing. On a laptop, expect
   it to take roughly the same length as the video itself.

2. When it finishes, look in the same folder as your video. There's
   now a file with the same name but ending in `.srt` — for example
   `vacation.srt` next to `vacation.mp4`.

3. **Open the `.srt` file** in Notepad (right-click → Open With →
   Notepad). Read through the text. Fix any names, technical terms,
   or words the computer misheard. Save the file.

   Don't change the timestamps (the lines like
   `00:00:14,190 --> 00:00:16,510`) — those tell the tool when each
   subtitle should appear.

4. **Drag the same video onto `run.bat` again.**
   This time it builds the final video with the subtitles burned in.

When it's done, look for a file ending in `.subbed.mp4` next to your
original video. That's the one you upload to YouTube.

## Going offline

After setup is done, you can disconnect from the internet entirely.
The whole transcription and rendering pipeline runs on your machine.

## Troubleshooting

**"setup.bat" closes immediately when I double-click it** — the
script paused waiting for you to press a key. Look for the window;
it might be hidden behind another one.

**"winget is missing"** — your Windows is too old. Open the
Microsoft Store, search for "App Installer" by Microsoft, install or
update it. Then run `setup.bat` again.

**Pop-up asks for admin / UAC** — that's Windows asking permission
to install Python or ffmpeg. Click Yes.

**Setup says "ffmpeg is missing the subtitles filter"** — the
Windows ffmpeg build doesn't include subtitle rendering. The setup
script asks for the right one (`Gyan.FFmpeg`); if you already had
a different one installed, uninstall it first.

**Transcription runs but the words are wrong** — that's expected
for names, slang, or technical terms. That's why you edit the `.srt`
in step 3 before rendering.

**Transcription is impossibly slow** — `medium` is the default
model. If your laptop is from before ~2018, ask whoever sent you
this tool to switch to `small` (faster, slightly less accurate).
