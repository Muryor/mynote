#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 _fix_array_left_braces 函数

验证方程组 array/cases 环境的 \\left\\{ 自动补全功能
"""

import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

from core.ocr_to_examx import _fix_array_left_braces, _sanitize_math_block


def test_fix_array_left_braces():
    """测试 array/cases 左大括号补全"""
    
    print("=" * 80)
    print("测试 _fix_array_left_braces")
    print("=" * 80)
    
    # 测试用例 1：应该被补全的例子（缺少 \\left\\{）
    test_cases_should_fix = [
        # 简单 array 环境
        (
            r"方程组 \begin{array}{l} x + y = 1 \\ x - y = 0 \end{array}\right.",
            r"方程组 \left\{\begin{array}{l} x + y = 1 \\ x - y = 0 \end{array}\right."
        ),
        # cases 环境
        (
            r"f(x) = \begin{cases} x, & x > 0 \\ -x, & x < 0 \end{cases}\right.",
            r"f(x) = \left\{\begin{cases} x, & x > 0 \\ -x, & x < 0 \end{cases}\right."
        ),
        # 多个方程
        (
            r"\begin{array}{c} a + b = 5 \\ a - b = 1 \end{array}\right. 则 a = 3",
            r"\left\{\begin{array}{c} a + b = 5 \\ a - b = 1 \end{array}\right. 则 a = 3"
        ),
    ]
    
    print("\n应该被补全的例子：")
    for i, (input_text, expected) in enumerate(test_cases_should_fix, 1):
        result = _fix_array_left_braces(input_text)
        status = "✅" if result == expected else "❌"
        print(f"{status} 测试 {i}:")
        print(f"  输入: {input_text[:80]}...")
        print(f"  期望: {expected[:80]}...")
        print(f"  结果: {result[:80]}...")
        if result != expected:
            print(f"  错误: 不匹配！")
            print(f"  完整输入: {input_text}")
            print(f"  完整期望: {expected}")
            print(f"  完整结果: {result}")
        print()
    
    # 测试用例 2：不应该被修改的例子
    test_cases_should_not_fix = [
        # 已经有 \\left\\{
        r"\left\{\begin{array}{l} x + y = 1 \\ x - y = 0 \end{array}\right.",
        # 没有 \\right.
        r"\begin{array}{l} x + y = 1 \\ x - y = 0 \end{array}",
        # 没有 array 或 cases
        r"普通数学公式 x + y = 1 \right.",
        # left 和 right 数量相等
        r"\left(\begin{matrix} a & b \\ c & d \end{matrix}\right)",
        # 上下文中已有 \\{
        r"系统 \{ \begin{array}{l} x = 1 \\ y = 2 \end{array}\right.",
    ]
    
    print("\n不应该被修改的例子（保持原样）：")
    for i, input_text in enumerate(test_cases_should_not_fix, 1):
        result = _fix_array_left_braces(input_text)
        status = "✅" if result == input_text else "❌"
        print(f"{status} 测试 {i}:")
        print(f"  输入: {input_text[:80]}...")
        print(f"  结果: {result[:80]}...")
        if result != input_text:
            print(f"  错误: 不应该被修改！")
            print(f"  完整输入: {input_text}")
            print(f"  完整结果: {result}")
        print()
    
    # 测试用例 3：边界情况
    edge_cases = [
        ("", ""),  # 空字符串
        ("普通文本", "普通文本"),  # 无数学内容
        (r"\begin{array}{l} x \end{array}", r"\begin{array}{l} x \end{array}"),  # 无 \\right.
    ]
    
    print("\n边界情况：")
    for i, (input_text, expected) in enumerate(edge_cases, 1):
        result = _fix_array_left_braces(input_text)
        status = "✅" if result == expected else "❌"
        print(f"{status} 测试 {i}:")
        print(f"  输入: '{input_text}'")
        print(f"  结果: '{result}'")
        if result != expected:
            print(f"  错误: 不匹配！")
        print()


def test_with_sanitize_math_block():
    """测试与 _sanitize_math_block 的集成"""
    
    print("=" * 80)
    print("测试与 _sanitize_math_block 集成")
    print("=" * 80)
    
    # 测试：缺少 \\left\\{ 的方程组经过完整清洗流程后应该被补全
    test_case = r"方程组 \begin{array}{l} x + y = 1 \\ x - y = 0 \end{array}\right. 的解为"
    
    print(f"\n输入: {test_case}")
    result = _sanitize_math_block(test_case)
    print(f"输出: {result}")
    
    # 检查是否包含 \\left\\{
    if r'\left\{' in result:
        print("✅ 成功补全 \\left\\{")
    else:
        print("❌ 未能补全 \\left\\{")
    
    # 检查 left/right 是否平衡（不应该被降级）
    if r'\left' in result and r'\right' in result:
        print("✅ left/right 保留（未被降级）")
    elif r'\left' not in result and r'\right' not in result:
        print("⚠️  left/right 被降级（可能是其他问题）")
    
    print()


def test_with_real_files():
    """用实际文件测试（如果可用）"""
    
    print("=" * 80)
    print("测试实际文件")
    print("=" * 80)
    
    output_dir = Path("word_to_tex/output")
    if not output_dir.exists():
        print("\n⚠️  word_to_tex/output 目录不存在，跳过实际文件测试")
        return
    
    tex_files = list(output_dir.glob("*_examx.tex"))
    if not tex_files:
        print("\n⚠️  未找到 *_examx.tex 文件，跳过实际文件测试")
        return
    
    print(f"\n找到 {len(tex_files)} 个文件，测试前 2 个：")
    
    for tex_file in tex_files[:2]:
        print(f"\n处理: {tex_file.name}")
        
        try:
            content = tex_file.read_text(encoding='utf-8')
            
            # 统计 array/cases 环境
            import re
            array_count = len(re.findall(r'\\begin\{array\}', content))
            cases_count = len(re.findall(r'\\begin\{cases\}', content))
            right_dot_count = len(re.findall(r'\\right\.', content))
            
            print(f"  统计：")
            print(f"    \\begin{{array}}: {array_count}")
            print(f"    \\begin{{cases}}: {cases_count}")
            print(f"    \\right.: {right_dot_count}")
            
            # 查找可能需要补全的模式
            # 查找 \\begin{array} 或 \\begin{cases} 前 50 个字符内没有 \\left 的情况
            pattern = re.compile(r'(.{0,50})\\begin\{(?:array|cases)\}')
            matches = pattern.findall(content)
            
            needs_fix = 0
            for prefix in matches:
                if r'\left' not in prefix and r'\{' not in prefix:
                    needs_fix += 1
            
            print(f"  可能需要补 \\left\\{{ 的环境: {needs_fix}")
            
        except Exception as e:
            print(f"  ❌ 处理失败: {e}")


if __name__ == "__main__":
    test_fix_array_left_braces()
    print("\n" + "=" * 80)
    test_with_sanitize_math_block()
    print("\n" + "=" * 80)
    test_with_real_files()
    print("\n" + "=" * 80)
    print("测试完成！")
