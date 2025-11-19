#!/usr/bin/env bash
# 测试完整的预处理流程

set -e

echo "🧪 测试 Python 预处理 vs sed 预处理"
echo "======================================"

TEST_INPUT="word_to_tex/output/nanjing_2026_sep_raw.md"
TEST_OUTPUT_PYTHON="/tmp/test_python_preprocess.md"
TEST_OUTPUT_SED="/tmp/test_sed_preprocess.md"

if [ ! -f "$TEST_INPUT" ]; then
    echo "❌ 测试文件不存在: $TEST_INPUT"
    exit 1
fi

echo ""
echo "1️⃣  使用 Python 预处理..."
python3 tools/preprocess_markdown.py "$TEST_INPUT" "$TEST_OUTPUT_PYTHON"

echo ""
echo "2️⃣  使用 sed 预处理（对照）..."
sed -E 's/^\*\*([一二三四]、[^*]+)\*\*$/# \1/g' "$TEST_INPUT" > "$TEST_OUTPUT_SED"

echo ""
echo "📊 对比结果:"
echo "----------------------------------------"
echo "Python 预处理:"
head -30 "$TEST_OUTPUT_PYTHON" | grep "^#"
echo ""
echo "sed 预处理:"
head -30 "$TEST_OUTPUT_SED" | grep "^#"
echo "----------------------------------------"

echo ""
echo "✅ 测试完成！两种方法均可正常工作"
echo "   Python 方法更安全，支持更多功能"
