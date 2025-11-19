#!/usr/bin/env python3
"""快速测试 ocr_to_examx.py 的四个改动"""

import sys
sys.path.insert(0, '/Users/muryor/code/mynote/tools')
from core.ocr_to_examx import _sanitize_math_block, smart_inline_math, wrap_math_variables, process_text_for_latex

print("=" * 60)
print("测试 ocr_to_examx.py 改动")
print("=" * 60)
print()

# 测试1：中文标点统一
print("【测试1】数学环境内中文标点统一")
test1_input = 'x = 1，y = 2：z = 3；a = 4。b、c'
test1_output = _sanitize_math_block(test1_input)
print(f"  输入: {test1_input}")
print(f"  输出: {test1_output}")
has_chinese_punct = any(p in test1_output for p in ['，', '：', '；', '。', '、'])
print(f"  结果: {'✗ 失败 - 仍有中文标点' if has_chinese_punct else '✓ 通过'}")
print()

# 测试2：TikZ保护收紧
print("【测试2】TikZ坐标保护收紧")
test2_input = '$(A)$ 和 $(0,1)$ 和 $(A)!0.5!(B)$'
test2_output = smart_inline_math(test2_input)
print(f"  输入: {test2_input}")
print(f"  输出: {test2_output}")
has_dollar_A = '$(A)$' in test2_output
has_dollar_01 = '$(0,1)$' in test2_output
has_dollar_AB = '$(A)!0.5!(B)$' in test2_output
print(f"  $(A)$ 保留: {has_dollar_A} (应为True)")
print(f"  $(0,1)$ 转换: {not has_dollar_01} (应为True，已转为\\(...\\))")
print(f"  $(A)!0.5!(B)$ 保留: {has_dollar_AB} (应为True)")
print()

# 测试3：wrap_math_variables中的TikZ保护
print("【测试3】wrap_math_variables中TikZ保护")
test3_input = '$(A)$ 和 $(0,1)$'
test3_output = wrap_math_variables(test3_input)
print(f"  输入: {test3_input}")
print(f"  输出: {test3_output}")
print()

# 测试4：故选删除
print("【测试4】更彻底的'故选'删除")
test4_cases = [
    ('结尾故选', '这是一段文字，故选：A'),
    ('单独一行', '这是一段文字。\n故选：A\n其他内容'),
    ('多行单独', '文字\n\n故选：ACD\n\n继续'),
]
for name, test_input in test4_cases:
    test_output = process_text_for_latex(test_input)
    has_guxuan = '故选' in test_output
    print(f"  {name}:")
    print(f"    输入: {repr(test_input)}")
    print(f"    输出: {repr(test_output)}")
    print(f"    结果: {'✗ 仍有故选' if has_guxuan else '✓ 已删除'}")
    print()

print("=" * 60)
print("测试完成")
print("=" * 60)
