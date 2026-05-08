# video-subtitler — three-step offline workflow:
#
#   make setup                          (one time)
#   make model                          (one time, needs internet)
#   make transcribe VIDEO=path/to/v.mov
#       ... edit the generated .srt ...
#   make encode VIDEO=path/to/v.mov
#
# Run "make help" for the full list of targets.

SHELL := /usr/bin/env bash
.DEFAULT_GOAL := help

# --- venv + python ------------------------------------------------------------
PYTHON ?= $(shell command -v python3.13 2>/dev/null || command -v python3.12 2>/dev/null || command -v python3 2>/dev/null)
VENV   := .venv
PY     := $(VENV)/bin/python
PIP    := $(VENV)/bin/pip

export PYTHONPATH := src

# --- ffmpeg auto-detect for macOS --------------------------------------------
# Homebrew's default ffmpeg formula doesn't ship libass, so the `subtitles`
# filter is missing. ffmpeg-full does. If installed, prepend it to PATH so
# users don't have to set it themselves.
UNAME := $(shell uname -s)
ifeq ($(UNAME),Darwin)
  FFMPEG_FULL := /opt/homebrew/opt/ffmpeg-full/bin
  ifneq ($(wildcard $(FFMPEG_FULL)/ffmpeg),)
    export PATH := $(FFMPEG_FULL):$(PATH)
  endif
endif

# --- argument forwarding ------------------------------------------------------
# Optional flags passed through to the CLI, e.g.:
#   make encode VIDEO=v.mov FLAGS="--clean"
FLAGS ?=

.PHONY: help setup check model transcribe encode clean nuke

help:  ## show this help
	@awk 'BEGIN { FS = ":.*## "; printf "\n  Usage: make <target> [VIDEO=path] [FLAGS=...]\n\n  Targets:\n" } \
		/^[a-zA-Z_-]+:.*## / { printf "    %-12s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo

# --- setup --------------------------------------------------------------------

setup: $(VENV)/.installed  ## create venv, install deps, verify ffmpeg

$(VENV)/.installed: requirements.txt
	@test -n "$(PYTHON)" || { echo "error: no python3.x found on PATH"; exit 1; }
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@$(MAKE) --no-print-directory check
	@touch $@

check:  ## verify ffmpeg has libass (the 'subtitles' filter)
	@command -v ffmpeg >/dev/null 2>&1 || { \
		echo "error: ffmpeg not on PATH."; \
		echo "       macOS:   brew install ffmpeg-full"; \
		echo "       Windows: see docs/setup-windows.md"; \
		exit 1; }
	@ffmpeg -filters 2>/dev/null | grep -q ' subtitles ' || { \
		echo "error: ffmpeg lacks the 'subtitles' filter (no libass)."; \
		echo "       macOS: brew install ffmpeg-full"; \
		exit 1; }
	@printf "  ffmpeg ok: %s\n" "$$(command -v ffmpeg)"

# --- model --------------------------------------------------------------------

model: $(VENV)/.installed  ## download whisper-medium weights (one-time, needs internet)
	$(PY) -m subtitler --download-model

# --- pipeline -----------------------------------------------------------------

transcribe: $(VENV)/.installed  ## transcribe VIDEO -> .srt + .words.json (review the .srt next)
	@test -n "$(VIDEO)" || { echo "usage: make transcribe VIDEO=path/to/video.mov"; exit 2; }
	@test -f "$(VIDEO)" || { echo "error: $(VIDEO) not found"; exit 2; }
	$(PY) -m subtitler "$(VIDEO)" $(FLAGS)

encode: $(VENV)/.installed  ## burn edited .srt back into VIDEO -> .subbed.mp4
	@test -n "$(VIDEO)" || { echo "usage: make encode VIDEO=path/to/video.mov"; exit 2; }
	@test -f "$(VIDEO)" || { echo "error: $(VIDEO) not found"; exit 2; }
	$(PY) -m subtitler "$(VIDEO)" --render $(FLAGS)

# --- cleanup ------------------------------------------------------------------

clean:  ## remove generated files for one VIDEO (keeps the source video)
	@test -n "$(VIDEO)" || { echo "usage: make clean VIDEO=path/to/video.mov"; exit 2; }
	@stem="$(VIDEO)"; stem="$${stem%.*}"; \
	rm -fv "$$stem.wav" "$$stem.srt" "$$stem.words.json" "$$stem.ass" "$$stem.subbed.mp4" 2>/dev/null || true; \
	echo "cleaned generated files for $(VIDEO)"

nuke:  ## remove the venv (model cache in ~/.cache/huggingface stays)
	rm -rf $(VENV)
