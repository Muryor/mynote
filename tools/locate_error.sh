#!/usr/bin/env bash
# 快速从 LaTeX 日志中定位错误到具体行，并给出上下文 & 常见原因提示

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

LOG_FILE="${1:-"${ROOT}/output/.aux/wrap-exam-teacher.log"}"

if [[ ! -f "$LOG_FILE" ]]; then
  echo "❌ Log file not found: $LOG_FILE"
  exit 1
fi

echo "🔍 分析错误日志: $LOG_FILE"
echo ""

# 封装一个小工具函数：从 log 中提取类似 ./path/to/file.tex:123: 的信息
extract_file_and_line() {
  grep -oP '\./[^:]+\.tex:\d+' "$LOG_FILE" | head -1 || true
}

# ---------- Runaway argument ----------
if grep -q "Runaway argument" "$LOG_FILE"; then
  echo "━━━ Runaway argument 错误 ━━━"
  echo "说明：通常是宏参数（比如 \\explain{...}）里出现了空行或括号不配对。"
  echo ""

  FILE_LINE="$(extract_file_and_line)"
  if [[ -n "${FILE_LINE}" ]]; then
    FILE="${FILE_LINE%%:*}"
    LINE="${FILE_LINE##*:}"

    echo "📄 文件: $FILE"
    echo "📍 行号: $LINE"
    echo ""

    TEX_PATH="${ROOT}/${FILE#./}"
    if [[ -f "$TEX_PATH" ]]; then
      echo "━━━ 错误上下文 (±5 行) ━━━"
      start=$(( LINE > 5 ? LINE - 5 : 1 ))
      end=$(( LINE + 5 ))
      nl -ba "$TEX_PATH" | sed -n "${start},${end}p" | sed "s/^ *${LINE}\b/>>> &/"
      echo ""

      # 检查常见原因
      CONTEXT="$(sed -n "${start},${end}p" "$TEX_PATH")"

      if echo "$CONTEXT" | grep -q '\\explain{'; then
        echo "可能原因："
        echo "  • \\explain{...} 中存在空行（段落分隔）"
        echo "  • 或者 \\explain{...} 内部的花括号不平衡"
        echo ""
      fi
    fi
  fi
fi

# ---------- Missing $ inserted ----------
if grep -q "Missing \$inserted" "$LOG_FILE"; then
  echo "━━━ 数学模式错误 (Missing \$ inserted) ━━━"
  grep -B 2 -A 4 "Missing \$inserted" "$LOG_FILE" | head -20
  echo ""
fi

# ---------- Undefined control sequence ----------
if grep -q "Undefined control sequence" "$LOG_FILE"; then
  echo "━━━ 未定义命令 (Undefined control sequence) ━━━"
  grep -A 2 "Undefined control sequence" "$LOG_FILE" | head -20
  echo ""
fi

echo "✅ 分析结束。如需更进一步，请结合 output/last_error.log 一起查看。"
