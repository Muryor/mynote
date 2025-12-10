#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试OCR修复脚本的关键函数
"""

import sys
sys.path.insert(0, '/Users/muryor/code/mynote/tools/core')

from ocr_to_examx import fix_right_boundary_errors, fix_reversed_delimiters

def test_fix_right_boundary_errors():
    """测试任务1：修复 \\right. 边界处理问题"""
    print("=" * 60)
    print("测试任务1：修复 \\right. 边界处理问题")
    print("=" * 60)
    
    test_cases = [
        (r'\right.\ $$', r'\right.\)', '反斜杠+空格+双美元'),
        (r'\right.\\ $$', r'\right.\)', '双反斜杠+双美元'),
        (r'\right.  $$', r'\right.\)', '空格+双美元'),
        (r'\right.$$', r'\right.\)', '直接跟双美元'),
        (r'\right.，则', r'\right.\)，则', '直接跟中文标点'),
        (r'\right.所以', r'\right.\)所以', '直接跟中文文字'),
    ]
    
    passed = 0
    failed = 0
    
    for input_text, expected, description in test_cases:
        result = fix_right_boundary_errors(input_text)
        if result == expected:
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
    
    print(f"任务1 结果: {passed} passed, {failed} failed\n")
    return passed, failed


def test_fix_reversed_delimiters():
    """测试任务4：增强反向定界符修复"""
    print("=" * 60)
    print("测试任务4：增强反向定界符修复")
    print("=" * 60)
    
    test_cases = [
        # 基本测试 - 删除不匹配的 \)
        (r'在\)x^2\(的值', r'在x^2\(的值\)', '删除不匹配的 \\) 并补充 \\)'),
        # 测试有未闭合的 \( 时会自动补充
        (r'公式\(x^2', r'公式\(x^2\)', '补充未闭合的 \\('),
    ]
    
    passed = 0
    failed = 0
    
    for input_text, expected, description in test_cases:
        result = fix_reversed_delimiters(input_text)
        if result == expected:
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


def test_math_state_machine():
    """测试任务2和3：MathStateMachine的新方法"""
    print("=" * 60)
    print("测试任务2和3：split_chinese_from_math 和 fix_math_symbol_chinese_boundary")
    print("=" * 60)
    
    from ocr_to_examx import MathStateMachine
    
    sm = MathStateMachine()
    
    # 测试任务2：split_chinese_from_math
    print("\n测试 split_chinese_from_math:")
    test_cases_task2 = [
        (r'\(在x^2\)', r'在\(x^2\)', '开头中文'),
        (r'\(x^2的值\)', r'\(x^2\)的值', '结尾中文'),
        (r'\(在x^2的值\)', r'在\(x^2\)的值', '两端中文'),
    ]
    
    passed2 = 0
    failed2 = 0
    for input_text, expected, description in test_cases_task2:
        result = sm.split_chinese_from_math(input_text)
        if result == expected:
            print(f"✅ PASS: {description}")
            print(f"   输入: {repr(input_text)}")
            print(f"   输出: {repr(result)}")
            passed2 += 1
        else:
            print(f"❌ FAIL: {description}")
            print(f"   输入: {repr(input_text)}")
            print(f"   期望: {repr(expected)}")
            print(f"   实际: {repr(result)}")
            failed2 += 1
        print()
    
    # 测试任务3：fix_math_symbol_chinese_boundary
    print("\n测试 fix_math_symbol_chinese_boundary:")
    test_cases_task3 = [
        # 更简单的测试用例 - 只有一次分离
        (r'\(\therefore直线是垂直的\)', r'\(\therefore\)直线是垂直的', '\\therefore后跟中文（简单）'),
        # 复杂的嵌套案例需要配合其他函数
        (r'\(\therefore直线\)', r'\(\therefore\)直线', '\\therefore后跟中文'),
    ]
    
    passed3 = 0
    failed3 = 0
    for input_text, expected, description in test_cases_task3:
        result = sm.fix_math_symbol_chinese_boundary(input_text)
        if result == expected:
            print(f"✅ PASS: {description}")
            print(f"   输入: {repr(input_text)}")
            print(f"   输出: {repr(result)}")
            passed3 += 1
        else:
            print(f"❌ FAIL: {description}")
            print(f"   输入: {repr(input_text)}")
            print(f"   期望: {repr(expected)}")
            print(f"   实际: {repr(result)}")
            failed3 += 1
        print()
    
    print(f"任务2 结果: {passed2} passed, {failed2} failed")
    print(f"任务3 结果: {passed3} passed, {failed3} failed\n")
    
    return passed2 + passed3, failed2 + failed3


def test_final_cleanup():
    """测试任务6：final_cleanup"""
    print("=" * 60)
    print("测试任务6：final_cleanup")
    print("=" * 60)
    
    from ocr_to_examx import MathStateMachine
    
    sm = MathStateMachine()
    
    test_cases = [
        (r'$$残留的美元$$', r'残留的美元', '清理残留的 $$'),
        (r'\(\)', '', '清理空数学模式'),
        (r'\(\(\(x\)\)\)', r'\(x\)', '清理连续定界符'),
    ]
    
    passed = 0
    failed = 0
    
    for input_text, expected, description in test_cases:
        result = sm.final_cleanup(input_text)
        if result == expected:
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
    print("OCR修复脚本测试套件")
    print("=" * 60 + "\n")
    
    total_passed = 0
    total_failed = 0
    
    # 运行所有测试
    p1, f1 = test_fix_right_boundary_errors()
    p2, f2 = test_math_state_machine()
    p3, f3 = test_fix_reversed_delimiters()
    p4, f4 = test_final_cleanup()
    
    total_passed = p1 + p2 + p3 + p4
    total_failed = f1 + f2 + f3 + f4
    
    # 总结
    print("=" * 60)
    print("总体测试结果")
    print("=" * 60)
    print(f"✅ 通过: {total_passed}")
    print(f"❌ 失败: {total_failed}")
    print(f"总计: {total_passed + total_failed}")
    print(f"通过率: {total_passed / (total_passed + total_failed) * 100:.1f}%")
    print("=" * 60)
    
    sys.exit(0 if total_failed == 0 else 1)
