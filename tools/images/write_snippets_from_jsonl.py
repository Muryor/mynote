#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""根据已生成的 TikZ 代码 JSONL 将 snippet 写入规范目录。

用例场景：
  1. 已运行 export_image_jobs.py 生成 image_jobs.jsonl
  2. 外部 AI Agent 读取每个图片任务并生成 TikZ（不一定能 import 本仓库）
  3. Agent 输出统一的 generated_tikz.jsonl，格式：{"id": "...", "tikz_code": "..."}
  4. 本脚本合并两者，根据规范写入 {exam_dir}/tikz_snippets/{id}.tex

使用示例：
  python tools/images/write_snippets_from_jsonl.py \
    --jobs-file content/exams/auto/nanjing_2026_sep/image_jobs.jsonl \
    --tikz-file /path/to/generated_tikz.jsonl

可选覆盖目录（不推荐常用，仅调试）：
  python tools/images/write_snippets_from_jsonl.py \
    --jobs-file .../image_jobs.jsonl \
    --tikz-file generated_tikz.jsonl \
    --snippets-dir /tmp/manual_tikz

字段要求：
  image_jobs.jsonl 行对象至少包含 id + (tikz_snippets_dir/exam_dir/exam_prefix 三者之一)
  generated_tikz.jsonl 行对象至少包含 id + tikz_code

写入日志格式：
  [TikZ] write snippet: id=<id>  ->  <path>

退出码：
  0 正常完成
  1 缺少输入文件或解析失败
  2 写入过程中存在错误（仍可能部分成功）
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List
import sys

# Ensure repository root on sys.path for 'tools.images.utils'
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.images.utils import get_tikz_snippets_dir, write_tikz_snippet_to_dir


def load_jsonl(path: Path) -> List[Dict]:
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    items = []
    with path.open('r', encoding='utf-8') as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                items.append(obj)
            except json.JSONDecodeError as e:
                raise ValueError(f"解析 JSONL 失败 {path}:{line_no}: {e}") from e
    return items


def build_tikz_map(tikz_items: List[Dict]) -> Dict[str, str]:
    m = {}
    for obj in tikz_items:
        _id = obj.get('id')
        code = obj.get('tikz_code')
        if not _id or code is None:
            continue
        m[_id] = code
    return m


def main():
    parser = argparse.ArgumentParser(description='根据 generated TikZ JSONL 写入 snippet 文件')
    parser.add_argument('--jobs-file', type=Path, required=True, help='export_image_jobs.py 生成的 image_jobs.jsonl')
    parser.add_argument('--tikz-file', type=Path, required=True, help='AI 生成的 tikz 代码 JSONL，每行包含 id + tikz_code')
    parser.add_argument('--snippets-dir', type=Path, default=None,
                        help='强制所有 snippet 写入该目录（调试用，正常情况下不要提供）')
    parser.add_argument('--dry-run', action='store_true', help='只打印计划写入，不实际创建文件')

    args = parser.parse_args()

    try:
        jobs = load_jsonl(args.jobs_file)
        tikz_items = load_jsonl(args.tikz_file)
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return 1

    tikz_map = build_tikz_map(tikz_items)
    if not tikz_map:
        print("⚠️  tikz 文件中未解析到任何 (id, tikz_code) 记录")
        return 1

    print(f"读取 jobs 条目: {len(jobs)}")
    print(f"读取 tikz 条目: {len(tikz_map)}")

    missing = []
    written = 0
    errors = 0

    for job in jobs:
        image_id = job.get('id')
        if not image_id:
            continue
        code = tikz_map.get(image_id)
        if code is None:
            missing.append(image_id)
            continue
        try:
            if args.snippets_dir:
                target_dir = args.snippets_dir
            else:
                target_dir = get_tikz_snippets_dir(job)
            if args.dry_run:
                print(f"[DRY-RUN] would write: id={image_id} -> {target_dir / (image_id + '.tex')}")
            else:
                write_tikz_snippet_to_dir(image_id, code, target_dir)
            written += 1
        except Exception as e:
            print(f"✗ 写入失败 id={image_id}: {e}")
            errors += 1

    print("\n结果：")
    print(f"  ✓ 成功写入: {written}")
    print(f"  ✗ 写入错误: {errors}")
    print(f"  ☐ 缺少 tikz_code: {len(missing)}")
    if missing:
        print("  列表（前20）：" + ", ".join(missing[:20]))

    if errors > 0:
        return 2
    return 0


if __name__ == '__main__':
    exit(main())
