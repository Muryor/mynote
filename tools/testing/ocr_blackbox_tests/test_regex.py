#!/usr/bin/env python3
"""测试嵌套定界符正则表达式"""
import re

# 测试模式
test_cases = [
    r'\(P,B\(，\)C,D均在球O\)',
    r'\(x_{O} = 0\(，\therefore\)O(0,1)\)',
]

for test in test_cases:
    print(f'输入: {test}')
    
    # 匹配 \(...\(标点\)...\) 模式
    # 使用非贪婪匹配和更精确的边界
    pattern = r'\\\\\\((.*)\\\\\\(([，。；：、！？])\\\\\\)(.*?)\\\\\\)'
    match = re.search(pattern, test)
    if match:
        print(f'  匹配成功')
        print(f'  前部分: {match.group(1)}')
        print(f'  标点: {match.group(2)}')
        print(f'  后部分: {match.group(3)}')
        
        # 重组
        before = match.group(1)
        punct = match.group(2)
        after = match.group(3)
        
        result = ''
        if before.strip():
            result += r'\(' + before + r'\)'
        result += punct
        if after.strip():
            result += r'\(' + after + r'\)'
        
        print(f'  重组结果: {result}')
    else:
        print('  未匹配')
    print()
