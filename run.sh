#!/usr/bin/env bash
# Drag-equivalent for macOS/Linux:
#   ./run.sh path/to/video.mp4
#
# First call: transcribes, writes <name>.srt for review.
# Edit the .srt, then call ./run.sh on the same video to render.

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 path/to/video.{mp4,mov,mkv}"
  exit 1
fi

VIDEO="$1"
STEM="${VIDEO%.*}"
SRT="${STEM}.srt"

HERE="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$HERE/.venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "$HERE/.venv/bin/activate"
fi

if [ -f "$SRT" ]; then
  echo "Found $SRT — running render stage."
  python -m subtitler "$VIDEO" --render --clean
else
  python -m subtitler "$VIDEO"
fi
