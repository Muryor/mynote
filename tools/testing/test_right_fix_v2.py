#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试并修复反向数学定界符问题"""

import re

def fix_right_period_delimiter(text: str) -> str:
    """
    修复 \\right. 后的定界符问题
    
    问题模式: \\end{array} \\right.\\)，得\\(\\left\\{
    正确模式: \\end{array} \\right.，得\\left\\{
    """
    # 直接替换字符串，不用复杂的正则
    # 模式: \right.\)，得\(
    # 改为: \right.，得
    
    count = 0
    result = text
    
    # 模式1: \right.\)，得\(  → \right.，得
    pattern1 = r'\right.\)，得\('
    if pattern1 in result:
        before_count = result.count(pattern1)
        result = result.replace(pattern1, r'\right.，得')
        count += before_count
        print(f"✅ 修复了 {before_count} 处 '\\right.\\)，得\\(' 模式")
    
    # 模式2: \right.\)，则\(  → \right.，则
    pattern2 = r'\right.\)，则\('
    if pattern2 in result:
        before_count = result.count(pattern2)
        result = result.replace(pattern2, r'\right.，则')
        count += before_count
        print(f"✅ 修复了 {before_count} 处 '\\right.\\)，则\\(' 模式")
    
    # 模式3: \right.\)，\par  → \right.，\par
    pattern3 = r'\right.\)，\par'
    if pattern3 in result:
        before_count = result.count(pattern3)
        result = result.replace(pattern3, r'\right.，\par')
        count += before_count
        print(f"✅ 修复了 {before_count} 处 '\\right.\\)，\\par' 模式")
    
    if count > 0:
        print(f"✅ 总共修复了 {count} 处 \\right. 定界符问题")
    
    return result


# 测试用例
test_case = r"""则有\(\left\{ \begin{array}{r}
\overrightarrow{n} \cdot \overrightarrow{BC} = 0 \\
\overrightarrow{n} \cdot \overrightarrow{PC} = 0
\end{array} \right.\)，得\(\left\{ \begin{array}{r}
4y = 0 \\
2\sqrt{3}x + 2y - 2z = 0
\end{array} \right.\)，\par"""

print("原始文本:")
print(test_case)
print("\n" + "="*60 + "\n")

fixed = fix_right_period_delimiter(test_case)
print("修复后:")
print(fixed)
print("\n" + "="*60 + "\n")

# 验证
print("验证:")
print(f"原文包含 '\\right.\\)，得\\(': {'\\right.\\)，得\\(' in test_case}")
print(f"修复后包含 '\\right.\\)，得\\(': {'\\right.\\)，得\\(' in fixed}")
print(f"修复后包含 '\\right.，得': {'\\right.，得' in fixed}")
