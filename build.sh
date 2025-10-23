#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<USAGE
Usage:
  ./build.sh exam {teacher|student|both}
  ./build.sh handout {teacher|student|both}
  ./build.sh clean
USAGE
}

cmd="${1:-}"
variant="${2:-teacher}"

ensure_output() { mkdir -p output; }

# latex_run() {
#   local job="$1"
#   local input="$2"
#   local pass="$3"  # teacher|student
#   ensure_output
#   xelatex -interaction=nonstopmode -halt-on-error -jobname="${job}" -output-directory=output "\\PassOptionsToPackage{${pass}}{styles/examx}\\input{${input}}"
#   xelatex -interaction=nonstopmode -halt-on-error -jobname="${job}" -output-directory=output "\\PassOptionsToPackage{${pass}}{styles/examx}\\input{${input}}"
# }

latex_run() {
  local job="$1"
  local input="$2"
  local pass="$3"  # teacher|student
  ensure_output
  # 明确 jobname；同时把 exam 与 examx 的变体信号都传进引擎
  xelatex -interaction=nonstopmode -halt-on-error -jobname="${job}" "\\def\\examvariant{${pass}}\\PassOptionsToPackage{${pass}}{styles/examx}\\input{${input}}"
  xelatex -interaction=nonstopmode -halt-on-error -jobname="${job}" "\\def\\examvariant{${pass}}\\PassOptionsToPackage{${pass}}{styles/examx}\\input{${input}}"
}

case "${cmd}" in
  exam)
    case "${variant}" in
      teacher) latex_run "main-exam-teacher"    "main-exam.tex"    "teacher" ;;
      student) latex_run "main-exam-student"    "main-exam.tex"    "student" ;;
      both)    latex_run "main-exam-teacher"    "main-exam.tex"    "teacher" ;
               latex_run "main-exam-student"    "main-exam.tex"    "student" ;;
      *) usage; exit 1 ;;
    esac
    ;;
  handout)
    case "${variant}" in
      teacher) latex_run "main-handout-teacher" "main-handout.tex" "teacher" ;;
      student) latex_run "main-handout-student" "main-handout.tex" "student" ;;
      both)    latex_run "main-handout-teacher" "main-handout.tex" "teacher" ;
               latex_run "main-handout-student" "main-handout.tex" "student" ;;
      *) usage; exit 1 ;;
    esac
    ;;
  clean)
    rm -f output/*.{pdf,log,aux,out,toc,nav,snm,synctex*} 2>/dev/null || true
    find . -type f \( -name "*.aux" -o -name "*.log" -o -name "*.out" -o -name "*.toc" -o -name "*.synctex*" \) -delete
    ;;
  *)
    usage; exit 1 ;;
esac
