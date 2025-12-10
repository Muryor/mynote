#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
预处理 OCR 试卷 markdown（支持图片 OCR、PDF OCR 等多种来源）

主要功能：
1. 删除分页标记：<br><span class='markdown-page-line'>...</span><br><br>
2. 统一【解析】格式：去掉 # 前缀，合并空行
3. 自动插入题型分节标题（可配置）
4. 压缩连续空行（最多保留 2 行）

新增 OCR 修复功能（v2）：
5. 修复 LaTeX 命令后缺空格：\\therefore A, \\because B, \\Rightarrow x 等
6. 修复 OCR 错误的特殊符号：∳ -> ∴, ∵ 等
7. 拆分同行选项：A. xxx B. yyy -> 分行
8. 删除点评内容：点评：xxx 到下一题开始
9. 替换 \textcircled 为 LaTeX 可用格式
10. 修复 Markdown 标题前缀：# 一、选择题 -> 一、选择题
11. 删除填空题结尾的 "故答案为：XXX" 重复内容
12. 检测并报告题目顺序错乱问题
"""

import argparse
import re
import sys
from typing import List, Dict, Tuple, Optional


# ============================================================
#  正则表达式定义
# ============================================================

# 分页标记：<br><span class='markdown-page-line'> ... </span><br><br>
PAGE_MARK_RE = re.compile(
    r"<br><span class=['\"]markdown-page-line['\"][^>]*>.*?</span><br><br>",
    re.DOTALL,
)

# 解析标题：# 【解析】（1～6 级标题都算）
PARSE_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s*【解析】\s*$")

# 题号行：开头是若干空格 + 数字 + . 或 ． 然后空格
QUESTION_RE = re.compile(r"^\s*(\d+)[\.\．]\s+")

# LaTeX 命令后缺空格的模式（需要后面跟字母/数字时加空格）
LATEX_COMMANDS_NEED_SPACE = [
    r"\\therefore",
    r"\\because",
    r"\\Rightarrow",
    r"\\Leftarrow",
    r"\\Leftrightarrow",
    r"\\implies",
    r"\\iff",
    r"\\forall",
    r"\\exists",
    r"\\in",
    r"\\notin",
    r"\\subset",
    r"\\supset",
    r"\\cup",
    r"\\cap",
    r"\\land",
    r"\\lor",
    r"\\neg",
    r"\\perp",
    r"\\parallel",
]

# 选项模式：A. B. C. D. 或 A． B． 等
OPTION_PATTERN = re.compile(r"([A-D])[\.\．]\s*")

# 点评开始模式
COMMENT_START_RE = re.compile(r"^点评[：:（(]")

# 故答案为模式（用于填空题末尾清理）
ANSWER_SUFFIX_RE = re.compile(r"故答案为[：:].*?[。\.\n]?$")

# OCR 错误符号映射
OCR_SYMBOL_FIXES = {
    "∳": "∴",  # OCR 经常把 ∴ 识别成 ∳
    "．": ".",  # 全角句点 -> 半角
    "，": ",",  # 全角逗号 -> 半角（在数学公式中）
}

# 需要删除的零宽度/不可见字符
INVISIBLE_CHARS = [
    "\u200b",  # 零宽度空格 (Zero Width Space)
    "\u200c",  # 零宽度非连接符 (Zero Width Non-Joiner)
    "\u200d",  # 零宽度连接符 (Zero Width Joiner)
    "\ufeff",  # 字节顺序标记 (BOM)
    "\u00a0",  # 不间断空格 (Non-breaking space) - 保留在某些情况下可能需要
]


def remove_invisible_chars(text: str) -> str:
    """删除零宽度空格等不可见字符。"""
    for char in INVISIBLE_CHARS:
        text = text.replace(char, "")
    return text


def remove_page_markers(text: str) -> str:
    """去掉 PDF OCR 导出的分页 html 标记。"""
    return PAGE_MARK_RE.sub("", text)


# ============================================================
#  新增 OCR 修复函数
# ============================================================

def fix_latex_spacing(text: str) -> str:
    r"""
    修复 LaTeX 命令后缺少空格的问题。
    
    例如：
        $\thereforeA=B$ -> $\therefore A=B$
        $\becausex>0$ -> $\because x>0$
        $\Rightarrowf(x)$ -> $\Rightarrow f(x)$
    """
    for cmd in LATEX_COMMANDS_NEED_SPACE:
        # 匹配命令后直接跟字母或数字的情况（在 $ 内）
        pattern = re.compile(rf"({cmd})([a-zA-Z0-9])")
        text = pattern.sub(r"\1 \2", text)
    return text


def fix_ocr_symbols(text: str) -> str:
    r"""
    修复 OCR 识别错误的特殊符号。
    
    例如：
        ∳ -> ∴ (therefore)
        【锤子数学解析】 -> 【解析】
        \int a= -> a= (OCR 误识别积分符号)
        \doubleprime -> '' (二阶导数符号)
    """
    for wrong, correct in OCR_SYMBOL_FIXES.items():
        text = text.replace(wrong, correct)
    
    # 统一解析标签格式
    text = re.sub(r'【锤子数学解析】', '【解析】', text)
    text = re.sub(r'【详解】', '【解析】', text)
    
    # 修复 OCR 误识别的积分符号：\int a= 应该是 a=
    # 通常是把 a 误识别成 \int
    text = re.sub(r'\\int\s*([a-zA-Z])\s*=', r'\1=', text)
    text = re.sub(r'\\in\s*t\s*([a-zA-Z])\s*=', r'\1=', text)  # \in t a= 的情况
    
    # 修复 \doubleprime -> '' (二阶导数)
    text = text.replace(r'\doubleprime', "''")
    
    # 修复 OCR 错误把中文夹在 $ 之间：$从而$ -> 从而
    # 匹配 $纯中文$ 的模式，把它们解开
    # 注意：要避免匹配 $A$为$P(k)$ 中的 $为$（这是两个数学块之间的中文）
    # 使用负向后顾确保 $ 前面不是数学字符，使用负向前瞻确保 $ 后面不是数学字符
    # 数学字符包括：字母、数字、括号等
    math_char_before = r'[a-zA-Z0-9)\]}]'
    math_char_after = r'[a-zA-Z0-9(\[{]'
    text = re.sub(
        rf'(?<!{math_char_before})[$]([一-龥，。！？、；：""''（）【】]+)[$](?!{math_char_after})',
        r'\1',
        text
    )
    
    return text

def fix_latex_delimiters(text: str) -> str:
    r"""
    修复 OCR 识别错误的 LaTeX 分隔符。
    
    常见错误：
        \right\). -> \right.    (误把 \right. 识别成 \right\).)
        \left\(  -> \left(      (误把 \left( 识别成 \left\()
        \right\) -> \right)     (多余的反斜杠)
        \left\{  但后面用 \right\) -> 应该是 \right.
    """
    # 修复 \right\). -> \right.
    text = re.sub(r'\\right\s*\\\)\s*\.', r'\\right.', text)
    
    # 修复 \right\) 在应该用 \right. 的地方（前面是 \left\{）
    # 这种情况 \left\{...\right\) 应该变成 \left\{...\right.
    # 简化处理：如果 \right\) 不匹配 \left(，则改成 \right.
    # 这里我们用一个简单的启发式：\right\) 紧跟着句号或逗号，说明可能是错误
    text = re.sub(r'\\right\s*\\\)\s*([,，。\.\s])', r'\\right.\1', text)
    
    # 如果 \right\) 出现但没有配对的 \left(，也修复
    # 处理 \left\{ 配 \right\) 的错误 -> \left\{ 配 \right.
    # 用正则查找 \left\{....\right\) 模式
    # 这个比较复杂，暂时用简单方法：\right\) 后跟 $ 结束符
    text = re.sub(r'\\right\s*\\\)\s*(\$)', r'\\right.\1', text)
    
    return text


def fix_broken_dollar_lines(text: str) -> str:
    r"""
    修复不规范的 $ 使用。
    
    处理：
    1. 单独一行的 $ 后跟中文（如 "从而$"） -> 删除 $
    2. 单独一行的 $ 前有中文（如 "$故存在"） -> 删除 $ 并合并
    """
    lines = text.split('\n')
    result = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # 检查是否是 "中文$" 格式（$ 在行尾，前面是中文）
        if stripped.endswith('$') and not stripped.endswith('$$'):
            before_dollar = stripped[:-1].strip()
            # 如果 $ 前面是纯中文或汉字结尾，删除 $
            if before_dollar and re.search(r'[\u4e00-\u9fa5]$', before_dollar):
                line = line.replace(stripped, before_dollar)
        
        # 检查是否是 "$中文" 格式（$ 在行首，后面是中文开头）
        if stripped.startswith('$') and not stripped.startswith('$$'):
            after_dollar = stripped[1:].strip()
            # 如果 $ 后面是纯中文开头，删除 $
            if after_dollar and re.match(r'^[\u4e00-\u9fa5]', after_dollar):
                line = line.replace(stripped, after_dollar)
        
        result.append(line)
    
    return '\n'.join(result)


def fix_multiline_dollar_math(text: str) -> str:
    r"""
    修复跨行的 $ 数学公式。
    
    OCR 有时会把显示数学写成：
    $
    公式内容
    $
    
    这应该改成：
    $$
    公式内容
    $$
    """
    lines = text.split('\n')
    result = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # 检测单独一行的 $（不是 $$）
        if stripped == '$':
            # 检查这是否是多行数学的开始
            # 向后找，看是否有对应的结束 $
            j = i + 1
            math_content = []
            found_end = False
            
            while j < len(lines):
                next_stripped = lines[j].strip()
                if next_stripped == '$':
                    found_end = True
                    break
                elif next_stripped == '$$':
                    # 可能是格式混乱，不处理
                    break
                else:
                    math_content.append(lines[j])
                    j += 1
            
            if found_end and math_content:
                # 转换为 $$...$$ 格式
                result.append('$$')
                result.extend(math_content)
                result.append('$$')
                i = j + 1  # 跳过结束的 $
                continue
        
        result.append(line)
        i += 1
    
    return '\n'.join(result)


def split_inline_options(text: str) -> str:
    """
    拆分同一行内的多个选项。
    
    例如：
        A. $f(x)=1$ B. $g(x)=2$
    变成：
        A. $f(x)=1$
        B. $g(x)=2$
    
    支持多种格式：
        - A. xxx B. yyy
        - A.$xxx$ B.$yyy$
        - A．xxx B．yyy（全角）
    """
    lines = text.split("\n")
    new_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        # 跳过空行
        if not stripped:
            new_lines.append(line)
            continue
        
        # 检测是否包含选项模式（A. B. C. D.）
        # 只处理看起来像选项行的内容
        if not re.search(r'[A-D][\.\．]\s*', stripped):
            new_lines.append(line)
            continue
        
        # 使用更强的模式拆分：在 B. C. D. 前面如果有内容就拆分
        # 模式：(空格或$或)或}或中文) + (B/C/D) + (./．)
        # 改进版：找到所有 [^A]后跟 B./C./D. 的位置
        
        parts = []
        current_pos = 0
        
        # 找到所有可能的拆分点
        for match in re.finditer(r'(?<=[\s\$\)\}\u4e00-\u9fff0-9])([B-D])[\.\．]', stripped):
            if match.start() > current_pos:
                parts.append(stripped[current_pos:match.start()].strip())
                current_pos = match.start()
        
        # 添加剩余部分
        if current_pos < len(stripped):
            parts.append(stripped[current_pos:].strip())
        
        # 如果没有拆分成功，尝试另一种模式
        if len(parts) <= 1:
            # 尝试用正则直接拆分
            # 匹配模式：选项内容后跟下一个选项
            split_pattern = re.compile(r'([A-D][\.\．]\s*[^\s].*?)(?=\s+[B-D][\.\．]|$)')
            matches = split_pattern.findall(stripped)
            if matches and len(matches) > 1:
                parts = [m.strip() for m in matches if m.strip()]
        
        # 输出
        if len(parts) > 1:
            for part in parts:
                if part:
                    new_lines.append(part)
        else:
            new_lines.append(line)
    
    return "\n".join(new_lines)


def remove_comment_sections(lines: List[str]) -> List[str]:
    """
    删除点评内容：从 "点评：" 开始到下一题题号结束。
    
    点评通常出现在【解析】之后，下一道题之前。
    """
    result = []
    in_comment = False
    
    for line in lines:
        stripped = line.strip()
        
        # 检测点评开始
        if COMMENT_START_RE.match(stripped):
            in_comment = True
            continue
        
        # 检测下一题开始（结束点评）
        if in_comment and QUESTION_RE.match(stripped):
            in_comment = False
        
        # 检测分节标题开始（也结束点评）
        if in_comment and (stripped.startswith("二、") or 
                          stripped.startswith("三、") or 
                          stripped.startswith("四、") or
                          stripped.startswith("五、") or
                          stripped.startswith("## ")):
            in_comment = False
        
        if not in_comment:
            result.append(line)
    
    return result


def fix_markdown_headings(text: str) -> str:
    """
    修复 Markdown 标题前缀。
    
    # 一、选择题 -> 一、选择题
    # 深度挖掘与改编 -> 深度挖掘与改编
    """
    lines = text.split("\n")
    new_lines = []
    
    for line in lines:
        stripped = line.strip()
        # 匹配 # + 中文开头（不是【解析】）
        if re.match(r"^#{1,6}\s+[一二三四五六七八九十]、", stripped):
            # 分节标题，保留但转为 ##
            new_line = re.sub(r"^#{1,6}\s+", "## ", stripped)
            new_lines.append(new_line)
        elif re.match(r"^#{1,6}\s+(?!【解析】)", stripped):
            # 其他标题，直接去掉 #
            new_line = re.sub(r"^#{1,6}\s+", "", stripped)
            new_lines.append(new_line)
        else:
            new_lines.append(line)
    
    return "\n".join(new_lines)


def fix_textcircled(text: str) -> str:
    """
    替换 \\textcircled{数字} 为更通用的格式。
    
    \\textcircled{1} -> ①
    """
    circled_map = {
        "1": "①", "2": "②", "3": "③", "4": "④", "5": "⑤",
        "6": "⑥", "7": "⑦", "8": "⑧", "9": "⑨", "10": "⑩",
    }
    
    def replace_circled(match):
        num = match.group(1)
        return circled_map.get(num, f"({num})")
    
    text = re.sub(r"\\textcircled\{(\d+)\}", replace_circled, text)
    return text


def clean_answer_suffix(text: str) -> str:
    """
    删除填空题【解析】末尾的 "故答案为：XXX" 重复内容。
    
    这种重复通常出现在菁优网/智学网格式中。
    """
    # 在【解析】块的末尾（下一个题号之前）清理
    lines = text.split("\n")
    result = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # 检测是否是【解析】行
        if "【解析】" in line:
            result.append(line)
            i += 1
            
            # 收集解析内容直到下一题
            explain_lines = []
            while i < len(lines):
                next_line = lines[i]
                if QUESTION_RE.match(next_line.strip()):
                    break
                explain_lines.append(next_line)
                i += 1
            
            # 检查最后几行是否有 "故答案为"
            if explain_lines:
                last_idx = len(explain_lines) - 1
                # 向上找非空行
                while last_idx >= 0 and not explain_lines[last_idx].strip():
                    last_idx -= 1
                
                if last_idx >= 0:
                    last_line = explain_lines[last_idx]
                    # 如果最后一行是 "故答案为：xxx"，删除
                    if re.search(r"故答案为[：:]", last_line):
                        explain_lines[last_idx] = ""
            
            result.extend(explain_lines)
        else:
            result.append(line)
            i += 1
    
    return "\n".join(result)


def detect_question_order_issues(lines: List[str]) -> List[str]:
    """
    检测题目顺序问题并返回警告列表。
    
    例如：第4题在第3题之前，或题号不连续。
    """
    warnings = []
    qpos = find_question_lines(lines)
    
    if not qpos:
        return warnings
    
    # 按行号排序
    sorted_by_line = sorted(qpos.items(), key=lambda x: x[1])
    
    # 检查题号是否递增
    prev_num = 0
    for qnum, line_idx in sorted_by_line:
        if qnum < prev_num:
            warnings.append(
                f"⚠️ 题目顺序错乱：第{qnum}题（行{line_idx+1}）出现在第{prev_num}题之后"
            )
        elif qnum > prev_num + 1 and prev_num > 0:
            # 题号跳跃（可能是分节导致的）
            missing = list(range(prev_num + 1, qnum))
            if missing:
                warnings.append(
                    f"⚠️ 题号不连续：第{prev_num}题后跳到第{qnum}题，缺少 {missing}"
                )
        prev_num = qnum
    
    return warnings


def normalize_parse_blocks(lines: List[str]) -> List[str]:
    """
    把形如

        # 【解析】

        (1) xxx

    变成

        【解析】(1) xxx

    只在整行只包含「# + 【解析】」时触发。
    """
    out: List[str] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        if PARSE_HEADING_RE.match(line):
            # 向后找到第一行非空内容
            j = i + 1
            while j < n and lines[j].strip() == "":
                j += 1

            if j < n:
                content = lines[j].lstrip()
                # 如果本来就以【解析】开头，就直接保留那一行
                if content.startswith("【解析】"):
                    new_line = content
                else:
                    # 常见解析第一行会以 (1) / （1） 开头
                    # 不额外加空格，直接拼接
                    new_line = "【解析】" + content
                out.append(new_line)
                # 跳过 [i, j] 这些行
                i = j + 1
            else:
                # 理论上很少出现：后面没有内容
                out.append("【解析】")
                i += 1
        else:
            out.append(line)
            i += 1

    return out


def find_question_lines(lines: List[str]) -> Dict[int, int]:
    """
    扫描所有行，找到形如「数字. 题干」的题号行。

    返回：题号 -> 首次出现的行号
    """
    pos: Dict[int, int] = {}
    for idx, line in enumerate(lines):
        m = QUESTION_RE.match(line)
        if not m:
            continue

        num = int(m.group(1))

        # 简单的过滤：如果上一行是「点评」「改编」「拓展」之类，
        # 很可能是解析里的子题，不当成正式题号。
        prev_idx = idx - 1
        while prev_idx >= 0 and lines[prev_idx].strip() == "":
            prev_idx -= 1
        if prev_idx >= 0:
            prev_line = lines[prev_idx]
            if any(key in prev_line for key in ("点评", "改编", "拓展")):
                continue

        if num not in pos:
            pos[num] = idx
    return pos


def add_section_headers(
    lines: List[str],
    sections: List[Tuple[int, str]],
    disable: bool = False,
) -> List[str]:
    """
    在指定题号行之前插入分节标题。

    sections: [(起始题号, "一、选择题"), ...]
    """
    if disable or not sections:
        return lines

    qpos = find_question_lines(lines)

    # 记录：原始行号 -> 要插入的 header 列表
    insertions: Dict[int, List[str]] = {}

    for qnum, title in sections:
        if qnum in qpos:
            idx = qpos[qnum]
            insertions.setdefault(idx, []).append(f"## {title}")

    if not insertions:
        return lines

    out: List[str] = []
    for idx, line in enumerate(lines):
        if idx in insertions:
            # 在题号行之前插入标题，前后各留一空行稍微美观一点
            if out and out[-1].strip() != "":
                out.append("")
            for header in insertions[idx]:
                out.append(header)
            if line.strip() != "":
                out.append("")
        out.append(line)

    return out


def collapse_blank_lines(text: str, max_consecutive: int = 2) -> str:
    """把过多连续空行压缩到最多 max_consecutive 行。"""
    lines = text.splitlines()
    new_lines: List[str] = []
    blanks = 0
    for line in lines:
        if line.strip() == "":
            blanks += 1
            if blanks <= max_consecutive:
                new_lines.append("")
        else:
            blanks = 0
            new_lines.append(line)
    return "\n".join(new_lines)


def parse_section_args(raw_sections: List[str]) -> List[Tuple[int, str]]:
    """
    解析命令行里多次出现的 --section 选项：

        --section "1:一、选择题" --section "9:二、多选题"

    返回 [(1, "一、选择题"), (9, "二、多选题")]
    """
    sections: List[Tuple[int, str]] = []
    for item in raw_sections:
        if ":" not in item:
            raise ValueError(f"--section 参数格式应为 '数字:标题'，现在是：{item!r}")
        left, right = item.split(":", 1)
        left = left.strip()
        right = right.strip()
        if not left.isdigit():
            raise ValueError(f"--section 左边必须是题号数字，现在是：{left!r}")
        sections.append((int(left), right))
    # 按题号排序，保证从小到大插入
    sections.sort(key=lambda x: x[0])
    return sections


def preprocess_markdown(
    text: str,
    sections: List[Tuple[int, str]],
    disable_sections: bool = False,
    verbose: bool = False,
) -> Tuple[str, List[str]]:
    """
    整体预处理管线。
    
    返回：(处理后的文本, 警告列表)
    """
    warnings = []
    
    # 0. 删除零宽度空格等不可见字符（最先处理）
    text = remove_invisible_chars(text)
    
    # 1. 清理分页标记
    text = remove_page_markers(text)
    
    # 2. 修复 OCR 错误符号
    text = fix_ocr_symbols(text)
    
    # 2.3. 修复跨行的 $ 数学公式 -> $$
    text = fix_multiline_dollar_math(text)
    
    # 2.4. 修复不规范的 $ 行（中文$, $中文）
    text = fix_broken_dollar_lines(text)
    
    # 2.5. 修复 LaTeX 分隔符错误（\right\). -> \right.）
    text = fix_latex_delimiters(text)
    
    # 3. 修复 LaTeX 命令后缺空格
    text = fix_latex_spacing(text)
    
    # 4. 替换 \textcircled
    text = fix_textcircled(text)
    
    # 5. 修复 Markdown 标题前缀
    text = fix_markdown_headings(text)
    
    # 6. 拆分同行选项
    text = split_inline_options(text)
    
    # 按行处理
    lines = text.splitlines()
    
    # 7. 检测题目顺序问题
    order_warnings = detect_question_order_issues(lines)
    warnings.extend(order_warnings)
    
    # 8. 删除点评内容
    lines = remove_comment_sections(lines)
    
    # 9. 统一【解析】格式
    lines = normalize_parse_blocks(lines)
    
    # 10. 加题型分节标题
    lines = add_section_headers(lines, sections, disable=disable_sections)
    
    # 拼回字符串
    out_text = "\n".join(lines)
    
    # 11. 删除 "故答案为" 重复
    out_text = clean_answer_suffix(out_text)
    
    # 12. 压缩过多空行
    out_text = collapse_blank_lines(out_text, max_consecutive=2)
    
    return out_text, warnings


def main():
    parser = argparse.ArgumentParser(
        description="OCR 试卷 markdown 预处理脚本（支持图片 OCR、PDF OCR 等多种来源）"
    )
    parser.add_argument("input", help="输入 markdown 文件路径")
    parser.add_argument(
        "-o",
        "--output",
        help="输出 markdown 文件路径；若不指定则输出到标准输出",
    )
    parser.add_argument(
        "--section",
        action="append",
        default=None,
        metavar="SPEC",
        help=(
            "题型分节配置，可重复使用，多次指定。"
            "格式：'起始题号:标题'，例如："
            "--section '1:一、选择题' "
            "--section '9:二、多选题' "
            "--section '12:三、填空题' "
            "--section '15:四、解答题'"
        ),
    )
    parser.add_argument(
        "--no-sections",
        action="store_true",
        help="不自动插入题型分节标题（只做其他清理工作）",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="显示详细处理信息和警告",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="只检查问题，不输出处理结果",
    )

    args = parser.parse_args()

    # 默认分节（深圳中学这份试卷用的就是这一套）
    if args.section is None:
        sections = [
            (1, "一、选择题"),
            (9, "二、多选题"),
            (12, "三、填空题"),
            (15, "四、解答题"),
        ]
    else:
        sections = parse_section_args(args.section)

    with open(args.input, "r", encoding="utf-8") as f:
        text = f.read()

    processed, warnings = preprocess_markdown(
        text,
        sections=sections,
        disable_sections=args.no_sections,
        verbose=args.verbose,
    )

    # 输出警告
    if warnings:
        print("=" * 60, file=sys.stderr)
        print("预处理警告：", file=sys.stderr)
        for w in warnings:
            print(f"  {w}", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print(file=sys.stderr)

    if args.check_only:
        if warnings:
            print(f"发现 {len(warnings)} 个问题需要手动检查。", file=sys.stderr)
            sys.exit(1)
        else:
            print("检查通过，没有发现问题。", file=sys.stderr)
            sys.exit(0)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(processed)
        if args.verbose:
            print(f"✅ 已保存到 {args.output}", file=sys.stderr)
    else:
        # 直接打印到 stdout，方便管道操作
        print(processed)


if __name__ == "__main__":
    main()
