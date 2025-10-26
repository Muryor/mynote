#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  ./build.sh {exam|handout} {teacher|student|both}

Notes:
  - Outputs PDFs into ./output
  - Uses latexmk -xelatex (adds -shell-escape automatically if minted is used)
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

LATEXMK_OPTS=(-xelatex -interaction=nonstopmode -file-line-error -quiet ${SHELL_ESCAPE})

build_one() {
  local role="$1"  # teacher | student
  local tmptex
  tmptex="$(mktemp -t mmln.XXXXXX).tex"

  cat > "${tmptex}" <<EOF2
\\PassOptionsToPackage{${role}}{styles/examx}
\\input{${MAIN}}
EOF2

  latexmk "${LATEXMK_OPTS[@]}" -jobname="${TYPE}-${role}" "${tmptex}"

  if [[ -f "${TYPE}-${role}.pdf" ]]; then
    mv -f "${TYPE}-${role}.pdf" "output/${TYPE}-${role}.pdf"
  fi

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
