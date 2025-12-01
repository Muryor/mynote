#!/usr/bin/env bash
# Wrapper to build an exam (teacher/student/both) and copy outputs
# to `output/` with names derived from \examxtitle{}. Avoids overwriting
# existing files by appending -1, -2, ... if needed.

set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 path/to/converted_exam.tex {teacher|student|both}" >&2
  exit 1
fi

TEX_PATH="$1"
MODE="$2" # teacher | student | both

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
GET_TITLE="$ROOT_DIR/tools/utils/get_exam_title.py"
BUILD_SH="$ROOT_DIR/build.sh"
OUTPUT_DIR="$ROOT_DIR/output"

if [ ! -f "$TEX_PATH" ]; then
  echo "converted_exam.tex not found: $TEX_PATH" >&2
  exit 2
fi

if [ ! -f "$GET_TITLE" ]; then
  echo "Missing $GET_TITLE. Ensure tools/utils/get_exam_title.py exists." >&2
  exit 2
fi

TITLE="$(python3 "$GET_TITLE" "$TEX_PATH")"
if [ -z "$TITLE" ]; then
  TITLE="$(basename "$TEX_PATH" .tex)"
fi

# macOS ships bash 3.x where associative arrays (-A) are not available.
# Use a simple conditional mapping for compatibility.

map_output_filename() {
  local variant="$1"
  if [ "$variant" = "teacher" ]; then
    printf '%s' "wrap-exam-teacher.pdf"
  else
    printf '%s' "wrap-exam-student.pdf"
  fi
}

copy_named() {
  local variant="$1"
  local fname
  fname=$(map_output_filename "$variant")
  local src="$OUTPUT_DIR/$fname"
  if [ ! -f "$src" ]; then
    echo "Warning: expected build output not found: $src" >&2
    return 1
  fi
  local suffix=""
  if [ "$variant" = "teacher" ]; then suffix="（教师版）"; fi
  if [ "$variant" = "student" ]; then suffix="（学生版）"; fi
  local base="${TITLE}${suffix}.pdf"
  local dest="$OUTPUT_DIR/$base"
  if [ -e "$dest" ]; then
    i=1
    while [ -e "$OUTPUT_DIR/${TITLE}${suffix}-$i.pdf" ]; do
      i=$((i+1))
    done
    dest="$OUTPUT_DIR/${TITLE}${suffix}-$i.pdf"
  fi
  cp -a "$src" "$dest"
  echo "Saved: $dest"
}

run_build() {
  local variant="$1"
  echo "Running build.sh exam $variant..."
  # keep same env; build.sh is expected to write to output/
  # If SKIP_BUILD is set (non-empty), do not invoke build.sh; only perform copy.
  if [[ -n "${SKIP_BUILD-}" ]]; then
    echo "SKIP_BUILD is set; skipping internal build for $variant"
    return 0
  fi
  # Ensure we do NOT re-trigger the EXAM_TEX auto-naming hook in build.sh
  EXAM_TEX= "$BUILD_SH" exam "$variant"
}

case "$MODE" in
  teacher)
    run_build teacher
    copy_named teacher || true
    ;;
  student)
    run_build student
    copy_named student || true
    ;;
  both)
    run_build teacher || true
    copy_named teacher || true
    run_build student || true
    copy_named student || true
    ;;
  *)
    echo "Unknown mode: $MODE" >&2
    exit 3
    ;;
esac
