#!/usr/bin/env bash

set -euo pipefail

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
  echo "Usage: $0 OUTPUT_PATH [RESUME_URL]" >&2
  exit 64
fi

output_path="$1"
resume_url="${2:-https://stephens.page/resume/?pdf=1}"

google-chrome \
  --headless \
  --disable-gpu \
  --no-sandbox \
  --no-pdf-header-footer \
  --virtual-time-budget=5000 \
  --run-all-compositor-stages-before-draw \
  --print-to-pdf="$output_path" \
  "$resume_url" >/dev/null 2>&1
