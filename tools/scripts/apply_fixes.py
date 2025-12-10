#!/usr/bin/env python3
"""Apply post-processing fixes to a converted exam TeX file"""

import re
import sys

def fix_nested_subquestions(text: str) -> str:
    """修复嵌套子题号格式"""
    # 匹配 \item 后紧跟 (i)/(ii)/(iii) 等
    pattern = r'\\item\s+\(([ivxIVX]+)\)'
    text = re.sub(pattern, r'\\item[(\1)]', text)
    
    # 同样处理全角括号
    pattern_cn = r'\\item\s+（([ivxIVX]+)）'
    text = re.sub(pattern_cn, r'\\item[(\1)]', text)
    
    return text

def fix_trig_function_spacing(text: str) -> str:
    """修复三角函数和对数函数后缺少空格的问题"""
    trig_funcs = ['sin', 'cos', 'tan', 'cot', 'sec', 'csc', 'arcsin', 'arccos', 'arctan',
                  'sinh', 'cosh', 'tanh', 'ln', 'log', 'lg', 'exp']
    
    for func in trig_funcs:
        pattern = rf'\\{func}([A-Za-z])(?![a-zA-Z])'
        text = re.sub(pattern, rf'\\{func} \1', text)
    
    return text

def fix_undefined_symbols(text: str) -> str:
    """替换可能未定义的数学符号"""
    text = re.sub(r'\\bigtriangleup\b', r'\\triangle', text)
    return text

def main():
    if len(sys.argv) < 2:
        print("Usage: python apply_fixes.py <tex_file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    original = text
    text = fix_nested_subquestions(text)
    text = fix_trig_function_spacing(text)
    text = fix_undefined_symbols(text)
    
    if text != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"✅ Applied fixes to {file_path}")
    else:
        print(f"No changes needed for {file_path}")

if __name__ == "__main__":
    main()
