# Setting up video-subtitler on Windows

Hi 👋 — this is the full step-by-step. Follow every step in order.
Don't skip ahead. If something on your screen doesn't look like
what's described here, **stop and message Tancho** before continuing.

You'll do this **once**. After it's working, making subtitles is a
drag-and-drop.

## What you'll need

- A laptop running Windows 10 or Windows 11.
- Internet connection (only needed during setup — afterwards the
  tool runs offline).
- About **30–60 minutes**. Most of it is waiting; you don't have to
  babysit the screen.
- About **3 GB of free disk space** for Python, ffmpeg, and the
  speech-recognition model.

---

## Step 1 — Check your Windows version

Some old Windows builds can't run this. Two minutes to check.

1. Press the **Windows key** on your keyboard (the one with the
   Windows logo, between Ctrl and Alt).
2. Type **`winver`** (no quotes). Press **Enter**.
3. A small "About Windows" window opens. Read the line that starts
   with **"Version"**.

What to do based on what you see:

- **"Windows 11" — anything**: ✅ continue to Step 2.
- **"Windows 10 Version 2004 (OS Build 19041.x)"** or higher: ✅ continue to Step 2.
- **Anything older, or "Windows 8 / 7"**: stop here, message Tancho.

Close the small window when you're done.

---

## Step 2 — Download the tool from GitHub

You're going to download a ZIP file. Don't worry about Git, GitHub
accounts, or anything technical.

1. Open your web browser (Edge, Chrome, Firefox — any of them work).
2. Type or paste this address into the address bar and press Enter:

   <https://github.com/smarkovik/video-subtitler>

3. You'll see a page listing files like `README.md`, `setup.bat`,
   `src`, `docs`, etc.

4. Near the **top right**, find the green button labelled **"Code"** with a small `<>` icon. Click it.

5. A small menu pops down. Look at the **bottom of the menu** for the link **"Download ZIP"**. Click it.

6. A file called **`video-subtitler-main.zip`** starts downloading. It's small — well under 1 MB. Wait for it to finish.

---

## Step 3 — Extract the ZIP

ZIP files have to be "extracted" before you can use them on Windows.

1. Open **File Explorer** (the yellow folder icon on your taskbar,
   or press **Windows key + E**).
2. In the left sidebar, click **"Downloads"**.
3. Find the file **`video-subtitler-main.zip`**.
4. **Right-click** it. From the menu choose **"Extract All..."**.
5. A window appears asking where to extract. Click **"Browse..."**.
6. In the left sidebar of the Browse window, click **"Desktop"**.
   Then click **"Select Folder"**.
7. Make sure the box "**Show extracted files when complete**" is
   ticked. Click **"Extract"**.

8. After a few seconds, a new File Explorer window opens. You'll be
   inside a folder called `video-subtitler-main` containing **another** folder with the same name. Double-click into the inner one.

9. **You should now see these files** (among others):

   ```
   setup.bat
   ui.bat
   run.bat
   README.md
   WINDOWS-SETUP.md
   Makefile
   src/
   docs/
   ```

   If you see those — Step 3 is done. **Keep this File Explorer
   window open** — you'll need it for the next step.

---

## Step 4 — Run the setup (the slow step)

This installs Python, ffmpeg, and downloads the 1.5 GB speech model.
Allow **5–15 minutes** depending on your internet speed.

1. In the File Explorer window from Step 3, find **`setup.bat`**.

2. **Double-click `setup.bat`**.

3. **Possible popup #1**: Windows might say *"Windows protected your
   PC"* with a blue background. If you see it:

   - Click the small **"More info"** link.
   - A new button appears: **"Run anyway"**. Click it.

4. A black window opens with a header that reads:

   ```
   ============================================================
     video-subtitler — first-time setup
   ============================================================
   ```

   It pauses and says **"Press any key to continue..."**. Press any
   key (the spacebar is fine).

5. The window prints progress lines like:

   - `==> Checking prerequisites`
   - `==> Installing Python and ffmpeg`
   - `==> Verifying ffmpeg has subtitle support`
   - `==> Creating Python virtual environment`
   - `==> Installing Python dependencies`
   - `==> Downloading Whisper-medium speech model (~1.5 GB)`

6. **Possible popup #2 and #3**: While installing Python and ffmpeg,
   Windows may pop up a "User Account Control" prompt asking if you
   want to allow changes to your device. **Click Yes** every time.

7. **The slowest line is the model download.** The window will look
   frozen for 5–15 minutes. **It's not frozen — it's downloading.** Don't close it. Don't press anything. Just wait.

8. When everything is done you'll see this:

   ```
   ============================================================
     Setup complete. You can close this window.

     To subtitle a video: drag it onto run.bat
   ============================================================

   Press any key to continue . . .
   ```

   Press any key to close the window. **Setup is done forever.**

If instead you see **"Setup failed"** — screenshot the window and
message Tancho. Don't try to fix it yourself.

---

## Step 5 — Open the tool for the first time

1. In the same folder, find **`ui.bat`**. Double-click it.

2. A black window opens with:

   ```
   Starting the video-subtitler UI...
   Your browser should open in a moment.
   Leave this window open while you work. Close it to stop the server.
   ```

3. After 2–3 seconds, **your default web browser opens automatically** to a page titled "video-subtitler" with a big dashed box that says **"Drop a video here"**.

