#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
text_cleaning.py - 文本清理模块 - LaTeX转义、Markdown清理、格式化

从 ocr_to_examx.py 提取的共享工具函数，供 exam 和 handout 转换器使用。

生成时间: 自动提取
源文件: tools/core/ocr_to_examx.py
"""

from pathlib import Path
from typing import List, Optional
import re

# ============================================================
# 文本清理模块 - LaTeX转义、Markdown清理、格式化
# ============================================================

LATEX_SPECIAL_CHARS = {
    "%": r"\%",
    "&": r"\&",
    "#": r"\#",
    "~": r"\textasciitilde{}",
}


def escape_latex_special(text: str, in_math_mode: bool = False) -> str:
    r"""转义 LaTeX 特殊字符（增强版 v1.9.2）

    🆕 v1.9.2 改进:
    1. 正确保护数学模式内的 & （用于 matrix/array 列分隔）
    2. 保护已转义的字符（\&, \%, \#）
    3. 保护 LaTeX 命令（\text{}, \left, \right 等）
    """
    if not text:
        return text
        
    # 保护已经转义的字符
    protected_escaped = []
    def save_escaped(match):
        protected_escaped.append(match.group(0))
        return f"@@ESCAPED_{len(protected_escaped)-1}@@"
    
    # 保护已转义的特殊字符
    text = re.sub(r'\\[%&#~]', save_escaped, text)
    
    if in_math_mode:
        # 在数学模式内，不转义 &（用于 array/matrix 列分隔）
        for char in ["%", "#", "~"]:
            if char in LATEX_SPECIAL_CHARS:
                text = text.replace(char, LATEX_SPECIAL_CHARS[char])
    else:
        # 保护注释
        protected_comments = []
        def save_comment(match):
            protected_comments.append(match.group(0))
            return f"@@COMMENT_{len(protected_comments)-1}@@"
        text = re.sub(r'%.*$', save_comment, text, flags=re.MULTILINE)
        
        # 保护数学模式内的 &（用于 array/matrix/tabular）
        protected_math = []
        def save_math(match):
            protected_math.append(match.group(0))
            return f"@@MATH_{len(protected_math)-1}@@"
        
        # 保护 \(...\) 和 \[...\] 内的内容
        text = re.sub(r'\\\([^)]*\\\)', save_math, text, flags=re.DOTALL)
        text = re.sub(r'\\\[[^\]]*\\\]', save_math, text, flags=re.DOTALL)
        
        # 保护 tabular/array/matrix 环境
        text = re.sub(r'\\begin\{(tabular|array|matrix|pmatrix|bmatrix|vmatrix|cases)\}.*?\\end\{\1\}', 
                       save_math, text, flags=re.DOTALL)
        
        # 转义特殊字符
        for char, escaped in LATEX_SPECIAL_CHARS.items():
            text = text.replace(char, escaped)
        
        # 恢复保护的数学模式
        for i, math_block in enumerate(protected_math):
            text = text.replace(f"@@MATH_{i}@@", math_block)
        
        # 恢复保护的注释
        for i, comment in enumerate(protected_comments):
            text = text.replace(f"@@COMMENT_{i}@@", comment)
    
    # 恢复保护的已转义字符
    for i, escaped in enumerate(protected_escaped):
        text = text.replace(f"@@ESCAPED_{i}@@", escaped)
    
    # 清理可能的异常模式
    text = re.sub(r'\\\)([\u4e00-\u9fa5]{1,3})\\\(', r'\1', text)

    # 统一常见数学符号的排版
    text = standardize_math_symbols(text)
    
    return text




def standardize_math_symbols(text: str) -> str:
    r"""标准化数学符号（虚数单位/圆周率/自然底数等）

    修复 P2-001: 处理 \text{数字}、\text{数字π} 等模式
    🆕 P1-001: 添加数学函数和数集符号的标准化
    """
    if not text:
        return text

    # 🆕 P1-001: 数学函数替换 (\text{sin} → \sin)
    math_func_replacements = [
        (r'\\text\{\s*sin\s*\}', r'\\sin'),
        (r'\\text\{\s*cos\s*\}', r'\\cos'),
        (r'\\text\{\s*tan\s*\}', r'\\tan'),
        (r'\\text\{\s*cot\s*\}', r'\\cot'),
        (r'\\text\{\s*sec\s*\}', r'\\sec'),
        (r'\\text\{\s*csc\s*\}', r'\\csc'),
        (r'\\text\{\s*ln\s*\}', r'\\ln'),
        (r'\\text\{\s*log\s*\}', r'\\log'),
        (r'\\text\{\s*lg\s*\}', r'\\lg'),
        (r'\\text\{\s*lim\s*\}', r'\\lim'),
        (r'\\text\{\s*max\s*\}', r'\\max'),
        (r'\\text\{\s*min\s*\}', r'\\min'),
        (r'\\text\{\s*exp\s*\}', r'\\exp'),
        (r'\\text\{\s*arcsin\s*\}', r'\\arcsin'),
        (r'\\text\{\s*arccos\s*\}', r'\\arccos'),
        (r'\\text\{\s*arctan\s*\}', r'\\arctan'),
    ]
    
    for pattern, replacement in math_func_replacements:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # 🆕 P1-001: 数集符号替换 (\text{N} → \mathbb{N})
    number_set_replacements = [
        (r'\\text\{\s*N\s*\}', r'\\mathbb{N}'),
        (r'\\text\{\s*Z\s*\}', r'\\mathbb{Z}'),
        (r'\\text\{\s*Q\s*\}', r'\\mathbb{Q}'),
        (r'\\text\{\s*R\s*\}', r'\\mathbb{R}'),
        (r'\\text\{\s*C\s*\}', r'\\mathbb{C}'),
    ]
    
    for pattern, replacement in number_set_replacements:
        text = re.sub(pattern, replacement, text)

    # 虚数单位 - 保持 \text{i} 格式与范本一致
    # 注释掉以下转换，保留原始 \text{i} 格式
    # text = re.sub(r'\\text\{\s*i\s*\}', r'\\mathrm{i}', text)
    # text = re.sub(r'\\text\{\s*-\s*i\s*\}', r'-\\mathrm{i}', text)

    # 🆕 P2-001: 处理 \text{数字π} 或 \text{数字\pi}（必须在 \text{数字} 之前）
    text = re.sub(r'\\text\{(\d+)π\}', r'\1\\pi', text)
    text = re.sub(r'\\text\{(\d+)\\pi\}', r'\1\\pi', text)

    # 🆕 P2-001: 处理 \text{π数字} 或 \text{\pi数字}
    text = re.sub(r'\\text\{π(\d+)\}', r'\\pi\1', text)
    text = re.sub(r'\\text\{\\pi(\d+)\}', r'\\pi\1', text)

    # 🆕 P2-001: 处理 \text{数字}
    text = re.sub(r'\\text\{(\d+)\}', r'\1', text)

    # 圆周率
    text = re.sub(r'\\text\{\s*π\s*\}', r'\\pi', text)
    text = re.sub(r'(?<!\\)π', r'\\pi', text)

    # 自然对数底 e：仅在作为指数底数时替换
    text = re.sub(r'\\text\{\s*e\s*\}(?=\s*[\^_])', r'\\mathrm{e}', text)

    return text


# DEPRECATED: 已被 MathStateMachine 替换，保留以兼容旧测试；主流程不再调用


def normalize_fullwidth_brackets(text: str) -> str:
    """🆕 v1.6.3：统一全角括号为半角

    注意：不要替换用于 meta 标记的【】
    """
    pairs = {
        "（": "(",
        "）": ")",
        "｛": "{",
        "｝": "}",
        # 不替换 ［］，避免影响某些 Markdown 语法
    }
    for fw, hw in pairs.items():
        text = text.replace(fw, hw)
    return text


def convert_markdown_table_to_latex(text: str) -> str:
    """将 Markdown 表格转换为 LaTeX tabular"""
    table_pattern = r'(\|[^\n]+\|\n)+\|[-:\s|]+\|\n(\|[^\n]+\|\n)+'

    def convert_one_table(match):
        table_text = match.group(0)
        lines = [line.strip() for line in table_text.split('\n') if line.strip()]

        data_lines = [line for line in lines if not re.match(r'^\|[-:\s|]+\|$', line)]

        if not data_lines:
            return table_text

        rows = []
        for line in data_lines:
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            rows.append(cells)

        if not rows:
            return table_text

        ncols = len(rows[0])
        latex = "\\begin{center}\n"
        latex += f"\\begin{{tabular}}{{{'c' * ncols}}}\n"
        latex += "\\hline\n"

        header = rows[0]
        latex += " & ".join(escape_latex_special(cell, False) for cell in header)
        latex += " \\\n\\hline\n"

        for row in rows[1:]:
            latex += " & ".join(escape_latex_special(cell, False) for cell in row)
            latex += " \\\n"

        latex += "\\hline\n\\end{tabular}\n\\end{center}"
        return latex

    return re.sub(table_pattern, convert_one_table, text)


def convert_ascii_table_blocks(text: str) -> str:
    """将由横线 + 空格对齐组成的 ASCII 表格转换为 tabular"""
    if not text:
        return text

    lines = text.splitlines()
    result: List[str] = []
    i = 0

    def _is_rule(line: str) -> bool:
        stripped = line.strip()
        if not stripped:
            return False
        return all(ch in {'-', ' '} for ch in stripped) and stripped.count('-') >= 6

    def _convert_block(block: List[str]) -> Optional[str]:
        inner = [ln.rstrip() for ln in block[1:-1]]
        rows = [ln.strip() for ln in inner if ln.strip() and not _is_rule(ln)]
        if len(rows) < 2:
            return None

        split_rows = [re.split(r'\s{2,}', row) for row in rows]
        col_count = max(len(r) for r in split_rows)
        if col_count < 2:
            return None

        def _pad(row: List[str]) -> List[str]:
            padded = [cell.strip() for cell in row]
            while len(padded) < col_count:
                padded.append('')
            return padded[:col_count]

        latex_lines = ["\\begin{center}", f"\\begin{{tabular}}{{{'c' * col_count}}}", "\\hline"]

        header = _pad(split_rows[0])
        latex_lines.append(" & ".join(escape_latex_special(cell, False) for cell in header) + r" \\")
        latex_lines.append("\\hline")

        for row in split_rows[1:]:
            cells = _pad(row)
            latex_lines.append(" & ".join(escape_latex_special(cell, False) for cell in cells) + r" \\")

        latex_lines.append("\\hline")
        latex_lines.append("\\end{tabular}")
        latex_lines.append("\\end{center}")
        return "\n".join(latex_lines)

    while i < len(lines):
        if _is_rule(lines[i]):
            j = i + 1
            while j < len(lines) and not _is_rule(lines[j]):
                j += 1
            if j < len(lines):
                block = lines[i:j + 1]
                converted = _convert_block(block)
                if converted:
                    result.append(converted)
                    i = j + 1
                    continue
        result.append(lines[i])
        i += 1

    return "\n".join(result)


def clean_markdown(text: str) -> str:
    """清理 markdown 垃圾

    🆕 v1.3 改进：统一中英文标点
    🆕 v1.6.3：增强全角括号统一
    """
    # 🆕 v1.6.3：首先统一全角括号
    text = normalize_fullwidth_brackets(text)

    text = re.sub(
        r"<br><span class='markdown-page-line'>.*?</span><br><br>",
        "\n", text, flags=re.S,
    )
    text = re.sub(
        r"<span id='page\d+' class='markdown-page-text'>\[.*?\]</span>",
        "", text,
    )

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 预清理装饰性图片及其属性
    text = remove_decorative_images(text)
    text = clean_image_attributes(text)

    # 🆕 v1.3 改进：统一中英文标点
    # 保护已有的LaTeX命令
    protected = []
    def save_latex_cmd(match):
        protected.append(match.group(0))
        return f"@@LATEXCMD{len(protected)-1}@@"
    text = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', save_latex_cmd, text)

    # 统一括号（全角→半角）- 已在 normalize_fullwidth_brackets 中处理
    text = text.replace('（', '(').replace('）', ')')
    # 统一引号（弯引号→直引号）
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")

    # 恢复LaTeX命令
    for i, cmd in enumerate(protected):
        text = text.replace(f"@@LATEXCMD{i}@@", cmd)

    # 清理代码块标记
    text = re.sub(r'```[a-z]*\n?', '', text)
    text = re.sub(r'```', '', text)

    # 转换表格
    text = convert_ascii_table_blocks(text)
    if '|' in text and '---' in text:
        text = convert_markdown_table_to_latex(text)

    # 处理下划线
    text = text.replace(r'\_', '@@ESCAPED_UNDERSCORE@@')
    text = re.sub(r'(?<!\\)_(?![{_])', r'\\_', text)
    text = text.replace('@@ESCAPED_UNDERSCORE@@', r'\_')

    return text.strip()


# ==================== 题目解析函数 ====================



def clean_image_attributes(text: str) -> str:
    r"""统一清理 Markdown 图片标记中的属性块（增强版 P2-001）
    
    支持：
    - 单行属性块：{width="3in" height="2in"}
    - 跨行属性块：{width="3in"\nheight="2in"}
    - 科学计数法尺寸：{width="1.38e-2in"}
    - 孤立的 width/height 行
    - 极小图片移除（OCR 噪声）
    """
    if not text:
        return text

    # 🆕 P1-004 修复：支持跨行属性块（使用 DOTALL 标志）
    # 匹配包含科学计数法的尺寸值，如 1.3888888888888888e-2in
    attr_pattern = re.compile(
        r'\{[^{}]*(?:width|height)\s*=\s*"[^"]*"[^{}]*\}',
        re.IGNORECASE | re.DOTALL
    )
    text = attr_pattern.sub('', text)

    # 🆕 P2-001: 清理孤立的 width="..." / height="..." 行
    text = re.sub(r'^\s*(width|height)="[^"]*"\s*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    
    # 🆕 P2-001: 清理跨行的属性块
    text = re.sub(r'\{width="[^"]*"\s*\n\s*height="[^"]*"\}', '', text, flags=re.MULTILINE)
    
    # 🆕 P2-001: 清理单行完整属性块
    text = re.sub(r'\{width="[^"]*"\s+height="[^"]*"\}', '', text)
    
    # 🆕 P2-001: 清理残留的 height="..." 和 width="..."（带可能的尾随 }）
    text = re.sub(r'height="[^"]*"[}]*', '', text)
    text = re.sub(r'width="[^"]*"[}]*', '', text)
    
    # 🆕 P2-001: 移除极小图片（尺寸使用科学计数法 e-2 或更小，可能是 OCR 噪声）
    tiny_pattern = re.compile(
        r'!\[[^\]]*\]\([^)]+\)\s*\{[^}]*?(?:\d+\.?\d*e-[2-9]|\d+\.?\d*e-\d{2,})in[^}]*\}',
        re.IGNORECASE | re.DOTALL
    )
    text = tiny_pattern.sub('', text)
    
    return text




def remove_decorative_images(text: str) -> str:
    """移除极小的装饰性图片（通常是 OCR 噪声）

    检测尺寸小于 0.1in 的图片，包括科学计数法格式如:
    - 1.3888888888888888e-2in (约 0.014in)
    - 1e-3in (0.001in)
    - 0.01in, 0.001in (常规小数格式)
    """
    if not text:
        return text

    # 🆕 P1-003 修复：匹配科学计数法格式的极小尺寸（e-2, e-3 或更小）
    # 支持文件首行、行中、行尾的图片标记
    tiny_sci_pattern = re.compile(
        r'!\[[^\]]*\]\([^)]+\)\{[^}]*?(?:\d+\.?\d*e-[2-9]|\d+\.?\d*e-\d{2,})in[^}]*\}',
        re.IGNORECASE | re.DOTALL,
    )
    text = tiny_sci_pattern.sub('', text)

    # 🆕 P1-003 修复：匹配常规小数格式的极小尺寸（0.0开头）
    tiny_decimal_pattern = re.compile(
        r'!\[[^\]]*\]\([^)]+\)\{[^}]*?0\.0\d+in[^}]*\}',
        re.IGNORECASE | re.DOTALL,
    )
    text = tiny_decimal_pattern.sub('', text)

    return text




def clean_residual_image_attrs(text: str) -> str:
    r"""清理残留的图片属性块

    🆕 v1.7 增强：清理更多 Markdown 图片属性残留
    🆕 v1.6 P0 修复：清理 Pandoc 生成的图片属性
    """
    if not text:
        return text

    text = clean_image_attributes(text)

    # 清理单独成行的属性块开始
    text = re.sub(r'^\s*\{width="[^"]*"\s*$', '', text, flags=re.MULTILINE)
    # 清理单独成行的属性块结束
    text = re.sub(r'^\s*height="[^"]*"\}\s*$', '', text, flags=re.MULTILINE)

    # 清理跨行的属性块
    text = re.sub(r'\{width="[^"]*"\s*\n\s*height="[^"]*"\}', '', text, flags=re.MULTILINE)

    # 清理单行完整属性块
    text = re.sub(r'\{width="[^"]*"\s+height="[^"]*"\}', '', text)

    # 🆕 v1.7：清理残留的 height="..." 和 width="..." （带可能的尾随 }）
    text = re.sub(r'height="[^"]*"[}]*', '', text)
    text = re.sub(r'width="[^"]*"[}]*', '', text)

    return text




def fix_markdown_bold_residue(text: str) -> str:
    r"""🆕 v1.9.7：清理 Markdown 粗体残留
    
    问题来源：
    - Word 文档中某些标点被加粗，Pandoc 转换为 **，** 等
    - 预处理可能没有完全清理干净
    
    保守策略：
    - 只处理"纯标点或短文本+标点被粗体包裹"的情况
    - 不处理正常的粗体文本
    
    例如：
    - **，** → ，
    - **，得证.** → ，得证.
    - **。** → 。
    """
    import re
    
    # 模式1：纯标点被粗体包裹 **，** **。** **；** 等
    text = re.sub(r'\*\*([，。；、：！？,.;:!?])\*\*', r'\1', text)
    
    # 模式2：标点开头+短文本+标点结尾被粗体包裹
    # 例如：**，得证.** → ，得证.
    text = re.sub(r'\*\*([，。；、：,.;:][^\*]{0,10}[.．。])\*\*', r'\1', text)
    
    # 🆕 v1.9.10：将 **方法一：xxx** 转换为 \textbf{方法一：xxx}
    # 保守策略：只处理看起来像标题/方法名的粗体文本
    # 模式：**文本** 其中文本长度 > 2 且不含数学符号
    def replace_bold(m):
        content = m.group(1)
        # 跳过包含数学符号的内容（可能是数学公式粗体）
        if '\\(' in content or '\\)' in content or '$' in content:
            return m.group(0)  # 保持原样
        return r'\textbf{' + content + '}'
    
    text = re.sub(r'\*\*([^*]{2,}?)\*\*', replace_bold, text)
    
    return text




def remove_blank_lines_in_macro_args(text: str) -> str:
    """删除宏参数中的空行（增强版）"""
    macros = ['explain', 'topics', 'answer', 'difficulty', 'source']
    
    for macro in macros:
        pattern = rf'(\\{macro}\{{)([^{{}}]*(?:\{{[^{{}}]*\}}[^{{}}]*)*?)(\}})'
        
        def clean_arg(match):
            prefix = match.group(1)
            arg = match.group(2)
            suffix = match.group(3)
            
            # 改进1：删除连续空行
            arg = re.sub(r'\n\s*\n+', '\n', arg)
            
            # 改进2：删除段首段尾空行
            arg = arg.strip()
            
            # 改进3：清理行首行尾空格（保留缩进）
            lines = arg.split('\n')
            lines = [line.rstrip() for line in lines]
            arg = '\n'.join(lines)
            
            return prefix + arg + suffix
        
        text = re.sub(pattern, clean_arg, text, flags=re.DOTALL)
    
    return text



def collapse_consecutive_blank_lines(text: str, max_blank_lines: int = 1) -> str:
    """将连续空行折叠到指定数量以内（默认最多 1 行）。

    Args:
        text: 输入文本
        max_blank_lines: 允许的最大连续空行数（>=0）。
    """
    import re

    if max_blank_lines < 0:
        max_blank_lines = 0

    # 连续换行符数量超过 (max_blank_lines + 1) 时压缩
    keep_newlines = max_blank_lines + 1  # 例如允许 1 行空行 → 保留 2 个换行符
    pattern = rf'\n{{{keep_newlines + 1},}}'
    replacement = '\n' * keep_newlines
    return re.sub(pattern, replacement, text)



def remove_blank_lines_before_meta(text: str) -> str:
    """移除元信息宏 (topics/difficulty/answer/explain/source) 前多余的空行。

    避免题目末尾因为图片/环境后的空行拉开题干与元信息的距离。
    """
    import re

    pattern = r'\n\s*\n+(?=\\(topics|difficulty|answer|explain|source)\{)'
    return re.sub(pattern, '\n', text)



def remove_image_todo_blocks(text: str) -> str:
    """删除未填充的 IMAGE_TODO 占位块（避免版面留白）。"""
    import re

    # 结构：\begin{center} … % IMAGE_TODO_START … \begin{tikzpicture} … \end{tikzpicture} … % IMAGE_TODO_END … \end{center}
    pattern = re.compile(r"\n?\s*\\begin\{center\}.*?% IMAGE_TODO_START.*?% IMAGE_TODO_END.*?\\end\{center\}\s*\n?", re.DOTALL)
    return re.sub(pattern, "\n", text)




def soft_wrap_paragraph(s: str, limit: int = 80) -> str:
    """🆕 任务2：为长段落在标点处添加软换行，便于 LaTeX 报错定位

    功能：对于超过指定长度的字符串，在合适的标点位置插入换行符，
    使得每行长度不超过 limit，便于 LaTeX 编译时快速定位错误行。

    逻辑：
    - 如果字符串长度 < limit，直接返回
    - 如果较长：
      - 从头扫描，记录最近的"可拆分标点"位置（。；？！，）
      - 当当前行长度超过 limit/2 时，在最近标点后插入换行
      - 避免在 LaTeX 命令内部拆行（遇到 \\ 开头的 token 时不拆）

    Args:
        s: 输入字符串
        limit: 每行最大长度限制（默认 80）

    Returns:
        添加软换行后的字符串
    """
    if not s or len(s) < limit:
        return s

    # 可拆分的中文标点
    breakable_puncts = set('。；？！，')

    result = []
    current_line = []
    current_length = 0
    last_punct_pos = -1  # 记录当前行中最近的标点位置

    i = 0
    while i < len(s):
        char = s[i]

        # 检测 LaTeX 命令（以 \ 开头）
        if char == '\\' and i + 1 < len(s):
            # 收集完整的 LaTeX 命令
            cmd_start = i
            i += 1
            # 跳过命令名（字母）
            while i < len(s) and s[i].isalpha():
                i += 1
            # 跳过可能的参数（花括号）
            if i < len(s) and s[i] == '{':
                brace_depth = 1
                i += 1
                while i < len(s) and brace_depth > 0:
                    if s[i] == '{':
                        brace_depth += 1
                    elif s[i] == '}':
                        brace_depth -= 1
                    i += 1

            # 将整个命令作为一个单元添加
            cmd = s[cmd_start:i]
            current_line.append(cmd)
            current_length += len(cmd)
            continue

        # 检测换行符 - 保留原有换行
        if char == '\n':
            result.append(''.join(current_line))
            result.append('\n')
            current_line = []
            current_length = 0
            last_punct_pos = -1
            i += 1
            continue

        # 普通字符
        current_line.append(char)
        current_length += 1

        # 记录可拆分标点的位置
        if char in breakable_puncts:
            last_punct_pos = len(current_line) - 1

        # 检查是否需要换行
        if current_length > limit // 2 and last_punct_pos >= 0:
            # 在最近的标点后换行
            before_break = ''.join(current_line[:last_punct_pos + 1])
            after_break = current_line[last_punct_pos + 1:]

            result.append(before_break)
            result.append('\n')

            current_line = after_break
            current_length = len(after_break)
            last_punct_pos = -1

        i += 1

    # 添加剩余内容
    if current_line:
        result.append(''.join(current_line))

    return ''.join(result)





# ============================================================
# 导出列表
# ============================================================

__all__ = [
    'LATEX_SPECIAL_CHARS',
    'escape_latex_special',
    'standardize_math_symbols',
    'normalize_fullwidth_brackets',
    'convert_markdown_table_to_latex',
    'convert_ascii_table_blocks',
    'clean_markdown',
    'clean_image_attributes',
    'remove_decorative_images',
    'clean_residual_image_attrs',
    'fix_markdown_bold_residue',
    'remove_blank_lines_in_macro_args',
    'soft_wrap_paragraph',
]
