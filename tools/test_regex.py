#!/usr/bin/env python3
import re

# 测试 TikZ 坐标正则
tikz_pattern = r'\$\([A-Za-z][A-Za-z0-9]*(?:[!+\-][\d\.]+|[!+\-]\([A-Za-z][A-Za-z0-9]*\))*\)\$'
test_str = '点$(A)$在坐标$(B)!0.5!(C)$'
print('测试字符串:', test_str)
print('当前模式匹配:', re.findall(tikz_pattern, test_str))

# 测试更宽松的模式 - 匹配 $(任何内容)$ 只要内部没有空格或复杂数学
tikz_pattern2 = r'\$\([A-Za-z0-9!+\-*/\.\(\):,\s]+\)\$'
print('宽松模式匹配:', re.findall(tikz_pattern2, test_str))

# 测试 $\(...\)$ 清理
fix_pattern = r'\$\s*\\\((.+?)\\\)\s*\$'
test_str2 = '集合$\\(A\\) = \\{x\\}$'
print('\n测试字符串2:', test_str2)
print('匹配 $\\(...)$:', re.findall(fix_pattern, test_str2))
result = re.sub(fix_pattern, r'\\(\1\\)', test_str2, flags=re.DOTALL)
print('替换结果:', result)
