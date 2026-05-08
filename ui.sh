#!/usr/bin/env bash
# Open the video-subtitler UI in your browser.
#
# Run "make setup" first if you haven't already.

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"

if [ ! -x "$HERE/.venv/bin/python" ]; then
  echo ".venv is missing. Run: make setup"
  exit 1
fi

# macOS: prefer ffmpeg-full when present (the default brew formula
# lacks libass and the burn step would fail).
if [ "$(uname -s)" = "Darwin" ] && [ -d /opt/homebrew/opt/ffmpeg-full/bin ]; then
  export PATH="/opt/homebrew/opt/ffmpeg-full/bin:$PATH"
fi

export PYTHONPATH="$HERE/src"
exec "$HERE/.venv/bin/python" -m subtitler.server
