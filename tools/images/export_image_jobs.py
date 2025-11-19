#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
export_image_jobs.py - 从 converted_exam.tex 提取 IMAGE_TODO 块生成 JSONL

功能：
1. 解析 TeX 文件中的 IMAGE_TODO_START/END 注释块
2. 提取图片元数据（id, path, width, inline, context 等）
3. 生成 image_jobs.jsonl 供 AI Agent 批量处理

使用方法：
    # 单个文件
    python tools/images/export_image_jobs.py \\
        --files content/exams/auto/nanjing2026/converted_exam.tex \\
        --output word_to_tex/output/nanjing2026_image_jobs.jsonl

    # 多个文件
    python tools/images/export_image_jobs.py \\
        --files content/exams/auto/*/converted_exam.tex \\
        --output word_to_tex/output/all_image_jobs.jsonl

输出格式（JSONL）：
    每行一个 JSON 对象，包含：
    - id: 图片唯一标识符
    - exam_slug: 试卷 slug
    - tex_file: 来源 TeX 文件路径
    - question_index: 题号
    - sub_index: 小问编号
    - path: 图片相对路径
    - width_pct: 宽度百分比（整数）
    - inline: 是否为内联图片（布尔值）
    - context_before: 图片前文
    - context_after: 图片后文
    - todo_block_start_line: IMAGE_TODO_START 行号（1-based）
    - todo_block_end_line: IMAGE_TODO_END 行号（1-based）
"""

import re
import json
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple


def parse_kv_line(line: str) -> Dict[str, str]:
    """解析 IMAGE_TODO_START 行中的 key=value 对

    Args:
        line: IMAGE_TODO_START 注释行

    Returns:
        键值对字典

    Example:
        >>> parse_kv_line("% IMAGE_TODO_START id=test-Q1-img1 path=media/img.png width=60% inline=false")
        {'id': 'test-Q1-img1', 'path': 'media/img.png', 'width': '60%', 'inline': 'false'}
    """
    kv_dict = {}
    # 匹配 key=value 模式，value 可以包含路径字符
    pattern = r'(\w+)=([\w\-./]+%?)'
    matches = re.findall(pattern, line)
    for key, value in matches:
        kv_dict[key] = value
    return kv_dict


def extract_context_line(line: str, prefix: str) -> Optional[str]:
    """提取 CONTEXT_BEFORE/AFTER 行的内容

    Args:
        line: 注释行
        prefix: "CONTEXT_BEFORE" 或 "CONTEXT_AFTER"

    Returns:
        上下文文本，如果不匹配则返回 None
    """
    pattern = rf'%\s*{prefix}:\s*(.*)$'
    match = re.match(pattern, line)
    if match:
        return match.group(1).strip()
    return None


def extract_slug_from_path(tex_file: Path) -> str:
    """从 TeX 文件路径提取 exam_slug

    Args:
        tex_file: TeX 文件路径

    Returns:
        exam_slug，如果无法提取则返回 "unknown"

    Example:
        >>> extract_slug_from_path(Path("content/exams/auto/nanjing2026/converted_exam.tex"))
        'nanjing2026'
    """
    # 尝试从路径中提取 auto/<slug>/ 模式
    parts = tex_file.parts
    try:
        auto_idx = parts.index('auto')
        if auto_idx + 1 < len(parts):
            return parts[auto_idx + 1]
    except (ValueError, IndexError):
        pass

    # 如果无法从路径提取，返回文件名（去掉扩展名）
    return tex_file.stem.replace('_converted', '').replace('_exam', '')


def extract_slug_from_id(image_id: str) -> str:
    """从图片 ID 提取 exam_slug

    Args:
        image_id: 图片 ID，格式如 "nanjing2026-Q3-img1"

    Returns:
        exam_slug

    Example:
        >>> extract_slug_from_id("nanjing2026-Q3-img1")
        'nanjing2026'
    """
    # ID 格式：<slug>-Q<n>-img<m>
    match = re.match(r'^(.+?)-Q\d+', image_id)
    if match:
        return match.group(1)
    return "unknown"


def parse_image_todos(tex_file: Path) -> List[Dict]:
    """解析 TeX 文件中的所有 IMAGE_TODO 块

    Args:
        tex_file: TeX 文件路径

    Returns:
        图片任务列表，每个任务是一个字典
    """
    if not tex_file.exists():
        print(f"⚠️  文件不存在: {tex_file}")
        return []

    with open(tex_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    image_jobs = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i].strip()

        # 查找 IMAGE_TODO_START
        if line.startswith('% IMAGE_TODO_START'):
            start_line = i + 1  # 1-based line number

            # 解析 key=value 对
            kv_dict = parse_kv_line(line)

            # 检查必需字段
            if 'id' not in kv_dict:
                print(f"⚠️  警告: {tex_file}:{start_line} 缺少 id 字段，跳过")
                i += 1
                continue

            # 初始化任务对象
            job = {
                'id': kv_dict.get('id', 'unknown'),
                'exam_slug': extract_slug_from_id(kv_dict.get('id', '')),
                'tex_file': str(tex_file),
                'question_index': int(kv_dict.get('question_index', 0)),
                'sub_index': int(kv_dict.get('sub_index', 1)),
                'path': kv_dict.get('path', ''),
                'width_pct': int(kv_dict.get('width', '60%').rstrip('%')),
                'inline': kv_dict.get('inline', 'false').lower() == 'true',
                'context_before': '',
                'context_after': '',
                'todo_block_start_line': start_line,
                'todo_block_end_line': 0
            }

            # 如果从 ID 无法提取 slug，尝试从路径提取
            if job['exam_slug'] == 'unknown':
                job['exam_slug'] = extract_slug_from_path(tex_file)

            # 继续读取后续行，查找 CONTEXT 和 IMAGE_TODO_END
            i += 1
            while i < n:
                current_line = lines[i].strip()

                # 提取 CONTEXT_BEFORE
                context_before = extract_context_line(current_line, 'CONTEXT_BEFORE')
                if context_before:
                    job['context_before'] = context_before
                    i += 1
                    continue

                # 提取 CONTEXT_AFTER
                context_after = extract_context_line(current_line, 'CONTEXT_AFTER')
                if context_after:
                    job['context_after'] = context_after
                    i += 1
                    continue

                # 找到 IMAGE_TODO_END
                if current_line.startswith('% IMAGE_TODO_END'):
                    job['todo_block_end_line'] = i + 1  # 1-based
                    image_jobs.append(job)
                    break

                i += 1

            # 如果没有找到 IMAGE_TODO_END，记录警告
            if job['todo_block_end_line'] == 0:
                print(f"⚠️  警告: {tex_file}:{start_line} IMAGE_TODO_START 没有匹配的 END，跳过")
                continue

        i += 1

    return image_jobs


def export_image_jobs(tex_files: List[Path], output_file: Path) -> int:
    """导出所有图片任务到 JSONL 文件

    Args:
        tex_files: TeX 文件列表
        output_file: 输出 JSONL 文件路径

    Returns:
        导出的任务数量
    """
    all_jobs = []

    for tex_file in tex_files:
        print(f"📄 处理文件: {tex_file}")
        jobs = parse_image_todos(tex_file)
        print(f"   找到 {len(jobs)} 个图片任务")
        all_jobs.extend(jobs)

    if not all_jobs:
        print("\n⚠️  未找到任何图片任务")
        # 创建空文件
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text('', encoding='utf-8')
        return 0

    # 写入 JSONL
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        for job in all_jobs:
            f.write(json.dumps(job, ensure_ascii=False) + '\n')

    print(f"\n✅ 成功导出 {len(all_jobs)} 个图片任务到: {output_file}")
    return len(all_jobs)


def main():
    parser = argparse.ArgumentParser(
        description='从 converted_exam.tex 提取 IMAGE_TODO 块生成 JSONL',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例：
  # 单个文件
  python tools/images/export_image_jobs.py \\
      --files content/exams/auto/nanjing2026/converted_exam.tex \\
      --output word_to_tex/output/nanjing2026_image_jobs.jsonl

  # 多个文件（使用 glob）
  python tools/images/export_image_jobs.py \\
      --files content/exams/auto/*/converted_exam.tex \\
      --output word_to_tex/output/all_image_jobs.jsonl

  # 自动输出到同目录
  python tools/images/export_image_jobs.py \\
      --files content/exams/auto/nanjing2026/converted_exam.tex
        """
    )

    parser.add_argument(
        '--files',
        nargs='+',
        type=Path,
        required=True,
        help='要处理的 TeX 文件列表'
    )

    parser.add_argument(
        '--output',
        type=Path,
        default=None,
        help='输出 JSONL 文件路径（默认：与第一个输入文件同目录的 image_jobs.jsonl）'
    )

    args = parser.parse_args()

    # 确定输出文件路径
    if args.output is None:
        # 默认输出到第一个文件的同目录
        first_file = args.files[0]
        args.output = first_file.parent / 'image_jobs.jsonl'

    print("━" * 60)
    print("📸 IMAGE_TODO 导出工具")
    print("━" * 60)
    print(f"输入文件: {len(args.files)} 个")
    print(f"输出文件: {args.output}")
    print()

    # 导出任务
    count = export_image_jobs(args.files, args.output)

    print("\n" + "━" * 60)
    if count > 0:
        print(f"✅ 导出完成，共 {count} 个图片任务")
        print(f"📄 输出文件: {args.output}")
        print("\n💡 下一步:")
        print("  1. AI Agent 读取 image_jobs.jsonl")
        print("  2. 对每个任务，使用 view 工具查看图片")
        print("  3. 生成对应的 TikZ 代码")
        print("  4. 替换 TeX 文件中的 TODO 占位符")
    else:
        print("⚠️  未找到任何图片任务")

    return 0 if count >= 0 else 1


if __name__ == '__main__':
    exit(main())
