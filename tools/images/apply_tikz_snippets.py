#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
apply_tikz_snippets.py - 将 AI 生成的 TikZ 代码回填到 converted_exam.tex

功能：
1. 从 snippets 目录加载所有 TikZ 代码片段（{id}.tex）
2. 解析 TeX 文件中的 IMAGE_TODO_START/END 块
3. 用对应的 TikZ 代码替换占位符
4. 保留 IMAGE_TODO_START/END 注释用于追踪

使用方法：
    # 覆盖原文件
    python tools/images/apply_tikz_snippets.py \\
        --tex-file content/exams/auto/nanjing2026/converted_exam.tex \\
        --snippets-dir word_to_tex/output/tikz_snippets

    # 输出到新文件
    python tools/images/apply_tikz_snippets.py \\
        --tex-file content/exams/auto/nanjing2026/converted_exam.tex \\
        --snippets-dir word_to_tex/output/tikz_snippets \\
        --output content/exams/auto/nanjing2026/converted_exam_tikz.tex

TikZ 片段格式：
    文件名：{id}.tex（例如：nanjing2026-Q3-img1.tex）
    内容：完整的 TikZ 环境，例如：
        \\begin{tikzpicture}[scale=1.0]
          \\draw[->] (-3,0) -- (3,0) node[right] {$x$};
          \\draw[->] (0,-2) -- (0,2) node[above] {$y$};
        \\end{tikzpicture}
