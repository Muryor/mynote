import re

# 读取文件
with open('content/exams/g3/jinhua_exam_raw.tex', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 清理 choices 中的"故选：X"等多余文字
content = re.sub(r'(\s+)故选[:：][ABCD]+\.?', r'', content)

# 2. 修正圆的方程中的\-
content = content.replace('(x\\-1)', '(x-1)')
content = content.replace('3x\\-4y', '3x-4y')
content = content.replace('x\\-b', 'x-b')
content = content.replace('c\\-d', 'c-d')
content = content.replace('a\\-b', 'a-b')

# 3. 修正 i 为虚数单位（在复数中）
content = content.replace('2+i', '2+\\mathrm{i}')
content = content.replace('2-i', '2-\\mathrm{i}')
content = content.replace('-2+i', '-2+\\mathrm{i}')
content = content.replace('-2-i', '-2-\\mathrm{i}')

# 4. 修正指数格式
content = re.sub(r'a\^{5}_{3}', r'a^{\\frac{5}{3}}', content)

# 5. 修正角度符号
content = content.replace('60^{\\circ}', '60^\\circ')
content = content.replace('30^{\\circ}', '30^\\circ')
content = content.replace('0^{\\circ}', '0^\\circ')

# 6. 修正向量符号
content = re.sub(r'\\overline\{([a-z])\}', r'\\vec{\1}', content)

# 7. 清理填空题多余的"故答案为"
content = re.sub(r'\n+故答案为[:：]\s*\d+\n', '\n', content)

# 8. 修正复数分式
content = content.replace('\\frac{(2+i)(2-i)}{2+i}', '\\frac{5(2-\\mathrm{i})}{(2+\\mathrm{i})(2-\\mathrm{i})}')

# 保存
with open('content/exams/g3/g3_jinhua_2025_mock1.tex', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 精修完成，保存到 g3_jinhua_2025_mock1.tex")
print(f"文件行数: {len(content.splitlines())}")
