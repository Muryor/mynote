#!/usr/bin/env python3
import re

with open('content/exams/auto/lishui_2026_nov/converted_exam.tex', 'r') as f:
    content = f.read()

# 简单策略：在\begin{question}到\end{choices}之间，以及explain中包含中文的行，将\[...\]改为\(...\)
lines = content.split('\n')
new_lines = []

for i, line in enumerate(lines):
    # 如果行中同时有\[和中文字符（或在choices/question环境中），转换为行内公式
    if '\\[' in line:
        # 检查是否在题目、选项行
        if ('\\begin{question}' in line or '\\item' in line or 
            (i > 0 and any(x in lines[i-1] for x in ['\\begin{question}', '\\begin{choices}'])) or
            (len(line) > 100 and any(ord(c) > 127 for c in line))):  # 长行且有中文
            line = line.replace('\\[', '\\(').replace('\\]', '\\)')
    
    new_lines.append(line)

content = '\n'.join(new_lines)

with open('content/exams/auto/lishui_2026_nov/converted_exam.tex', 'w') as f:
    f.write(content)

print("Math mode conversion completed")
