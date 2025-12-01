#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试表格边框添加功能

确保 add_table_borders() 函数不会引入 bug：
1. 正确添加竖线边框到列格式
2. 添加 \hline 到表格首尾和每行后
3. 不影响已有边框的表格
4. 处理各种边缘情况
"""

import sys
import os

# 添加 tools/core 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))


def add_table_borders(text: str) -> str:
    r"""为 LaTeX 表格添加边框
    
    将无边框表格：
        \begin{tabular}{ccc}
        A & B & C \\
        1 & 2 & 3 \\
        \end{tabular}
    
    转换为有边框表格：
        \begin{tabular}{|c|c|c|}
        \hline
        A & B & C \\
        \hline
        1 & 2 & 3 \\
        \hline
        \end{tabular}
    
    Args:
        text: LaTeX 文本
        
    Returns:
        添加边框后的文本
    """
    if not text or '\\begin{tabular}' not in text:
        return text
    
    import re
    
    # 匹配整个 tabular 环境
    pattern = re.compile(
        r'(\\begin\{tabular\}\{)([^}]+)(\})(.*?)(\\end\{tabular\})',
        re.DOTALL
    )
    
    def process_table(match):
        begin_part = match.group(1)  # \begin{tabular}{
        col_spec = match.group(2)     # ccc 或 |c|c|c| 等
        end_bracket = match.group(3)  # }
        content = match.group(4)      # 表格内容
        end_part = match.group(5)     # \end{tabular}
        
        # 如果已经有边框，不修改
        if '|' in col_spec:
            return match.group(0)
        
        # 添加竖线到列格式
        # ccc -> |c|c|c|
        new_col_spec = '|' + '|'.join(list(col_spec)) + '|'
        
        # 处理表格内容，添加 \hline
        lines = content.split('\n')
        new_lines = []
        
        # 首行前添加 \hline
        has_content = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # 跳过空行
            if not stripped:
                new_lines.append(line)
                continue
            
            # 第一个非空行前添加 \hline
            if not has_content and stripped:
                new_lines.append('\\hline')
                has_content = True
            
            # 添加当前行
            new_lines.append(line)
            
            # 如果行包含数据（含 &），在其后添加 \hline
            if '&' in stripped or '\\\\' in stripped:
                # 避免重复添加 \hline
                next_line_index = i + 1
                next_is_hline = False
                if next_line_index < len(lines):
                    next_stripped = lines[next_line_index].strip()
                    if next_stripped == '\\hline':
                        next_is_hline = True
                
                if not next_is_hline:
                    new_lines.append('\\hline')
        
        new_content = '\n'.join(new_lines)
        
        return f"{begin_part}{new_col_spec}{end_bracket}{new_content}{end_part}"
    
    return pattern.sub(process_table, text)


# 测试用例
def run_tests():
    print("=" * 70)
    print("表格边框添加功能测试")
    print("=" * 70)
    
    tests_passed = 0
    tests_failed = 0
    
    # 测试 1：基本无边框表格
    test1_input = r"""
\begin{tabular}{ccc}
A & B & C \\
1 & 2 & 3 \\
\end{tabular}
"""
    test1_expected_patterns = [
        r'\{|c|c|c|\}',  # 列格式有边框
        r'\\hline',       # 包含 \hline
    ]
    
    result1 = add_table_borders(test1_input)
    test1_pass = all(re.search(p, result1) for p in test1_expected_patterns)
    
    print(f"\n测试 1: 基本无边框表格")
    print(f"输入:\n{test1_input}")
    print(f"输出:\n{result1}")
    print(f"结果: {'✅ PASS' if test1_pass else '❌ FAIL'}")
    
    if test1_pass:
        tests_passed += 1
    else:
        tests_failed += 1
    
    # 测试 2：已有边框的表格（不应修改）
    test2_input = r"""
\begin{tabular}{|c|c|c|}
\hline
A & B & C \\
\hline
\end{tabular}
"""
    result2 = add_table_borders(test2_input)
    test2_pass = result2 == test2_input
    
    print(f"\n测试 2: 已有边框的表格（不应修改）")
    print(f"输入:\n{test2_input}")
    print(f"输出:\n{result2}")
    print(f"结果: {'✅ PASS' if test2_pass else '❌ FAIL'}")
    
    if test2_pass:
        tests_passed += 1
    else:
        tests_failed += 1
    
    # 测试 3：实际试卷表格（5列）
    test3_input = r"""
\begin{center}
\begin{tabular}{ccccc}
\hline
$x/{}^{\circ}\mathbb{C}$ & -2 & -1 & 0 & 1 \\
\hline
$y/$百元 & 5 & 4 & 2 & 1 \\
\hline
\end{tabular}
\end{center}
"""
    result3 = add_table_borders(test3_input)
    test3_pass = '|c|c|c|c|c|' in result3
    
    print(f"\n测试 3: 实际试卷表格（5列）")
    print(f"输入:\n{test3_input}")
    print(f"输出:\n{result3}")
    print(f"结果: {'✅ PASS' if test3_pass else '❌ FAIL'}")
    
    if test3_pass:
        tests_passed += 1
    else:
        tests_failed += 1
    
    # 测试 4：空表格（边缘情况）
    test4_input = r"""
\begin{tabular}{cc}
\end{tabular}
"""
    result4 = add_table_borders(test4_input)
    test4_pass = '|c|c|' in result4
    
    print(f"\n测试 4: 空表格（边缘情况）")
    print(f"输入:\n{test4_input}")
    print(f"输出:\n{result4}")
    print(f"结果: {'✅ PASS' if test4_pass else '❌ FAIL'}")
    
    if test4_pass:
        tests_passed += 1
    else:
        tests_failed += 1
    
    # 测试 5：多个表格
    test5_input = r"""
\begin{tabular}{cc}
A & B \\
\end{tabular}

Some text here.

\begin{tabular}{ccc}
X & Y & Z \\
\end{tabular}
"""
    result5 = add_table_borders(test5_input)
    test5_pass = result5.count('|c|c|') >= 1 and result5.count('|c|c|c|') >= 1
    
    print(f"\n测试 5: 多个表格")
    print(f"输入:\n{test5_input}")
    print(f"输出:\n{result5}")
    print(f"结果: {'✅ PASS' if test5_pass else '❌ FAIL'}")
    
    if test5_pass:
        tests_passed += 1
    else:
        tests_failed += 1
    
    # 测试 6：包含数学公式的表格
    test6_input = r"""
\begin{tabular}{cccc}
\hline
$P\left( K^{2} \geq k_{0} \right)$ & 0.10 & 0.05 & 0.010 \\
\hline
$k_{0}$ & 2.706 & 3.841 & 6.635 \\
\hline
\end{tabular}
"""
    result6 = add_table_borders(test6_input)
    test6_pass = '|c|c|c|c|' in result6
    
    print(f"\n测试 6: 包含数学公式的表格")
    print(f"输入:\n{test6_input}")
    print(f"输出:\n{result6}")
    print(f"结果: {'✅ PASS' if test6_pass else '❌ FAIL'}")
    
    if test6_pass:
        tests_passed += 1
    else:
        tests_failed += 1
    
    # 总结
    print("\n" + "=" * 70)
    print(f"测试总结: {tests_passed} 通过, {tests_failed} 失败")
    print("=" * 70)
    
    return tests_failed == 0


if __name__ == "__main__":
    import re
    success = run_tests()
    sys.exit(0 if success else 1)
