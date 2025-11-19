#!/usr/bin/env python3
import re

# 测试字符串
test = r'集合$\(A\) = \{x\}$'
print('输入:', repr(test))

# 在 raw 字符串中，\\( 实际上是两个字符：\ 和 (
# 在正则中，\\( 匹配字面的 \(
pattern1 = r'\$\s*\\\((.+?)\\\)\s*\$'
print('模式1:', repr(pattern1))
result1 = re.findall(pattern1, test)
print('findall结果1:', result1)

result_sub = re.sub(pattern1, r'\\(\1\\)', test, flags=re.DOTALL)
print('sub结果:', repr(result_sub))

# 测试实际的输入（不是 raw 字符串）
test2 = '集合$\\(A\\) = \\{x\\}$'
print('\n实际输入:', repr(test2))
result2 = re.findall(pattern1, test2)
print('findall结果2:', result2)
result_sub2 = re.sub(pattern1, r'\\(\1\\)', test2, flags=re.DOTALL)
print('sub结果2:', repr(result_sub2))
