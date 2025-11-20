#!/usr/bin/env bash
set -euo pipefail


usage() {
  cat <<'USAGE'
Usage: ./build.sh {exam|handout} {teacher|student|both}
       ./build.sh clean
       ./build.sh test-batch [docx...]
All PDFs will be placed in ./output
USAGE
  exit 1
}


if [[ "${1:-}" == "clean" ]]; then
  ROOT="$(cd "$(dirname "$0")" && pwd)"
  OUT="${ROOT}/output"
  echo "Cleaning intermediate files in $OUT ..."
  # Remove all non-pdf, non-synctex.gz files in output/
  find "$OUT" -type f ! \( -name '*.pdf' -o -name '*.synctex.gz' \) -delete
  # Remove .aux subdir contents but keep the dir
  [[ -d "$OUT/.aux" ]] && rm -rf "$OUT/.aux"/* 2>/dev/null || true
  echo "✅ Clean complete."
  exit 0
fi

# Run batch tests with timeouts and logging
if [[ "${1:-}" == "test-batch" ]]; then
  ROOT="$(cd "$(dirname "$0")" && pwd)"
  shift 1
  # Pass remaining args (docx paths) through to the runner
  python3 "${ROOT}/tools/testing/run_batch_tests.py" "$@"
  exit $?
fi

TYPE="${1:-}"; MODE="${2:-}"
[[ -z "${TYPE}" || -z "${MODE}" ]] && usage

case "${TYPE}" in
  exam)    MAIN="main-exam.tex" ;;
  handout) MAIN="main-handout.tex" ;;
  *) usage ;;
esac

ROOT="$(cd "$(dirname "$0")" && pwd)"
OUT="${ROOT}/output"
SKIP_ERROR_CLEANUP="${SKIP_ERROR_CLEANUP:-}"  # If set (non-empty), retain .aux artifacts on error for forensic analysis.

# Ensure output directories exist
ensure_dirs() {
  mkdir -p "${OUT}" "${OUT}/.aux"
}

ensure_dirs

# ---------------------------------------------------------------
# Error pattern definitions (fatal vs undefined reference warnings)
# ---------------------------------------------------------------
# fatal_pattern: real TeX fatal errors that require user intervention.
# Matches:
#   - Line starting with '!'
#   - Runaway argument issues
#   - Environment/file premature end while scanning
#   - Undefined control sequence
#   - Generic Fatal error markers
#
# undefref_pattern: only undefined reference warnings (non‑fatal, safe to retry with -f)
#   - LaTeX Warning: Reference `...` on page ... undefined
#   - LaTeX Warning: There were undefined references.
# ---------------------------------------------------------------
fatal_pattern='^! |Runaway argument|File ended while scanning use of|Undefined control sequence|Fatal error'
undefref_pattern='LaTeX Warning: Reference `.*` on page .* undefined|LaTeX Warning: There were undefined references\.'

extract_errors() {
  local logfile="$1"
  local role="${2:-unknown}"
  local error_log="${OUT}/last_error.log"

  # Always truncate/create fresh error log to avoid stale content.
  : > "$error_log"

  if [[ ! -f "$logfile" ]]; then
    {
      echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      echo "编译错误摘要 ($(date '+%Y-%m-%d %H:%M:%S'))"
      echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      echo ""
      echo "Type: ${TYPE}" 
      echo "Role: ${role}" 
      echo "Log: ${logfile}" 
      echo "Generated: $(date '+%Y-%m-%d %H:%M:%S')" 
      echo ""
      echo "Log file missing; no details available."
    } >> "$error_log"
    echo "⚠️  日志文件不存在: $logfile"
    echo "💾 完整错误日志已保存到: $error_log"
    return 1
  fi

  {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "编译错误摘要 ($(date '+%Y-%m-%d %H:%M:%S'))"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Type: ${TYPE}" 
    echo "Role: ${role}" 
    echo "Log: ${logfile}" 
    echo "Generated: $(date '+%Y-%m-%d %H:%M:%S')" 
    echo ""
  } >> "$error_log"

  # Classification summary
  if grep -Eq "$fatal_pattern" "$logfile" 2>/dev/null; then
    echo "Detected fatal TeX error pattern(s) matching: $fatal_pattern" >> "$error_log"
    echo "" >> "$error_log"
  elif grep -Eq "$undefref_pattern" "$logfile" 2>/dev/null; then
    echo "Only undefined reference warnings detected (will allow forced recompile)." >> "$error_log"
    echo "" >> "$error_log"
  else
    echo "No explicit fatal TeX error pattern found; inspect tail for context." >> "$error_log"
    echo "" >> "$error_log"
  fi

  # Show first explicit '!' error context if present
  if grep -n -E "^! " "$logfile" >/dev/null 2>&1; then
    echo "--- First TeX error (context) ---" >> "$error_log"
    grep -n -E "^! " "$logfile" | head -1 | cut -d: -f1 | while read -r lineno; do
      local start=$(( lineno > 10 ? lineno - 10 : 1 ))
      sed -n "${start},$((lineno + 10))p" "$logfile" >> "$error_log"
    done
    echo "" >> "$error_log"
  fi

  # Fatal phrase matches (extended list)
  local extra_fatal=("Runaway argument" "File ended while scanning use of" "Missing } inserted" "Extra }, or forgotten \\endgroup" "TeX capacity exceeded" "Emergency stop" "Undefined control sequence" "Fatal error")
  for p in "${extra_fatal[@]}"; do
    if grep -q "$p" "$logfile" 2>/dev/null; then
      echo "--- Fatal pattern: $p ---" >> "$error_log"
      grep -n -C3 "$p" "$logfile" >> "$error_log" || true
      echo "" >> "$error_log"
    fi
  done

  echo "--- Log tail (last 80 lines) ---" >> "$error_log"
  tail -n 80 "$logfile" >> "$error_log" || true

  # 🆕 智能错误分析
  {
    echo "━━━ 智能错误分析 (高频模式) ━━━"
    echo ""

    if grep -q "Runaway argument" "$logfile"; then
      echo "【错误类型】Runaway argument"
      echo "【常见原因】"
      echo "  1. \\explain{...} 中存在空行（连续两个换行会被 TeX 视为 \\par）"
      echo "  2. 某个宏的参数块内花括号 { } 不平衡"
      echo "  3. 数学环境 \\( / \\) 或 \\[ / \\] 未成对出现"
      echo ""
      echo "【建议操作】"
      echo "  • 运行: VALIDATE_BEFORE_BUILD=1 ./build.sh ${TYPE} ${role}"
      echo "    （会调用 tools/validate_tex.py 进行预检查）"
      echo "  • 或单独运行: tools/locate_error.sh ${logfile}"
      echo ""
    fi

    if grep -q "Missing \$inserted" "$logfile"; then
      echo "【错误类型】Missing \$ inserted (数学模式缺失)"
      echo "【建议】检查该行附近是否缺少 \$，或者把数学符号包在$ ... $ 中。"
      echo ""
    fi

    if grep -q "Undefined control sequence" "$logfile"; then
      echo "【错误类型】Undefined control sequence"
      echo "【建议】"
      echo "  • 检查命令是否拼写错误"
      echo "  • 检查是否忘记加载对应宏包（例如 amsmath, tikz 等）"
      echo ""
    fi
  } >> "$error_log"

  # Console summary
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Compilation summary: type=${TYPE} role=${role}"
  if grep -Eq "$fatal_pattern" "$logfile" 2>/dev/null; then
    echo "Main issue: fatal TeX error detected (see ${OUT}/last_error.log)"
  elif grep -Eq "$undefref_pattern" "$logfile" 2>/dev/null; then
    echo "Main issue: undefined references (warnings)"
  else
    echo "Main issue: no fatal error pattern matched; review tail (see ${OUT}/last_error.log)"
  fi
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "💾 完整错误日志已保存到: $error_log"
}

cleanup_on_error() {
  local role="$1"
  echo ""
  echo "🧹 清理编译失败的中间文件..."
  
  # 删除这次编译的所有中间文件
  find "${OUT}" -type f \( \
    -name "wrap-${TYPE}-${role}.*" -o \
    -name "*.aux" -o -name "*.fls" -o \
    -name "*.fdb_latexmk" -o -name "*.xdv" \
  \) -delete 2>/dev/null || true
  
  [[ -d "${OUT}/.aux" ]] && rm -rf "${OUT}/.aux"/* 2>/dev/null || true
  
  echo "✅ 中间文件已清理"
}

compile() {
  local role="$1"   # teacher | student
  local wrap="${OUT}/wrap-${TYPE}-${role}.tex"
  local logfile="${OUT}/.aux/wrap-${TYPE}-${role}.log"
  
  printf "%% auto wrapper\n"           >  "${wrap}"
  if [[ "$role" == "teacher" ]]; then
    printf "\\PassOptionsToPackage{teacher}{styles/examx}\n" >> "${wrap}"
  else
    printf "\\PassOptionsToPackage{student}{styles/examx}\n" >> "${wrap}"
  fi
  printf "\\input{%s}\n" "${MAIN}"     >> "${wrap}"
  
  echo "📝 编译 ${TYPE} (${role} 模式)..."
  
  # ---------- 新增：预编译 LaTeX 语法检查 ----------
  if [[ -n "${VALIDATE_BEFORE_BUILD:-}" ]]; then
    echo "🔍 运行预编译检查 (tools/validate_tex.py)..."
    if command -v python3 &>/dev/null && [[ -f "${ROOT}/tools/validate_tex.py" ]]; then
      # 从 metadata.tex 中提取 \examSourceFile
      local meta_file="${ROOT}/settings/metadata.tex"
      local source_file=""
      if [[ -f "$meta_file" ]]; then
        source_file=$(grep "^\\\\newcommand{\\\\examSourceFile}" "$meta_file" | sed -n 's/.*{\(.*\)}/\1/p' | head -1)
      fi
      if [[ -n "$source_file" && -f "${ROOT}/${source_file}" ]]; then
        # 这里的 source_file 就是 content/exams/auto/.../converted_exam.tex
        if ! python3 "${ROOT}/tools/validate_tex.py" "${ROOT}/${source_file}"; then
          echo "⚠️  预检查发现问题，继续尝试编译，但很可能失败（建议先修复上述错误）"
        fi
      else
        echo "ℹ️  未能从 metadata.tex 中解析 examSourceFile，跳过预检查"
      fi
    else
      echo "ℹ️  未找到 python3 或 tools/validate_tex.py，跳过预检查"
    fi
  fi
  # ---------- 预检查结束 ----------
  
  # 运行 latexmk，捕获返回值
  local ret=0
  latexmk -xelatex -interaction=nonstopmode -file-line-error \
          -outdir="${OUT}/.aux" "${wrap}" > "${OUT}/build.log" 2>&1 || ret=$?
  
  # Enhanced error classification & handling
  if [[ $ret -ne 0 ]] && [[ -f "$logfile" ]]; then
    if grep -Eq "$fatal_pattern" "$logfile" 2>/dev/null; then
      echo ""; echo "❌ 检测到 TeX 致命错误，终止编译（${role} 模式）"; echo ""
      if grep -q "l\.[0-9]" "$logfile" 2>/dev/null; then
        echo "📍 编译中断位置："
        grep "l\.[0-9]" "$logfile" | tail -3
        echo ""
      fi
      extract_errors "$logfile" "$role"
      echo "BUILD_STATUS role=${role} type=${TYPE} status=error"
      if [[ -z "$SKIP_ERROR_CLEANUP" ]]; then
        cleanup_on_error "$role"
      else
        echo "🔍 保留中间文件用于错误分析 (SKIP_ERROR_CLEANUP=1)"
      fi
      return 1
    elif grep -Eq "$undefref_pattern" "$logfile" 2>/dev/null; then
      echo "ℹ️  仅检测到未定义引用相关警告，尝试使用 -f 强制完成编译..."
      local ret2=0
      latexmk -xelatex -f -interaction=nonstopmode -file-line-error \
              -outdir="${OUT}/.aux" "${wrap}" >> "${OUT}/build.log" 2>&1 || ret2=$?
      if [[ $ret2 -ne 0 ]]; then
        echo ""; echo "❌ 强制编译失败 (second pass)"; echo ""
        extract_errors "$logfile" "$role"
        echo "BUILD_STATUS role=${role} type=${TYPE} status=error"
        if [[ -z "$SKIP_ERROR_CLEANUP" ]]; then
          cleanup_on_error "$role"
        else
          echo "🔍 保留中间文件用于错误分析 (SKIP_ERROR_CLEANUP=1)"
        fi
        return 1
      else
        echo "ℹ️  强制编译成功，继续后续处理"
      fi
    else
      echo ""; echo "❌ 编译返回码非 0，未匹配致命错误模式但仍失败（${role} 模式）"; echo ""
      if grep -q "l\.[0-9]" "$logfile" 2>/dev/null; then
        echo "📍 编译中断位置："
        grep "l\.[0-9]" "$logfile" | tail -3
        echo ""
      fi
      extract_errors "$logfile" "$role"
      echo "BUILD_STATUS role=${role} type=${TYPE} status=error"
      if [[ -z "$SKIP_ERROR_CLEANUP" ]]; then
        cleanup_on_error "$role"
      else
        echo "🔍 保留中间文件用于错误分析 (SKIP_ERROR_CLEANUP=1)"
      fi
      return 1
    fi
  fi
  
  # 移动 PDF 到 output 根目录
  local pdf_name="wrap-${TYPE}-${role}.pdf"
  if [[ -f "${OUT}/.aux/${pdf_name}" ]]; then
    mv "${OUT}/.aux/${pdf_name}" "${OUT}/${pdf_name}"
    # 同时移动 synctex.gz 文件（用于 IDE 反向搜索）
    local synctex_name="wrap-${TYPE}-${role}.synctex.gz"
    if [[ -f "${OUT}/.aux/${synctex_name}" ]]; then
      mv "${OUT}/.aux/${synctex_name}" "${OUT}/${synctex_name}"
    fi
    echo "✅ PDF 已生成: ${OUT}/${pdf_name}"
    # Optional: remove stale last_error.log on success
    [[ -f "${OUT}/last_error.log" ]] && rm -f "${OUT}/last_error.log"
    echo "BUILD_STATUS role=${role} type=${TYPE} status=success"
    return 0
  else
    echo "❌ PDF 文件未生成"
    extract_errors "$logfile" "$role"
    echo "BUILD_STATUS role=${role} type=${TYPE} status=error"
    cleanup_on_error "$role"
    return 1
  fi
}

cleanup_artifacts() {
  echo "🧹 清理中间文件..."
  
  # Remove minted directories
  rm -rf _minted-* */_minted-* "${OUT}/_minted-"* 2>/dev/null || true
  
  # Keep only PDFs, synctex.gz, and last_error.log in output root
  find "${OUT}" -maxdepth 1 -type f ! \( \
    -name '*.pdf' -o -name '*.synctex.gz' -o -name 'last_error.log' -o -name 'build.log' \
  \) -delete 2>/dev/null || true
  
  # Clean .aux subdirectory but keep it for next build
  [[ -d "${OUT}/.aux" ]] && rm -rf "${OUT}/.aux"/* 2>/dev/null || true
  
  echo "✅ 清理完成"
}

case "${MODE}" in
  teacher) 
    if ! compile teacher; then
      echo ""
      echo "❌ 编译失败，请查看上面的错误信息"
      exit 1
    fi
    ;;
  student) 
    if ! compile student; then
      echo ""
      echo "❌ 编译失败，请查看上面的错误信息"
      exit 1
    fi
    ;;
  both)    
    if ! compile teacher; then
      echo ""
      echo "❌ teacher 模式编译失败"
      exit 1
    fi
    if ! compile student; then
      echo ""
      echo "❌ student 模式编译失败"
      exit 1
    fi
    ;;
  *) usage ;;
esac

cleanup_artifacts
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 编译成功！PDF 文件在 ./output 目录"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
