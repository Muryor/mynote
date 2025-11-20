#!/usr/bin/env bash
# 编译回归测试：确保 exam/handout + teacher/student 四种组合都能通过

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

FAILED=0

echo "🧪 开始编译回归测试..."
echo ""

# 组合：exam/handout × teacher/student
for TYPE in exam handout; do
  for MODE in teacher student; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "▶ 测试组合: TYPE=${TYPE}, MODE=${MODE}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if SKIP_ERROR_CLEANUP=1 ./build.sh "${TYPE}" "${MODE}" &>/dev/null; then
      echo "✅ ${TYPE} (${MODE}) - PASS"
    else
      echo "❌ ${TYPE} (${MODE}) - FAIL"
      FAILED=$((FAILED + 1))

      if [[ -f output/last_error.log ]]; then
        echo "   错误摘要（last_error.log 前 20 行）："
        echo "--------------------------------------------------"
        head -20 output/last_error.log | sed 's/^/   /'
        echo "--------------------------------------------------"
      fi
    fi
    echo ""
  done
done

if (( FAILED == 0 )); then
  echo "🎉 所有组合均编译通过！"
  exit 0
else
  echo "❌ 共 ${FAILED} 个组合失败，请优先修复上述错误。"
  exit 1
fi
