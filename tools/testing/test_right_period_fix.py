#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""测试并修复反向数学定界符问题"""

import re

def fix_right_period_delimiter(text: str) -> str:
    r"""
    修复 \right. 后的定界符问题
    
    问题模式: \end{array} \right.\)，得\(\left\{
    正确模式: \end{array} \right.，得\left\{
    """
    # 模式: \right.\)，[文本]\(
    # 需要正确转义反斜杠和括号
    pattern = r'\\right\\.\\\\\\)，(.*?)\\\\\\('
    
    count = 0
    def replacer(match):
        nonlocal count
        middle_text = match.group(1)
        # 如果中间只有简单的中文（如"得"），则移除 \) 和 \(
        if len(middle_text.strip()) < 10 and not re.search(r'\\[a-zA-Z]', middle_text):
            count += 1
            return rf'\right.，{middle_text}'
        return match.group(0)
    
    result = re.sub(pattern, replacer, text)
    
    if count > 0:
        print(f"✅ 修复了 {count} 处 \\right. 定界符问题")
    
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
