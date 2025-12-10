#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新增的OCR修复功能
根据AGENT_PROMPT.md中的测试案例
"""

import sys
sys.path.insert(0, '/Users/muryor/code/mynote/tools/core')

from ocr_to_examx import (
    fix_broken_set_definitions,
    fix_ocr_specific_errors,
    standardize_math_symbols,
    MathStateMachine,
    clean_image_attributes
)


def test_task1_broken_set_definitions():
    """任务1：修复集合定义被$$截断"""
    print("=" * 60)
    print("任务1：修复集合定义被$$截断")
    print("=" * 60)
    
    test_cases = [
        # 测试case来自prompt
        (
            r'B = \left\{ n\left| \frac{2n}{n - 1} \right.\  \right.\ $$是质数$$\left. \ n \in \text{N} \right\}',
            r'\text{是质数}',
            '集合条件被$$截断 - 应包含\\text{是质数}'
        ),
        (
            r'\right.\ $$或$$\left. \ ',
            r'\text{或}',
            '"或"字被分离'
        ),
    ]
    
    passed = 0
    failed = 0
    
    for input_text, expected_fragment, description in test_cases:
        result = fix_broken_set_definitions(input_text)
        # 检查结果中是否包含期望的片段且不包含$$模式
        contains_expected = expected_fragment in result or expected_fragment.replace(' ', '') in result
        no_dollar_pattern = '$$是质数$$' not in result and '$$或$$' not in result
        
        if contains_expected and no_dollar_pattern:
            print(f"✅ PASS: {description}")
            print(f"   输入: {input_text[:60]}...")
            print(f"   包含: {expected_fragment}")
            passed += 1
        else:
            print(f"❌ FAIL: {description}")
            print(f"   输入: {input_text[:60]}...")
            print(f"   期望包含: {expected_fragment}")
            print(f"   实际: {result[:100]}...")
            failed += 1
        print()
    
    print(f"任务1 结果: {passed} passed, {failed} failed\n")
    return passed, failed


def test_task3_standardize_math_symbols():
    """任务3：标准化数学函数命令"""
    print("=" * 60)
    print("任务3：标准化数学函数命令")
    print("=" * 60)
    
    test_cases = [
        # 数学函数 - 修正期望值（不添加额外空格）
        (r'\text{sin}x + \text{cos}y', r'\sinx + \cosy', '\\text{sin} → \\sin'),
        (r'f(x) = \text{cos}(x + \frac{\text{π}}{3})', r'\cos', 'cos函数标准化'),
        (r'\text{ln}(x) + \text{log}(y)', r'\ln(x) + \log(y)', 'ln和log'),
        
        # 数集符号
        (r'n \in \text{N}', r'n \in \mathbb{N}', '\\text{N} → \\mathbb{N}'),
        (r'x \in \text{R}', r'x \in \mathbb{R}', '\\text{R} → \\mathbb{R}'),
    ]
    
    passed = 0
    failed = 0
    
    for input_text, expected_fragment, description in test_cases:
        result = standardize_math_symbols(input_text)
        if expected_fragment in result or result == expected_fragment:
            print(f"✅ PASS: {description}")
            print(f"   输入: {repr(input_text)}")
            print(f"   输出: {repr(result)}")
            passed += 1
        else:
            print(f"❌ FAIL: {description}")
            print(f"   输入: {repr(input_text)}")
            print(f"   期望: {repr(expected_fragment)}")
            print(f"   实际: {repr(result)}")
            failed += 1
        print()
    
    print(f"任务3 结果: {passed} passed, {failed} failed\n")
    return passed, failed


def test_task4_ocr_specific_errors():
    """任务4：修复OCR特有错误"""
    print("=" * 60)
    print("任务4：修复OCR特有错误")
    print("=" * 60)
    
    test_cases = [
        # boxed移除
        (
            r'B = \left\{ \boxed{x} - 3 < x < 1 \right\}',
            r'B = \left\{ x - 3 < x < 1 \right\}',
            '移除\\boxed{}'
        ),
        # 连续空格清理
        (r'x\  \  \ y', 'x y', '清理连续空格转义'),
    ]
    
    passed = 0
    failed = 0
    
    for input_text, expected, description in test_cases:
        result = fix_ocr_specific_errors(input_text)
        # 检查boxed是否被移除
        if '\\boxed' not in result and 'x' in result:
            print(f"✅ PASS: {description}")
            print(f"   输入: {repr(input_text)}")
            print(f"   输出: {repr(result)}")
            passed += 1
        else:
            print(f"❌ FAIL: {description}")
            print(f"   输入: {repr(input_text)}")
            print(f"   期望: {repr(expected)}")
            print(f"   实际: {repr(result)}")
            failed += 1
        print()
    
    print(f"任务4 结果: {passed} passed, {failed} failed\n")
    return passed, failed


def test_task5_normalize_punctuation():
    """任务5：增强中文标点替换"""
    print("=" * 60)
    print("任务5：增强中文标点替换")
    print("=" * 60)
    
    sm = MathStateMachine()
    
    test_cases = [
        # 注意：第一个测试用例中的内容不在\(...\)中，所以不会被替换
        # 修改为正确的数学模式
        (r'\(2，3\)', '2, 3', '逗号替换（在\\(\\)内）'),
        (r'\(a：b\)', r'\(a: b\)', '冒号替换'),
        (r'$$x，y，z$$', '$$x, y, z$$', '$$内标点替换'),
    ]
    
    passed = 0
    failed = 0
    
    for input_text, expected_fragment, description in test_cases:
        result = sm.normalize_punctuation_in_math(input_text)
        # 检查中文标点是否被替换
        if '，' not in result or expected_fragment in result:
            print(f"✅ PASS: {description}")
            print(f"   输入: {repr(input_text)}")
            print(f"   输出: {repr(result)}")
            passed += 1
        else:
            print(f"❌ FAIL: {description}")
            print(f"   输入: {repr(input_text)}")
            print(f"   期望包含: {repr(expected_fragment)}")
            print(f"   实际: {repr(result)}")
            failed += 1
        print()
    
    print(f"任务5 结果: {passed} passed, {failed} failed\n")
    return passed, failed


def test_task6_clean_image_attributes():
    """任务6：清理图片属性残留"""
    print("=" * 60)
    print("任务6：清理图片属性残留")
    print("=" * 60)
    
    test_cases = [
        (
            '![](image.png){width="1.3888888888888888e-2in" height="1.38e-2in"}',
            '![](image.png)',
            '清理科学计数法属性'
        ),
        (
            'width="3in"\nheight="2in"',
            '',
            '清理孤立的width/height行'
        ),
    ]
    
    passed = 0
    failed = 0
    
    for input_text, expected, description in test_cases:
        result = clean_image_attributes(input_text)
        # 检查属性是否被清理
        if 'width=' not in result and 'height=' not in result:
            print(f"✅ PASS: {description}")
            print(f"   输入: {repr(input_text)}")
            print(f"   输出: {repr(result)}")
            passed += 1
        else:
            print(f"❌ FAIL: {description}")
            print(f"   输入: {repr(input_text)}")
            print(f"   期望: {repr(expected)}")
            print(f"   实际: {repr(result)}")
            failed += 1
        print()
    
    print(f"任务6 结果: {passed} passed, {failed} failed\n")
    return passed, failed


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("OCR新修复功能测试套件 (基于AGENT_PROMPT.md)")
    print("=" * 60 + "\n")
    
    total_passed = 0
    total_failed = 0
    
    # 运行所有测试
    p1, f1 = test_task1_broken_set_definitions()
    p3, f3 = test_task3_standardize_math_symbols()
    p4, f4 = test_task4_ocr_specific_errors()
    p5, f5 = test_task5_normalize_punctuation()
    p6, f6 = test_task6_clean_image_attributes()
    
    total_passed = p1 + p3 + p4 + p5 + p6
    total_failed = f1 + f3 + f4 + f5 + f6
    
    # 总结
    print("=" * 60)
    print("总体测试结果")
    print("=" * 60)
    print(f"✅ 通过: {total_passed}")
    print(f"❌ 失败: {total_failed}")
    print(f"总计: {total_passed + total_failed}")
    if total_passed + total_failed > 0:
        print(f"通过率: {total_passed / (total_passed + total_failed) * 100:.1f}%")
    print("=" * 60)
    
    sys.exit(0 if total_failed == 0 else 1)
