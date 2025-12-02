#!/usr/bin/env python3
"""测试 fix_left_pipe_without_right 和 fix_angle_bracket_notation 函数"""

import sys
sys.path.insert(0, '/Users/muryor/code/mynote/tools/core')
from ocr_to_examx import fix_left_pipe_without_right, fix_angle_bracket_notation

def test_fix_left_pipe():
    """测试 fix_left_pipe_without_right 函数"""
    test_cases = [
        # (输入, 期望输出, 描述)
        (r'\left| x \right|', r'\left| x \right|', '已正确配对，不变'),
        (r'\left| x |', r'\left| x \right|', '缺少 \\right，需修复'),
        (r'\left| a \right|\left| b \right|', r'\left| a \right|\left| b \right|', '连续两个正确配对'),
        (r'\frac{1}{\left| x |}', r'\frac{1}{\left| x \right|}', '分数中缺少 \\right'),
        (r'\left| \left| x \right| \right|', r'\left| \left| x \right| \right|', '嵌套正确配对'),
        # 来自实际错误的测试用例
        (r'\frac{\vec{a} \cdot \vec{b}}{\left| \vec{b} |} \cdot \frac{\vec{b}}{\left| \vec{b} |} = 2\vec{b}',
         r'\frac{\vec{a} \cdot \vec{b}}{\left| \vec{b} \right|} \cdot \frac{\vec{b}}{\left| \vec{b} \right|} = 2\vec{b}',
         '实际错误案例：向量投影公式'),
        (r'\frac{\vec{a} \cdot \vec{b}}{\left| \vec{a} |\left| \vec{b} |}',
         r'\frac{\vec{a} \cdot \vec{b}}{\left| \vec{a} \right|\left| \vec{b} \right|}',
         '实际错误案例：连续两个缺少 \\right'),
    ]

    print('测试 fix_left_pipe_without_right:')
    print('=' * 60)
    passed = 0
    failed = 0
    for inp, expected, desc in test_cases:
        result = fix_left_pipe_without_right(inp)
        if result == expected:
            print(f'✅ {desc}')
            passed += 1
        else:
            print(f'❌ {desc}')
            print(f'   输入: {inp}')
            print(f'   期望: {expected}')
            print(f'   实际: {result}')
            failed += 1
        print()
    
    print(f'通过: {passed}/{passed+failed}')
    return failed == 0


def test_fix_angle_bracket():
    """测试 fix_angle_bracket_notation 函数"""
    test_cases = [
        # (输入, 期望输出, 描述)
        (r'\cos\left. <\vec{a},\vec{b}\right.>', r'\cos\langle \vec{a},\vec{b}\rangle', 
         '向量夹角 \\left. <...\\right.>'),
        (r'\left. < A, B \right. >', r'\langle  A, B \rangle', 
         '简单夹角表示'),
        (r'\langle a, b \rangle', r'\langle a, b \rangle', 
         '已正确格式，不变'),
        (r'a < b > c', r'a < b > c', 
         '普通大小比较符号，不变'),
    ]

    print('\n测试 fix_angle_bracket_notation:')
    print('=' * 60)
    passed = 0
    failed = 0
    for inp, expected, desc in test_cases:
        result = fix_angle_bracket_notation(inp)
        if result == expected:
            print(f'✅ {desc}')
            passed += 1
        else:
            print(f'❌ {desc}')
            print(f'   输入: {inp}')
            print(f'   期望: {expected}')
            print(f'   实际: {result}')
            failed += 1
        print()
    
    print(f'通过: {passed}/{passed+failed}')
    return failed == 0


if __name__ == '__main__':
    print('🧪 测试新增的修复函数')
    print('=' * 60)
    
    result1 = test_fix_left_pipe()
    result2 = test_fix_angle_bracket()
    
    print('\n' + '=' * 60)
    if result1 and result2:
        print('✅ 所有测试通过！')
        sys.exit(0)
    else:
        print('❌ 有测试失败')
        sys.exit(1)
