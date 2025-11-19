#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_v15_fixes.py - 测试 v1.5 核心修复功能

测试内容：
1. 数学公式双重包裹修复
2. 单行选项展开
"""

import sys
from pathlib import Path

# 添加工具路径
sys.path.insert(0, str(Path(__file__).parent))

from ocr_to_examx import smart_inline_math, fix_double_wrapped_math, expand_inline_choices


def test_smart_inline_math():
    """测试数学公式转换"""
    print("=" * 60)
    print("测试 1: smart_inline_math - 数学公式转换")
    print("=" * 60)
    
    test_cases = [
        # (输入, 期望输出, 说明)
        (
            "已知$$\\text{\\mathrm{i}}$$是虚数单位",
            "已知\\(\\text{\\mathrm{i}}\\)是虚数单位",
            "显示公式转行内公式"
        ),
        (
            "集合$$(A) = \\{x\\}$$",
            "集合\\((A) = \\{x\\}\\)",
            "显示公式转行内公式（包含括号）"
        ),
        (
            "已知$x = 1$和$y = 2$",
            "已知\\(x = 1\\)和\\(y = 2\\)",
            "单美元符号转换"
        ),
        (
            "点$(A)$在坐标$(B)!0.5!(C)$",
            "点$(A)$在坐标$(B)!0.5!(C)$",
            "保护TikZ坐标"
        ),
        (
            "已知\\(x^2\\)和$$y^2$$",
            "已知\\(x^2\\)和\\(y^2\\)",
            "保护已有行内公式，转换显示公式"
        ),
    ]
    
    passed = 0
    failed = 0
    
    for i, (input_text, expected, description) in enumerate(test_cases, 1):
        result = smart_inline_math(input_text)
        if result == expected:
            print(f"✅ 测试 {i}: {description}")
            print(f"   输入: {input_text}")
            print(f"   输出: {result}")
            passed += 1
        else:
            print(f"❌ 测试 {i}: {description}")
            print(f"   输入: {input_text}")
            print(f"   期望: {expected}")
            print(f"   实际: {result}")
            failed += 1
        print()
    
    print(f"通过: {passed}/{passed+failed}")
    return failed == 0


def test_fix_double_wrapped_math():
    """测试双重包裹修正"""
    print("=" * 60)
    print("测试 2: fix_double_wrapped_math - 双重包裹清理")
    print("=" * 60)
    
    test_cases = [
        (
            "已知\\(z\\) = 1和\\(w\\) = 2",
            "已知\\(z\\) = 1和\\(w\\) = 2",
            "保持正常的\\(...\\)不变"
        ),
        (
            "集合$\\(A\\) = \\{x\\}$",
            "集合\\(A\\) = \\{x\\}",
            "清理$\\(...)$嵌套"
        ),
        (
            "\\(\\(x^2\\)\\)",
            "\\(x^2\\)",
            "清理三重嵌套"
        ),
        (
            "正常\\(x\\)不变",
            "正常\\(x\\)不变",
            "不影响正常格式"
        ),
    ]
    
    passed = 0
    failed = 0
    
    for i, (input_text, expected, description) in enumerate(test_cases, 1):
        result = fix_double_wrapped_math(input_text)
        if result == expected:
            print(f"✅ 测试 {i}: {description}")
            print(f"   输入: {input_text}")
            print(f"   输出: {result}")
            passed += 1
        else:
            print(f"❌ 测试 {i}: {description}")
            print(f"   输入: {input_text}")
            print(f"   期望: {expected}")
            print(f"   实际: {result}")
            failed += 1
        print()
    
    print(f"通过: {passed}/{passed+failed}")
    return failed == 0


def test_expand_inline_choices():
    """测试单行选项展开"""
    print("=" * 60)
    print("测试 3: expand_inline_choices - 单行选项展开")
    print("=" * 60)
    
    test_cases = [
        (
            "> A．$$- 1$$ B．1 C．$$- \\text{\\mathrm{i}}$$ D．i",
            "A．$$- 1$$\nB．1\nC．$$- \\text{\\mathrm{i}}$$\nD．i",
            "展开单行多选项"
        ),
        (
            "> A. 选项1 B. 选项2 C. 选项3 D. 选项4",
            "A. 选项1\nB. 选项2\nC. 选项3\nD. 选项4",
            "展开英文标点选项"
        ),
        (
            "> A、\\(x^2\\) B、\\(y^2\\) C、\\(z^2\\) D、\\(w^2\\)",
            "A、\\(x^2\\)\nB、\\(y^2\\)\nC、\\(z^2\\)\nD、\\(w^2\\)",
            "展开顿号选项"
        ),
        (
            "> 这是一个单独的引用块",
            "> 这是一个单独的引用块",
            "保持单个引用块不变"
        ),
        (
            "A．普通选项不在引用块",
            "A．普通选项不在引用块",
            "非引用块内容不变"
        ),
    ]
    
    passed = 0
    failed = 0
    
    for i, (input_text, expected, description) in enumerate(test_cases, 1):
        result = expand_inline_choices(input_text)
        if result == expected:
            print(f"✅ 测试 {i}: {description}")
            print(f"   输入: {repr(input_text)}")
            print(f"   输出: {repr(result)}")
            passed += 1
        else:
            print(f"❌ 测试 {i}: {description}")
            print(f"   输入: {repr(input_text)}")
            print(f"   期望: {repr(expected)}")
            print(f"   实际: {repr(result)}")
            failed += 1
        print()
    
    print(f"通过: {passed}/{passed+failed}")
    return failed == 0


def main():
    """运行所有测试"""
    print("🧪 ocr_to_examx.py v1.5 核心修复功能测试")
    print()
    
    results = []
    results.append(("smart_inline_math", test_smart_inline_math()))
    print()
    results.append(("fix_double_wrapped_math", test_fix_double_wrapped_math()))
    print()
    results.append(("expand_inline_choices", test_expand_inline_choices()))
    print()
    
    print("=" * 60)
    print("测试总结")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 所有测试通过！")
        return 0
    else:
        print("⚠️  部分测试失败，请检查")
        return 1


if __name__ == "__main__":
    sys.exit(main())
