#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
image_handling.py - 图片处理模块 - 路径处理、占位符生成

从 ocr_to_examx.py 提取的共享工具函数，供 exam 和 handout 转换器使用。

生成时间: 自动提取
源文件: tools/core/ocr_to_examx.py
"""

from pathlib import Path
from typing import List, Dict, Tuple, Optional
import re
import shutil

# ============================================================
# 图片处理模块 - 路径处理、占位符生成
# ============================================================

IMAGE_PATTERN = re.compile(r"!\[\]\((images/[^)]+)\)(?:\{width=(\d+)%\})?")


IMAGE_PATTERN_WITH_ID = re.compile(
    r"!\[@@@([^\]]+)\]\(([^)]+)\)(?:\s*\{[^}]*\})?",
    re.MULTILINE | re.DOTALL,
)

IMAGE_PATTERN_NO_ID = re.compile(
    r"!\[\]\(([^)]+)\)(?:\s*\{[^}]*\})?",
    re.MULTILINE | re.DOTALL,
)


def find_markdown_and_images(input_path: Path) -> Tuple[Path, Optional[Path]]:
    """智能识别输入路径"""
    input_path = Path(input_path).resolve()
    
    if input_path.is_file() and input_path.suffix == '.md':
        md_file = input_path
        return md_file, detect_images_for_markdown(md_file)
    
    if input_path.is_dir():
        md_files = list(input_path.glob('*_local.md'))
        if not md_files:
            md_files = list(input_path.glob('*.md'))
        
        if not md_files:
            raise FileNotFoundError(f"在 {input_path} 中未找到 .md 文件")
        
        if len(md_files) > 1:
            print(f"⚠️  找到多个 .md 文件，使用：{md_files[0].name}")
        
        md_file = md_files[0]
        images_dir = detect_images_for_markdown(md_file)
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
    def clean_context(text: str, max_len: int = 80) -> str:
        r"""清理 CONTEXT 注释内容（增强版 v1.9.1）

        🆕 v1.9.1：
        - 增加最大长度到 80 字符（根据报告建议）
        - 更好地处理 LaTeX 环境命令
        - 去除 LaTeX 环境命令（\begin{...}、\end{...}）
        - 去除 LaTeX 命令（\xxx{...}）
        - 去除数学定界符 \(...\) 和 \[...\]
        - 截断到最多 max_len 字符
        - 检查括号平衡，如果不平衡则返回空字符串
        """
        if not text:
            return ""

        # 🆕 v1.9.1：更激进地去除 LaTeX 环境命令
        # 匹配 \begin{...} 或 \end{...}，并删除整个命令
        text = re.sub(r'\\begin\{[^}]+\}', '[ENV_START]', text)
        text = re.sub(r'\\end\{[^}]+\}', '[ENV_END]', text)

        # 去除 LaTeX 命令（\xxx{...}）
        text = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', text)

        # 去除数学定界符
        text = re.sub(r'\\\(|\\\)|\\\[|\\\]', '', text)

        # 去除多余的空格
        text = re.sub(r'\s+', ' ', text).strip()

        # 截断到第一个换行符
        if '\n' in text:
            text = text.split('\n')[0]

        # 🆕 v1.9.1：截断到最多 max_len 字符（默认 80）
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
    # 🆕 v1.8.4：转义路径中的特殊字符（下划线等）
    path_escaped = path.replace('_', '\\_') if path else ''
    
    if is_inline:
        # 内联图片：不使用 center 环境
        block = (
            f"\n% IMAGE_TODO_START id={img_id} path={path_escaped} width={width}% inline={inline} "
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
            f"% IMAGE_TODO_END id={img_id}\n"
        )
    else:
        # 独立图片：使用 center 环境
        block = (
            "\\begin{center}\n"
            f"% IMAGE_TODO_START id={img_id} path={path_escaped} width={width}% inline={inline} "
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
            "\\end{center}\n"  # 🆕 v1.7：不添加尾随空白行
        )

    return block


# 🆕 v1.9.9: P2-8 删除未使用的 merge_explanations 函数（死代码清理）




def infer_figures_dir(input_md: str) -> str:
    """根据 Markdown 文件名推断图片目录

    推断规则：
    1. 提取 md_path.stem 作为 prefix
    2. 去除常见后缀（_local, _preprocessed, _raw）
    3. 按顺序尝试以下候选目录：
       - word_to_tex/output/figures/{prefix}
       - word_to_tex/output/figures/{prefix}/media
    4. 返回第一个存在的目录，都不存在则返回空字符串

    Args:
        input_md: Markdown 文件路径

    Returns:
        推断出的图片目录路径，或空字符串
    """
    md_path = Path(input_md)

    # 提取文件名前缀（去除后缀）
    prefix = md_path.stem

    # 去除常见的 Markdown 文件后缀
    for suffix in ['_local', '_preprocessed', '_raw']:
        if prefix.endswith(suffix):
            prefix = prefix[:-len(suffix)]
            break

    # 候选目录列表（按优先级排序）
    candidates = [
        Path("word_to_tex/output/figures") / prefix,
        Path("word_to_tex/output/figures") / prefix / "media",
    ]

    # 返回第一个存在的目录
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return str(candidate)

    # 都不存在则返回空字符串
    return ""





# ============================================================
# 导出列表
# ============================================================

__all__ = [
    'IMAGE_PATTERN',
    'IMAGE_PATTERN_WITH_ID',
    'IMAGE_PATTERN_NO_ID',
    'find_markdown_and_images',
    'copy_images_to_output',
    'generate_image_todo_block',
    'infer_figures_dir',
]
