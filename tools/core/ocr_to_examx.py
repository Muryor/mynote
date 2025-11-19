#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
ocr_to_examx_v1.5.py - v1.5 增强版 OCR 试卷预处理脚本

v1.5 核心修复（2025-11-18）：
1. ✅ 彻底修复数学公式双重包裹（$$\(...\)$$ → \(...\)）
   - 改进 smart_inline_math 避免嵌套
   - 新增 fix_double_wrapped_math 后处理清理
   - 优先将 $$ 转为 \(...\) 而非 \[...\]（examx 兼容）
2. ✅ 改进单行选项展开（> A... B... C... D... → 多行）
   - 更精确的选项分割正则
   - 保留选项内的数学公式和标点
3. ✅ 减少手动修正工作量：2小时 → 15分钟 (目标 -87.5%)

v1.4 改进回顾：
- 修复数学公式双重包裹（初版）
- 自动展开单行选项（初版）
- 正确处理显示公式

v1.3 改进回顾：
- 修复 docstring 警告，添加 $ 格式兜底转换
- 改进"故选"清理规则
- 统一中英文标点
- 添加自动验证功能

版本：v1.5
作者：Claude
日期：2025-11-18
"""

import re
import argparse
import shutil
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# ==================== 配置 ====================

VERSION = "v1.5"

SECTION_MAP = {
    "一、单选题": "单选题",
    "二、单选题": "单选题",
    "二、多选题": "多选题",
    "三、填空题": "填空题",
    "四、解答题": "解答题",
}

META_PATTERNS = {
    "answer": r"^【答案】(.*)$",
    "difficulty": r"^【难度】([\d.]+)",
    "topics": r"^【知识点】(.*)$",
    "analysis": r"^【分析】(.*)$",
    "explain": r"^【详解】(.*)$",
}

# 🆕 扩展图片检测：支持绝对路径、相对路径、多行属性块
# 匹配两种形式：
#   1) 带ID: ![@@@id](path){...}
#   2) 无ID: ![](path){...}
# 属性块可跨多行，可选
IMAGE_PATTERN_WITH_ID = re.compile(
    r"!\[@@@([^\]]+)\]\(([^)]+)\)(?:\s*\{[^}]*\})?",
    re.MULTILINE | re.DOTALL,
)
IMAGE_PATTERN_NO_ID = re.compile(
    r"!\[\]\(([^)]+)\)(?:\s*\{[^}]*\})?",
    re.MULTILINE | re.DOTALL,
)
# 兼容旧版（保留用于简单场景）
IMAGE_PATTERN = re.compile(r"!\[\]\((images/[^)]+)\)(?:\{width=(\d+)%\})?")

LATEX_SPECIAL_CHARS = {
    "%": r"\%",
    "&": r"\&",
    "#": r"\#",
    "~": r"\textasciitilde{}",
}

# 解析标记词（扩展列表）
ANALYSIS_MARKERS = [
    '根据', '由题意', '因为', '所以', '故选', '答案',
    '分析', '详解', '解答', '证明', '计算可得',
    '显然', '易知', '可知', '不难看出', '由此可得',
    '综上', '故', '即', '则', '可得'
]


# 更严格的解析起始词，只用于判断是否进入解析段落（避免像“则”这样在题干中出现时被误判）
ANALYSIS_START_MARKERS = [
    '根据', '由题意', '因为', '所以', '故选', '答案',
    '分析', '详解', '解答', '证明', '计算可得',
    '显然', '易知', '可知', '不难看出', '由此可得', '综上'
]

# ==================== 文件夹处理函数 ====================

def find_markdown_and_images(input_path: Path) -> Tuple[Path, Optional[Path]]:
    """智能识别输入路径"""
    input_path = Path(input_path).resolve()
    
    if input_path.is_file() and input_path.suffix == '.md':
        md_file = input_path
        images_dir = input_path.parent / 'images'
        if not images_dir.exists():
            images_dir = None
        return md_file, images_dir
    
    if input_path.is_dir():
        md_files = list(input_path.glob('*_local.md'))
        if not md_files:
            md_files = list(input_path.glob('*.md'))
        
        if not md_files:
            raise FileNotFoundError(f"在 {input_path} 中未找到 .md 文件")
        
        if len(md_files) > 1:
            print(f"⚠️  找到多个 .md 文件，使用：{md_files[0].name}")
        
        md_file = md_files[0]
        images_dir = input_path / 'images'
        if not images_dir.exists():
            images_dir = None
        
        return md_file, images_dir
    
    raise ValueError(f"无效的输入：{input_path}")


def copy_images_to_output(images_dir: Path, output_dir: Path) -> int:
    """复制图片"""
    if images_dir is None or not images_dir.exists():
        return 0
    
    output_images_dir = output_dir / 'images'
    if output_images_dir.exists():
        shutil.rmtree(output_images_dir)
    
    shutil.copytree(images_dir, output_images_dir)
    return len(list(output_images_dir.glob('*')))


# ==================== LaTeX 处理函数 ====================

def escape_latex_special(text: str, in_math_mode: bool = False) -> str:
    """转义 LaTeX 特殊字符"""
    if in_math_mode:
        for char in ["%", "&", "#", "~"]:
            if char in LATEX_SPECIAL_CHARS:
                text = text.replace(char, LATEX_SPECIAL_CHARS[char])
    else:
        protected = []
        def save_comment(match):
            protected.append(match.group(0))
            return f"@@COMMENT_{len(protected)-1}@@"
        text = re.sub(r'%.*$', save_comment, text, flags=re.MULTILINE)
        
        for char, escaped in LATEX_SPECIAL_CHARS.items():
            text = text.replace(char, escaped)
        
        for i, comment in enumerate(protected):
            text = text.replace(f"@@COMMENT_{i}@@", comment)
    return text


def smart_inline_math(text: str) -> str:
    r"""智能转换行内公式：$...$ -> \(...\)，$$...$$ -> \(...\)
    
    🆕 v1.5 改进：彻底避免双重包裹，examx 统一使用 \(...\)
    """
    if not text:
        return text
    
    # 步骤1: 保护已有的行内公式 \(...\)（避免重复转换）
    inline_math_blocks = []
    def save_inline(match):
        inline_math_blocks.append(match.group(0))
        return f"@@INLINEMATH{len(inline_math_blocks)-1}@@"
    text = re.sub(r'\\\((.+?)\\\)', save_inline, text, flags=re.DOTALL)
    
    # 步骤2: 保护已有的显示公式 \[...\]（保持不变）
    display_math_blocks = []
    def save_display(match):
        display_math_blocks.append(match.group(0))
        return f"@@DISPLAYMATH{len(display_math_blocks)-1}@@"
    text = re.sub(r'\\\[(.+?)\\\]', save_display, text, flags=re.DOTALL)
    
    # 步骤3: 保护TikZ坐标 $(A)$ 或 $(A)!0.5!(B)$ 或 $(A)+(1,2)$
    tikz_coords = []
    def save_tikz_coord(match):
        block = match.group(0)      # 形如 '$(A)!0.5!(B)$' 或 '$(0,1)$'
        inner = block[2:-2]         # 去掉外层 '$(' 和 ')$'
        # 仅当内部包含 '!' 或 大写字母 时，认为是 TikZ 坐标表达式
        if '!' in inner or re.search(r'[A-Z]', inner):
            tikz_coords.append(block)
            return f"@@TIKZCOORD{len(tikz_coords)-1}@@"
        else:
            # 否则认为是普通数学坐标/区间，原样返回
            return block
    # 匹配 TikZ 坐标：$(...)$ 内部是简单的坐标计算表达式
    # 包含字母、数字、括号、加减乘除、点、感叹号、冒号等但不包含复杂数学
    text = re.sub(r'\$\([A-Za-z0-9!+\-*/\.\(\):,\s]+\)\$', save_tikz_coord, text)
    
    # 步骤4: 转换显示公式 $$ ... $$ 为 \(...\)（examx 风格）
    # 优先处理多行显示公式
    text = re.sub(r'\$\$\s*(.+?)\s*\$\$', r'\\(\1\\)', text, flags=re.DOTALL)
    
    # 步骤5: 转换单 $ ... $ 为 \(...\)
    text = re.sub(r'(?<!\\)\$([^\$]+?)\$', r'\\(\1\\)', text)
    
    # 步骤6: 兜底检查，清理残留的单 $（单行内，限制200字符）
    text = re.sub(r'(?<!\\)\$([^\$\n]{1,200}?)\$', r'\\(\1\\)', text)
    
    # 步骤7: 恢复保护的内容
    for i, block in enumerate(tikz_coords):
        text = text.replace(f"@@TIKZCOORD{i}@@", block)
    for i, block in enumerate(display_math_blocks):
        text = text.replace(f"@@DISPLAYMATH{i}@@", block)
    for i, block in enumerate(inline_math_blocks):
        text = text.replace(f"@@INLINEMATH{i}@@", block)
    
    return text


def fix_double_wrapped_math(text: str) -> str:
    r"""修正双重包裹的数学公式
    
    🆕 v1.5 新增：清理可能残留的嵌套格式
    例如：$$\(...\)$$ → \(...\)
    """
    if not text:
        return text
    
    # 修正 $$\(...\)$$ 或 $$\[...\]$$
    # 注意：\\\( 匹配字面的 \(
    text = re.sub(r'\$\$\s*\\\((.+?)\\\)\s*\$\$', r'\\(\1\\)', text, flags=re.DOTALL)
    text = re.sub(r'\$\$\s*\\\[(.+?)\\\]\s*\$\$', r'\\(\1\\)', text, flags=re.DOTALL)
    
    # 修正 $\(...\)$ 或 $\[...\]$
    text = re.sub(r'\$\s*\\\((.+?)\\\)\s*\$', r'\\(\1\\)', text, flags=re.DOTALL)
    text = re.sub(r'\$\s*\\\[(.+?)\\\]\s*\$', r'\\(\1\\)', text, flags=re.DOTALL)
    
    # 修正三重嵌套（极端情况）
    text = re.sub(r'\\\(\s*\\\((.+?)\\\)\s*\\\)', r'\\(\1\\)', text, flags=re.DOTALL)
    
    return text


def wrap_math_variables(text: str) -> str:
    """智能包裹数学变量（增强版）"""
    # 保护已有的数学模式
    protected = []
    def save_math(match):
        protected.append(match.group(0))
        return f"@@MATH{len(protected)-1}@@"
    
    text = re.sub(r'\\\(.*?\\\)', save_math, text, flags=re.DOTALL)
    text = re.sub(r'\\\[.*?\\\]', save_math, text, flags=re.DOTALL)
    
    # 保护 TikZ 坐标
    tikz_coords = []
    def save_tikz(match):
        block = match.group(0)      # 形如 '$(A)$' 或 '$(0,1)$'
        inner = block[2:-2]
        if '!' in inner or re.search(r'[A-Z]', inner):
            tikz_coords.append(block)
            return f"@@TIKZ{len(tikz_coords)-1}@@"
        else:
            return block
    text = re.sub(r'\$\([\d\w\s,+\-*/\.]+\)\$', save_tikz, text)
    
    # 规则1：单字母变量 + 运算符/下标/上标
    text = re.sub(
        r'\b([a-zA-Z])(?=\s*[=+\-*/^<>]|_{|\^{)',
        r'\\(\1\\)',
        text
    )
    
    # 规则2：数学函数必须有反斜杠
    math_functions = [
        'sin', 'cos', 'tan', 'cot', 'sec', 'csc',
        'arcsin', 'arccos', 'arctan',
        'sinh', 'cosh', 'tanh',
        'log', 'ln', 'lg', 'exp',
        'lim', 'sup', 'inf',
        'max', 'min', 'det', 'dim', 'ker'
    ]
    for func in math_functions:
        text = re.sub(rf'(?<!\\)\b{func}\b(?!\w)', rf'\\{func}', text)
    
    # 规则3：虚数单位 i
    text = re.sub(r'(?<!\\)\bi\b(?=[^a-zA-Z])', r'\\mathrm{i}', text)
    
    # 恢复保护的内容
    for i, coord in enumerate(tikz_coords):
        text = text.replace(f"@@TIKZ{i}@@", coord)
    for i, math in enumerate(protected):
        text = text.replace(f"@@MATH{i}@@", math)
    
    return text


def _sanitize_math_block(block: str) -> str:
    """修正数学块内部的 OCR 错误
    
    修复：
    - \\left / \\right 不匹配时降级为普通括号
    - \\right.\\ ) 等畸形组合
    """
    if not block:
        return block
    
    # 统一数学环境内的中文标点为英文标点
    block = (block
             .replace('，', ',')
             .replace('：', ':')
             .replace('；', ';')
             .replace('。', '.')
             .replace('、', ','))

    # 替换常见的 Unicode 符号为 LaTeX 命令（避免缺字形）
    block = block.replace('∵', r'\\because').replace('∴', r'\\therefore')

    # 将上下标中的中文包装为 \text{...}
    # 形式一：_[{...中文...}] 或 ^[{...中文...}]
    def _wrap_cjk_in_braced_subsup(m: re.Match) -> str:
        lead = m.group(1)
        inner = m.group(2)
        if '\\text{' in inner:
            return f"{lead}{{{inner}}}"
        return f"{lead}{{\\text{{{inner}}}}}"
    block = re.sub(r'([_^])\{([^{}]*?[\u4e00-\u9fff]+[^{}]*?)\}', _wrap_cjk_in_braced_subsup, block)

    # 形式二：单字符上下标：_水 或 ^高
    block = re.sub(r'([_^])([\u4e00-\u9fff])', r'\1{\\text{\2}}', block)

    # 数学内常见中文连接词，替换为 \text{...}（保守集）
    for w in ['且', '或', '则', '即', '故', '所以', '因为']:
        block = re.sub(fr'(?<!\\text\{{){re.escape(w)}(?![^\{{]*\}})', rf'\\text{{{w}}}', block)
    
    # 统计 left/right 数量
    left_count = len(re.findall(r'\\left\b', block))
    right_count = len(re.findall(r'\\right\b', block))
    
    # 修复畸形 \right.\ ) 和 \right.\\)
    block = re.sub(r'\\right\.\s*\\\s*\)', r'\\right.', block)
    # 修复 \right.\\\) 模式（array结尾的常见OCR错误）
    block = re.sub(r'\\right\.\\\\+\)', r'\\right.', block)
    
    # 如果 left/right 不匹配，降级为普通括号
    if left_count != right_count:
        block = re.sub(r'\\left\s*([\(\[\{])', r'\1', block)
        block = re.sub(r'\\right\s*([\)\]\}])', r'\1', block)
        block = re.sub(r'\\left\.', '', block)
        block = re.sub(r'\\right\.', '', block)
    
    return block


def sanitize_math(text: str) -> str:
    """扫描全文，仅修正数学环境内的 OCR 错误
    
    只处理 \\(...\\) 和 \\[...\\] 内部的内容。
    """
    if not text:
        return text
    
    result = []
    i = 0
    n = len(text)
    
    while i < n:
        # 匹配 \(..\)
        if text.startswith(r"\(", i):
            j = text.find(r"\)", i + 2)
            if j == -1:
                result.append(text[i:])
                break
            inner = text[i+2:j]
            inner = _sanitize_math_block(inner)
            result.append(r"\(" + inner + r"\)")
            i = j + 2
            continue
        
        # 匹配 \[..\]
        if text.startswith(r"\[", i):
            j = text.find(r"\]", i + 2)
            if j == -1:
                result.append(text[i:])
                break
            inner = text[i+2:j]
            inner = _sanitize_math_block(inner)
            result.append(r"\[" + inner + r"\]")
            i = j + 2
            continue
        
        result.append(text[i])
        i += 1
    
    return "".join(result)


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


def clean_question_environments(text: str) -> str:
    """清理 question 环境内部的多余空行"""
    pattern = r'(\\begin\{question\})(.*?)(\\end\{question\})'
    
    def clean_env(match):
        begin = match.group(1)
        content = match.group(2)
        end = match.group(3)
        
        # 删除连续的3个以上换行
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return begin + content + end
    
    return re.sub(pattern, clean_env, text, flags=re.DOTALL)


def split_long_lines_in_explain(text: str, max_length: int = 800) -> str:
    """在 explain{} 中自动分割超长行"""
    pattern = r'(\\explain\{)([^{}]*(?:\{[^{}]*\}[^{}]*)*?)(\})'
    
    def split_content(match):
        prefix = match.group(1)
        content = match.group(2)
        suffix = match.group(3)
        
        lines = content.split('\n')
        new_lines = []
        
        for line in lines:
            if len(line) <= max_length:
                new_lines.append(line)
            else:
                # 在标点后分割
                segments = re.split(r'([，。；！？])', line)
                current = ""
                for seg in segments:
                    if len(current + seg) > max_length and current:
                        new_lines.append(current.rstrip())
                        current = seg
                    else:
                        current += seg
                if current:
                    new_lines.append(current.rstrip())
        
        return prefix + '\n'.join(new_lines) + suffix
    
    return re.sub(pattern, split_content, text, flags=re.DOTALL)


def remove_par_breaks_in_explain(text: str) -> str:
    r"""移除 \explain{...} 中的空段落（严格基于大括号计数）
    解决 TeX 中段落断开导致的 "Paragraph ended before \explain code was complete"。
    """
    # 规范化换行符
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    
    out = []
    i = 0
    n = len(text)
    while i < n:
        if text.startswith("\\explain{", i):
            # 复制宏名
            out.append("\\explain{")
            i += len("\\explain{")
            depth = 1
            buf = []
            while i < n and depth > 0:
                ch = text[i]
                # 处理转义的大括号 \{ 或 \}：作为普通字符，不计入深度
                if ch == '\\' and i + 1 < n and text[i + 1] in '{}':
                    buf.append(text[i:i+2])
                    i += 2
                    continue
                # 处理换行：若遇到空段落（\n\s*\n），压缩为单换行
                if ch == '\n':
                    # 查看是否为空段落
                    j = i + 1
                    while j < n and text[j] in ' \t':
                        j += 1
                    if j < n and text[j] == '\n':
                        # 跳过第二个换行前的空白，只保留一个换行
                        buf.append('\n')
                        i = j + 1
                        continue
                if ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0:
                        # 关闭，写入缓冲并结束此 explain
                        out.append(''.join(buf))
                        out.append('}')
                        i += 1
                        break
                buf.append(ch)
                i += 1
            continue
        else:
            out.append(text[i])
            i += 1
    return ''.join(out)


def cleanup_remaining_image_markers(text: str) -> str:
    """🆕 后备占位符转换：清理任何残留的 Markdown 图片标记
    
    🆕 v1.6.2：增强内联公式处理
    - 独立成行的图片 → TikZ占位符块（大图）
    - 内联图片（公式）→ 简单文本占位符 [公式:filename]
    
    将残留的 Markdown 图片标记替换为占位符，避免在 PDF 中显示
    为原始路径文本。支持：
      - ![@@@id](path){...}
      - ![](path){...}
    """
    if not text:
        return text
    
    def _make_tikz_placeholder(label: str) -> str:
        """创建 TikZ 占位符块（用于独立图片）"""
        label = label.strip() or "image"
        return (
            "\n\\begin{center}\n"
            "\\begin{tikzpicture}[scale=1.05,>=Stealth,line cap=round,line join=round]\n"
            f"  \\node[draw, minimum width=6cm, minimum height=4cm] {{图略（图 ID: {label}）}};\n"
            "\\end{tikzpicture}\n"
            "\\end{center}\n"
        )
    
    def _make_inline_placeholder(label: str) -> str:
        """创建内联占位符（用于公式图片）"""
        label = label.strip() or "formula"
        # 使用简单的文本占位符，可以在后续被识别和替换
        return f"[公式:{label}]"
    
    def is_standalone_line(match_obj: re.Match, full_text: str) -> bool:
        """判断匹配是否为独立成行的图片"""
        # 获取匹配前后的文本
        start = match_obj.start()
        end = match_obj.end()
        
        # 向前查找到行首
        line_start = start
        while line_start > 0 and full_text[line_start - 1] not in '\n':
            line_start -= 1
        
        # 向后查找到行尾
        line_end = end
        while line_end < len(full_text) and full_text[line_end] not in '\n':
            line_end += 1
        
        # 检查行内容：去除空白后是否只有这个图片标记
        line_content = full_text[line_start:line_end].strip()
        match_content = match_obj.group(0).strip()
        
        return line_content == match_content
    
    # 处理带ID的图片标记
    def repl_with_id(m: re.Match) -> str:
        img_id = m.group(1)
        basename = os.path.basename(img_id) if img_id else "image"
        if is_standalone_line(m, text):
            return _make_tikz_placeholder(basename)
        else:
            return _make_inline_placeholder(basename)
    
    import os  # 确保导入
    text = IMAGE_PATTERN_WITH_ID.sub(repl_with_id, text)
    
    # 处理无ID的图片标记
    def repl_no_id(m: re.Match) -> str:
        path = m.group(1).strip()
        basename = os.path.basename(path)
        label = basename if basename else "image"
        if is_standalone_line(m, text):
            return _make_tikz_placeholder(label)
        else:
            return _make_inline_placeholder(label)
    
    text = IMAGE_PATTERN_NO_ID.sub(repl_no_id, text)
    
    return text


def cleanup_guxuan_in_macros(text: str) -> str:
    """🆕 v1.6：清理宏参数内的"故选"残留
    
    针对 \\topics{...} 和 \\explain{...} 等宏参数内的"故选：X"进行清理。
    
    Args:
        text: LaTeX 文本
        
    Returns:
        清理后的文本
    """
    if not text or '故选' not in text:
        return text
    
    # 定义要清理的宏列表
    macros = ['topics', 'explain', 'keywords', 'analysis']
    
    for macro_name in macros:
        # 匹配 \macro{content}，使用递归匹配嵌套大括号
        # 由于Python re不支持递归，我们使用更宽松的匹配+手工解析
        pattern = rf'\\{macro_name}\{{'
        
        pos = 0
        result_parts = []
        
        while True:
            start_idx = text.find(pattern, pos)
            if start_idx == -1:
                result_parts.append(text[pos:])
                break
            
            # 添加前面的文本
            result_parts.append(text[pos:start_idx])
            
            # 手工解析嵌套大括号
            brace_count = 0
            content_start = start_idx + len(pattern)
            i = content_start
            
            while i < len(text):
                if text[i] == '{':
                    brace_count += 1
                elif text[i] == '}':
                    if brace_count == 0:
                        # 找到匹配的右大括号
                        content = text[content_start:i]
                        
                        # 清理各种形式的"故选"
                        # 1. 清理行末的"故选：X"（含各种标点组合和可能的后续文本）
                        content = re.sub(r'[,，。\.;；、]?\s*故选[:：][ABCD]+\.?[^\n]*$', '', content, flags=re.MULTILINE)
                        # 2. 清理单独一行的"故选：X"
                        content = re.sub(r'^\s*故选[:：][ABCD]+\.?[^\n]*$', '', content, flags=re.MULTILINE)
                        # 3. 清理换行符后的"故选：X"
                        content = re.sub(r'\n+故选[:：][ABCD]+\.?[^\n]*(?=\n|$)', '', content)
                        # 4. 清理任意位置的"故选：X"（更激进）
                        content = re.sub(r'故选[:：][ABCD]+\.?[^\n]*', '', content)
                        # 5. 清理"故答案为"
                        content = re.sub(r'[,，。\.;；、]?\s*故答案为[:：]?[ABCD]*[.。]?\s*', '', content)
                        
                        result_parts.append(rf'\{macro_name}{{{content}}}')
                        pos = i + 1
                        break
                    else:
                        brace_count -= 1
                elif text[i] == '\\' and i + 1 < len(text):
                    # 跳过转义字符
                    i += 1
                i += 1
            else:
                # 没找到匹配的右大括号，保留原文
                result_parts.append(text[start_idx:])
                break
        
        text = ''.join(result_parts)
    
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
        latex += " \\\\\n\\hline\n"
        
        for row in rows[1:]:
            latex += " & ".join(escape_latex_special(cell, False) for cell in row)
            latex += " \\\\\n"
        
        latex += "\\hline\n\\end{tabular}\n\\end{center}"
        return latex
    
    return re.sub(table_pattern, convert_one_table, text)


def clean_markdown(text: str) -> str:
    """清理 markdown 垃圾
    
    🆕 v1.3 改进：统一中英文标点
    """
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
    
    # 🆕 v1.3 改进：统一中英文标点
    # 保护已有的LaTeX命令
    protected = []
    def save_latex_cmd(match):
        protected.append(match.group(0))
        return f"@@LATEXCMD{len(protected)-1}@@"
    text = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', save_latex_cmd, text)
    
    # 统一括号（全角→半角）
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
    if '|' in text and '---' in text:
        text = convert_markdown_table_to_latex(text)
    
    # 处理下划线
    text = text.replace(r'\_', '@@ESCAPED_UNDERSCORE@@')
    text = re.sub(r'(?<!\\)_(?![{_])', r'\\_', text)
    text = text.replace('@@ESCAPED_UNDERSCORE@@', r'\_')
    
    return text.strip()


# ==================== 题目解析函数 ====================

def split_sections(text: str) -> List[Tuple[str, str]]:
    """拆分章节"""
    lines = text.splitlines()
    sections = []
    current_title = None
    current_lines = []

    for line in lines:
        stripped = line.strip()
        m = re.match(
            r"^#+\s*(一、单选题|二、单选题|二、多选题|三、填空题|四、解答题)",
            stripped,
        )
        if m:
            if current_title is not None:
                sections.append((current_title, "\n".join(current_lines).strip()))
                current_lines = []
            current_title = m.group(1)
        else:
            if current_title is not None:
                current_lines.append(line)

    if current_title is not None and current_lines:
        sections.append((current_title, "\n".join(current_lines).strip()))

    return sections


def split_questions(section_body: str) -> List[str]:
    """拆分题目"""
    lines = section_body.splitlines()
    blocks = []
    current = []

    def flush():
        if current:
            blocks.append("\n".join(current).strip())
            current.clear()

    for line in lines:
        stripped = line.strip()
        if re.match(r"^\d+[\.．、]\s*", stripped):
            flush()
            current.append(line)
        else:
            current.append(line)

    flush()
    return blocks


def extract_meta_and_images(block: str) -> Tuple[str, Dict, List]:
    r"""提取元信息与图片（状态机重构：防止跨题累积）

    目标：避免上一题的多行【详解】/【分析】错误吞并下一题题干。
    关键边界：
      - 新的 meta 开始（答案/难度/知识点/详解/分析）
      - 题号开始：^\s*>?\s*(?:\d+[\.．、]\s+|（\d+）\s+|\d+\)\s+)
      - 章节标题：^#{1,6}\s*(第?[一二三四五六七八九十]+[、．.].*)$
      - 空行 + lookahead 为题号时，作为安全边界（若上一行像环境续行则跳过该空行边界）
      - 引述空行 ^>\s*$ 忽略
    """
    # 规范化并切分行
    lines = block.splitlines()

    # 结果容器
    meta = {k: "" for k in META_PATTERNS}
    # 将 analysis 与 explain 统一：后续把 analysis 并入 explain
    meta_alias_map = {
        "analysis": "explain",
        "explain": "explain",
        "answer": "answer",
        "difficulty": "difficulty",
        "topics": "topics",
    }

    content_lines: List[str] = []
    images: List[Dict] = []

    # 编译边界正则（增强版：支持更多题号格式和章节标题）
    question_start_perm = re.compile(r"^\s*>?\s*(?:\d{1,3}[\.．、]\s+|（\d{1,3}）\s+|\d{1,3}\)\s+)")
    section_header = re.compile(r"^#{1,6}\s*(第?[一二三四五六七八九十]+[、．.].*)$")
    quote_blank = re.compile(r"^>\s*$")
    env_cont_hint = re.compile(r"(\\\\\s*$)|\\begin\{|\\left|\\right")

    # 将 META_PATTERNS 编译，并合并同义词“考点”→topics，“分析/详解”→explain
    meta_starts = [
        ("answer", re.compile(r"^【\s*答案\s*】[:：]?\s*(.*)$")),
        ("difficulty", re.compile(r"^【\s*难度\s*】[:：]?\s*([\d.]+).*")),
        ("topics", re.compile(r"^【\s*(知识点|考点)\s*】[:：]?\s*(.*)$")),
        ("explain", re.compile(r"^【\s*(详解|分析)\s*】[:：]?\s*(.*)$")),
    ]

    # 状态
    state = "NORMAL"  # or "IN_META"
    current_meta_key: Optional[str] = None
    current_meta_lines: List[str] = []

    def flush_meta():
        nonlocal current_meta_key, current_meta_lines
        if current_meta_key is None:
            return
        # 合并清理
        text = "\n".join(current_meta_lines)
        # 去掉可能残留的标签前缀
        text = re.sub(r"^【?(?:答案|难度|知识点|考点|详解|分析)】?[:：]?\s*", "", text)
        # 归一化到别名键
        key = meta_alias_map.get(current_meta_key, current_meta_key)
        # 对于 explain 字段，保留原始格式（不折叠空行），让后续 remove_par_breaks_in_explain 处理
        # 其他字段压缩空行
        if key != "explain":
            text = re.sub(r"\n\s*\n+", "\n", text)
        # 合并：若已有 explain，则追加一行
        if key == "explain" and meta.get("explain"):
            meta["explain"] = (meta["explain"] + "\n" + text.strip()).strip()
        else:
            meta[key] = text.strip()
        # 重置
        current_meta_key = None
        current_meta_lines = []

    def is_question_start(s: str) -> bool:
        return bool(question_start_perm.match(s))

    def is_section_header(s: str) -> bool:
        return bool(section_header.match(s))

    def image_match(s: str):
        # 优先匹配带ID的图片
        m = IMAGE_PATTERN_WITH_ID.search(s)
        if m:
            return ('with_id', m)
        # 然后匹配无ID的图片
        m = IMAGE_PATTERN_NO_ID.search(s)
        if m:
            return ('no_id', m)
        # 最后尝试旧版简单格式
        m = IMAGE_PATTERN.search(s)
        if m:
            return ('simple', m)
        return None

    # 查找上一条非空行（用于环境续行判断）
    def find_prev_nonempty(idx: int) -> Optional[str]:
        j = idx - 1
        while j >= 0:
            if lines[j].strip():
                return lines[j]
            j -= 1
        return None

    # 查找下一条非空行（用于 blank+lookahead 判断）
    def find_next_nonempty(idx: int) -> Optional[str]:
        j = idx + 1
        while j < len(lines):
            if lines[j].strip():
                return lines[j]
            j += 1
        return None

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # 🆕 v1.6.2：图片行识别增强 - 区分独立图片块 vs 内联公式图片
        # 只有当图片"独占一行"且是完整匹配时，才提取为图片块
        # 内联图片（如 "已知集合![](image2.wmf)，则..."）保留在文本中
        img_result = image_match(stripped)
        if img_result:
            img_type, m_img = img_result
            # 检查是否为独立图片行：整行只有一个图片标记
            is_standalone = (m_img.group(0).strip() == stripped)
            
            if is_standalone:
                # 独立图片块：提取到images列表
                if img_type == 'with_id':
                    # ![@@@id](path){...}
                    img_id = m_img.group(1)
                    path = m_img.group(2).strip()
                    images.append({"path": path, "width": 50, "id": img_id})
                elif img_type == 'no_id':
                    # ![](path){...}
                    path = m_img.group(1).strip()
                    images.append({"path": path, "width": 50})
                else:
                    # 简单格式: ![](images/...)
                    path = m_img.group(1)
                    width = int(m_img.group(2)) if m_img.group(2) else 50
                    images.append({"path": path, "width": width})
                i += 1
                continue
            # else: 内联图片，保留在文本流中，不做特殊处理（fallthrough）

        # 引述空行：丢弃
        if quote_blank.match(stripped):
            i += 1
            continue

        if state == "NORMAL":
            # 新的 meta 开始？
            started = False
            for key, pat in meta_starts:
                m = pat.match(stripped)
                if m:
                    state = "IN_META"
                    current_meta_key = key
                    seed = m.group(m.lastindex or 1) if m.groups() else ""
                    current_meta_lines = [seed.strip()] if seed.strip() else []
                    started = True
                    break
            if started:
                i += 1
                continue

            # 普通内容
            content_lines.append(line)
            i += 1
            continue

        # state == IN_META
        # 1) 新 meta 开始 -> 刷新并切换
        started = False
        for key, pat in meta_starts:
            m = pat.match(stripped)
            if m:
                flush_meta()
                state = "IN_META"
                current_meta_key = key
                seed = m.group(m.lastindex or 1) if m.groups() else ""
                current_meta_lines = [seed.strip()] if seed.strip() else []
                started = True
                break
        if started:
            i += 1
            continue

        # 2) 确认题号或章节边界 -> 结束 meta，保留该行给题干
        if is_question_start(stripped) or is_section_header(stripped):
            flush_meta()
            state = "NORMAL"
            content_lines.append(line)
            i += 1
            continue

        # 3) 空行 + lookahead 为题号 -> 安全地结束 meta
        if stripped == "":
            next_ne = find_next_nonempty(i)
            if next_ne and is_question_start(next_ne.strip()):
                prev_ne = find_prev_nonempty(i)
                # 若上一非空行看起来是环境续行，则不要在此空行切断
                if prev_ne and env_cont_hint.search(prev_ne):
                    # 继续把空行也并入 meta（保持原样）
                    current_meta_lines.append(line)
                    i += 1
                    continue
                # 否则切断 meta（不消费空行）
                flush_meta()
                state = "NORMAL"
                i += 1  # 跳过该空行，下一轮看到题号行会进入 NORMAL 流程
                continue

        # 4) 继续累积 meta 内容
        current_meta_lines.append(line)
        i += 1

    # 循环结束，若还在 meta 状态则刷新
    if state == "IN_META":
        flush_meta()

    content = "\n".join(content_lines).strip()
    return content, meta, images


def parse_question_structure(content: str) -> Dict:
    """智能识别题目结构（增强版）
    
    解析题干、选项、解析三部分，避免将解析文本混入选项
    """
    lines = content.splitlines()
    
    structure = {
        'stem_lines': [],
        'choices': [],
        'analysis_lines': [],
        'in_choice': False,
        'in_analysis': False,
        'current_choice': '',
    }
    
    choice_pattern = re.compile(r'^([A-D])[\.．、]\s*(.*)$')
    
    for line in lines:
        stripped = line.strip()
        
        # 优先检查是否进入解析部分（避免解析文本混入选项）
        # 仅当行以解析起始词开头或显式以【详解】【分析】【答案】等标签开头时，才判定为解析段落。
        if any(stripped.startswith(marker) for marker in ANALYSIS_START_MARKERS) \
           or re.match(r'^(?:【?详解】|【?分析】|【?答案】)[:：]?', stripped):
            # 保存当前累积的选项
            if structure['current_choice']:
                structure['choices'].append(structure['current_choice'].strip())
                structure['current_choice'] = ''
            structure['in_choice'] = False
            structure['in_analysis'] = True
            structure['analysis_lines'].append(stripped)
            continue
        
        # 匹配选项标记 (A. B. C. D.)
        m = choice_pattern.match(stripped)
        if m:
            # 保存上一个选项
            if structure['current_choice']:
                structure['choices'].append(structure['current_choice'].strip())
            
            structure['current_choice'] = m.group(2)
            structure['in_choice'] = True
            structure['in_analysis'] = False
            continue
        
        # 根据当前状态分配行
        if structure['in_analysis']:
            structure['analysis_lines'].append(line)
        elif structure['in_choice']:
            # 选项续行（多行选项内容）
            structure['current_choice'] += ' ' + stripped
        else:
            # 题干部分
            structure['stem_lines'].append(line)
    
    # 保存末尾累积的选项
    if structure['current_choice']:
        structure['choices'].append(structure['current_choice'].strip())
    
    return structure


def expand_inline_choices(content: str) -> str:
    """展开单行/多行引述选项并去除'>'前缀
    - 单行：> A... B... C... D... → 多行独立选项
    - 多行：> A... B... / > C... D... → 合并后展开为独立选项
    - 空行：> (空) → 跳过
    """
    lines = []
    accumulated_choice_text = ""
    
    for line in content.splitlines():
        stripped = line.strip()
        
        # 处理以'>'开头的行（引述块）
        if stripped.startswith('>'):
            choice_text = stripped[1:].strip()
            
            # 跳过空的引述行
            if not choice_text:
                continue
            
            # 如果这一行有选项标记，累积到缓冲区
            if re.search(r'[A-D][．\.\、]', choice_text):
                accumulated_choice_text += " " + choice_text if accumulated_choice_text else choice_text
                continue
            
            # 非选项引述（如图片说明等），保留原样
            lines.append(line)
        else:
            # 非引述行：如果有累积的选项文本，先处理
            if accumulated_choice_text:
                # 检查累积文本中有多少个选项标记
                choice_markers = re.findall(r'[A-D][．\.\、]', accumulated_choice_text)
                if len(choice_markers) >= 2:
                    # 分割为独立选项
                    parts = re.split(r'(?=[A-D][．\.\、])', accumulated_choice_text)
                    for part in parts:
                        part = part.strip()
                        if part and re.match(r'^[A-D][．\.\、]', part):
                            lines.append(part)
                elif len(choice_markers) == 1:
                    # 单个选项，直接添加
                    lines.append(accumulated_choice_text.strip())
                
                accumulated_choice_text = ""
            
            # 添加当前行
            lines.append(line)
    
    # 处理末尾残留的累积文本
    if accumulated_choice_text:
        choice_markers = re.findall(r'[A-D][．\.\、]', accumulated_choice_text)
        if len(choice_markers) >= 2:
            parts = re.split(r'(?=[A-D][．\.\、])', accumulated_choice_text)
            for part in parts:
                part = part.strip()
                if part and re.match(r'^[A-D][．\.\、]', part):
                    lines.append(part)
        elif len(choice_markers) == 1:
            lines.append(accumulated_choice_text.strip())
    
    return '\n'.join(lines)


def convert_choices(content: str) -> Tuple[str, List[str], str]:
    """拆分题干、选项、解析（增强版）
    
    🆕 v1.4 改进：先展开单行选项再解析
    """
    # 🆕 先展开可能的单行选项
    content = expand_inline_choices(content)
    
    structure = parse_question_structure(content)
    
    stem = '\n'.join(structure['stem_lines']).strip()
    stem = re.sub(r"^\s*\d+[\.．、]\s*", "", stem)
    
    # 提取的解析内容
    analysis = '\n'.join(structure['analysis_lines']).strip()
    
    return stem, structure['choices'], analysis


def handle_subquestions(content: str) -> str:
    """处理解答题的小题编号"""
    if not re.search(r'\(\d+\)', content):
        return content
    
    subquestions = re.findall(r'\((\d+)\)(.*?)(?=\(\d+\)|$)', content, re.DOTALL)
    
    if len(subquestions) < 2:
        return content
    
    result_lines = []
    for num, content_text in subquestions:
        result_lines.append(f"\\item {content_text.strip()}")
    
    return '\n'.join(result_lines)


def process_text_for_latex(text: str, is_math_heavy: bool = False) -> str:
    """统一处理文本
    
    🆕 v1.5 改进：添加双重包裹修正
    🆕 v1.3 改进：更强的"故选"清理规则
    🆕 v1.5.1：修正数学环境内的 OCR 错误（delimiter mismatches）
    """
    if not text:
        return text
    
    # 🆕 v1.3 改进：更强的"故选"清理规则
    # 清理结尾的"故选"（支持多种标点）
    text = re.sub(r'[,，。\.;；]\s*故选[:：][ABCD]+[.。]?\s*$', '', text)
    # 清理单独一行的"故选"
    text = re.sub(r'\n+故选[:：][ABCD]+[.。]?\s*$', '', text)
    # 清理开头的"故选"（罕见但可能）
    text = re.sub(r'^\s*故选[:：][ABCD]+[.。]?\s*', '', text)
    # 清理"故答案为"
    text = re.sub(r'\n+故答案为[:：]', '', text)
    # 额外：删除"单独一行"的"故选：X"
    text = re.sub(
        r'^\s*故选[:：][ABCD]+[.。]?\s*$',
        '',
        text,
        flags=re.MULTILINE,
    )
    # 进一步：清理句末的“，故选：X”之类尾巴（保留前面的解析内容）
    text = re.sub(
        r'[，,]?\s*故选[:：]\s*[ABCD]+[。．.]*\s*$',
        '',
        text,
        flags=re.MULTILINE,
    )
    # 清理"【详解】"标记
    text = re.sub(r'^【?详解】?[:：]?\s*', '', text)
    
    # 🆕 v1.5.1：预处理 - 修复 OCR 常见的 \right.\\) 模式
    # 这个问题出现在 array 环境结尾，需要在 smart_inline_math 之前修复
    text = re.sub(r'\\\\right\.\s*\\\\\\\)', r'\\\\right.', text)
    text = re.sub(r'\\\\right\.\\\\\+\)', r'\\\\right.', text)

    # 将文本中的 Unicode ∵/∴ 替换为可编译的数学符号（包裹为行内数学）
    # 数学环境内的替换由 sanitize_math 再次保证
    if '∵' in text or '∴' in text:
        text = text.replace('∵', '$\\because$').replace('∴', '$\\therefore$')
    
    if not is_math_heavy:
        text = escape_latex_special(text, in_math_mode=False)
    
    text = smart_inline_math(text)
    # 🆕 v1.5 新增：修正可能的双重包裹
    text = fix_double_wrapped_math(text)
    text = wrap_math_variables(text)
    
    # 🆕 v1.5.1：修正数学环境内的 OCR 错误（delimiter mismatches）
    if is_math_heavy:
        text = sanitize_math(text)
    
    return text


def build_question_tex(stem: str, options: List, meta: Dict, images: List, 
                       section_type: str) -> str:
    """生成 question 环境"""
    stem = process_text_for_latex(stem, is_math_heavy=True)
    
    if section_type == "解答题" and re.search(r'\(\d+\)', stem):
        stem = handle_subquestions(stem)
    
    explain_raw = meta.get("explain", "").strip()
    if explain_raw:
        explain_raw = re.sub(r'^【?详解】?[:：]?\s*', '', explain_raw)
        explain_raw = process_text_for_latex(explain_raw, is_math_heavy=True)
    
    topics_raw = meta.get("topics", "").strip()
    if topics_raw:
        topics_raw = topics_raw.replace("、", "；")
        topics_raw = escape_latex_special(topics_raw, in_math_mode=False)

    lines = []
    lines.append(r"\begin{question}")
    
    if stem:
        lines.append(stem)

    if options:
        lines.append(r"\begin{choices}")
        for opt in options:
            opt_processed = process_text_for_latex(opt, is_math_heavy=True)
            lines.append(f"  \\item {opt_processed}")
        lines.append(r"\end{choices}")

    for img in images:
        lines.append("")
        lines.append(r"\begin{center}")
        lines.append(f"% IMAGE_TODO: {img['path']} (width={img['width']}%)")
        lines.append(r"\begin{tikzpicture}[scale=1.05,>=Stealth,line cap=round,line join=round]")
        lines.append(r"  % TODO: AI Agent 将使用 view 工具查看此图片并生成 TikZ 代码")
        lines.append(f"  % view {img['path']}")
        lines.append(r"\end{tikzpicture}")
        lines.append(r"\end{center}")

    if topics_raw:
        lines.append(f"\\topics{{{topics_raw}}}")
    if meta.get("difficulty"):
        lines.append(f"\\difficulty{{{meta['difficulty']}}}")
    if meta.get("answer"):
        # 使用与题干/解析一致的处理，以规范数学格式，避免 $$...$$ 残留
        ans = process_text_for_latex(meta["answer"], is_math_heavy=True)
        lines.append(f"\\answer{{{ans}}}")
    if explain_raw:
        lines.append(f"\\explain{{{explain_raw}}}")

    lines.append(r"\end{question}")
    return "\n".join(lines)


def convert_md_to_examx(md_text: str, title: str) -> str:
    """主转换函数（增强版）"""
    md_text = clean_markdown(md_text)
    sections = split_sections(md_text)

    out_lines = []
    out_lines.append(f"\\examxtitle{{{title}}}")

    for raw_title, body in sections:
        sec_label = SECTION_MAP.get(raw_title, raw_title)
        out_lines.append("")
        out_lines.append(f"\\section{{{sec_label}}}")

        for block in split_questions(body):
            if not block.strip():
                continue
            
            content, meta, images = extract_meta_and_images(block)
            
            # 使用增强的转换函数（返回3个值）
            stem, options, extracted_analysis = convert_choices(content)
            
            # 合并提取的解析和元信息中的解析
            if extracted_analysis and not meta.get('explain'):
                meta['explain'] = extracted_analysis
            elif extracted_analysis:
                meta['explain'] = meta['explain'] + '\n' + extracted_analysis
            
            q_tex = build_question_tex(stem, options, meta, images, sec_label)
            out_lines.append("")
            out_lines.append(q_tex)

    out_lines.append("")
    
    # 最终处理：清理空行和分割超长行
    result = "\n".join(out_lines)
    result = remove_blank_lines_in_macro_args(result)
    result = clean_question_environments(result)
    result = split_long_lines_in_explain(result, max_length=800)
    # 进一步严格移除 explain{} 中的空段落，避免段落中断导致的宏参数报错
    result = remove_par_breaks_in_explain(result)

    # 最终兜底：规范/移除残留的 $$ 显示数学标记
    # 1) 将成对 $$...$$ 统一为行内 \\(...\\)
    result = re.sub(r'\$\$\s*(.+?)\s*\$\$', r'\\(\1\\)', result, flags=re.DOTALL)
    # 2) 清理任何残留的孤立 $$（避免编译错误）
    result = result.replace('$$', '')
    
    # 🆕 后备占位符转换：清理任何残留的 Markdown 图片标记
    result = cleanup_remaining_image_markers(result)
    
    # 🆕 v1.6：清理宏参数内的"故选"残留（分两步）
    result = cleanup_guxuan_in_macros(result)
    
    # 🆕 v1.6.1：全局清理任何残留的"故选"（兜底方案）
    # 清理各种形式的"故选：X"，无论在什么位置
    result = re.sub(r'故选[:：][ABCD]+\.?[^\n}]*', '', result)
    # 清理"故答案为"
    result = re.sub(r'故答案为[:：]?[ABCD]*\.?', '', result)
    
    return result


# ==================== 🆕 v1.3 新增：自动验证函数 ====================

def validate_latex_output(tex_content: str) -> List[str]:
    """
    🆕 v1.3 新增：验证LaTeX输出，返回警告列表
    
    Args:
        tex_content: 生成的LaTeX内容
    
    Returns:
        警告信息列表
    """
    warnings = []
    
    # 检查1：残留的 $ 符号
    dollar_matches = re.findall(r'(?<!\\)\$[^\$]+\$', tex_content)
    if dollar_matches:
        warnings.append(f"⚠️  发现 {len(dollar_matches)} 处残留的 $ 格式")
        for i, match in enumerate(dollar_matches[:3], 1):  # 只显示前3个
            warnings.append(f"     示例{i}: {match}")
    
    # 检查2：残留的"故选"
    guxuan_matches = re.findall(r'故选[:：][ABCD]+', tex_content)
    if guxuan_matches:
        warnings.append(f"⚠️  发现 {len(guxuan_matches)} 处残留的'故选'")
    
    # 检查3：中文括号
    chinese_paren = re.findall(r'[（）]', tex_content)
    if chinese_paren:
        warnings.append(f"⚠️  发现 {len(chinese_paren)} 处中文括号")
    
    # 检查4：环境闭合
    begin_count = tex_content.count(r'\begin{question}')
    end_count = tex_content.count(r'\end{question}')
    if begin_count != end_count:
        warnings.append(f"❌ question 环境不匹配: {begin_count} 个 begin, {end_count} 个 end")
    
    begin_choices = tex_content.count(r'\begin{choices}')
    end_choices = tex_content.count(r'\end{choices}')
    if begin_choices != end_choices:
        warnings.append(f"❌ choices 环境不匹配: {begin_choices} 个 begin, {end_choices} 个 end")
    
    # 检查5：空行在宏参数中
    problematic_macros = []
    for macro in ['explain', 'topics', 'answer']:
        pattern = rf'\\{macro}\{{[^}}]*\n\s*\n[^}}]*\}}'
        if re.search(pattern, tex_content):
            problematic_macros.append(macro)
    if problematic_macros:
        warnings.append(f"⚠️  以下宏参数中可能有空行: {', '.join(problematic_macros)}")
    
    return warnings


# ==================== 主函数 ====================

def main():
    parser = argparse.ArgumentParser(
        description=f"OCR 试卷预处理脚本 - {VERSION}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🆕 v1.4 新增功能：
  - 修复数学公式双重包裹（$$\\(...\\)$$ → \\(...\\)）
  - 自动展开单行选项（> A... B... → 多行）
  - 正确处理显示公式（$$ → \\[...\\]）

✅ v1.3 改进回顾：
  - 修复 docstring 警告，添加 $ 格式兜底转换
  - 改进"故选"清理规则
  - 统一中英文标点（括号、引号）
  - 添加自动验证功能

✅ v1.2 改进回顾：
  - 加强空行清理（解决80%的Runaway argument错误）
  - 超长行自动分割（解决编译慢问题）
  - 增强数学变量检测（减少Missing $错误）
  - 增强选项解析（处理嵌入的解析内容）

使用示例:
  python3 ocr_to_examx.py "浙江省金华十校/" output/
        """
    )
    
    parser.add_argument("input", help="输入路径（.md 文件或 OCR 文件夹）")
    parser.add_argument("output", help="输出路径（目录或 .tex 文件）")
    parser.add_argument("--title", help="试卷标题", default=None)
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    
    args = parser.parse_args()
    
    try:
        print(f"🔍 OCR 试卷预处理脚本 - {VERSION}")
        print("━" * 60)
        md_file, images_dir = find_markdown_and_images(args.input)
        
        print(f"📄 Markdown: {md_file.name}")
        if images_dir:
            img_count = len(list(images_dir.glob('*')))
            print(f"🖼️  图片目录: {images_dir} ({img_count} 个文件)")
        else:
            print(f"⚠️  未找到图片目录")
        
        output_path = Path(args.output)
        if output_path.suffix == '.tex':
            output_tex = output_path
            output_dir = output_path.parent
        else:
            output_dir = output_path
            output_tex = output_dir / f"{md_file.stem.replace('_local', '_raw')}.tex"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if images_dir:
            img_count = copy_images_to_output(images_dir, output_dir)
            print(f"✅ 已复制 {img_count} 个图片到 {output_dir}/images/")
        
        title = args.title
        if title is None:
            input_path = Path(args.input)
            if input_path.is_dir():
                title = input_path.name
            else:
                title = md_file.stem.replace('_local', '')
        
        print(f"\n📖 正在转换...")
        print(f"📝 标题: {title}")
        
        md_text = md_file.read_text(encoding='utf-8')
        tex_text = convert_md_to_examx(md_text, title)
        
        # 🆕 v1.3：验证输出
        warnings = validate_latex_output(tex_text)
        
        output_tex.write_text(tex_text, encoding='utf-8')
        
        print(f"\n✅ 转换完成！")
        print("━" * 60)
        print(f"📊 输出文件: {output_tex}")
        print(f"📏 文件大小: {len(tex_text):,} 字节")
        
        question_count = tex_text.count(r'\begin{question}')
        image_count = tex_text.count('IMAGE_TODO')
        print(f"📋 题目数量: {question_count}")
        if image_count > 0:
            print(f"🖼️  图片占位: {image_count}")
        
        print(f"\n🆕 v1.4 改进已应用:")
        print(f"  ✅ 数学公式双重包裹修复")
        print(f"  ✅ 单行选项自动展开")
        print(f"  ✅ 显示公式正确处理")
        
        print(f"\n✅ v1.3 改进（已保留）:")
        print(f"  ✅ $ 格式兜底转换")
        print(f"  ✅ 增强的'故选'清理")
        print(f"  ✅ 中英文标点统一")
        print(f"  ✅ 自动验证功能")
        
        print(f"\n✅ v1.2 改进（已保留）:")
        print(f"  ✅ 空行清理增强")
        print(f"  ✅ 超长行自动分割")
        print(f"  ✅ 数学变量智能检测")
        print(f"  ✅ 选项解析增强")
        
        # 🆕 v1.3：显示验证结果
        if warnings:
            print(f"\n⚠️  验证发现 {len(warnings)} 个潜在问题:")
            for warning in warnings:
                print(f"  {warning}")
            print("\n💡 建议：使用 AI Agent 进行人工检查")
        else:
            print(f"\n✅ 验证通过：未发现明显问题")
        
        print("\n💡 下一步:")
        print("  1. AI Agent 读取此文件进行精修")
        print("  2. AI Agent 查看 images/ 中的图片")
        print("  3. AI Agent 生成 TikZ 代码")
        print("  4. 输出最终的 exam_final.tex")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

