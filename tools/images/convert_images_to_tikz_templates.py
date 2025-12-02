#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
convert_images_to_tikz_templates.py (v2.0)

将 TeX 文件中以 \\includegraphics 引入的图片替换为 TikZ 模板。

功能：
- 在每个图片处寻找最近的 `\\begin{question}` / `\\end{question}`，提取题目上下文。
- 简单解析题目中的数学表达式，尝试提取变量名。
- 根据题目关键字（如 三角形 / 圆 / 函数 / 正方形）选择启发式 TikZ 模板，插入到 TeX 中。
- 用 `IMAGE_TODO_START` / `IMAGE_TODO_END` 包裹（包含 context），以便后续人工或 AI 进一步完善。

v2.0 改进：
- 自动添加 \\begin{center}...\\end{center} 包裹
- 转义 CONTEXT 注释中的 LaTeX 命令，避免干扰编译
- 排除 tabular 环境，避免误将表格替换为 TikZ
- 修复重复 VARIABLES 注释问题
- 修复 TikZ 中 \\x 双反斜杠问题

用法：
    python3 tools/images/convert_images_to_tikz_templates.py <tex_file>

注意：此脚本使用启发式规则生成模板，不能保证自动完美复现原图。
"""

import re
import sys
import argparse
from pathlib import Path
from typing import List, Tuple, Dict, Optional


def find_includegraphics_blocks(text: str) -> List[Tuple[int, int, re.Match]]:
    """返回所有 \\begin{center}...\\includegraphics[...]...\\end{center} 的匹配
    
    排除包含 tabular 环境的块（表格不应被替换）
    """
    pattern = re.compile(
        r"\\begin\{center\}([\s\S]*?)\\includegraphics\[(?P<opts>.*?)\]\{(?P<path>.*?)\}([\s\S]*?)\\end\{center\}",
        re.DOTALL
    )
    matches = []
    for m in pattern.finditer(text):
        block_content = m.group(0)
        # 排除包含 tabular 的块
        if r'\begin{tabular}' in block_content or r'\end{tabular}' in block_content:
            continue
        matches.append((m.start(), m.end(), m))
    return matches


def find_enclosing_question_range(text: str, pos: int) -> Tuple[int, int, str]:
    """给定文本位置 pos，找到包含该位置的最近前向 \\begin{question} 与后向 \\end{question} 的范围。
    """
    begin_pat = re.compile(r"\\begin\{question\}")
    end_pat = re.compile(r"\\end\{question\}")

    begins = [m.start() for m in begin_pat.finditer(text) if m.start() < pos]
    if not begins:
        return 0, len(text), text
    start = begins[-1]

    end_match = end_pat.search(text, pos)
    if not end_match:
        end_match = end_pat.search(text, start)
    if end_match:
        end = end_match.end()
    else:
        end = len(text)

    return start, end, text[start:end]


def extract_math_snippets(question_text: str) -> List[str]:
    """提取题目中的数学片段"""
    snippets = []
    snippets += re.findall(r"\\\((.+?)\\\)", question_text, flags=re.DOTALL)
    snippets += [g for g in re.findall(r"\$(.+?)\$", question_text, flags=re.DOTALL) if g]
    snippets += re.findall(r"\\\[(.+?)\\\]", question_text, flags=re.DOTALL)
    return snippets


def extract_variables_from_math(math_snippets: List[str]) -> List[str]:
    """从数学片段中抽取可能的变量名（启发式）"""
    vars_set = set()
    macros = {"frac", "sqrt", "sum", "log", "ln", "sin", "cos", "tan", "mathrm", "left", "right",
              "cdot", "times", "div", "pm", "mp", "leq", "geq", "neq", "approx", "equiv"}
    for s in math_snippets:
        cleaned = re.sub(r"\\[A-Za-z]+", " ", s)
        tokens = re.findall(r"([A-Za-z][A-Za-z0-9_]*)", cleaned)
        for t in tokens:
            if t.lower() in macros:
                continue
            if len(t) > 6:
                continue
            vars_set.add(t)
    return sorted(vars_set)


def detect_keywords(question_text: str, image_name: str) -> str:
    """根据题目文本和图片名启发式判断图形类型"""
    combined = (question_text + " " + image_name).lower()
    
    # 立体几何关键字
    if any(k in combined for k in ["棱柱", "棱锥", "棱台", "正方体", "长方体", "四面体", "prism", "pyramid"]):
        return "solid"
    if any(k in combined for k in ["正方形", "square"]):
        return "square"
    if any(k in combined for k in ["三角形", "三角", "triangle"]):
        return "triangle"
    if any(k in combined for k in ["圆心", "半径", "圆", "circle", "椭圆", "ellipse"]):
        return "circle"
    if any(k in combined for k in ["函数", "图像", "f(x)", "y=", "plot", "graph", "曲线"]):
        return "axes_curve"
    if any(k in combined for k in ["直线", "line", "向量"]):
        return "line"
    return "generic"


def generate_tikz_body(shape_type: str, variables: List[str]) -> str:
    """为给定形状生成 TikZ 主体（不包含 begin/end 环境和 VARIABLES 注释）"""
    
    if shape_type == 'solid':
        body = (
            "  % 示例：立体几何（三棱柱）\n"
            "  \\coordinate (A) at (0,0);\n"
            "  \\coordinate (B) at (2,0);\n"
            "  \\coordinate (C) at (1,1.5);\n"
            "  \\coordinate (A1) at (0.5,2.5);\n"
            "  \\coordinate (B1) at (2.5,2.5);\n"
            "  \\coordinate (C1) at (1.5,4);\n"
            "  \\draw (A) -- (B) -- (C) -- cycle;\n"
            "  \\draw (A1) -- (B1) -- (C1) -- cycle;\n"
            "  \\draw (A) -- (A1); \\draw (B) -- (B1); \\draw (C) -- (C1);\n"
            "  \\node[below left] at (A) {$A$};\n"
            "  \\node[below right] at (B) {$B$};\n"
            "  \\node[above] at (C) {$C$};\n"
            "  \\node[left] at (A1) {$A_1$};\n"
            "  \\node[right] at (B1) {$B_1$};\n"
            "  \\node[above] at (C1) {$C_1$};\n"
        )
    elif shape_type == 'square':
        body = (
            "  % 示例：正方形，顶点标记 A,B,C,D\n"
            "  \\draw (0,0) -- (2,0) -- (2,2) -- (0,2) -- cycle;\n"
            "  \\node[below left] at (0,0) {$A$};\n"
            "  \\node[below right] at (2,0) {$B$};\n"
            "  \\node[above right] at (2,2) {$C$};\n"
            "  \\node[above left] at (0,2) {$D$};\n"
        )
    elif shape_type == 'triangle':
        body = (
            "  % 示例：三角形 ABC\n"
            "  \\coordinate (A) at (0,0);\n"
            "  \\coordinate (B) at (3,0);\n"
            "  \\coordinate (C) at (1.2,2);\n"
            "  \\draw (A) -- (B) -- (C) -- cycle;\n"
            "  \\node[below left] at (A) {$A$};\n"
            "  \\node[below right] at (B) {$B$};\n"
            "  \\node[above] at (C) {$C$};\n"
        )
    elif shape_type == 'circle':
        body = (
            "  % 示例：以 O 为圆心的圆\n"
            "  \\fill (0,0) circle (1.5pt) node[below left] {$O$};\n"
            "  \\draw (0,0) circle (1.5cm);\n"
        )
    elif shape_type == 'axes_curve':
        body = (
            "  % 示例：坐标轴和示意曲线\n"
            "  \\draw[->] (-3,0) -- (3,0) node[right] {$x$};\n"
            "  \\draw[->] (0,-2) -- (0,2) node[above] {$y$};\n"
            "  % 示例曲线（抛物线）\n"
            "  \\draw[domain=-1.5:1.5, smooth, variable=\\x, blue] plot ({\\x}, {\\x*\\x});\n"
        )
    elif shape_type == 'line':
        body = (
            "  % 示例：直线 l\n"
            "  \\draw[->] (-2,-1) -- (2,1) node[right] {$l$};\n"
        )
    else:
        body = (
            "  % 通用占位：请根据原图手工或 AI 生成具体绘图代码\n"
            "  \\node[draw, minimum width=5cm, minimum height=3cm] {图略（请绘制）};\n"
        )

    return body


def escape_context(text: str) -> str:
    """转义 CONTEXT 注释中的 LaTeX 命令，避免干扰编译器"""
    # 将常见的 LaTeX 环境命令替换为安全文本
    text = text.replace('\\begin{', '[BEGIN ')
    text = text.replace('\\end{', '[END ')
    text = text.replace('\\item', '[ITEM]')
    text = text.replace('\\includegraphics', '[IMG]')
    text = text.replace('\\par', '[PAR]')
    # 限制长度
    if len(text) > 150:
        text = text[:150] + '...'
    return text


def make_image_todo_block(
    image_id: str,
    path: str,
    width_pct: int,
    qidx: int,
    context_before: str,
    context_after: str,
    variables: List[str],
    tikz_body: str
) -> str:
    """构造完整的 IMAGE_TODO 块，包含 center 环境包裹"""
    
    # 转义 context 中的 LaTeX 命令
    cb = escape_context(context_before.replace('\n', ' ').strip())
    ca = escape_context(context_after.replace('\n', ' ').strip())
    vars_line = ', '.join(variables) if variables else '(none)'

    block = (
        "\\begin{center}\n"
        f"% IMAGE_TODO_START id={image_id} path={path} width={width_pct}% inline=false question_index={qidx} sub_index=1\n"
        f"% CONTEXT_BEFORE: {cb}\n"
        f"% CONTEXT_AFTER: {ca}\n"
        "\\begin{tikzpicture}[scale=1.0]\n"
        f"  % ORIGINAL_IMAGE: {path}\n"
        f"  % VARIABLES: {vars_line}\n"
        f"{tikz_body}"
        "\\end{tikzpicture}\n"
        f"% IMAGE_TODO_END id={image_id}\n"
        "\\end{center}\n"
    )
    return block


def convert_file(tex_path: Path, dry_run: bool = False) -> int:
    """转换单个 TeX 文件中的图片为 TikZ 模板
    
    Args:
        tex_path: TeX 文件路径
        dry_run: 如果为 True，只显示将要转换的内容，不实际修改文件
        
    Returns:
        转换的图片数量
    """
    text = tex_path.read_text(encoding='utf-8')
    matches = find_includegraphics_blocks(text)
    
    if not matches:
        print(f"📄 {tex_path.name}: 未找到可转换的 \\includegraphics 块")
        return 0

    print(f"📄 {tex_path.name}: 找到 {len(matches)} 个图片块")
    
    if dry_run:
        for i, (start, end, m) in enumerate(matches, 1):
            img_path = m.group('path')
            print(f"  [{i}] {Path(img_path).name}")
        return len(matches)

    # 反向迭代替换（避免索引位移问题）
    new_text = text
    begin_positions = [m.start() for m in re.finditer(r"\\begin\{question\}", text)]
    question_img_counts: Dict[int, int] = {}

    for start, end, m in reversed(matches):
        opts = m.group('opts')
        img_path = m.group('path')

        # 解析宽度
        width_pct = 30
        wmatch = re.search(r"width\s*=\s*([0-9.]+)\\textwidth", opts)
        if wmatch:
            try:
                width_pct = int(round(float(wmatch.group(1)) * 100))
            except Exception:
                pass

        # 找题目范围
        qstart, qend, qtext = find_enclosing_question_range(text, start)
        qidx = sum(1 for p in begin_positions if p <= qstart)

        # 更新图片序号
        question_img_counts[qidx] = question_img_counts.get(qidx, 0) + 1
        img_idx = question_img_counts[qidx]

        # 生成 ID
        try:
            auto_idx = tex_path.parts.index('auto')
            slug = tex_path.parts[auto_idx + 1]
        except Exception:
            slug = tex_path.stem
        image_id = f"{slug}-Q{qidx}-img{img_idx}"

        # 上下文片段
        rel_pos = start - qstart
        before_snip = qtext[max(0, rel_pos - 200):rel_pos]
        after_snip = qtext[rel_pos:min(len(qtext), rel_pos + 200)]

        # 提取变量和选择模板
        math_snips = extract_math_snippets(qtext)
        variables = extract_variables_from_math(math_snips)
        shape_type = detect_keywords(qtext, Path(img_path).name)
        tikz_body = generate_tikz_body(shape_type, variables)

        # 构造替换块
        block = make_image_todo_block(
            image_id, img_path, width_pct, qidx,
            before_snip, after_snip, variables, tikz_body
        )

        new_text = new_text[:start] + block + new_text[end:]
        print(f"  ✓ Q{qidx}-img{img_idx}: {Path(img_path).name} → {shape_type}")

    # 备份并写入
    backup_path = Path(str(tex_path) + '.bak')
    backup_path.write_text(text, encoding='utf-8')
    tex_path.write_text(new_text, encoding='utf-8')

    print(f"  💾 备份: {backup_path.name}")
    return len(matches)


def main():
    parser = argparse.ArgumentParser(
        description='将 TeX 文件中的 \\includegraphics 替换为 TikZ 模板',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 转换单个文件
  python3 tools/images/convert_images_to_tikz_templates.py \\
      content/exams/auto/exam_2025/converted_exam.tex

  # 预览模式（不修改文件）
  python3 tools/images/convert_images_to_tikz_templates.py --dry-run \\
      content/exams/auto/exam_2025/converted_exam.tex

  # 批量转换
  python3 tools/images/convert_images_to_tikz_templates.py \\
      content/exams/auto/*/converted_exam.tex
"""
    )
    
    parser.add_argument(
        'files',
        nargs='+',
        type=Path,
        help='要处理的 TeX 文件'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='预览模式：只显示将要转换的内容，不修改文件'
    )

    args = parser.parse_args()

    print("━" * 60)
    print("🎨 图片转 TikZ 模板工具 v2.0")
    print("━" * 60)
    
    if args.dry_run:
        print("📋 预览模式（不会修改文件）\n")
    
    total = 0
    for tex_file in args.files:
        if not tex_file.exists():
            print(f"⚠️  文件不存在: {tex_file}")
            continue
        count = convert_file(tex_file, dry_run=args.dry_run)
        total += count

    print()
    print("━" * 60)
    if args.dry_run:
        print(f"📊 预览完成：共 {total} 个图片可转换")
    else:
        print(f"✅ 转换完成：共 {total} 个图片已替换为 TikZ 模板")
        print("\n💡 下一步：")
        print("  1. 运行 ./build.sh exam both 验证编译")
        print("  2. 根据原图完善 TikZ 代码")


if __name__ == '__main__':
    main()
