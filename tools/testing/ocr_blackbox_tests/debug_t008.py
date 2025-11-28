#!/usr/bin/env python3
import sys
sys.path.insert(0, 'tools/core')
import importlib
import ocr_to_examx
importlib.reload(ocr_to_examx)
from ocr_to_examx import (
    process_text_for_latex,
    split_long_lines_in_explain,
    remove_par_breaks_in_explain,
    remove_blank_lines_in_macro_args
)
import re

# 精确模拟源文件中的内容
test = '联立$$\\left\\{ \\begin{array}{r}\nx = my + \\frac{3}{2} \\\\\ny^{2} = 6x\n\\end{array} \\right.\\ $$，得$$y^{2} - 6my - 9 = 0$$，'

# Step 1: process_text_for_latex
result = process_text_for_latex(test, is_math_heavy=True)
print("After process_text_for_latex:")
opens = len(re.findall(r'\\\(', result))
closes = len(re.findall(r'\\\)', result))
print(f"  \\( = {opens}, \\) = {closes}, diff = {opens - closes}")

# Step 2: remove_blank_lines_in_macro_args
result = remove_blank_lines_in_macro_args(result)
print("\nAfter remove_blank_lines_in_macro_args:")
opens = len(re.findall(r'\\\(', result))
closes = len(re.findall(r'\\\)', result))
print(f"  \\( = {opens}, \\) = {closes}, diff = {opens - closes}")

# Step 3: split_long_lines_in_explain
result = split_long_lines_in_explain(result, max_length=800)
print("\nAfter split_long_lines_in_explain:")
opens = len(re.findall(r'\\\(', result))
closes = len(re.findall(r'\\\)', result))
print(f"  \\( = {opens}, \\) = {closes}, diff = {opens - closes}")

# Step 4: remove_par_breaks_in_explain
result = remove_par_breaks_in_explain(result)
print("\nAfter remove_par_breaks_in_explain:")
opens = len(re.findall(r'\\\(', result))
closes = len(re.findall(r'\\\)', result))
print(f"  \\( = {opens}, \\) = {closes}, diff = {opens - closes}")

# Step 5: convert display math (skip comments)
def convert_display_math_skip_comments(text):
    lines = text.split('\n')
    result_lines = []
    for line in lines:
        if line.strip().startswith('%'):
            result_lines.append(line)
        else:
            line = re.sub(r'\$\$\s*(.+?)\s*\$\$', r'\\(\1\\)', line)
            result_lines.append(line)
    return '\n'.join(result_lines)

result = convert_display_math_skip_comments(result)
print("\nAfter convert_display_math_skip_comments:")
opens = len(re.findall(r'\\\(', result))
closes = len(re.findall(r'\\\)', result))
print(f"  \\( = {opens}, \\) = {closes}, diff = {opens - closes}")

print("\nFinal result:")
print(repr(result))
