#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: ./build.sh {exam|handout} {teacher|student|both}
All PDFs will be placed in ./output
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
OUT="${ROOT}/output"
mkdir -p "${OUT}"

compile() {
  local role="$1"   # teacher | student
  local wrap="${OUT}/wrap-${TYPE}-${role}.tex"
  printf "%% auto wrapper\n"           >  "${wrap}"
  if [[ "$role" == "teacher" ]]; then
    printf "\\PassOptionsToPackage{teacher}{styles/examx}\n" >> "${wrap}"
  else
    printf "\\PassOptionsToPackage{student}{styles/examx}\n" >> "${wrap}"
  fi
  printf "\\input{%s}\n" "${MAIN}"     >> "${wrap}"
  latexmk -xelatex -interaction=nonstopmode -file-line-error -outdir="${OUT}" "${wrap}"
}

case "${MODE}" in
  teacher) compile teacher ;;
  student) compile student ;;
  both)    compile teacher; compile student ;;
  *) usage ;;
esac
echo "✅ Done. PDFs in ./output"
