#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown → TeX → Validate Pipeline

快速回归工具，用于开发和调试阶段。
将 Markdown 转换为 TeX 并可选地进行预编译验证。

使用示例：
    # 基本用法（转换 + 校验）
    python tools/run_pipeline.py input.md --slug demo-2025

    # 只转换，不校验
    python tools/run_pipeline.py input.md --slug demo --no-validate

    # 指定输出路径
    python tools/run_pipeline.py input.md --slug demo --out-tex output/result.tex

    # 自定义标题
    python tools/run_pipeline.py input.md --slug demo --title "2025年测试卷"
"""

import argparse
import sys
from pathlib import Path

# 将 tools 目录添加到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.core.ocr_to_examx import convert_md_to_examx
from tools.validate_tex import TeXValidator


def run_pipeline(
    input_md: str,
    slug: str,
    title: str,
    out_tex: str,
    do_validate: bool,
    enable_issue_detection: bool,
) -> int:
    """运行完整的转换和校验管道

    Args:
        input_md: 输入 Markdown 文件路径
        slug: 试卷 slug/id
        title: 试卷标题
        out_tex: 输出 TeX 文件路径
        do_validate: 是否执行校验
        enable_issue_detection: 是否启用 issue 检测

    Returns:
        退出码：0=成功，1=转换失败，2=校验失败
    """
    # 检查输入文件
    md_path = Path(input_md)
    if not md_path.is_file():
        print(f"❌ Input Markdown file not found: {md_path}", file=sys.stderr)
        return 1

    # 确定输出路径
    if not out_tex:
        out_tex = str(md_path.with_suffix(".tex"))
    out_path = Path(out_tex)

    # 确定 slug 和 title
    if not slug:
        slug = md_path.stem
    if not title:
        title = md_path.stem

    print(f"📄 Input:  {md_path}")
    print(f"📝 Output: {out_path}")
    print(f"🏷️  Slug:   {slug}")
    print(f"📌 Title:  {title}")
    print()

    # Step 1: 读取 Markdown 文件
    try:
        md_text = md_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"❌ Failed to read Markdown file: {e}", file=sys.stderr)
        return 1

    # Step 2: 转换 Markdown → TeX
    print("🔄 Converting Markdown to TeX...")
    try:
        tex_content = convert_md_to_examx(
            md_text,
            title=title,
            slug=slug,
            enable_issue_detection=enable_issue_detection,
        )
    except Exception as e:
        print(f"❌ Failed to convert Markdown: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

    # Step 3: 写入 TeX 文件
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(tex_content, encoding="utf-8")
        print(f"✅ TeX file generated: {out_path}")
        print(f"   ({len(tex_content)} characters, {len(tex_content.splitlines())} lines)")
        print()
    except Exception as e:
        print(f"❌ Failed to write TeX file: {e}", file=sys.stderr)
        return 1

    # Step 4: 校验（可选）
    if do_validate:
        print("🔍 Running validation...")
        print("-" * 60)
        validator = TeXValidator(str(out_path))
        validation_ok = validator.validate()
        print("-" * 60)
        print()

        if validation_ok:
            print("✅ Pipeline succeeded: converted and validated")
            return 0
        else:
            print("⚠️  Pipeline completed with validation errors", file=sys.stderr)
            return 2
    else:
        print("⏭️  Validation skipped (--no-validate)")
        print("✅ Pipeline succeeded: conversion only")
        return 0


def main(argv=None) -> int:
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="Run Markdown → TeX → Validate pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 基本用法（转换 + 校验）
  %(prog)s demo.md --slug 2025-demo

  # 只转换，不校验
  %(prog)s demo.md --slug 2025-demo --no-validate

  # 指定输出路径和标题
  %(prog)s input.md --slug exam-001 --title "期末测试" --out-tex output/exam.tex

  # 禁用 issue 检测
  %(prog)s input.md --slug exam-001 --no-issue-detection
        """,
    )

    parser.add_argument(
        "input_md",
        help="Path to input Markdown file",
    )

    parser.add_argument(
        "--slug",
        default="",
        help="Slug/ID for this paper (default: derived from filename)",
    )

    parser.add_argument(
        "--title",
        default="",
        help="Title for this paper (default: derived from filename)",
    )

    parser.add_argument(
        "--out-tex",
        default="",
        help="Output TeX file path (default: same as input with .tex extension)",
    )

    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Only convert, skip validate_tex step",
    )

    parser.add_argument(
        "--no-issue-detection",
        action="store_true",
        help="Disable issue detection in ocr_to_examx",
    )

    args = parser.parse_args(argv)

    return run_pipeline(
        input_md=args.input_md,
        slug=args.slug,
        title=args.title,
        out_tex=args.out_tex,
        do_validate=not args.no_validate,
        enable_issue_detection=not args.no_issue_detection,
    )


if __name__ == "__main__":
    sys.exit(main())
