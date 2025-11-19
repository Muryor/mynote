#!/usr/bin/env bash
# 集成测试 v1.5 改进

echo "🧪 测试 ocr_to_examx.py v1.5 核心改进"
echo "========================================"
echo ""

# 创建测试输入
TEST_MD="/tmp/test_exam_input.md"
cat > "$TEST_MD" << 'EOF'
# 一、单选题

1．已知$$\text{\mathrm{i}}$$是虚数单位，则复数$$z = \frac{1 + \text{\mathrm{i}}}{\text{\mathrm{i}}}$$的虚部为

> A．$$- 1$$ B．1 C．$$- \text{\mathrm{i}}$$ D．i

【答案】A
【难度】0.7
【知识点】复数的运算
【详解】计算可得结果。故选A。

2．集合$$(A) = \{x | x > 0\}$$，$$(B) = \{x | x^2 \leq 4\}$$，则$$(A \cap B) = $$

> A. $$\{x | 0 < x < 2\}$$ B. $$\{x | 0 < x \leq 2\}$$ C. $$\{x | -2 \leq x < 0\}$$ D. $$\{x | -2 < x < 2\}$$

【答案】B
【难度】0.6
【知识点】集合的运算
【详解】计算交集可得答案。
EOF

echo "✓ 创建测试输入: $TEST_MD"
echo ""

# 运行转换
TEST_OUTPUT="/tmp/test_exam_output.tex"
python3 tools/ocr_to_examx.py "$TEST_MD" "$TEST_OUTPUT" --title "测试试卷" 2>&1 | tail -15

echo ""
echo "========================================"
echo "📊 检查转换结果"
echo "========================================"

# 检查关键改进点
echo ""
echo "1. 检查数学公式格式（应为 \\(...\\)，无双重包裹）:"
if grep -q '\$\$\\(' "$TEST_OUTPUT"; then
    echo "   ❌ 发现双重包裹: \$\$\\(...\\)\$\$"
    grep '\$\$\\(' "$TEST_OUTPUT" | head -3
else
    echo "   ✅ 无双重包裹格式"
fi

if grep -q '\\(' "$TEST_OUTPUT"; then
    COUNT=$(grep -o '\\(' "$TEST_OUTPUT" | wc -l | tr -d ' ')
    echo "   ✅ 找到 $COUNT 个行内公式 \\(...\\)"
fi

echo ""
echo "2. 检查选项格式（应为 choices 环境）:"
if grep -q '\\begin{choices}' "$TEST_OUTPUT"; then
    COUNT=$(grep -c '\\begin{choices}' "$TEST_OUTPUT")
    echo "   ✅ 找到 $COUNT 个 choices 环境"
else
    echo "   ❌ 未找到 choices 环境"
fi

if grep -q '> A\.' "$TEST_OUTPUT"; then
    echo "   ❌ 仍有 quote 块格式选项"
else
    echo "   ✅ 无 quote 块格式选项"
fi

echo ""
echo "3. 检查题目结构:"
Q_COUNT=$(grep -c '\\begin{question}' "$TEST_OUTPUT")
echo "   题目数量: $Q_COUNT"

echo ""
echo "4. 显示前50行输出样本:"
echo "----------------------------------------"
head -50 "$TEST_OUTPUT"
echo "----------------------------------------"

echo ""
echo "✅ 测试完成！"
echo "完整输出文件: $TEST_OUTPUT"
