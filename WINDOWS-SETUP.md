# Setting up video-subtitler on Windows

Hi 👋 — follow every step in order. Don't skip ahead. If anything on
your screen doesn't match what's described here, **stop and screenshot
the window for Tancho** before continuing.

> 🇷🇸 Српска верзија: [windows-setup.serbian.md](windows-setup.serbian.md)

You'll need:

- A laptop with Windows 10 or Windows 11.
- Internet connection (only during setup; offline afterwards).
- About **30–60 minutes** — most of it just waiting.
- About **3 GB of free disk space**.

You'll do this **once**. After it's working, making subtitles is a
drag-and-drop.

---

## Step 1 — Open Chrome and download the tool

1. **Open Chrome.** (Edge or Firefox also work — pick whichever you
   normally use.)

2. In the address bar at the top, type or paste this and press **Enter**:

   <https://github.com/smarkovik/video-subtitler>

3. You'll see a page listing files like `README.md`, `setup.bat`,
   `src`, `docs`, etc.

4. Near the **top right** of the file list, find the green button
   labelled **"Code"** with a small `<>` icon. Click it.

5. A small menu drops down. At the **bottom of the menu** there's a
   link **"Download ZIP"**. Click it.

6. A file called **`video-subtitler-main.zip`** downloads. It's
   small, well under 1 MB. Wait for the download to finish.

---

## Step 2 — Extract the ZIP

Windows can't run anything from inside a ZIP — you have to extract it
first.

1. Open **File Explorer** (the yellow folder icon on your taskbar,
   or press **Windows key + E**).

2. In the left sidebar click **"Downloads"**.

3. Find **`video-subtitler-main.zip`**, **right-click** it, and
   choose **"Extract All..."**.

4. A window asks where to extract. Click **"Browse..."**, pick
   **"Desktop"** in the left sidebar, click **"Select Folder"**, then
   click **"Extract"**.

5. A new File Explorer window opens. You'll be inside a folder
   called `video-subtitler-main` containing **another** folder with
   the same name. Double-click into the inner one.

6. You should now see files including:

   ```
   setup.bat
   ui.bat
   run.bat
   README.md
   src/
   docs/
   ```

   Keep this File Explorer window open — you'll need it for the next
   step.

---

## Step 3 — Run setup.bat (the slow step)

This installs Python, ffmpeg, and downloads the 1.5 GB speech model.
Allow **5–15 minutes** depending on your internet speed.

1. **Double-click `setup.bat`**.

2. **Possible popup**: Windows may say *"Windows protected your PC"*
   on a blue background. If you see it:

   - Click the small **"More info"** link.
   - A new button appears: **"Run anyway"**. Click it.

3. A black window opens. It pauses with **"Press any key to
   continue..."**. Press the spacebar.

4. The window prints progress headers:

   - `==> Checking prerequisites`
   - `==> Installing Python and ffmpeg`
   - `==> Verifying ffmpeg has subtitle support`
   - `==> Creating Python virtual environment`
   - `==> Installing Python dependencies`
   - `==> Downloading Whisper-medium speech model (~1.5 GB)`

5. **Possible popups**: while installing Python and ffmpeg, Windows
   may ask "Do you want to allow this app to make changes?". Click
   **Yes** every time.

6. **The model download is the slowest line.** The window will look
   frozen for 5–15 minutes. **It's not frozen — it's downloading.**
   Don't close it. Don't press anything. Just wait.

7. When everything finishes you'll see:

   ```
   ============================================================
     Setup complete. You can close this window.

     To subtitle a video: drag it onto run.bat
   ============================================================
   ```

   Press any key to close the window. **Setup is done forever** —
   you never need to run `setup.bat` again.

---

## Step 4 — Open the tool

1. In the same File Explorer folder, find **`ui.bat`**.

2. **Double-click `ui.bat`**.

3. A black window opens with:

   ```
   Starting the video-subtitler UI...
   Your browser should open in a moment.
   Leave this window open while you work. Close it to stop the server.
   ```

4. After 2–3 seconds, **your browser opens automatically** to a page
   titled "video-subtitler" with a big dashed box reading **"Drop a
   video here"**.

5. ⚠️ **Don't close the black window.** It's the running server —
   close it and the page stops working.

If the browser doesn't open by itself, open it manually, type
**`localhost:8765`** in the address bar, and press Enter.

---

## Step 5 — Now upload the video with drag and drop

Drag your video file from File Explorer onto the dashed box in the
browser.
