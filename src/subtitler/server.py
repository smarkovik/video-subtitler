"""FastAPI server that drives the same pipeline as the CLI but via a
local web UI.

State model:
- Each upload becomes a Job with its own working directory.
- The job moves through statuses: uploaded -> transcribing ->
  transcribed -> rendering -> rendered (or error at any point).
- Heavy work (transcribe, burn) runs in BackgroundTasks. Progress is
  appended to the Job in memory.
- The browser opens an SSE stream (/jobs/{id}/events) that drips out
  segments and log lines as they're produced. The endpoint exits
  when the job hits a terminal state, so the frontend opens it once
  per phase (transcribe, then render).

In-memory state is single-process and lives only as long as the
server. That's fine — this is a personal tool for one user, not a
hosted service.
"""

from __future__ import annotations

import asyncio
import json
import shutil
import threading
import uuid
import webbrowser
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .audio import extract_audio, probe_dimensions, probe_duration
from .ass import Style, write_ass
from .burn import burn
from .realign import realign
from .srt import write_srt
from .store import write_words_json
from .transcribe import Segment, transcribe


WEB_DIR = Path(__file__).parent / "web"
WORK_DIR = Path.cwd() / ".jobs"


@dataclass
class Job:
    id: str
    workdir: Path
    video: Path
    original_name: str
    status: str = "uploaded"
    message: str = ""
    segments: list[Segment] = field(default_factory=list)
    log: list[str] = field(default_factory=list)
    width: int = 0
    height: int = 0
    duration_s: float = 0.0
    # Progress: 0..100. phase identifies which step the percent is
    # describing so the frontend can route it to the right meter.
    progress_percent: int = 0
    progress_phase: str = ""  # "transcribe" | "burn" | ""


JOBS: dict[str, Job] = {}

app = FastAPI(title="video-subtitler")


# ---------- routes -----------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (WEB_DIR / "index.html").read_text(encoding="utf-8")


# Static files (app.js, style.css). Mounted at /static so the HTML
# can reference them without colliding with API routes.
app.mount(
    "/static",
    StaticFiles(directory=str(WEB_DIR), check_dir=False),
    name="static",
)


@app.post("/upload")
async def upload(file: UploadFile = File(...)) -> dict:
    job_id = uuid.uuid4().hex[:8]
    workdir = WORK_DIR / job_id
    workdir.mkdir(parents=True, exist_ok=True)

    suffix = Path(file.filename or "video.mp4").suffix or ".mp4"
    video_path = workdir / f"video{suffix}"
    with video_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    job = Job(
        id=job_id,
        workdir=workdir,
        video=video_path,
        original_name=file.filename or "video",
    )
    JOBS[job_id] = job
    job.log.append(f"Uploaded {job.original_name} ({video_path.stat().st_size // 1024} KB)")
    return {"job_id": job_id, "filename": job.original_name}


@app.post("/jobs/{job_id}/transcribe")
def start_transcribe(job_id: str, bg: BackgroundTasks) -> dict:
    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(404, "job not found")
    if job.status != "uploaded":
        raise HTTPException(400, f"job is in state {job.status}")
    bg.add_task(_do_transcribe, job)
    return {"status": "started"}


@app.post("/jobs/{job_id}/render")
def start_render(job_id: str, payload: dict, bg: BackgroundTasks) -> dict:
    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(404, "job not found")
    if job.status not in ("transcribed", "rendered", "error"):
        raise HTTPException(400, f"job is in state {job.status}")

    edited = [
        Segment(start=s["start"], end=s["end"], text=s["text"], words=[])
        for s in payload.get("segments", [])
    ]
    clean = bool(payload.get("clean", False))
    cyrillic = bool(payload.get("cyrillic", False))
    style_opts = {
        "font": payload.get("font") or "Arial",
        "highlight_hex": payload.get("highlight_hex") or "#FFEE00",
        "text_hex": payload.get("text_hex") or "#FFFFFF",
        "box_opacity": int(payload.get("box_opacity", 50)),
    }

    # Fresh log + status for this render pass; keep transcript segments.
    job.log = []
    job.status = "transcribed"
    bg.add_task(_do_render, job, edited, clean, cyrillic, style_opts)
    return {"status": "started"}


@app.get("/jobs/{job_id}/events")
async def events(job_id: str) -> StreamingResponse:
    return StreamingResponse(_event_stream(job_id), media_type="text/event-stream")


@app.get("/jobs/{job_id}/download")
def download(job_id: str) -> FileResponse:
    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(404, "job not found")
    out = job.workdir / "subbed.mp4"
    if not out.exists():
        raise HTTPException(404, "not rendered yet")
    stem = Path(job.original_name).stem or "video"
    return FileResponse(out, filename=f"{stem}.subbed.mp4", media_type="video/mp4")


