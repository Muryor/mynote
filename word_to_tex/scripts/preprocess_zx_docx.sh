#!/usr/bin/env bash
# preprocess_zx_docx.sh - 智学网/菁优网格式 Word → examx LaTeX 转换
#
# 智学网格式特点：
# - 答案带斜体标记：【答案】*B*
# - 解析分为【解析】【分析】和【解答】两部分
# - 【分析】包含考点说明（丢弃）
# - 【解答】包含实际解题过程（保留为详解）
# - 无【难度】和【知识点】标记
#
# Usage: ./preprocess_zx_docx.sh input.docx output_name [title]
#
# Steps:
# 1. Convert docx to markdown with pandoc
# 2. 智学网格式预处理（答案斜体移除、解析结构转换）
# 3. Run ocr_to_examx converter
# 4. Run agent_refine to create TikZ placeholders
# 5. 复制图片到试卷目录
# 6. Validate output

set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 input.docx output_name [title]"
  echo "Example: $0 shenzhen.docx shenzhen_2025 '深圳中学高三开学试卷'"
  echo ""
  echo "智学网格式特点："
  echo "  - 答案带斜体：【答案】*B* → 【答案】B"
  echo "  - 解析结构：【解析】【分析】+【解答】 → 【详解】"
  echo "  - 无难度/知识点标记"
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
echo "📝 智学网格式 Word → Examx 转换流程"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📄 输入文件: $INPUT_DOCX"
echo "📁 输出名称: $OUTPUT_NAME"
echo "📋 试卷标题: $TITLE"
echo ""

# Step 1: Convert docx to markdown
echo "步骤 1/6: Pandoc 转换 docx → markdown"
RAW_MD="$OUTPUT_DIR/${OUTPUT_NAME}_raw.md"
FIGURES_DIR="$OUTPUT_DIR/figures/${OUTPUT_NAME}"
pandoc "$INPUT_DOCX" -o "$RAW_MD" --extract-media="$FIGURES_DIR"
echo "✅ 生成: $RAW_MD"
echo "✅ 图片提取到: $FIGURES_DIR/media/"

# Step 2: 智学网格式预处理
echo "步骤 2/6: 智学网格式预处理（答案斜体移除、解析结构转换）"
PREPROCESSED_MD="$OUTPUT_DIR/${OUTPUT_NAME}_preprocessed.md"
python3 "$TOOLS_DIR/utils/preprocess_shenzhen_format.py" "$RAW_MD" "$PREPROCESSED_MD"
echo "✅ 生成: $PREPROCESSED_MD"

# Step 3: Run ocr_to_examx converter
echo "步骤 3/6: 转换为 examx 格式"
EXAMX_TEX="$OUTPUT_DIR/${OUTPUT_NAME}_examx.tex"
python3 "$TOOLS_DIR/core/ocr_to_examx.py" \
  "$PREPROCESSED_MD" \
  "$EXAMX_TEX" \
  --title "$TITLE" \
  --figures-dir "$FIGURES_DIR"
echo "✅ 生成: $EXAMX_TEX"

# Step 4: Run agent_refine
echo "步骤 4/6: Agent 精修（TikZ 占位符处理）"
AUTO_DIR="$ROOT_DIR/content/exams/auto/$OUTPUT_NAME"
REFINED_TEX="$AUTO_DIR/converted_exam.tex"
python3 "$TOOLS_DIR/core/agent_refine.py" "$EXAMX_TEX" "$REFINED_TEX" --create-tikz
echo "✅ 生成: $REFINED_TEX"

# Step 5: 复制图片到试卷目录
echo "步骤 5/6: 复制图片到试卷目录"
IMAGES_DIR="$AUTO_DIR/images/media"
mkdir -p "$IMAGES_DIR"
if [ -d "$FIGURES_DIR/media" ]; then
  IMAGE_COUNT=$(find "$FIGURES_DIR/media" -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" -o -name "*.gif" \) 2>/dev/null | wc -l | tr -d ' ')
  if [ "$IMAGE_COUNT" -gt 0 ]; then
    cp "$FIGURES_DIR/media/"*.{png,jpg,jpeg,gif} "$IMAGES_DIR/" 2>/dev/null || true
    echo "✅ 复制了 $IMAGE_COUNT 个图片到 $IMAGES_DIR"
  else
    echo "ℹ️  未找到需要复制的图片"
  fi
else
  echo "ℹ️  图片目录不存在: $FIGURES_DIR/media"
fi

# Step 6: Validation
echo "步骤 6/6: 验证输出"
QUESTION_COUNT=$(grep -c '\\begin{question}' "$REFINED_TEX" || echo "0")
TIKZ_COUNT=$(find "$AUTO_DIR/figures/tikz" -name "*.tikz" 2>/dev/null | wc -l | tr -d ' ')
IMAGE_COUNT_FINAL=$(find "$IMAGES_DIR" -type f \( -name "*.png" -o -name "*.jpg" \) 2>/dev/null | wc -l | tr -d ' ')
ANSWER_COUNT=$(grep -c '\\answer{' "$REFINED_TEX" || echo "0")
EXPLAIN_COUNT=$(grep -c '\\explain{' "$REFINED_TEX" || echo "0")

echo "  📋 题目数量: $QUESTION_COUNT"
echo "  📝 答案数量: $ANSWER_COUNT"
echo "  💡 详解数量: $EXPLAIN_COUNT"
echo "  🖼️  TikZ 文件: $TIKZ_COUNT"
echo "  📷 图片文件: $IMAGE_COUNT_FINAL"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 智学网格式转换完成！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📁 输出文件:"
echo "   Raw MD:     $RAW_MD"
echo "   Processed:  $PREPROCESSED_MD"
echo "   Raw TeX:    $EXAMX_TEX"
echo "   Refined:    $REFINED_TEX"
echo "   图片目录:   $IMAGES_DIR"
echo ""
echo "💡 下一步:"
echo "   1. 处理图片: python3 tools/images/process_images_to_tikz.py --mode include --files $REFINED_TEX"
echo "   2. 转换图片宏: python3 tools/images/convert_to_examimage.py $REFINED_TEX"
echo "   3. 修改 settings/metadata.tex:"
echo "      \\newcommand{\\examSourceFile}{content/exams/auto/${OUTPUT_NAME}/converted_exam.tex}"
echo "   4. 编译测试: ./build.sh exam both"
echo ""
echo "📊 智学网格式处理说明："
echo "   • 答案斜体已自动移除：【答案】*B* → 【答案】B"
echo "   • 解析结构已转换：【解析】【分析】+【解答】 → 【详解】"
echo "   • 考点说明已丢弃（【分析】内容）"
echo "   • 解答题答案字段为空，详解包含完整解答过程"
echo ""
