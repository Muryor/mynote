#!/usr/bin/env bash
# preprocess_docx.sh - Convert Word docx to examx-ready LaTeX
#
# Usage: ./preprocess_docx.sh input.docx output_name [title]
#
# Steps:
# 1. Convert docx to markdown with pandoc
# 2. Preprocess markdown (add # to section headers)
# 3. Run ocr_to_examx converter
# 4. Run agent_refine to create TikZ placeholders
# 5. Validate output

set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 input.docx output_name [title]"
  echo "Example: $0 exam.docx nanjing_2026 '江苏省南京市试题'"
  exit 1
fi

INPUT_DOCX="$1"
OUTPUT_NAME="$2"
TITLE="${3:-试卷}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
WORD_TO_TEX="$ROOT_DIR/word_to_tex"
OUTPUT_DIR="$WORD_TO_TEX/output"
TOOLS_DIR="$ROOT_DIR/tools"

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 Word → Examx 转换流程"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Step 1: Convert docx to markdown
echo "步骤 1/5: Pandoc 转换 docx → markdown"
RAW_MD="$OUTPUT_DIR/${OUTPUT_NAME}_raw.md"
# 使用文件名作为图片输出目录，避免覆盖
FIGURES_DIR="$OUTPUT_DIR/figures/${OUTPUT_NAME}"
pandoc "$INPUT_DOCX" -o "$RAW_MD" --extract-media="$FIGURES_DIR"
echo "✅ 生成: $RAW_MD"
echo "✅ 图片提取到: $FIGURES_DIR/media/"

# Step 2: Preprocess markdown (add # to section headers, preserve images)
echo "步骤 2/5: 预处理 markdown（Python 安全处理）"
PREPROCESSED_MD="$OUTPUT_DIR/${OUTPUT_NAME}_preprocessed.md"
python3 "$TOOLS_DIR/utils/preprocess_markdown.py" "$RAW_MD" "$PREPROCESSED_MD"
echo "✅ 生成: $PREPROCESSED_MD"

# Step 3: Run ocr_to_examx converter
echo "步骤 3/5: 转换为 examx 格式"
EXAMX_TEX="$OUTPUT_DIR/${OUTPUT_NAME}_examx.tex"
python3 "$TOOLS_DIR/core/ocr_to_examx.py" "$PREPROCESSED_MD" "$EXAMX_TEX" --title "$TITLE"
echo "✅ 生成: $EXAMX_TEX"

# Step 4: Run agent_refine
echo "步骤 4/5: Agent 精修（TikZ 占位符处理）"
AUTO_DIR="$ROOT_DIR/content/exams/auto/$OUTPUT_NAME"
REFINED_TEX="$AUTO_DIR/converted_exam.tex"
python3 "$TOOLS_DIR/core/agent_refine.py" "$EXAMX_TEX" "$REFINED_TEX" --create-tikz
echo "✅ 生成: $REFINED_TEX"

# Step 5: Validation
echo "步骤 5/5: 验证输出"
QUESTION_COUNT=$(grep -c '\\begin{question}' "$REFINED_TEX" || echo "0")
TIKZ_COUNT=$(find "$AUTO_DIR/figures/tikz" -name "*.tikz" 2>/dev/null | wc -l | tr -d ' ')
echo "  📋 题目数量: $QUESTION_COUNT"
echo "  🖼️  TikZ 文件: $TIKZ_COUNT"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 转换完成！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📁 输出文件:"
echo "   Raw TeX:    $EXAMX_TEX"
echo "   Refined:    $REFINED_TEX"
echo ""
echo "💡 下一步:"
echo "   1. 🎉 v1.5 已自动修复数学公式双重包裹和选项格式"
echo "   2. 补充 TikZ 图形代码（在 $AUTO_DIR/figures/tikz/）"
echo "   3. 使用 VS Code Copilot Agent 进行语义精修（中文润色、公式规范化）"
echo "   4. 编译测试: 修改 settings/metadata.tex 指向 $REFINED_TEX"
echo "                然后运行 ./build.sh exam teacher"
echo ""
echo "📊 v1.5 改进："
echo "   • 数学公式自动统一为 \\(...\\) 格式"
echo "   • 单行选项自动展开为 choices 环境"
echo "   • 预期手动修正时间：~15分钟（原 ~2小时）"
echo ""