4. ⚠️ **Don't close the black window.** It's the running server. If
   you close it, the page in the browser stops working.

If your browser doesn't open by itself:

- Open your browser manually.
- In the address bar, type: **`localhost:8765`** — press Enter.
- The page should appear.

---

## Step 6 — Subtitle your first video

The tool is now running. Here's how to use it.

### 6a. Upload a video

In the browser:

1. Open another File Explorer window. Find a video you want to
   subtitle (an `.mp4`, `.mov`, `.mkv`, or `.avi` file).
2. **Drag the video file from File Explorer onto the dashed box** in the browser.
3. The page changes to a "Transcribing..." view with a progress bar.

### 6b. Wait for transcription

- A progress bar fills up gradually.
- Underneath it, you'll see segments of text appear as the computer
  hears them.
- **On a laptop, this takes roughly as long as the video itself.** A 5-minute video → about 5 minutes of waiting. A 30-minute video → about 30 minutes.
- Don't close the black window or the browser tab.

### 6c. Review the transcript

When transcription finishes, the page changes to a **"Review the
transcript"** view. You'll see one editable box per spoken segment.

- **Read each line.** Look for:
  - Names of people, places, or products (the computer mishears these often).
  - Slang or unusual words.
  - Numbers (it sometimes writes them out as letters).
- **Click into a box and edit any line as needed.**
- **Don't touch the timestamps on the left** (e.g. `0:14–0:17`). Those tell the tool when each subtitle should appear.

### 6d. Choose a style (optional)

Below the transcript there's a panel called **"Subtitle style"**. Click it to expand. You can change:

- **Font**: Arial is the default and works everywhere. Try others if you like.
- **Highlight colour**: the colour of the active word (yellow by default).
- **Text colour**: the colour of the other words (white by default).
- **Box opacity**: how solid the black background is, 0% to 100%.
- **Position**: top / middle / bottom of the screen.
- **Strip mode**: per-word boxes (default) vs one long strip across the whole width.
- **Corner radius**: only matters when strip mode is on — rounds the strip corners.

The little preview at the bottom of the panel shows roughly what
the result will look like.

### 6e. Render

Click the orange **"Render video"** button.

- A new progress bar appears.
- This step burns the subtitles into the video. **Plan on roughly the same length as the video again.**

### 6f. Download

When rendering finishes, a green **"Download subtitled video"** button appears.

- Click it. The finished video saves to your Downloads folder.
- The filename ends with `.subbed.mp4`. **That's the file to upload to YouTube.**

---

## How to use the tool from now on

Setup is one-time. Day to day:

| What you want to do | How |
|---|---|
| Open the tool | Double-click `ui.bat`. Browser opens automatically. |
| Subtitle a new video | Drop it onto the page in the browser. |
| Stop the tool | Close the black window. |

You **never** need to run `setup.bat` again — unless you accidentally delete the `.venv` folder, in which case run it once more.

---

## If something goes wrong

**The black window flashed open and closed instantly.**
The script paused waiting for a key press. The window might be
hiding behind another one. Look for it on the taskbar.

**`setup.bat` says "winget is missing".**
Your Windows 10 is too old. Open the Microsoft Store, search for
**"App Installer"** by Microsoft, and click **Get** / **Update**.
Then run `setup.bat` again.

Direct link: <https://apps.microsoft.com/detail/9NBLGGH4NNS1>

**Setup got stuck for more than 30 minutes on the model download.**
Kill it (close the window), reconnect to the internet if needed, and
double-click `setup.bat` again. The download resumes from where it
stopped — it doesn't restart from zero.

**The browser opens but the page is blank or says "can't connect".**
Wait 5 more seconds and refresh the page (F5). If still blank, close
the black window and double-click `ui.bat` again.

**The transcription is wildly wrong.**
For names, slang, and technical terms — that's expected. That's why
there's a review step. Edit the boxes and continue.

**The transcription is wrong on most words, not just names.**
The audio might be too quiet, too noisy, or in a language other
than Serbian. Try a clip of clearer speech to confirm the tool is
working.

**It's been more than 3× the video length and transcription isn't
done.**
Your laptop is older than the tool can handle gracefully. Message
Tancho — there's a smaller speech model that runs faster.

**Anything else weird.**
Screenshot the black window and message Tancho. Include what step
you were on.

---

## Appendix — Manual install (only if `setup.bat` keeps failing)

You should not need this. Try `setup.bat` first. This is a backup
plan only.

If `setup.bat` fails repeatedly, you can install the prerequisites
yourself:

1. **Python 3.13** from <https://www.python.org/downloads/windows/>.
   Click "Latest Python 3.13 Release", scroll to "Files", download
   "Windows installer (64-bit)". When you run the installer, **tick
   the box "Add python.exe to PATH"** on the first screen — this is
   critical.

2. **ffmpeg** from <https://www.gyan.dev/ffmpeg/builds/>. Download
   "ffmpeg-release-essentials.zip". Extract to `C:\ffmpeg`. Add
   `C:\ffmpeg\bin` to your PATH (Start → "Edit the system
   environment variables" → "Environment Variables..." → under "User
   variables" find `Path` → "Edit..." → "New" → paste
   `C:\ffmpeg\bin` → OK on every window).

3. Re-run `setup.bat`. It will see Python and ffmpeg are already
   installed, skip them, and just create the venv and download the
   model.
