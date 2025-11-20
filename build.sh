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

# Ensure output directories exist
ensure_dirs() {
  mkdir -p "${OUT}" "${OUT}/.aux"
}

ensure_dirs

extract_errors() {
  local logfile="$1"
  local error_log="${OUT}/last_error.log"
  
  if [[ ! -f "$logfile" ]]; then
    echo "⚠️  日志文件不存在: $logfile"
    return 1
  fi
  
  # 提取错误信息
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" > "$error_log"
  echo "编译错误摘要 ($(date '+%Y-%m-%d %H:%M:%S'))" >> "$error_log"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$error_log"
  echo "" >> "$error_log"
  
  # 提取 LaTeX 错误
  if grep -q "LaTeX Error" "$logfile"; then
    echo "【LaTeX 错误】" >> "$error_log"
    grep -B 2 -A 5 "LaTeX Error" "$logfile" | head -30 >> "$error_log"
    echo "" >> "$error_log"
  fi
  
  # 提取文件错误位置 (! 开头的错误)
  if grep -q "^! " "$logfile"; then
    echo "【语法错误】" >> "$error_log"
    grep -B 1 -A 3 "^! " "$logfile" | head -20 >> "$error_log"
    echo "" >> "$error_log"
  fi
  
  # Runaway argument / environment scanning issues
  if grep -q "Runaway argument" "$logfile"; then
    echo "【Runaway argument】" >> "$error_log"
    grep -B 3 -A 5 "Runaway argument" "$logfile" | tail -40 >> "$error_log"
    echo "" >> "$error_log"
  fi

  if grep -q "File ended while scanning use of" "$logfile"; then
    echo "【环境提前结束扫描】" >> "$error_log"
    grep -B 2 -A 6 "File ended while scanning use of" "$logfile" >> "$error_log"
    echo "" >> "$error_log"
  fi

  if grep -q "Argument of \\environment question  has an extra }" "$logfile"; then
    echo "【question 环境多余的 }】" >> "$error_log"
    grep -B 2 -A 5 "Argument of \\environment question  has an extra }" "$logfile" >> "$error_log"
    echo "" >> "$error_log"
  fi

  # 提取 "Paragraph ended before" 类型的错误（通常是未闭合的花括号）
  if grep -q "Paragraph ended before" "$logfile"; then
    echo "【未闭合的环境/命令】" >> "$error_log"
    grep -B 3 -A 5 "Paragraph ended before" "$logfile" >> "$error_log"
    echo "" >> "$error_log"
  fi
  
  # 🆕 提取编译卡住的位置（最后处理的文件行号）
  if grep -q "l\.[0-9]" "$logfile"; then
    echo "【编译中断位置】" >> "$error_log"
    echo "LaTeX 在以下位置停止处理：" >> "$error_log"
    grep "l\.[0-9]" "$logfile" | tail -5 >> "$error_log"
    echo "" >> "$error_log"
  fi
  
  # 🆕 提取最后读取的内容文件
  if grep -q "converted_exam.tex" "$logfile"; then
    echo "【问题文件】" >> "$error_log"
    grep "converted_exam.tex" "$logfile" | tail -3 >> "$error_log"
    echo "" >> "$error_log"
  fi
  
  # 提取未定义引用
  if grep -q "undefined" "$logfile"; then
    echo "【未定义的引用】" >> "$error_log"
    grep "undefined" "$logfile" | head -10 >> "$error_log"
    echo "" >> "$error_log"
  fi
  
  # 显示错误摘要
  cat "$error_log"
  echo ""
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
  
  # 运行 latexmk，捕获返回值
  local ret=0
  latexmk -xelatex -interaction=nonstopmode -file-line-error \
          -outdir="${OUT}/.aux" "${wrap}" > "${OUT}/build.log" 2>&1 || ret=$?
  
  # 检查是否有真正的错误（不只是警告）
  if [[ $ret -ne 0 ]] && [[ -f "$logfile" ]]; then
    if grep -q "LaTeX Error" "$logfile" || grep -q "^! " "$logfile" || grep -q "Paragraph ended before" "$logfile"; then
      # 真正的错误
      echo ""
      echo "❌ 编译失败！"
      echo ""
      
      # 🆕 尝试定位具体错误位置
      if grep -q "l\.[0-9]" "$logfile"; then
        echo "📍 编译中断位置："
        grep "l\.[0-9]" "$logfile" | tail -3
        echo ""
      fi
      
      # 提示未闭合的环境错误
      if grep -q "Paragraph ended before" "$logfile"; then
        echo "⚠️  检测到未闭合的命令或环境（可能缺少 } 花括号）"
        echo ""
      fi
      
      tail -50 "${OUT}/build.log"
      echo ""
      extract_errors "$logfile"
      cleanup_on_error "$role"
      return 1
    elif grep -q "undefined" "$logfile"; then
      # 只是引用未定义的警告，强制完成编译
      echo "ℹ️  检测到未定义的引用，使用 -f 强制完成编译..."
      latexmk -xelatex -f -interaction=nonstopmode -file-line-error \
              -outdir="${OUT}/.aux" "${wrap}" >> "${OUT}/build.log" 2>&1 || true
    fi
  fi
  
  # 移动 PDF 到 output 根目录
  local pdf_name="wrap-${TYPE}-${role}.pdf"
  if [[ -f "${OUT}/.aux/${pdf_name}" ]]; then
    mv "${OUT}/.aux/${pdf_name}" "${OUT}/${pdf_name}"
    echo "✅ PDF 已生成: ${OUT}/${pdf_name}"
    return 0
  else
    echo "❌ PDF 文件未生成"
    extract_errors "$logfile"
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
