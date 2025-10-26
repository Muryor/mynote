#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  ./build.sh {exam|handout} {teacher|student|both}

Notes:
  - All PDFs and aux files go to ./output
  - Uses latexmk -xelatex; auto-add -shell-escape when minted is detected
USAGE
  exit 1
}

TYPE="${1:-}"; MODE="${2:-}"
[[ -z "${TYPE}" || -z "${MODE}" ]] && usage

case "${TYPE}" in
  exam)    MAIN="main-exam.tex" ;;
  handout) MAIN="main-handout.tex" ;;
  *) usage ;;
esac

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "${ROOT}"
mkdir -p output

# detect minted usage
if grep -R --include="*.tex" -n "\\usepackage.*{minted}" "${ROOT}" >/dev/null 2>&1; then
  SHELL_ESCAPE="-shell-escape"
else
  SHELL_ESCAPE=""
fi

# put EVERYTHING in ./output
LATEXMK_OPTS=(-xelatex -interaction=nonstopmode -file-line-error -quiet -outdir=output ${SHELL_ESCAPE})

build_one() {
  local role="$1"  # teacher | student
  local tmptex
  tmptex="$(mktemp -t mmln.XXXXXX).tex"

  cat > "${tmptex}" <<EOF2
\\PassOptionsToPackage{${role}}{styles/examx}
\\input{${MAIN}}
EOF2

  latexmk "${LATEXMK_OPTS[@]}" -jobname="${TYPE}-${role}" "${tmptex}"

  # PDF 已经在 ./output 下，无需再移动
  latexmk -c "${tmptex}" >/dev/null 2>&1 || true
  rm -f "${tmptex}"
}

case "${MODE}" in
  teacher) build_one teacher ;;
  student) build_one student ;;
  both)    build_one teacher; build_one student ;;
  *) usage ;;
esac

echo "✅ Done. See ./output"
