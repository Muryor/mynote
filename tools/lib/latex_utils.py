#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
latex_utils.py - LaTeX工具模块 - 环境处理、格式化

从 ocr_to_examx.py 提取的共享工具函数，供 exam 和 handout 转换器使用。

生成时间: 自动提取
源文件: tools/core/ocr_to_examx.py
"""

import re

# ============================================================
# LaTeX工具模块 - 环境处理、格式化
# ============================================================

def fix_tabular_environments(text: str) -> str:
    r"""🆕 v1.9.1：修复 tabular 环境缺失列格式（P1）

    检测并修复 \begin{tabular} 缺少列格式参数的问题
    例如：\begin{tabularend{center} → \begin{tabular}{|c|c|}...\end{center}

    Args:
        text: LaTeX 文本

    Returns:
        修复后的文本
    """
    if not text or '\\begin{tabular}' not in text:
        return text

    import re

    # 检测不完整的 tabular（后面没有紧跟 {列格式}）
    pattern = re.compile(r'\\begin\{tabular\}(?!\s*\{)')

    def fix_tabular(match):
        # 获取匹配位置
        start_pos = match.end()

        # 查找后续内容，尝试推断列数
        # 向后查找最多500个字符
        remaining = text[start_pos:start_pos+500]

        # 尝试找到第一行内容（到 \\ 或换行）
        first_row_match = re.search(r'([^\n\\]+?)(?:\\\\|\n)', remaining)
        if first_row_match:
            first_row = first_row_match.group(1)
            # 统计 & 的数量来推断列数
            col_count = first_row.count('&') + 1
        else:
            # 默认2列
            col_count = 2

        # 生成默认的列格式（居中对齐，带竖线）
        col_format = '|' + 'c|' * col_count

        return match.group(0) + '{' + col_format + '}'

    return pattern.sub(fix_tabular, text)




def add_table_borders(text: str) -> str:
    r"""🆕 v1.9.8：为 LaTeX 表格添加边框（2025-12-01）
    
    将无边框表格转换为有边框表格，符合试卷格式要求。
    
    转换示例：
        \begin{tabular}{ccc}        →  \begin{tabular}{|c|c|c|}
        A & B & C \\                    \hline
        1 & 2 & 3 \\                    A & B & C \\
        \end{tabular}                   \hline
                                        1 & 2 & 3 \\
                                        \hline
                                        \end{tabular}
    
    Args:
        text: LaTeX 文本
        
    Returns:
        添加边框后的文本
        
    Notes:
        - 只处理无边框表格（列格式不含 |）
        - 已有边框的表格不修改
        - 自动添加 \hline 到表格首尾和每行后
    """
    if not text or '\\begin{tabular}' not in text:
        return text
    
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
        
        # 添加竖线到列格式：ccc -> |c|c|c|
        new_col_spec = '|' + '|'.join(list(col_spec)) + '|'
        
        # 处理表格内容，添加 \hline
        lines = content.split('\n')
        new_lines = []
        
        # 首行前添加 \hline（若首行已是 \hline 则不重复）
        has_content = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # 跳过空行
            if not stripped:
                new_lines.append(line)
                continue
            
            # 第一个非空行前添加 \hline（避免重复）
            if not has_content and stripped:
                if stripped != '\\hline':
                    new_lines.append('\\hline')
                has_content = True
            
            # 添加当前行
            new_lines.append(line)
            
            # 如果行包含数据（含 & 或 \\），在其后添加 \hline
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




def fix_fill_in_blanks(text: str) -> str:
    r"""🆕 v1.9.10：为填空题自动补充横线占位符
    
    问题：Word 下划线样式在 docx→md 转换时丢失，导致填空题没有空白横线
    修复：在「填空题」section 内，为题尾全角句号前插入 \fillin{}
    
    逻辑：
    1. 定位 \section{填空题} 到下一个 \section{ 之间的内容
    2. 对每个 \begin{question}...\end{question} 块：
       - 跳过已有 \fillin 或 \choices 的题目
       - 查找 \topics 前最后一个全角句号 ．
       - 在句号前插入 \fillin{}
    
    示例：
        则公比为\n．\n\topics{...}
        ↓
        则公比为\fillin{}\n．\n\topics{...}
    """
    import re
    
    # 定位填空题 section
    start = text.find("\\section{填空题}")
    if start == -1:
        return text
    
    end = text.find(r"\section{", start + 1)
    if end == -1:
        end = len(text)
    
    prefix, body, suffix = text[:start], text[start:end], text[end:]
    
    # 匹配所有 question 环境
    question_re = re.compile(r"(\\begin\{question\}.*?\\end\{question\})", re.DOTALL)
    
    def fix_block(block: str) -> str:
        # 跳过选择题或已有 fillin 的题目
        if "\\fillin" in block or "\\choices" in block:
            return block
        
        topics_idx = block.find(r"\topics")
        if topics_idx == -1:
            return block
        
        before_topics = block[:topics_idx]
        dot_idx = before_topics.rfind("．")  # 全角句号
        if dot_idx == -1:
            return block
        
        # 避免重复插入
        if before_topics[max(0, dot_idx - 10):dot_idx].find("\\fillin") != -1:
            return block
        
        new_before = before_topics[:dot_idx] + r"\fillin{}" + before_topics[dot_idx:]
        return new_before + block[topics_idx:]
    
    body = question_re.sub(lambda m: fix_block(m.group(1)), body)
    return prefix + body + suffix


# 🆕 v1.9.9: P2-8 删除未使用的 wrap_math_variables 函数（死代码清理）




def remove_par_breaks_in_explain(text: str) -> str:
    r"""移除 \explain{...} 中的空段落（改进版：正确处理嵌套括号）

    🆕 v1.8.2：完全重写，修复括号计数错误
    - 正确处理 \{ \} 转义括号（不计入 depth）
    - 正确处理反斜杠转义（\\ 后的字符不处理）
    - 将空段落替换为 % 注释而非 \par（更安全）
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    out = []
    i = 0
    n = len(text)

    while i < n:
        if text.startswith("\\explain{", i):
            out.append("\\explain{")
            i += len("\\explain{")
            depth = 1
            buf = []

            while i < n and depth > 0:
                # 处理反斜杠转义序列
                if text[i] == '\\' and i + 1 < n:
                    next_char = text[i + 1]
                    # \{ 和 \} 不计入括号深度
                    if next_char in '{}':
                        buf.append(text[i:i+2])
                        i += 2
                        continue
                    # 其他反斜杠序列（如 \\, \left, \right 等）直接复制
                    buf.append(text[i])
                    i += 1
                    continue

                # 检测空段落（连续两个换行，中间只有空白）
                if text[i] == '\n':
                    j = i + 1
                    while j < n and text[j] in ' \t':
                        j += 1
                    if j < n and text[j] == '\n':
                        # 空段落：替换为注释行
                        buf.append('\n%\n')
                        i = j + 1
                        continue

                # 普通大括号计数
                if text[i] == '{':
                    depth += 1
                    buf.append(text[i])
                    i += 1
                elif text[i] == '}':
                    depth -= 1
                    if depth == 0:
                        # 找到匹配的闭括号
                        out.append(''.join(buf))
                        out.append('}')
                        i += 1
                        break
                    buf.append(text[i])
                    i += 1
                else:
                    buf.append(text[i])
                    i += 1

            # 如果循环结束但 depth > 0，说明括号不匹配（保留原内容）
            if depth > 0:
                out.append(''.join(buf))
        else:
            out.append(text[i])
            i += 1

    return ''.join(out)




def clean_question_environments(text: str) -> str:
    """清理 question 环境内部的多余空行，并检测缺少题干的题目"""
    pattern = r'(\\begin\{question\})(.*?)(\\end\{question\})'

    def clean_env(match):
        begin = match.group(1)
        content = match.group(2)
        end = match.group(3)

        # 删除连续的3个以上换行
        content = re.sub(r'\n{3,}', '\n\n', content)

        # 🆕 v1.8: 检测缺少题干的题目（直接从 \item 开始）
        # 去除前导空白后检查是否以 \item 开头
        content_stripped = content.lstrip()
        if content_stripped.startswith('\\item'):
            # 在 \begin{question} 后插入 TODO 注释
            warning = '\n% ⚠️ TODO: 补充题干 - 此题直接从 \\item 开始，请在上方添加题目主干描述\n'
            content = warning + content

        return begin + content + end

    return re.sub(pattern, clean_env, text, flags=re.DOTALL)





# ============================================================
# 导出列表
# ============================================================

__all__ = [
    'fix_tabular_environments',
    'add_table_borders',
    'fix_fill_in_blanks',
    'remove_par_breaks_in_explain',
    'clean_question_environments',
]
