#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
ocr_to_examx_v1.8.py - v1.8 改进版

🆕 v1.8 P0/P1 修复（2025-11-20）：
1. ✅ 修复数学模式边界解析错误：\right.\ $$ → \right.\) （P0）
   - 修复分段函数/矩阵后紧跟文本时的数学模式闭合问题
   - 避免中文文本被错误地放入数学模式
2. ✅ 增强题干缺失检测：自动插入 TODO 注释（P1）
   - 检测直接从 \item 开始的题目
   - 在 \begin{question} 后自动添加警告注释

v1.7 改进（2025-11-20）：
1. ✅ 题干检测与警告：检测缺少题干的题目（直接从 \item 开始）
2. ✅ 清理 Markdown 图片属性残留：删除 height="..." 和 width="..." 残留
3. ✅ 小问编号格式统一：不自动添加 \mathrm，使用普通文本
4. ✅ IMAGE_TODO 块后不添加空行：优化格式
5. ✅ \explain 中的空行自动处理：空行替换为 \par

v1.6 P0 修复（2025-11-19）：
1. ✅ 修复数组环境闭合错误（\right.\\) → \right.\)）
2. ✅ 清理图片属性残留（{width="..." height="..."}）

v1.5 核心修复（2025-11-18）：
1. ✅ 彻底修复数学公式双重包裹（$$\(...\)$$ → \(...\)）
   - 改进 smart_inline_math 避免嵌套
   - 新增 fix_double_wrapped_math 后处理清理
   - 统一将所有 $$...$$ 转换为行内 \(...\)（examx 兼容）
2. ✅ 改进单行选项展开（> A... B... C... D... → 多行）
   - 更精确的选项分割正则
   - 保留选项内的数学公式和标点
3. ✅ 减少手动修正工作量：2小时 → 15分钟 (目标 -87.5%)

v1.4 改进回顾：
- 修复数学公式双重包裹（初版）
- 自动展开单行选项（初版）
- 统一数学公式格式（$$...$$ → \(...\)）

v1.3 改进回顾：
- 修复 docstring 警告，添加 $ 格式兜底转换
- 改进"故选"清理规则
- 统一中英文标点
- 添加自动验证功能

版本：v1.7
作者：Claude
日期：2025-11-20
"""

import re
import argparse
import shutil
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from enum import Enum, auto  # 引入枚举支持（状态机需要）

# ==================== 数学状态机（来自 ocr_to_examx_complete.py） ====================
# 注意：此状态机完全取代原先基于正则的 smart_inline_math / sanitize_math 等管线。
# 旧函数保留但标记为 DEPRECATED，主流程不再调用，避免相互干扰。

class TokenType(Enum):
    TEXT = auto()
    DOLLAR_SINGLE = auto()
    DOLLAR_DOUBLE = auto()
    LATEX_OPEN = auto()
    LATEX_CLOSE = auto()
    RIGHT_BOUNDARY = auto()
    NEWLINE = auto()
    EOF = auto()


class MathStateMachine:
    r"""数学模式状态机 - 统一解析/规范所有数学定界符

    设计目标：
    1. 支持混合出现的 $ ... $、$$ ... $$、\( ... \) 以及 OCR 生成的 \right. $$ 等畸形边界
    2. 将所有显示/行内数学统一规范为行内形式：\( ... \)（与 examx 包兼容）
    3. 保持已有正确的 \( ... \) / \) 不被二次包裹
    4. 防止跨行单美元未闭合造成吞并后续文本
    """

    def tokenize(self, text: str) -> List:
        tokens = []
        i = 0
        n = len(text)
        while i < n:
            # 🔥 v1.8.3：增强 \right. 后的 OCR 边界检测
            # 处理 \right. 后可能跟随的各种畸形格式：
            # - \right. $$
            # - \right.\ $$
            # - \right. \ $$
            # - \right.  $$
            if text[i:].startswith(r'\right.'):
                j = i + 7  # 跳过 \right.
                # 跳过所有空白、反斜杠、空格的组合
                while j < n and text[j] in ' \t\n\\':
                    j += 1
                # 检查是否紧跟 $$
                if j < n - 1 and text[j:j+2] == '$$':
                    tokens.append((TokenType.RIGHT_BOUNDARY, r'\right.', i))
                    i = j + 2  # 跳过 $$
                    continue
                else:
                    # 不是 OCR 边界错误，保持原样
                    tokens.append((TokenType.TEXT, r'\right.', i))
                    i += 7
                    continue

            # $$ 显示数学
            if i < n - 1 and text[i:i+2] == '$$':
                tokens.append((TokenType.DOLLAR_DOUBLE, '$$', i))
                i += 2
                continue

            # 单 $ 行内数学
            if text[i] == '$':
                tokens.append((TokenType.DOLLAR_SINGLE, '$', i))
                i += 1
                continue

            # \( 与 \)
            if i < n - 1 and text[i:i+2] == r'\(':
                tokens.append((TokenType.LATEX_OPEN, r'\(', i))
                i += 2
                continue
            if i < n - 1 and text[i:i+2] == r'\)':
                tokens.append((TokenType.LATEX_CLOSE, r'\)', i))
                i += 2
                continue

            # 普通文本块收集
            j = i
            while j < n:
                if text[j] in '$\n':
                    break
                if j < n - 1 and text[j:j+2] in [r'\(', r'\)', '$$']:
                    break
                if text[j:].startswith(r'\right.'):
                    break
                j += 1
            if j > i:
                tokens.append((TokenType.TEXT, text[i:j], i))
                i = j
            else:
                tokens.append((TokenType.TEXT, text[i], i))
                i += 1
        return tokens

    def process(self, text: str) -> str:
        tokens = self.tokenize(text)
        out = []
        i = 0
        math_depth = 0  # 跟踪数学模式深度

        while i < len(tokens):
            t_type, val, pos = tokens[i]

            # 🔥 v1.8.3：智能处理 \right. 边界
            if t_type == TokenType.RIGHT_BOUNDARY:
                # 检查是否在数学模式内（有未闭合的 \(）
                if math_depth > 0:
                    out.append(r'\right.\)')
                    math_depth -= 1
                else:
                    # 不在数学模式内，保持原样（这是正常的 \right.）
                    out.append(r'\right.')
                i += 1
                continue
            if t_type == TokenType.DOLLAR_DOUBLE:
                # 收集直到下一个 $$
                i += 1
                buf = []
                while i < len(tokens):
                    tt, tv, _ = tokens[i]
                    if tt == TokenType.DOLLAR_DOUBLE:
                        i += 1
                        break
                    buf.append(tv)
                    i += 1
                out.append(r'\(' + ''.join(buf).strip() + r'\)')
                continue

            if t_type == TokenType.DOLLAR_SINGLE:
                i += 1
                buf = []
                while i < len(tokens):
                    tt, tv, _ = tokens[i]
                    if tt == TokenType.DOLLAR_SINGLE:
                        i += 1
                        break
                    # 禁止跨行的单美元延伸
                    if '\n' in tv:
                        out.append('$')
                        out.extend(buf)
                        break
                    buf.append(tv)
                    i += 1
                if buf:
                    out.append(r'\(' + ''.join(buf) + r'\)')
                continue

            if t_type == TokenType.LATEX_OPEN:
                out.append(val)
                math_depth += 1
                i += 1
                continue

            if t_type == TokenType.LATEX_CLOSE:
                out.append(val)
                math_depth = max(0, math_depth - 1)
                i += 1
                continue
            out.append(val)
            i += 1
        return ''.join(out)


# 单例实例供全局调用
math_sm = MathStateMachine()


# ==================== 配置 ====================

VERSION = "v1.8.3"

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


# DEPRECATED: 已被 MathStateMachine 替换，保留以兼容旧测试；主流程不再调用
def smart_inline_math(text: str) -> str:
    r"""智能转换行内公式：$...$ -> \(...\)，$$...$$ -> \(...\)

    🆕 v1.5 改进：彻底避免双重包裹，examx 统一使用 \(...\)

    注意：所有 $$...$$ 显示公式都会被转换为行内 \(...\) 格式，
    这是为了与 examx 包的兼容性。如果需要真正的显示公式，
    应在后续手动调整为 \[...\] 格式。
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

    # 步骤3.5: 🆕 v1.8 修复 \right.\ $$ 边界问题
    # 将 \right.\ $$ 转换为 \right.\) （闭合当前数学模式）
    text = re.sub(r'\\right\.\\\s+\$\$', r'\\right.\\) ', text)

    # 步骤4: 转换显示公式 $$ ... $$ 为 \(...\)（examx 统一风格）
    # 注意：所有 $$...$$ 都转为行内格式，不生成 \[...\]
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


