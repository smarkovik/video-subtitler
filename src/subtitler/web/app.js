"use strict";

// ---------- helpers ----------------------------------------------------------

const $ = (id) => document.getElementById(id);

function showStage(name) {
  document.querySelectorAll(".stage").forEach(s => s.classList.remove("active"));
  $("stage-" + name).classList.add("active");
}

function fmtTime(s) {
  const m = Math.floor(s / 60);
  const ss = Math.floor(s % 60).toString().padStart(2, "0");
  return `${m}:${ss}`;
}

function appendLog(el, text, cls = "info") {
  const div = document.createElement("div");
  div.className = cls;
  div.textContent = text;
  el.appendChild(div);
  el.scrollTop = el.scrollHeight;
}

function autosize(ta) {
  ta.style.height = "auto";
  ta.style.height = (ta.scrollHeight + 2) + "px";
}

// ---------- state ------------------------------------------------------------

let jobId = null;
const segments = [];   // grows as transcribe events arrive

// ---------- upload + drag-drop ----------------------------------------------

const drop = $("drop");
const fileInput = $("file");

drop.addEventListener("click", () => fileInput.click());
["dragenter", "dragover"].forEach(ev =>
  drop.addEventListener(ev, e => {
    e.preventDefault();
    drop.classList.add("over");
  })
);
["dragleave", "drop"].forEach(ev =>
  drop.addEventListener(ev, e => {
    e.preventDefault();
    drop.classList.remove("over");
  })
);
drop.addEventListener("drop", e => {
  if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener("change", () => {
  if (fileInput.files.length) handleFile(fileInput.files[0]);
});

async function handleFile(file) {
  showStage("transcribe");
  setProgress("bar1", "pct1", 0);
  $("status1").textContent = `Uploading ${file.name} (${(file.size / 1024 / 1024).toFixed(1)} MB)...`;

  const fd = new FormData();
  fd.append("file", file);

  let resp;
  try {
    resp = await fetch("/upload", { method: "POST", body: fd });
  } catch (err) {
    return showError(`Upload failed: ${err.message}`);
  }
  if (!resp.ok) return showError(`Upload failed: HTTP ${resp.status}`);

  const data = await resp.json();
  jobId = data.job_id;
  $("status1").textContent = `Transcribing — ${file.name}`;

  await fetch(`/jobs/${jobId}/transcribe`, { method: "POST" });
  streamEvents(jobId, onTranscribeMsg, $("log1"));
}

// ---------- SSE --------------------------------------------------------------

function streamEvents(id, handler, logEl) {
  const es = new EventSource(`/jobs/${id}/events`);
  es.onmessage = (e) => {
    let msg;
    try { msg = JSON.parse(e.data); } catch { return; }
    handler(msg, es, logEl);
  };
  es.onerror = () => es.close();
  return es;
}

// ---------- transcribe phase -------------------------------------------------

function setProgress(barId, pctId, percent) {
  $(barId).style.width = percent + "%";
  $(pctId).textContent = percent + "%";
}

function onTranscribeMsg(msg, es, logEl) {
  if (msg.type === "segment") {
    segments[msg.index] = msg.segment;
    const line = document.createElement("div");
    line.className = "seg-line";
    line.innerHTML = `<span class="ts">[${fmtTime(msg.segment.start)}]</span> ` +
                     escapeHtml(msg.segment.text);
    logEl.appendChild(line);
    logEl.scrollTop = logEl.scrollHeight;
  } else if (msg.type === "log") {
    appendLog(logEl, msg.message, "info");
  } else if (msg.type === "progress" && msg.phase === "transcribe") {
    setProgress("bar1", "pct1", msg.percent);
  } else if (msg.type === "status") {
    if (msg.status === "transcribed") {
      setProgress("bar1", "pct1", 100);
      es.close();
      showEditor();
    } else if (msg.status === "error") {
      es.close();
      showError(msg.message || "transcription failed");
    }
  }
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

// ---------- editor -----------------------------------------------------------

function showEditor() {
  const segsEl = $("segments");
  segsEl.innerHTML = "";

  segments.forEach((seg, idx) => {
    const row = document.createElement("div");
    row.className = "seg";

    const ts = document.createElement("div");
    ts.className = "ts";
    ts.textContent = `${fmtTime(seg.start)}–${fmtTime(seg.end)}`;

    const ta = document.createElement("textarea");
    ta.value = seg.text;
    ta.dataset.idx = idx;
    ta.rows = 1;
    ta.spellcheck = false;
    ta.addEventListener("input", () => autosize(ta));

    row.appendChild(ts);
    row.appendChild(ta);
    segsEl.appendChild(row);
  });

  showStage("edit");
  // Autosize after layout settles, and pull preview into sync.
  requestAnimationFrame(() => {
    document.querySelectorAll("#segments textarea").forEach(autosize);
    syncPreview();
  });
}

// ---------- render phase -----------------------------------------------------

// ---------- live style preview -----------------------------------------------

function syncPreview() {
  const font = $("opt-font").value;
  const hi = $("opt-highlight").value;
  const tx = $("opt-text").value;
  const op = parseInt($("opt-opacity").value, 10);
  const pos = $("opt-position").value;
  const fullStrip = $("opt-fullstrip").checked;
  const radius = parseInt($("opt-radius").value, 10);

  $("opt-highlight-hex").textContent = hi.toUpperCase();
  $("opt-text-hex").textContent = tx.toUpperCase();
  $("opt-opacity-label").textContent = op;
  $("opt-radius-label").textContent = radius;

  // Radius only matters in full-strip mode.
  $("field-radius").classList.toggle("disabled", !fullStrip);

  // Position → vertical alignment of preview content.
  const preview = $("preview");
  preview.style.alignItems =
    pos === "top" ? "flex-start" :
    pos === "middle" ? "center" :
    "flex-end";

  // Strip vs word-boxes.
  const inner = $("preview-inner");
  inner.classList.toggle("strip", fullStrip);
  if (fullStrip) {
    inner.style.background = `rgba(0, 0, 0, ${op / 100})`;
    inner.style.borderRadius = radius + "px";
  } else {
    inner.style.background = "transparent";
    inner.style.borderRadius = "0";
  }

  document.querySelectorAll("#preview .pw").forEach(el => {
    el.style.fontFamily = `${font}, sans-serif`;
    el.style.color = el.classList.contains("active") ? hi : tx;
    el.style.background = fullStrip ? "transparent" : `rgba(0, 0, 0, ${op / 100})`;
  });
}

[
  "opt-font", "opt-highlight", "opt-text", "opt-opacity",
  "opt-position", "opt-fullstrip", "opt-radius",
].forEach(id => $(id).addEventListener("input", syncPreview));
$("opt-fullstrip").addEventListener("change", syncPreview);

$("btn-render").addEventListener("click", startRender);
$("btn-rerender").addEventListener("click", () => showStage("edit"));

async function startRender() {
  const tas = document.querySelectorAll("#segments textarea");
  const edited = Array.from(tas).map((ta, i) => ({
    start: segments[i].start,
    end: segments[i].end,
    text: ta.value.trim(),
  }));

  const payload = {
    segments: edited,
    clean: $("opt-clean").checked,
    cyrillic: false,
    font: $("opt-font").value,
    highlight_hex: $("opt-highlight").value,
    text_hex: $("opt-text").value,
    box_opacity: parseInt($("opt-opacity").value, 10),
    position: $("opt-position").value,
    full_strip: $("opt-fullstrip").checked,
    radius: parseInt($("opt-radius").value, 10),
  };

  showStage("render");
  $("status2").textContent = "Rendering...";
  $("log2").innerHTML = "";
  setProgress("bar2", "pct2", 0);

  await fetch(`/jobs/${jobId}/render`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  streamEvents(jobId, onRenderMsg, $("log2"));
}

function onRenderMsg(msg, es, logEl) {
  if (msg.type === "log") {
    appendLog(logEl, msg.message, "info");
  } else if (msg.type === "progress" && msg.phase === "burn") {
    setProgress("bar2", "pct2", msg.percent);
  } else if (msg.type === "status") {
    if (msg.status === "rendered") {
      setProgress("bar2", "pct2", 100);
      es.close();
      $("download").href = `/jobs/${jobId}/download`;
      showStage("done");
    } else if (msg.status === "error") {
      es.close();
      showError(msg.message || "render failed");
    }
  }
}

// ---------- error / restart --------------------------------------------------

function showError(text) {
  $("log-err").textContent = text;
  showStage("error");
}

function restart() {
  jobId = null;
  segments.length = 0;
  fileInput.value = "";
  $("log1").innerHTML = "";
  $("log2").innerHTML = "";
  $("log-err").textContent = "";
  showStage("upload");
}

["btn-restart", "btn-restart-2", "btn-restart-3"].forEach(id =>
  $(id).addEventListener("click", restart)
);