# ---------- event streaming --------------------------------------------------

async def _event_stream(job_id: str):
    job = JOBS.get(job_id)
    if job is None:
        yield _sse({"type": "error", "message": "job not found"})
        return

    last_seg = 0
    last_log = 0
    last_status: str | None = None
    last_progress: tuple[str, int] = ("", -1)

    while True:
        while last_seg < len(job.segments):
            seg = job.segments[last_seg]
            yield _sse({
                "type": "segment",
                "index": last_seg,
                "segment": {
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text,
                },
            })
            last_seg += 1

        while last_log < len(job.log):
            yield _sse({"type": "log", "message": job.log[last_log]})
            last_log += 1

        cur_progress = (job.progress_phase, job.progress_percent)
        if cur_progress != last_progress and job.progress_phase:
            yield _sse({
                "type": "progress",
                "phase": job.progress_phase,
                "percent": job.progress_percent,
            })
            last_progress = cur_progress

        if job.status != last_status:
            yield _sse({
                "type": "status",
                "status": job.status,
                "message": job.message,
            })
            last_status = job.status

        if job.status in ("transcribed", "rendered", "error"):
            return

        await asyncio.sleep(0.25)


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


# ---------- background tasks -------------------------------------------------

def _do_transcribe(job: Job) -> None:
    try:
        job.status = "transcribing"
        job.progress_phase = "transcribe"
        job.progress_percent = 0

        job.log.append("Extracting audio...")
        wav = job.workdir / "audio.wav"
        extract_audio(job.video, wav)

        job.log.append("Probing video dimensions...")
        job.width, job.height = probe_dimensions(job.video)
        job.duration_s = probe_duration(job.video)
        job.log.append(
            f"Video is {job.width}x{job.height}, "
            f"{int(job.duration_s // 60)}m{int(job.duration_s % 60):02d}s long."
        )

        job.log.append("Transcribing (Whisper-medium, int8 on CPU). This is the slow part.")

        def on_segment(s: Segment) -> None:
            job.segments.append(s)
            if job.duration_s > 0:
                pct = int(s.end / job.duration_s * 100)
                job.progress_percent = max(0, min(99, pct))

        transcribe(wav, on_segment=on_segment, progress=False)

        write_srt(job.segments, job.workdir / "transcript.srt")
        write_words_json(job.segments, job.workdir / "words.json")

        job.progress_percent = 100
        job.log.append(f"Done — {len(job.segments)} segments.")
        job.status = "transcribed"
    except Exception as e:
        job.message = str(e)
        job.log.append(f"ERROR: {e}")
        job.status = "error"


def _do_render(
    job: Job,
    edited: list[Segment],
    clean: bool,
    cyrillic: bool,
    style_opts: dict,
) -> None:
    try:
        job.status = "rendering"

        job.log.append("Reattaching word timings to edited text...")
        merged = realign(edited, job.segments)

        if clean:
            from .cleanup import strip_fillers
            merged = strip_fillers(merged)
            job.log.append("Stripped filler words.")

        if cyrillic:
            from .translit import latin_to_cyrillic_segments
            merged = latin_to_cyrillic_segments(merged)
            job.log.append("Transliterated to Cyrillic.")

        style = Style.for_video(job.width, job.height, **style_opts)
        ass_path = job.workdir / "subs.ass"
        write_ass(merged, ass_path, style)
        job.log.append(
            f"Built ASS — {style.width}x{style.height}, font={style.font!r} "
            f"{style.font_size}px, {style.max_words_per_line} words/line, "
            f"box opacity {style_opts['box_opacity']}%."
        )

        out_path = job.workdir / "subbed.mp4"
        job.log.append("Burning subtitles into video. Roughly as long as the video itself.")
        job.progress_phase = "burn"
        job.progress_percent = 0

        def on_burn_progress(t_seconds: float) -> None:
            if job.duration_s > 0:
                pct = int(t_seconds / job.duration_s * 100)
                job.progress_percent = max(0, min(99, pct))

        burn(job.video, ass_path, out_path, on_progress=on_burn_progress)

        job.progress_percent = 100
        job.log.append("Render complete.")
        job.status = "rendered"
    except Exception as e:
        job.message = str(e)
        job.log.append(f"ERROR: {e}")
        job.status = "error"


# ---------- launcher ---------------------------------------------------------

def main() -> None:
    import uvicorn
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    url = "http://localhost:8765"
    print(f"video-subtitler UI on {url}")
    print("Press Ctrl+C to stop.")
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="warning")


if __name__ == "__main__":
    main()
