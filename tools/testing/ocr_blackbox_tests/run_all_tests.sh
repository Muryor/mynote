#!/bin/bash
# 批量运行 OCR 黑箱测试

set -e  # 遇到错误立即退出

echo "🧪 OCR 黑箱测试 - 批量运行"
echo "========================================"

# 配置
INPUT_DIR="word_to_tex/output"
TEST_SCRIPT="tools/testing/ocr_blackbox_tests/run_tests.py"
ANALYZE_SCRIPT="tools/testing/ocr_blackbox_tests/analyze_results.py"
REPORTS_DIR="tools/testing/ocr_blackbox_tests/reports"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 统计变量
total_files=0
passed_files=0
failed_files=0

# 清理旧报告（可选）
# rm -rf "$REPORTS_DIR"/*.json

# 查找所有预处理文件
files=("$INPUT_DIR"/*_preprocessed.md)

if [ ! -e "${files[0]}" ]; then
    echo -e "${RED}❌ 错误: 未找到测试文件${NC}"
    echo "   请确保 $INPUT_DIR 目录下有 *_preprocessed.md 文件"
    exit 1
fi

echo "📂 测试数据目录: $INPUT_DIR"
echo "📝 测试脚本: $TEST_SCRIPT"
echo ""

# 遍历每个文件
for file in "${files[@]}"; do
    if [ ! -f "$file" ]; then
        continue
    fi
    
    total_files=$((total_files + 1))
    filename=$(basename "$file")
    
    echo "----------------------------------------"
    echo "[$total_files] 测试: $filename"
    echo "----------------------------------------"
    
    # 运行测试
    if python3 "$TEST_SCRIPT" "$file" 2>&1 | tail -25; then
        passed_files=$((passed_files + 1))
        echo -e "${GREEN}✅ 通过${NC}"
    else
        failed_files=$((failed_files + 1))
        echo -e "${RED}❌ 失败${NC}"
    fi
    
    echo ""
done

echo "========================================"
echo "📊 测试汇总"
echo "========================================"
echo "总文件数: $total_files"
echo -e "通过: ${GREEN}$passed_files${NC}"
echo -e "失败: ${RED}$failed_files${NC}"
echo ""

# 生成分析报告
echo "📝 生成分析报告..."
if python3 "$ANALYZE_SCRIPT"; then
    echo -e "${GREEN}✅ 报告生成成功${NC}"
    echo ""
    echo "📄 查看报告:"
    echo "   - tools/testing/ocr_blackbox_tests/SUMMARY.md"
    echo "   - tools/testing/ocr_blackbox_tests/ISSUES.md"
else
    echo -e "${RED}❌ 报告生成失败${NC}"
    exit 1
fi

echo ""
echo "========================================"
echo "🎉 测试完成！"
echo "========================================"

# 返回状态码
if [ $failed_files -gt 0 ]; then
    echo -e "${YELLOW}⚠️  存在失败的测试${NC}"
    exit 1
else
    echo -e "${GREEN}✅ 所有测试通过${NC}"
    exit 0
fi