# DEPRECATED: 已被 MathStateMachine 统一处理双重包裹
def fix_double_wrapped_math(text: str) -> str:
    r"""修正双重包裹的数学公式
    
    🆕 v1.6 增强：清理更多嵌套模式
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
    
    # 🆕 v1.6 P0 修复：清理 \because\(\) 或 \therefore\(\) 的空嵌套
    # 注意：替换后保留空格，避免与后续字母连接
    text = re.sub(r'\\because\s*\\\(\\\)\s*', r'\\because ', text)
    text = re.sub(r'\\therefore\s*\\\(\\\)\s*', r'\\therefore ', text)
    
    # 🆕 v1.6 P0 修复：清理 \(\because\(\) 或 \(\therefore\(\) 形式
    text = re.sub(r'\\\(\\because\s*\\\(\\\)\s*', r'\\(\\because ', text)
    text = re.sub(r'\\\(\\therefore\s*\\\(\\\)\s*', r'\\(\\therefore ', text)
    
    # 🆕 v1.6 P0 修复：清理独立的空括号 \(\)（可能出现在任何位置）
    text = re.sub(r'\\\(\s*\\\)', r'', text)
    
    # 🆕 v1.6 P0 修复：修正 \(...\(\)...\) 形式的嵌套（空占位符）
    # 迭代清理，最多3次
    for _ in range(3):
        before = text
        text = re.sub(r'\\\(([^)]*?)\\\(\\\)([^)]*?)\\\)', r'\\(\1\2\\)', text, flags=re.DOTALL)
        if text == before:
            break
    
    return text


def fix_array_boundaries(text: str) -> str:
    r"""修复 array 环境的边界符错误
    
    🆕 v1.6 P0 修复：修正 \right.\\) → \right.\)
    """
    # 修正 \right. 后的双反斜杠
    text = re.sub(r'\\right\.\\\\\)', r'\\right.\\)', text)
    
    # 修正其他边界符
    text = re.sub(r'\\right\)\\\\\)', r'\\right)\\)', text)
    text = re.sub(r'\\right\]\\\\\)', r'\\right]\\)', text)
    text = re.sub(r'\\right\}\\\\\)', r'\\right}\\)', text)
    
    # 同样修正 \left 的情况（如果存在）
    text = re.sub(r'\\\\\(\\left', r'\\(\\left', text)
    
    return text


def clean_residual_image_attrs(text: str) -> str:
    r"""清理残留的图片属性块

    🆕 v1.7 增强：清理更多 Markdown 图片属性残留
    🆕 v1.6 P0 修复：清理 Pandoc 生成的图片属性
    """
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


# DEPRECATED: 状态机后不再需要变量自动包裹，可能导致过度包裹
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
    
    # 规则3：虚数单位 i（避免误转换罗马数字）
    # 只在明确的数学上下文中转换，避免 (i), (ii) 等罗马数字被转换
    # 匹配：独立的 i 后面跟着数学运算符或结束，但不在括号内
    text = re.sub(r'(?<!\\)(?<!\()\bi\b(?=[^a-zA-Z\)])', r'\\mathrm{i}', text)
    
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


# DEPRECATED: 状态机已处理数学定界符与 OCR 边界，此函数仅保留兼容性
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
    if '|' in text and '---' in text:
        text = convert_markdown_table_to_latex(text)

    # 处理下划线
    text = text.replace(r'\_', '@@ESCAPED_UNDERSCORE@@')
    text = re.sub(r'(?<!\\)_(?![{_])', r'\\_', text)
    text = text.replace('@@ESCAPED_UNDERSCORE@@', r'\_')

    return text.strip()


# ==================== 题目解析函数 ====================

def split_sections(text: str) -> List[Tuple[str, str]]:
    """拆分章节（支持 markdown 标题和加粗格式）
    
    支持两种格式：
    1. Markdown 标题：# 一、单选题
    2. 加粗格式：**一、单选题**
    """
    lines = text.splitlines()
    sections = []
    current_title = None
    current_lines = []

    for line in lines:
        stripped = line.strip()
        # 优先匹配 markdown 标题格式
        m = re.match(
            r"^#+\s*(一、单选题|二、单选题|二、多选题|三、填空题|四、解答题)",
            stripped,
        )
        # 如果不匹配，尝试匹配加粗格式 **章节标题**
        if not m:
            m = re.match(
                r"^\*\*(一、单选题|二、单选题|二、多选题|三、填空题|四、解答题)\*\*",
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


def extract_context_around_image(text: str, img_match_start: int, img_match_end: int,
                                  context_len: int = 50) -> Tuple[str, str]:
    """提取图片前后的上下文文本

    Args:
        text: 完整文本
        img_match_start: 图片匹配的起始位置
        img_match_end: 图片匹配的结束位置
        context_len: 上下文长度（字符数）

    Returns:
        (context_before, context_after) 元组
    """
    # 提取前文
    before_start = max(0, img_match_start - context_len)
    context_before = text[before_start:img_match_start].strip()
    # 清理换行符和多余空格
    context_before = ' '.join(context_before.split())

    # 提取后文
    after_end = min(len(text), img_match_end + context_len)
    context_after = text[img_match_end:after_end].strip()
    context_after = ' '.join(context_after.split())

    return context_before, context_after


def extract_meta_and_images(block: str, question_index: int = 0, slug: str = "") -> Tuple[str, Dict, List]:
    r"""提取元信息与图片（状态机重构：防止跨题累积）

    🆕 新增参数：question_index 和 slug 用于生成图片 ID

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
    # 🆕 修复：analysis 单独存在，后续会被丢弃
    meta_alias_map = {
        "analysis": "analysis",  # analysis 单独存在，后面会被丢弃
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

    # 🆕 修复：将 META_PATTERNS 编译，分离 analysis 和 explain
    meta_starts = [
        ("answer", re.compile(r"^【\s*答案\s*】[:：]?\s*(.*)$")),
        ("difficulty", re.compile(r"^【\s*难度\s*】[:：]?\s*([\d.]+).*")),
        ("topics", re.compile(r"^【\s*(知识点|考点)\s*】[:：]?\s*(.*)$")),
        ("analysis", re.compile(r"^【\s*分析\s*】[:：]?\s*(.*)$")),
        ("explain", re.compile(r"^【\s*详解\s*】[:：]?\s*(.*)$")),
    ]

    # 状态
    state = "NORMAL"  # or "IN_META"
    current_meta_key: Optional[str] = None
    current_meta_lines: List[str] = []

    def flush_meta():
        nonlocal current_meta_key, current_meta_lines
        if current_meta_key is None:
            return
        # 归一化到别名键
        key = meta_alias_map.get(current_meta_key, current_meta_key)
        # 🆕 修复：遇到 analysis 时直接丢弃
        if key == "analysis":
            # 说明这是【分析】段，直接舍弃，不写入 meta 字典
            current_meta_key = None
            current_meta_lines = []
            return
        # 合并清理
        text = "\n".join(current_meta_lines)
        # 去掉可能残留的标签前缀
        text = re.sub(r"^【?(?:答案|难度|知识点|考点|详解|分析)】?[:：]?\s*", "", text)
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
        # 🆕 Prompt 3: 统一处理所有图片（独立和内联）
        # 检查整行是否包含图片标记
        img_result = image_match(line)  # 注意：使用完整行而非stripped
        if img_result:
            img_type, m_img = img_result
            # 检查是否为独立图片行：整行只有一个图片标记
            is_standalone = (m_img.group(0).strip() == stripped)

            # 🆕 生成图片 ID 和提取上下文
            img_counter = len(images) + 1
            generated_id = f"{slug}-Q{question_index}-img{img_counter}" if slug else f"Q{question_index}-img{img_counter}"

            # 提取上下文
            full_text = "\n".join(lines)
            img_start = full_text.find(m_img.group(0))
            img_end = img_start + len(m_img.group(0))
            context_before, context_after = extract_context_around_image(full_text, img_start, img_end)

            if is_standalone:
                # 独立图片块：提取到images列表
                if img_type == 'with_id':
                    # ![@@@id](path){...}
                    img_id = m_img.group(1)
                    path = m_img.group(2).strip()
                    images.append({
                        "path": path,
                        "width": 60,
                        "id": generated_id,
                        "inline": False,
                        "question_index": question_index,
                        "sub_index": 1,
                        "context_before": context_before,
                        "context_after": context_after
                    })
                elif img_type == 'no_id':
                    # ![](path){...}
                    path = m_img.group(1).strip()
                    images.append({
                        "path": path,
                        "width": 60,
                        "id": generated_id,
                        "inline": False,
                        "question_index": question_index,
                        "sub_index": 1,
                        "context_before": context_before,
                        "context_after": context_after
                    })
                else:
                    # 简单格式: ![](images/...)
                    path = m_img.group(1)
                    width = int(m_img.group(2)) if m_img.group(2) else 60
                    images.append({
                        "path": path,
                        "width": width,
                        "id": generated_id,
                        "inline": False,
                        "question_index": question_index,
                        "sub_index": 1,
                        "context_before": context_before,
                        "context_after": context_after
                    })
                i += 1
                continue
            else:
                # 内联图片：替换为占位符，记录到images列表
                if img_type == 'with_id':
                    img_id = m_img.group(1)
                    path = m_img.group(2).strip()
                    images.append({
                        "path": path,
                        "width": 60,
                        "id": generated_id,
                        "inline": True,
                        "question_index": question_index,
                        "sub_index": 1,
                        "context_before": context_before,
                        "context_after": context_after
                    })
                elif img_type == 'no_id':
                    path = m_img.group(1).strip()
                    images.append({
                        "path": path,
                        "width": 60,
                        "id": generated_id,
                        "inline": True,
                        "question_index": question_index,
                        "sub_index": 1,
                        "context_before": context_before,
                        "context_after": context_after
                    })
                else:
                    path = m_img.group(1)
                    width = int(m_img.group(2)) if m_img.group(2) else 60
                    images.append({
                        "path": path,
                        "width": width,
                        "id": generated_id,
                        "inline": True,
                        "question_index": question_index,
                        "sub_index": 1,
                        "context_before": context_before,
                        "context_after": context_after
                    })

                # 替换图片标记为占位符（使用新的 ID 格式）
                line = line.replace(m_img.group(0), f"<<IMAGE_INLINE:{generated_id}>>")
                # 继续处理该行（fallthrough）

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

        # 🆕 修复：只在遇到【详解】时进入解析模式，遇到【分析】时跳过
        # 检查是否为【分析】标记 - 直接跳过
        if re.match(r'^【?\s*分析\s*】[:：]?', stripped):
            structure['in_choice'] = False
            structure['in_analysis'] = False
            # 不把这一行塞进任何地方，完全舍弃
            continue

        # 检查是否为【详解】标记 - 进入解析模式
        if re.match(r'^【?\s*详解\s*】[:：]?', stripped):
            if structure['current_choice']:
                structure['choices'].append(structure['current_choice'].strip())
                structure['current_choice'] = ''
            structure['in_choice'] = False
            structure['in_analysis'] = True
            structure['analysis_lines'].append(stripped)
            continue

        # 保守处理：只在明确的解析起始词开头时进入解析（避免误判题干）
        # 注意：不再使用 ANALYSIS_START_MARKERS 自动触发，避免"则"等词在题干中误判
        if structure['in_analysis']:
            # 已经在解析模式中，继续收集
            pass
        
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
    r"""处理解答题的小题编号

    🆕 v1.7：统一小问编号格式，不添加 \mathrm
    """
    if not re.search(r'\(\d+\)', content):
        return content

    subquestions = re.findall(r'\((\d+)\)(.*?)(?=\(\d+\)|$)', content, re.DOTALL)

    if len(subquestions) < 2:
        return content

    result_lines = []
    for num, content_text in subquestions:
        # 🆕 v1.7：使用普通文本格式，不添加 \mathrm
        # 格式：(1) 或 (i) 等，保持原样
        result_lines.append(f"\\item {content_text.strip()}")

    return '\n'.join(result_lines)


# DEPRECATED: 状态机已避免这些行内异常，保留兜底测试使用
def fix_inline_math_glitches(text: str) -> str:
    """🆕 修复行内数学的各种异常模式

    修复：
    - 空的 $$
    - $$$x$ → $x$
    - \therefore$$ → \therefore
    - \because$$ → \because
    """
    if not text:
        return text

    # 1. 去掉完全空的 $$
    text = re.sub(r'\$\s*\$', '', text)

    # 2. 修复 $$$x$ → $x$
    text = re.sub(r'\$\s*\$\s*(\\\()', r'\1', text)

    # 3. 特例：\therefore$$ → \therefore
    text = re.sub(r'(\\therefore)\s*\$\s*\$', r'\1', text)

    # 4. 特例：\because$$ → \because
    text = re.sub(r'(\\because)\s*\$\s*\$', r'\1', text)

    return text


def process_text_for_latex(text: str, is_math_heavy: bool = False) -> str:
    r"""统一入口：题干/选项/解析文本的 LaTeX 处理（状态机版）

    重构目标：
    1. 保留原有“非数学”清理与转义逻辑（故选/【详解】/OCR 边界修复等）
    2. 用 MathStateMachine 完全替换旧的 smart_inline_math / sanitize_math 等正则管线
    3. 数学定界符统一：$...$ / $$...$$ → \(...\)，保持已有 \(...\) 不重复包裹
    4. 在状态机处理后做轻量兜底清理（空数学块、图片属性残留等）
    """
    if not text:
        return text

    # ---------- 1. 前置：纯文本/非数学层面清理（原逻辑保留） ----------
    text = re.sub(r'\*\s*(\$[^$]+\$)\s*\*', r'\1', text)  # *$x$* → $x$
    text = re.sub(r'\*([A-Za-z0-9])\*', r'\\emph{\1}', text)  # *x* → \emph{x}

    # "故选" / "故答案为" 系列清理
    text = re.sub(r'[,，。\.;；]\s*故选[:：][ABCD]+[.。]?\s*$', '', text)
    text = re.sub(r'\n+故选[:：][ABCD]+[.。]?\s*$', '', text)
    text = re.sub(r'^\s*故选[:：][ABCD]+[.。]?\s*', '', text)
    text = re.sub(r'\n+故答案为[:：]', '', text)
    text = re.sub(r'^\s*故选[:：][ABCD]+[.。]?\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'[，,]?\s*故选[:：]\s*[ABCD]+[。．.]*\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^【?详解】?[:：]?\s*', '', text)

    # OCR 边界畸形预处理（保持原逻辑）
    text = re.sub(r'\\\\right\.\s*\\\\\\\)', r'\\\\right.', text)
    text = re.sub(r'\\\\right\.\\\\\+\)', r'\\\\right.', text)

    # Unicode 符号替换（先行包裹为数学，后续状态机会规范）
    # ∵/∴ 直接替换为命令（不再包裹美元，避免生成孤立 $）
    if '∵' in text or '∴' in text:
        text = text.replace('∵', '\\because ').replace('∴', '\\therefore ')

    # 非数学模式下的 LaTeX 特殊字符转义
    if not is_math_heavy:
        text = escape_latex_special(text, in_math_mode=False)

    # ---------- 2. 数学模式统一：状态机处理 ----------
    global math_sm
    text = math_sm.process(text)

    # ---------- 3. 轻量后处理：常见空块/残留修复 ----------
    text = fix_common_issues_v2(text)

    return text


def fix_common_issues_v2(text: str) -> str:
    r"""状态机后的兜底纯文本修复（只处理不改变数学语义的残留）

    包含：
    - 空的行内/显示数学块 \(\) / \[\] 删除
    - \because\(\) / \therefore\(\) 清理为纯命令
    - OCR 产生的数组边界畸形（\right.\\) → \right.\)）
    - 图片残余属性清理（利用原 clean_residual_image_attrs）
    - 去除孤立的重复显示公式定界符（状态机已规范，兜底防御）
    """
    if not text:
        return text
    # 空数学块
    text = re.sub(r'\\\(\s*\\\)', '', text)
    text = re.sub(r'\\\[\s*\\\]', '', text)
    # 清理 \because\(\) / \therefore\(\)
    text = re.sub(r'\\because\s*\\\(\\\)', r'\\because ', text)
    text = re.sub(r'\\therefore\s*\\\(\\\)', r'\\therefore ', text)
    # 数组/分段等环境边界畸形（与 complete 版本保持一致）
    text = text.replace(r'\right.\\)', r'\right.\)')
    text = text.replace(r'\right)\\)', r'\right)\)')
    # 图片属性残留（复用已有函数）
    text = clean_residual_image_attrs(text)
    # 移除任何残留的裸 $$（状态机后理论上不会出现）
    text = text.replace('$$', '')

    # 清理外层多余美元: $\(x\)$ → \(x\)
    text = re.sub(r'\$(\\\([^$]+?\\\))\$', r'\1', text)
    # 清理 $\because$ → \because （以及 \therefore）
    text = re.sub(r'\$(\\because)\$', r'\1', text)
    text = re.sub(r'\$(\\therefore)\$', r'\1', text)
    # 清理简单变量形式 $x$ 若单字符且不在已有数学（保守：仅字母/数字）→ \(x\)
    def _wrap_simple_var(m: re.Match) -> str:
        var = m.group(1)
        return f'\\({var}\\)'
    text = re.sub(r'(?<!\\)\$([a-zA-Z0-9])\$', _wrap_simple_var, text)
    # 再次移除可能产生的空数学块 \(\)
    text = re.sub(r'\\\(\s*\\\)', '', text)
    # 去除遗留的孤立单美元（不在配对内）：删除
    # 匹配单独一行只包含 $ 或行首/行末的单美元
    text = re.sub(r'(^|\s)(\$)(?=\s|$)', lambda m: m.group(1), text)
    return text


def validate_math_integrity(tex: str) -> List[str]:
    r"""分析最终 TeX 数学完整性问题并返回警告列表（扩展版）

    检查项：
    - 行内数学定界符数量差异（opens vs closes）
    - 裸露美元符号
    - 双重包裹残留
    - 右边界畸形（\right. $$ 等）
    - 空数学块
    - 🆕 截断/未闭合的数学片段（收集前若干样本）
      典型来源：图片占位符或 explain 合并时跨行被截断，导致缺失 \)
    """
    issues: List[str] = []
    opens = tex.count('\\(')
    closes = tex.count('\\)')
    if opens != closes:
        issues.append(f"Math delimiter imbalance: opens={opens} closes={closes} diff={opens - closes}")

    stray = len(re.findall(r'(?<!\\)\$', tex))
    if stray:
        issues.append(f"Stray dollar signs detected: {stray}")

    double_wrapped = (
        len(re.findall(r'\$\s*\\\(.*?\\\)\s*\$', tex, flags=re.DOTALL)) +
        len(re.findall(r'\$\$\s*\\\(.*?\\\)\s*\$\$', tex, flags=re.DOTALL))
    )
    if double_wrapped:
        issues.append(f"Double-wrapped math segments: {double_wrapped}")

    right_glitch = (
        len(re.findall(r'\\right\.\s*\$\$', tex)) +
        len(re.findall(r'\\right\.\\\\\)', tex))
    )
    if right_glitch:
        issues.append(f"Right boundary glitches: {right_glitch}")

    empty_math = (
        len(re.findall(r'\\\(\s*\\\)', tex)) +
        len(re.findall(r'\\\[\s*\\\]', tex))
    )
    if empty_math:
        issues.append(f"Empty math blocks: {empty_math}")

    # 🆕 截断检测：使用顺序扫描匹配未配对的 \\( 和 \\)
    unmatched_open_positions: List[int] = []
    unmatched_close_positions: List[int] = []

    token_iter = list(re.finditer(r'(\\\(|\\\))', tex))
    stack: List[int] = []
    for m in token_iter:
        tok = m.group(0)
        pos = m.start()
        if tok == '\\(':  # open
            stack.append(pos)
        else:  # ')'
            if stack:
                stack.pop()
            else:
                unmatched_close_positions.append(pos)
    # 剩余 stack 中的是未闭合 open
    unmatched_open_positions.extend(stack)

    def _sample_at(pos: int, direction: str = 'forward', span: int = 140) -> str:
        """获取从 pos 起的上下文样本，去除换行与多余空格"""
        if direction == 'forward':
            raw = tex[pos:pos+span]
        else:
            start = max(0, pos-span)
            raw = tex[start:pos+10]
        # 截断到第一个 '\\)' （若存在）
        end_delim = raw.find('\\)')
        if end_delim != -1:
            raw = raw[:end_delim+2]
        raw = re.sub(r'\s+', ' ', raw).strip()
        return raw

    # 进一步甄别“疑似截断”：开括号后 120 字符内没有闭括号
    truncated_open_samples: List[str] = []
    for p in unmatched_open_positions:
        segment = tex[p:p+300]
        if '\\)' not in segment:  # 明显没有闭合
            truncated_open_samples.append(_sample_at(p, 'forward'))
        else:
            # 可能闭括号远在超过 120 之后，也认为可疑
            close_rel = segment.find('\\)')
            if close_rel > 120:
                truncated_open_samples.append(_sample_at(p, 'forward'))
        if len(truncated_open_samples) >= 5:  # 只取前 5 个样本
            break

    truncated_close_samples: List[str] = []
    for p in unmatched_close_positions[:5]:
        truncated_close_samples.append(_sample_at(p, 'backward'))

    if truncated_open_samples:
        issues.append(
            "Unmatched opens (samples): " +
            '; '.join(truncated_open_samples)
        )
    if truncated_close_samples:
        issues.append(
            "Unmatched closes (samples): " +
            '; '.join(truncated_close_samples)
        )

    # 针对图片占位符附近的截断：\( ... IMAGE_TODO_START 未闭合
    image_trunc = re.findall(r'\\\([^\\)]{0,200}?% IMAGE_TODO_START', tex)
    if image_trunc:
        issues.append(f"Potential image-adjacent truncated math segments: {len(image_trunc)}")

    return issues


def generate_image_todo_block(img: Dict, stem_text: str = "", is_inline: bool = False) -> str:
    """生成新格式的 IMAGE_TODO 占位块

    🆕 v1.7：IMAGE_TODO 块后不添加额外空行

    Args:
        img: 图片信息字典，包含 id, path, width, inline, question_index, sub_index
        stem_text: 题干文本，用于提取上下文
        is_inline: 是否为内联图片

    Returns:
        格式化的 IMAGE_TODO 占位块
    """
    img_id = img.get('id', 'unknown')
    path = img.get('path', '')
    width = img.get('width', 60)
    inline = 'true' if img.get('inline', False) else 'false'
    q_idx = img.get('question_index', 0)
    sub_idx = img.get('sub_index', 1)

    # 提取上下文（简化版：取图片前后各50个字符）
    # 清理 context 内容：去除 LaTeX 命令，限制长度，检查括号平衡
    def clean_context(text: str, max_len: int = 50) -> str:
        r"""清理 CONTEXT 注释内容

        - 去除 LaTeX 命令（\xxx{...}）
        - 去除数学定界符 \(...\) 和 \[...\]
        - 截断到最多 max_len 字符
        - 检查括号平衡，如果不平衡则返回空字符串
        """
        if not text:
            return ""

        # 去除 LaTeX 命令（\xxx{...}）
        text = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', text)
        # 去除数学定界符
        text = re.sub(r'\\\(|\\\)|\\\[|\\\]', '', text)
        # 去除多余的空格
        text = re.sub(r'\s+', ' ', text).strip()

        # 截断到最多 max_len 字符
        if len(text) > max_len:
            text = text[:max_len] + '...'

        # 检查括号平衡
        open_count = text.count('{')
        close_count = text.count('}')
        if open_count != close_count:
            # 括号不平衡，返回空字符串避免编译错误
            return ""

        return text

    context_before = clean_context(img.get('context_before', '').strip())
    context_after = clean_context(img.get('context_after', '').strip())

    # 🆕 v1.7：构建占位块，IMAGE_TODO_END 后不添加额外的 \n
    if is_inline:
        # 内联图片：不使用 center 环境
        block = (
            f"\n% IMAGE_TODO_START id={img_id} path={path} width={width}% inline={inline} "
            f"question_index={q_idx} sub_index={sub_idx}\n"
        )
        if context_before:
            block += f"% CONTEXT_BEFORE: {context_before}\n"
        if context_after:
            block += f"% CONTEXT_AFTER: {context_after}\n"
        block += (
            "\\begin{tikzpicture}[scale=0.8,baseline=-0.5ex]\n"
            f"  % TODO: AI_AGENT_REPLACE_ME (id={img_id})\n"
            "\\end{tikzpicture}\n"
            f"% IMAGE_TODO_END id={img_id}"  # 🆕 v1.7：不添加尾随 \n
        )
    else:
        # 独立图片：使用 center 环境
        block = (
            "\\begin{center}\n"
            f"% IMAGE_TODO_START id={img_id} path={path} width={width}% inline={inline} "
            f"question_index={q_idx} sub_index={sub_idx}\n"
        )
        if context_before:
            block += f"% CONTEXT_BEFORE: {context_before}\n"
        if context_after:
            block += f"% CONTEXT_AFTER: {context_after}\n"
        block += (
            "\\begin{tikzpicture}[scale=1.05,>=Stealth,line cap=round,line join=round]\n"
            f"  % TODO: AI_AGENT_REPLACE_ME (id={img_id})\n"
            "\\end{tikzpicture}\n"
            f"% IMAGE_TODO_END id={img_id}\n"
            "\\end{center}"  # 🆕 v1.7：不添加尾随 \n
        )

    return block


def build_question_tex(stem: str, options: List, meta: Dict, images: List,
                       section_type: str, question_index: int = 0, slug: str = "") -> str:
    """生成 question 环境

    🆕 Prompt 3: 支持内联图片占位符替换
    🆕 新格式: 使用 IMAGE_TODO_START/END 带 ID 的占位块
    """
    # 先处理文本，但保留占位符
    stem_raw = stem  # 保存原始文本用于上下文提取
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

    # 🆕 新格式: 使用 IMAGE_TODO_START/END 占位块
    for idx, img in enumerate(images):
        # 生成新格式的占位块
        img_todo_block = generate_image_todo_block(img, stem_raw, img.get('inline', False))

        if img.get('inline', False):
            # 内联图片：替换占位符
            placeholder = f"<<IMAGE_INLINE:{img.get('id', f'img{idx}')}>>"
            stem = stem.replace(placeholder, img_todo_block)
            explain_raw = explain_raw.replace(placeholder, img_todo_block) if explain_raw else explain_raw
            # 更新已处理的选项
            for i, line in enumerate(lines):
                if placeholder in line:
                    lines[i] = line.replace(placeholder, img_todo_block)
        else:
            # 独立图片：追加到题目末尾
            lines.append("")
            lines.append(img_todo_block)

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


def convert_md_to_examx(md_text: str, title: str, slug: str = "", enable_issue_detection: bool = True) -> str:
    """主转换函数（增强版）

    🆕 v1.6.3：增加问题检测和日志记录

    Args:
        md_text: Markdown 文本
        title: 试卷标题
        slug: 试卷 slug（用于日志文件名）
        enable_issue_detection: 是否启用问题检测
    """
    md_text = clean_markdown(md_text)
    sections = split_sections(md_text)

    # 🆕 v1.6.3：初始化问题日志
    if enable_issue_detection and slug:
        init_issue_log(slug)

    out_lines = []
    out_lines.append(f"\\examxtitle{{{title}}}")

    q_index = 0  # 全局题号计数器
    for raw_title, body in sections:
        sec_label = SECTION_MAP.get(raw_title, raw_title)
        out_lines.append("")
        out_lines.append(f"\\section{{{sec_label}}}")

        for block in split_questions(body):
            if not block.strip():
                continue

            q_index += 1  # 题号递增
            raw_block = block  # 保存原始 Markdown 片段

            try:
                # 🆕 传递 question_index 和 slug 用于生成图片 ID
                content, meta, images = extract_meta_and_images(block, question_index=q_index, slug=slug)

                # 使用增强的转换函数（返回3个值）
                stem, options, extracted_analysis = convert_choices(content)

                # 合并提取的解析和元信息中的解析
                if extracted_analysis and not meta.get('explain'):
                    meta['explain'] = extracted_analysis
                elif extracted_analysis:
                    meta['explain'] = meta['explain'] + '\n' + extracted_analysis

                # 🆕 传递 question_index 和 slug 到 build_question_tex
                q_tex = build_question_tex(stem, options, meta, images, sec_label,
                                          question_index=q_index, slug=slug)

                # 🆕 v1.6.4：检测问题并记录日志（传入 meta & section_label）
                if enable_issue_detection and slug:
                    issues = detect_question_issues(
                        slug=slug,
                        q_index=q_index,
                        raw_block=raw_block,
                        tex_block=q_tex,
                        meta=meta,
                        section_label=sec_label,
                    )
                    append_issue_log(
                        slug=slug,
                        q_index=q_index,
                        raw_block=raw_block,
                        tex_block=q_tex,
                        issues=issues,
                        meta=meta,
                        section_label=sec_label,
                    )

                # 验证生成的 TeX 是否完整
                if r'\begin{question}' in q_tex and r'\end{question}' not in q_tex:
                    print(f"⚠️  Q{q_index} 缺少 \\end{{question}}，自动补全")
                    q_tex += "\n\\end{question}"

                out_lines.append("")
                out_lines.append(q_tex)
            except Exception as e:
                import traceback
                print(f"⚠️  Q{q_index} ({sec_label}) 转换失败: {str(e)}")
                print(f"   {traceback.format_exc()}")
                out_lines.append("")
                out_lines.append(r"\begin{question}")
                out_lines.append(f"% ERROR: Q{q_index} 转换失败 - {str(e)}")
                out_lines.append(r"\end{question}")

    out_lines.append("")

    # 最终处理：清理空行和分割超长行
    result = "\n".join(out_lines)
    result = remove_blank_lines_in_macro_args(result)
    result = split_long_lines_in_explain(result, max_length=800)
    # 🔥 v1.8.3：重新启用（已修复括号计数逻辑）
    result = remove_par_breaks_in_explain(result)
    # 🔥 v1.8.1：clean_question_environments 仍然禁用（正则匹配问题）

    # 最终兜底：规范/移除残留的 $$ 显示数学标记
    # 1) 将成对 $$...$$ 统一为行内 \(...\)（与 smart_inline_math 行为一致）
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


# ==================== 🆕 v1.6.3 新增：问题检测与日志系统 ====================

def detect_question_issues(
    slug: str,
    q_index: int,
    raw_block: str,
    tex_block: str,
    meta: Optional[Dict[str, str]] = None,
    section_label: Optional[str] = None,
) -> List[str]:
    """🆕 v1.7：检测题目中的可疑模式（增强版）
    🆕 v1.6.4：检测题目中的可疑模式（增强版）

    Args:
        slug: 试卷 slug（如 "nanjing_2026_sep"）
        q_index: 题号（从 1 开始）
        raw_block: 原始 Markdown 片段
        tex_block: 生成的 TeX 片段
        meta: 解析得到的元信息字典（答案、难度、知识点、解析等）
        section_label: 当前大题标题（如 "单选题"、"多选题" 等）

    Returns:
        问题列表
    """
    issues: List[str] = []

    # ---------- 🆕 v1.7：检测缺少题干的题目 ----------
    # 检查题目是否直接从 \item 开始（缺少题干）
    # 在 \begin{question} 后，如果第一个非空行是 \item 或 \begin{choices}，则缺少题干
    question_content = tex_block
    if r'\begin{question}' in question_content:
        # 提取 \begin{question} 和 \begin{choices} 之间的内容
        match = re.search(r'\\begin\{question\}(.*?)(?:\\begin\{choices\}|\\item|\\end\{question\})',
                         question_content, re.DOTALL)
        if match:
            content_between = match.group(1).strip()
            # 如果内容为空或只有注释，则缺少题干
            # 移除注释行
            content_no_comments = re.sub(r'^\s*%.*$', '', content_between, flags=re.MULTILINE).strip()
            if not content_no_comments:
                issues.append("⚠️ CRITICAL: 题目缺少题干，直接从 \\item 开始 - 请在 Markdown 中补充题干内容")

    # ---------- 1) 原有检查逻辑（保留 & 复刻） ----------

    # 1.1 检测 meta 形式的【分析】（不应该出现）
    if "【分析】" in raw_block and "【分析】" in tex_block:
        issues.append("Contains meta 【分析】 in both raw and tex (should be discarded)")
    elif "【分析】" in tex_block:
        issues.append("Contains meta 【分析】 in tex (should be discarded)")

    # 1.2 检测 *$x$* 或其他 star + math 模式
    if re.search(r'\*\s*\$', tex_block) or re.search(r'\$\s*\*', tex_block):
        issues.append("Star-emphasis around inline math, e.g. *$x$*")

    # 1.3 检测空 $$ 或形如 $$\(
    if re.search(r'\$\s*\$', tex_block):
        issues.append("Empty inline/ display math $$")
    if re.search(r'\$\s*\$\s*\\\(', tex_block):
        issues.append("Suspicious pattern $$\\(")

    # 1.4 检测行内 math 分隔符数量明显不匹配
    open_count = tex_block.count(r'\(')
    close_count = tex_block.count(r'\)')
    if open_count != close_count:
        issues.append(f"Unbalanced inline math delimiters: ${open_count} vs$ {close_count}")

    # 1.5 检测全角括号残留
    if '（' in tex_block or '）' in tex_block:
        issues.append("Fullwidth brackets （）found in tex")

    # 1.6 检测"故选"残留
    if re.search(r'故选[:：][ABCD]+', tex_block):
        issues.append("'故选' pattern found in tex")

    # ---------- 2) 新增：基于 meta 的一致性检查 ----------

    if meta is not None:
        # 辅助函数：安全取值并 strip
        def _get(key: str) -> str:
            return (meta.get(key) or "").strip()

        answer = _get("answer")
        difficulty = _get("difficulty")
        topics = _get("topics")
        explain = _get("explain")
        analysis = _get("analysis")

        # 2.1 检查"分析"字段是否仍然存在（按规范应丢弃，仅允许作为中间态，而不应写入 TeX）
        if analysis:
            issues.append("Meta contains 'analysis' field (【分析】) – it should not be used in output")

        # 2.2 检查 section/大题 与答案必需性
        sec = section_label or ""
        is_choice_section = ("单选" in sec) or ("多选" in sec)

        # 对选择题，小题通常必须有答案
        if is_choice_section and not answer:
            issues.append("Choice question in section '{0}' has no 【答案】 meta".format(sec or "?"))

        # 对于非选择题，答案缺失不一定是致命错误，但可以提示
        if not is_choice_section and not answer:
            issues.append("Question has no 【答案】 meta (section='{0}')".format(sec or "?"))

        # 2.3 meta 与 TeX 的映射一致性
        has_answer_macro = "\\answer{" in tex_block
        has_explain_macro = "\\explain{" in tex_block

        if answer and not has_answer_macro:
            issues.append("Meta has answer but TeX is missing \\answer{}")
        if has_answer_macro and not answer:
            issues.append("TeX has \\answer{} but meta.answer is empty")

        if explain and not has_explain_macro:
            issues.append("Meta has explain but TeX is missing \\explain{}")
        if has_explain_macro and not explain:
            issues.append("TeX has \\explain{} but meta.explain is empty")

        # 2.4 确保 \\explain{} 不会偷偷吃进【分析】内容
        # 这里只做简单文本级检测：如果 raw_block 里有"【分析】"且 meta.explain 为空，则额外提示
        if "【分析】" in raw_block and not explain:
            issues.append("Raw block contains 【分析】 but meta.explain is empty – this question is treated as 'no explain'")

        # 2.5 检测超长 explain 内容（>500行）
        if explain:
            explain_lines = explain.count('\n') + 1
            if explain_lines > 500:
                issues.append(f"⚠️  LONG_EXPLAIN: {explain_lines} lines (>500) – may cause conversion issues")
            elif explain_lines > 200:
                issues.append(f"Long explain: {explain_lines} lines (>200) – consider simplification")

    return issues


def append_issue_log(
    slug: str,
    q_index: int,
    raw_block: str,
    tex_block: str,
    issues: List[str],
    meta: Optional[Dict[str, str]] = None,
    section_label: Optional[str] = None,
) -> None:
    """🆕 v1.6.4：将问题记录到 debug 日志（增强版）

    Args:
        slug: 试卷 slug
        q_index: 题号
        raw_block: 原始 Markdown 片段
        tex_block: 生成的 TeX 片段
        issues: 问题列表
        meta: 解析得到的元信息字典（可选）
        section_label: 当前大题标题（如 "单选题" / "多选题" 等）
    """
    if not issues:
        return

    debug_dir = Path("word_to_tex/output/debug")
    debug_dir.mkdir(parents=True, exist_ok=True)
    log_file = debug_dir / f"{slug}_issues.log"

    with log_file.open("a", encoding="utf-8") as f:
        f.write(f"{'='*80}\n")
        f.write(f"# Q{q_index} issues (section={section_label or 'N/A'})\n\n")

        # 简要 meta 概览（如果有）
        if meta is not None:
            # 只展示关键信息，避免日志太冗长
            summary_keys = ["answer", "difficulty", "topics", "explain", "analysis"]
            f.write("## Meta summary:\n")
            for key in summary_keys:
                if key in meta:
                    val = (meta.get(key) or "").strip()
                    if len(val) > 80:
                        val_display = val[:77] + "..."
                    else:
                        val_display = val
                    f.write(f"- {key}: {val_display}\n")
            f.write("\n")

        f.write("## Issues:\n")
        for issue in issues:
            f.write(f"- {issue}\n")

        f.write("\n## Raw Markdown:\n")
        f.write("```markdown\n")
        f.write(raw_block.strip() + "\n")
        f.write("```\n\n")

        f.write("## Generated TeX:\n")
        f.write("```tex\n")
        f.write(tex_block.strip() + "\n")
        f.write("```\n\n")


def init_issue_log(slug: str) -> None:
    """🆕 v1.6.3：初始化问题日志文件

    Args:
        slug: 试卷 slug
    """
    debug_dir = Path("word_to_tex/output/debug")
    debug_dir.mkdir(parents=True, exist_ok=True)
    log_file = debug_dir / f"{slug}_issues.log"

    # 清空旧日志
    with log_file.open("w", encoding="utf-8") as f:
        f.write(f"# Issue Detection Log for {slug}\n")
        f.write(f"# Generated: {Path(__file__).name} v{VERSION}\n")
        f.write(f"# Date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("\n")


# ==================== 🆕 v1.3 新增：自动验证函数 ====================

def assert_no_analysis_meta_in_auto_tex(slug: str) -> None:
    """🆕 v1.6.3：检查 auto 目录中是否残留【分析】meta 段

    Args:
        slug: 试卷 slug（如 "nanjing_2026_sep"）

    Raises:
        RuntimeError: 如果发现【分析】残留
    """
    root = Path("content/exams/auto") / slug
    if not root.exists():
        return

    for tex in root.rglob("*.tex"):
        txt = tex.read_text(encoding="utf-8")
        # 只拦类似【分析】这类 meta 段，而不是自然语言中的"分析"二字
        if re.search(r"【\s*分析\s*】", txt):
            raise RuntimeError(f"[ANALYSIS-META-LEFTOVER] {tex} still contains 【分析】.")


def validate_latex_output(tex_content: str) -> List[str]:
    """
    🆕 v1.3 新增：验证LaTeX输出，返回警告列表
    🆕 v1.6.3：增加【分析】残留检查

    Args:
        tex_content: 生成的LaTeX内容

    Returns:
        警告信息列表
    """
    warnings = []

    # 🆕 检查0：【分析】meta 段残留
    analysis_meta = re.findall(r'【\s*分析\s*】', tex_content)
    if analysis_meta:
        warnings.append(f"❌ 发现 {len(analysis_meta)} 处【分析】meta 段残留（应已被丢弃）")

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
🆕 v1.5 核心功能：
  - 修复数学公式双重包裹（$$\\(...\\)$$ → \\(...\\)）
  - 统一数学公式格式：所有 $$...$$ 转换为行内 \\(...\\)
  - 自动展开单行选项（> A... B... → 多行）
  - 强制检查【分析】残留（确保已被丢弃）

✅ v1.4 改进回顾：
  - 数学公式双重包裹修复（初版）
  - 单行选项自动展开（初版）

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
    parser.add_argument("--legacy-math", action="store_true", help="使用旧数学正则管线 (smart_inline_math 等) 进行数学处理，仅测试比较用")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    
    args = parser.parse_args()
    
    try:
        print(f"🔍 OCR 试卷预处理脚本 - {VERSION}")
        print("━" * 60)
        # 可选：切换到旧数学管线（A/B 测试用）
        _orig_process = None
        if args.legacy_math:
            print("⚠️ 使用 legacy 数学管线 (smart_inline_math 等) — 仅供比较测试")
            _orig_process = process_text_for_latex
            def _legacy_wrapper(t: str, is_math_heavy: bool = False):
                if not t:
                    return t
                # 前置清理（复用现行版本的初段逻辑）
                t = re.sub(r'\*\s*(\$[^$]+\$)\s*\*', r'\1', t)
                t = re.sub(r'\*([A-Za-z0-9])\*', r'\\emph{\1}', t)
                t = re.sub(r'[,，。\.;；]\s*故选[:：][ABCD]+[.。]?\s*$', '', t)
                t = re.sub(r'\n+故选[:：][ABCD]+[.。]?\s*$', '', t)
                t = re.sub(r'^\s*故选[:：][ABCD]+[.。]?\s*', '', t)
                t = re.sub(r'\n+故答案为[:：]', '', t)
                t = re.sub(r'^\s*故选[:：][ABCD]+[.。]?\s*$', '', t, flags=re.MULTILINE)
                t = re.sub(r'[，,]?\s*故选[:：]\s*[ABCD]+[。．.]*\s*$', '', t, flags=re.MULTILINE)
                t = re.sub(r'^【?详解】?[:：]?\s*', '', t)
                if '∵' in t or '∴' in t:
                    t = t.replace('∵', '$\\because$').replace('∴', '$\\therefore$')
                if not is_math_heavy:
                    t = escape_latex_special(t, in_math_mode=False)
                t = smart_inline_math(t)
                t = fix_double_wrapped_math(t)
                t = fix_inline_math_glitches(t)
                return t
            process_text_for_latex = _legacy_wrapper  # type: ignore

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

        # 🆕 v1.6.3：提取 slug 用于问题日志
        slug = md_file.stem.replace('_local', '').replace('_preprocessed', '').replace('_raw', '')

        print(f"\n📖 正在转换...")
        print(f"📝 标题: {title}")
        print(f"🏷️  Slug: {slug}")

        md_text = md_file.read_text(encoding='utf-8')
        tex_text = convert_md_to_examx(md_text, title, slug=slug, enable_issue_detection=True)
        
        # 🆕 v1.6 P0 修复：后处理清理
        tex_text = fix_array_boundaries(tex_text)
        tex_text = clean_residual_image_attrs(tex_text)
        
        # 🆕 v1.3：验证输出
        warnings = validate_latex_output(tex_text)
        integrity_issues = validate_math_integrity(tex_text)
        
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
        
        # 🆕 v1.6.3：显示问题日志信息
        debug_log = Path("word_to_tex/output/debug") / f"{slug}_issues.log"
        if debug_log.exists():
            log_size = debug_log.stat().st_size
            if log_size > 100:  # 如果日志文件有实质内容
                print(f"\n📋 问题检测日志: {debug_log}")
                print(f"   文件大小: {log_size:,} 字节")
            else:
                print(f"\n✅ 未检测到问题（日志为空）")

        # 🆕 v1.3：显示验证结果
        if warnings or integrity_issues:
            combined = warnings + integrity_issues
            print(f"\n⚠️  验证发现 {len(combined)} 个潜在问题:")
            for issue in combined:
                print(f"  {issue}")
            print("\n💡 建议：使用 AI Agent 检查并人工确认数学结构")
        else:
            print(f"\n✅ 验证通过：未发现明显问题 (结构 + 数学)" )

        print("\n💡 下一步:")
        print("  1. AI Agent 读取此文件进行精修")
        print("  2. AI Agent 查看 images/ 中的图片")
        print("  3. AI Agent 生成 TikZ 代码")
        print("  4. 输出最终的 exam_final.tex")
        if debug_log.exists() and debug_log.stat().st_size > 100:
            print(f"  5. 查看问题日志: {debug_log}")

        # 🆕 Prompt 1: 强制检查【分析】残留
        if slug:
            print(f"\n🔍 检查【分析】残留...")
            try:
                assert_no_analysis_meta_in_auto_tex(slug)
                print(f"✅ 未发现【分析】残留")
            except RuntimeError as e:
                print(f"❌ {e}")
                raise

        # 恢复原数学处理函数（若启用 legacy）
        if _orig_process is not None:
            process_text_for_latex = _orig_process  # type: ignore
        return 0
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


# ==================== 🆕 v1.6.3 新增：简单单元测试 ====================

def run_self_tests() -> bool:
    """🆕 v1.6.3：运行简单的自测用例

    Returns:
        True if all tests pass, False otherwise
    """
    print("🧪 运行自测用例...")
    print("=" * 60)

    all_passed = True

    # 测试 1：【分析】段被正确丢弃
    print("\n测试 1: 【分析】段被正确丢弃")
    test_md = """
# 一、单选题

1. 测试题目

A. 选项A
B. 选项B

【分析】这是分析内容，应该被丢弃
【详解】这是详解内容，应该被保留
【答案】A
"""
    result = convert_md_to_examx(test_md, "测试", slug="", enable_issue_detection=False)
    if "【分析】" in result:
        print("  ❌ FAILED: 【分析】未被丢弃")
        all_passed = False
    elif "这是分析内容" in result:
        print("  ❌ FAILED: 分析内容未被丢弃")
        all_passed = False
    elif "这是详解内容" not in result:
        print("  ❌ FAILED: 详解内容未被保留")
        all_passed = False
    else:
        print("  ✅ PASSED")

    # 测试 2：【详解】被正确保留到 \explain{}
    print("\n测试 2: 【详解】被正确保留到 \\explain{}")
    if "\\explain{" in result and "这是详解内容" in result:
        print("  ✅ PASSED")
    else:
        print("  ❌ FAILED: 详解未正确保留")
        all_passed = False

    # 测试 3：*$x$* 模式被正确修复
    print("\n测试 3: *$x$* 模式被正确修复")
    test_text = "这是一个 *$x$* 变量和 *y* 强调"
    result_text = process_text_for_latex(test_text, is_math_heavy=True)
    if "*$" in result_text or "$*" in result_text:
        print(f"  ❌ FAILED: *$x$* 模式未被修复")
        print(f"     结果: {result_text}")
        all_passed = False
    elif "\\emph{y}" not in result_text:
        print(f"  ❌ FAILED: *y* 未转换为 \\emph{{y}}")
        print(f"     结果: {result_text}")
        all_passed = False
    else:
        print("  ✅ PASSED")

    # 测试 4：全角括号被统一
    print("\n测试 4: 全角括号被统一")
    test_text = "这是（全角括号）和｛花括号｝"
    result_text = normalize_fullwidth_brackets(test_text)
    if "（" in result_text or "）" in result_text or "｛" in result_text or "｝" in result_text:
        print(f"  ❌ FAILED: 全角括号未被统一")
        print(f"     结果: {result_text}")
        all_passed = False
    else:
        print("  ✅ PASSED")

    # 测试 5：空 $$ 被清理
    print("\n测试 5: 空 $$ 被清理")
    test_text = "这是 $$ 空数学和 $x$ 正常数学"
    result_text = fix_inline_math_glitches(test_text)
    if "$$" in result_text:
        print(f"  ❌ FAILED: 空 $$ 未被清理")
        print(f"     结果: {result_text}")
        all_passed = False
    else:
        print("  ✅ PASSED")

    # 测试 6：内联图片被正确处理（旧版）
    print("\n测试 6: 内联图片被正确处理（旧版）")
    test_md = """
# 一、单选题

1. 已知集合![](image2.wmf)，则 A∩B 等于

A. 选项A
B. 选项B

【答案】A
"""
    result = convert_md_to_examx(test_md, "测试", slug="", enable_issue_detection=False)
    # 检查：不应该有残留的 ![](image2.wmf)
    if "![](image2.wmf)" in result:
        print(f"  ❌ FAILED: 内联图片标记未被转换")
        all_passed = False
    # 检查：应该有 IMAGE_TODO 注释
    elif "IMAGE_TODO" not in result or "image2.wmf" not in result:
        print(f"  ❌ FAILED: 内联图片未生成 IMAGE_TODO 占位符")
        all_passed = False
    else:
        print("  ✅ PASSED")

    # 测试 7：新格式 IMAGE_TODO_START/END 占位块
    print("\n测试 7: 新格式 IMAGE_TODO_START/END 占位块")
    test_md_new = """
# 一、单选题

1. 已知函数 f(x) 在区间 [0,1] 上单调递增，如图所示：

![](media/graph1.png)

则下列结论中正确的是

A. f(0) < f(1)
B. f(0) > f(1)

【答案】A

2. 集合 A={x|x>0}，集合 B 如图![](media/venn.wmf)所示，则 A∩B 等于

A. 选项A
B. 选项B

【答案】B
"""
    result_new = convert_md_to_examx(test_md_new, "测试新格式", slug="test2025", enable_issue_detection=False)

    # 检查1：不应该有残留的 Markdown 图片语法
    if "![](media/graph1.png)" in result_new or "![](media/venn.wmf)" in result_new:
        print(f"  ❌ FAILED: Markdown 图片语法未被转换")
        all_passed = False
    # 检查2：应该有两个 IMAGE_TODO_START 标记
    elif result_new.count("IMAGE_TODO_START") != 2:
        print(f"  ❌ FAILED: IMAGE_TODO_START 数量不正确 (期望2个，实际{result_new.count('IMAGE_TODO_START')}个)")
        all_passed = False
    # 检查3：应该有两个 IMAGE_TODO_END 标记
    elif result_new.count("IMAGE_TODO_END") != 2:
        print(f"  ❌ FAILED: IMAGE_TODO_END 数量不正确")
        all_passed = False
    # 检查4：第一个图片应该是独立图片 (inline=false)
    elif "inline=false" not in result_new:
        print(f"  ❌ FAILED: 未找到独立图片标记 (inline=false)")
        all_passed = False
    # 检查5：第二个图片应该是内联图片 (inline=true)
    elif "inline=true" not in result_new:
        print(f"  ❌ FAILED: 未找到内联图片标记 (inline=true)")
        all_passed = False
    # 检查6：应该包含 question_index 字段
    elif "question_index=" not in result_new:
        print(f"  ❌ FAILED: 未找到 question_index 字段")
        all_passed = False
    # 检查7：应该包含 AI_AGENT_REPLACE_ME 标记
    elif "AI_AGENT_REPLACE_ME" not in result_new:
        print(f"  ❌ FAILED: 未找到 AI_AGENT_REPLACE_ME 标记")
        all_passed = False
    # 检查8：应该包含 CONTEXT_BEFORE 或 CONTEXT_AFTER
    elif "CONTEXT_BEFORE" not in result_new and "CONTEXT_AFTER" not in result_new:
        print(f"  ❌ FAILED: 未找到上下文信息 (CONTEXT_BEFORE/AFTER)")
        all_passed = False
    # 检查9：ID 应该包含 slug 和题号
    elif "test2025-Q1" not in result_new or "test2025-Q2" not in result_new:
        print(f"  ❌ FAILED: 图片 ID 格式不正确 (应包含 slug-Q{n})")
        all_passed = False
    else:
        print("  ✅ PASSED")
        # 打印一个示例供检查
        print("\n  示例输出片段:")
        lines = result_new.split('\n')
        for i, line in enumerate(lines):
            if 'IMAGE_TODO_START' in line:
                # 打印该行及后续5行
                for j in range(i, min(i+6, len(lines))):
                    print(f"    {lines[j]}")
                break

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有测试通过！")
        return True
    else:
        print("❌ 部分测试失败")
        return False


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        success = run_self_tests()
        exit(0 if success else 1)
    else:
        exit(main())

