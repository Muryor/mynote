#!/bin/bash
# -*- coding: utf-8 -*-
# 
# OCR 脚本重构 - 快速验证脚本
# 
# 用途：验证重构环境和依赖，生成初步报告
#

set -e  # 遇到错误立即退出

echo "================================"
echo "OCR 脚本重构 - 环境验证"
echo "================================"
echo ""

# 检查 Python 版本
echo "[1/6] 检查 Python 版本..."
python3 --version
echo "✓ Python 可用"
echo ""

# 检查源文件
echo "[2/6] 检查源文件..."
if [ -f "tools/core/ocr_to_examx.py" ]; then
    lines=$(wc -l < tools/core/ocr_to_examx.py)
    echo "✓ 源文件存在: tools/core/ocr_to_examx.py ($lines 行)"
else
    echo "✗ 错误: 源文件不存在"
    exit 1
fi
echo ""

# 检查输出目录
echo "[3/6] 检查输出目录..."
if [ -d "tools/lib" ]; then
    echo "✓ 输出目录存在: tools/lib/"
    existing=$(ls tools/lib/*.py 2>/dev/null | wc -l)
    echo "  现有模块文件: $existing 个"
else
    echo "! 输出目录不存在，将在提取时创建"
fi
echo ""

# 检查提取脚本
echo "[4/6] 检查提取脚本..."
if [ -f "tools/extract_modules.py" ]; then
    echo "✓ 提取脚本存在: tools/extract_modules.py"
    if [ -x "tools/extract_modules.py" ]; then
        echo "  可执行权限: 是"
    else
        echo "  可执行权限: 否 (将自动添加)"
        chmod +x tools/extract_modules.py
    fi
else
    echo "✗ 错误: 提取脚本不存在"
    exit 1
fi
echo ""

# 分析源文件结构
echo "[5/6] 分析源文件结构..."
echo "  函数数量: $(grep -c '^def ' tools/core/ocr_to_examx.py)"
echo "  类数量: $(grep -c '^class ' tools/core/ocr_to_examx.py)"
echo "  常量数量: $(grep -c '^[A-Z_][A-Z_0-9]*\s*=' tools/core/ocr_to_examx.py)"
echo ""

# 检查文档
echo "[6/6] 检查重构文档..."
docs=("REFACTORING_PLAN.md" "README_REFACTORING.md")
for doc in "${docs[@]}"; do
    if [ -f "tools/$doc" ]; then
        echo "  ✓ $doc"
    else
        echo "  ✗ $doc (缺失)"
    fi
done
echo ""

# 生成摘要
echo "================================"
echo "验证完成！"
echo "================================"
echo ""
echo "下一步操作："
echo ""
echo "1. 阅读重构计划："
echo "   cat tools/REFACTORING_PLAN.md | less"
echo ""
echo "2. 阅读快速指南："
echo "   cat tools/README_REFACTORING.md | less"
echo ""
echo "3. 运行代码提取（预览模式）："
echo "   python3 tools/extract_modules.py --dry-run  # TODO: 添加此选项"
echo ""
echo "4. 运行代码提取（正式提取）："
echo "   python3 tools/extract_modules.py"
echo ""
echo "5. 验证提取结果："
echo "   ls -lh tools/lib/"
echo "   head -50 tools/lib/math_processing.py"
echo ""
echo "6. 运行测试："
echo "   python3 tools/testing/quick_test_changes.py"
echo ""
echo "================================"
echo "准备就绪！ 🚀"
echo "================================"