"""

import re
import argparse
import shutil
from pathlib import Path
from typing import Dict, Optional, Tuple


def load_tikz_snippets(snippets_dir: Path) -> Dict[str, str]:
    """加载所有 TikZ 代码片段

    Args:
        snippets_dir: TikZ 片段目录

    Returns:
        字典 {id: tikz_code}
    """
    if not snippets_dir.exists():
        print(f"⚠️  警告: snippets 目录不存在: {snippets_dir}")
        return {}

    tikz_map = {}
    tex_files = list(snippets_dir.glob('*.tex'))

    if not tex_files:
        print(f"⚠️  警告: {snippets_dir} 中未找到 .tex 文件")
        return {}

    for tex_file in tex_files:
        # 文件名（不含扩展名）作为 id
        snippet_id = tex_file.stem
        try:
            tikz_code = tex_file.read_text(encoding='utf-8')
            tikz_map[snippet_id] = tikz_code
            print(f"  ✓ 加载 snippet: {snippet_id}")
        except Exception as e:
            print(f"  ✗ 加载失败 {tex_file.name}: {e}")

    return tikz_map


def parse_image_todo_start(line: str) -> Optional[str]:
    """从 IMAGE_TODO_START 行解析出 id

    Args:
        line: IMAGE_TODO_START 注释行

    Returns:
        图片 id，如果解析失败返回 None

    Example:
        >>> parse_image_todo_start("% IMAGE_TODO_START id=test-Q1-img1 path=...")
        'test-Q1-img1'
    """
    match = re.search(r'id=([^\s]+)', line)
    if match:
        return match.group(1)
    return None


def apply_tikz_to_tex(tex_file: Path, tikz_map: Dict[str, str], output_file: Optional[Path] = None) -> Tuple[int, int, int]:
    """将 TikZ 代码应用到 TeX 文件

    Args:
        tex_file: 输入 TeX 文件
        tikz_map: TikZ 代码映射 {id: code}
        output_file: 输出文件路径（None 表示覆盖原文件）

    Returns:
        (替换数量, 跳过数量, 总 TODO 数量)
    """
    if not tex_file.exists():
        raise FileNotFoundError(f"TeX 文件不存在: {tex_file}")

    with open(tex_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    output_lines = []
    i = 0
    n = len(lines)

    replaced_count = 0
    skipped_count = 0
    total_todos = 0

    while i < n:
        line = lines[i]

        # 检查是否为 IMAGE_TODO_START
        if '% IMAGE_TODO_START' in line:
            total_todos += 1

            # 解析 id
            image_id = parse_image_todo_start(line)

            if image_id is None:
                print(f"⚠️  警告: 第 {i+1} 行无法解析 id，保留原样")
                output_lines.append(line)
                i += 1
                continue

            # 保留 IMAGE_TODO_START 行
            output_lines.append(line)
            i += 1

            # 收集 CONTEXT 行（保留）
            context_lines = []
            while i < n and (lines[i].strip().startswith('% CONTEXT_BEFORE:') or
                            lines[i].strip().startswith('% CONTEXT_AFTER:')):
                context_lines.append(lines[i])
                i += 1

            # 写入 CONTEXT 行
            output_lines.extend(context_lines)

            # 检查是否有对应的 TikZ snippet
            if image_id in tikz_map:
                # 替换：插入 TikZ 代码
                tikz_code = tikz_map[image_id]
                # 确保 TikZ 代码以换行结尾
                if not tikz_code.endswith('\n'):
                    tikz_code += '\n'
                output_lines.append(tikz_code)
                replaced_count += 1

                # 跳过原始的 \begin{tikzpicture} ... \end{tikzpicture} 和 TODO 注释
                # 一直跳到 IMAGE_TODO_END
                while i < n:
                    current_line = lines[i]
                    if '% IMAGE_TODO_END' in current_line:
                        # 保留 IMAGE_TODO_END 行
                        output_lines.append(current_line)
                        i += 1
                        break
                    # 跳过这一行（占位符内容）
                    i += 1
            else:
                # 没有对应的 snippet，保留原样
                print(f"⚠️  警告: 缺少 snippet: id={image_id}（第 {i} 行）")
                skipped_count += 1

                # 原样复制直到 IMAGE_TODO_END
                while i < n:
                    current_line = lines[i]
                    output_lines.append(current_line)
                    if '% IMAGE_TODO_END' in current_line:
                        i += 1
                        break
                    i += 1
        else:
            # 非 IMAGE_TODO 块，原样复制
            output_lines.append(line)
            i += 1

    # 写入输出文件
    if output_file is None:
        output_file = tex_file

    # 如果覆盖原文件，先备份
    if output_file == tex_file:
        backup_file = tex_file.with_suffix('.tex.bak')
        shutil.copy2(tex_file, backup_file)
        print(f"\n📦 备份原文件: {backup_file}")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)

    return replaced_count, skipped_count, total_todos


def main():
    parser = argparse.ArgumentParser(
        description='将 AI 生成的 TikZ 代码回填到 converted_exam.tex',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例：
  # 覆盖原文件（会自动备份为 .tex.bak）
  python tools/images/apply_tikz_snippets.py \\
      --tex-file content/exams/auto/nanjing2026/converted_exam.tex \\
      --snippets-dir word_to_tex/output/tikz_snippets

  # 输出到新文件
  python tools/images/apply_tikz_snippets.py \\
      --tex-file content/exams/auto/nanjing2026/converted_exam.tex \\
      --snippets-dir word_to_tex/output/tikz_snippets \\
      --output content/exams/auto/nanjing2026/converted_exam_tikz.tex

TikZ 片段格式：
  文件名：{id}.tex（例如：nanjing2026-Q3-img1.tex）
  内容：完整的 TikZ 环境，例如：
      \\begin{tikzpicture}[scale=1.0]
        \\draw[->] (-3,0) -- (3,0) node[right] {$x$};
        \\draw[->] (0,-2) -- (0,2) node[above] {$y$};
      \\end{tikzpicture}
        """
    )

    parser.add_argument(
        '--tex-file',
        type=Path,
        required=True,
        help='目标 TeX 文件路径'
    )

    parser.add_argument(
        '--snippets-dir',
        type=Path,
        required=False,
        default=None,
        help='TikZ 片段目录（包含 {id}.tex 文件）。若未提供，默认使用 TeX 文件所在目录的 tikz_snippets 子目录'
    )

    parser.add_argument(
        '--output',
        type=Path,
        default=None,
        help='输出文件路径（默认覆盖原文件）'
    )

    args = parser.parse_args()

    print("━" * 60)
    print("🎨 TikZ 代码回填工具")
    print("━" * 60)
    print(f"输入文件: {args.tex_file}")
    # 推断 snippets 目录：优先使用显式参数，否则使用 tex 文件所在目录的 tikz_snippets
    if args.snippets_dir is None:
        inferred = args.tex_file.parent / 'tikz_snippets'
        args.snippets_dir = inferred
    print(f"Snippets 目录: {args.snippets_dir.resolve()}")
    if args.output:
        print(f"输出文件: {args.output}")
    else:
        print(f"输出文件: {args.tex_file} (覆盖)")
    print()

    # 加载 TikZ snippets
    print("📂 加载 TikZ 片段...")
    tikz_map = load_tikz_snippets(args.snippets_dir)
    print(f"✓ 加载了 {len(tikz_map)} 个 TikZ 片段")
    print()

    # 应用 TikZ 代码
    print("🔄 处理 TeX 文件...")
    try:
        replaced, skipped, total = apply_tikz_to_tex(
            args.tex_file,
            tikz_map,
            args.output
        )

        print("\n" + "━" * 60)
        print("✅ 处理完成")
        print("━" * 60)
        print(f"📊 统计信息:")
        print(f"  - 总 IMAGE_TODO 数量: {total}")
        print(f"  - 成功替换: {replaced}")
        print(f"  - 跳过（缺少 snippet）: {skipped}")

        if args.output:
            print(f"\n📄 输出文件: {args.output}")
        else:
            print(f"\n📄 已更新: {args.tex_file}")

        if skipped > 0:
            print(f"\n⚠️  注意: 有 {skipped} 个图片缺少 TikZ 代码，请检查上方警告信息")
            print("💡 提示: 为缺失的图片生成 TikZ 代码后，再次运行此脚本")

        return 0 if skipped == 0 else 1

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
