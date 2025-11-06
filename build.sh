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

# Ensure output directories exist
ensure_dirs() {
  mkdir -p "${OUT}" "${OUT}/.aux"
}

ensure_dirs

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
\
  # Fallback: if XeLaTeX wrote only XDV, convert to PDF
  if ls "${OUT}/"*.xdv >/dev/null 2>&1; then
    for xdv in "${OUT}/"*.xdv; do
      pdf="${xdv%.xdv}.pdf"
      if [[ ! -f "$pdf" ]]; then
        echo "[info] Converting $(basename "$xdv") -> $(basename "$pdf")"
        xdvipdfmx -q -E -o "$pdf" "$xdv" || {
          echo "[warn] xdvipdfmx failed for $xdv"; exit 1; }
      fi
    done
  fi
}

cleanup_artifacts() {
  # Clean with latexmk
  latexmk -C -outdir="${OUT}" 2>/dev/null || true
  
  # Remove minted directories
  rm -rf _minted-* */_minted-* "${OUT}/_minted-"* 2>/dev/null || true
  
  # Remove specific artifact types, keep only PDFs
  find "${OUT}" -type f \( \
    -name '*.aux' -o -name '*.log' -o -name '*.fls' -o \
    -name '*.fdb_latexmk' -o -name '*.out' -o -name '*.toc' -o \
    -name '*.synctex.gz' -o -name '*.run.xml' -o -name '*.bcf' -o \
    -name '*.xdv' -o -name '*.nav' -o -name '*.snm' -o \
    -name 'wrap-*.tex' \
  \) -delete 2>/dev/null || true
  
  # Clean .aux subdirectory but keep the directory itself
  [[ -d "${OUT}/.aux" ]] && rm -rf "${OUT}/.aux"/* 2>/dev/null || true
}

case "${MODE}" in
  teacher) compile teacher ;;
  student) compile student ;;
  both)    compile teacher; compile student ;;
  *) usage ;;
esac

cleanup_artifacts
echo "✅ Done. PDFs in ./output"
