#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Thin modular entrypoint for Markdown → examx LaTeX conversion.

Phase-A bridge:
- Reuses legacy convert_md_to_examx implementation for now
- Exposes the same CLI as ocr_to_examx.py
- Intended to be switched to tools.lib modules in Phase-B
"""

import argparse
import sys
from pathlib import Path

# Prefer shared libs on sys.path
CORE_DIR = Path(__file__).resolve().parent
TOOLS_DIR = CORE_DIR.parent
ROOT_DIR = TOOLS_DIR.parent
sys.path.insert(0, str(ROOT_DIR))

# Modular converters
from tools.converters import ExamConverter


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Convert Markdown to examx LaTeX (modular entry)")
    parser.add_argument("input_md", help="Input Markdown file")
    parser.add_argument("output_tex", help="Output TeX file")
    parser.add_argument("--title", default="", help="Paper title")
    parser.add_argument("--slug", default="", help="Slug/ID for this paper")
    parser.add_argument("--figures-dir", default="", help="Figures directory (for image copy)")
    parser.add_argument("--no-issue-detection", action="store_true", help="Disable issue detection")
    args = parser.parse_args(argv)

    md_path = Path(args.input_md)
    if not md_path.is_file():
        print(f"❌ Input Markdown not found: {md_path}", file=sys.stderr)
        return 1

    if not args.slug:
        args.slug = md_path.stem
    if not args.title:
        args.title = md_path.stem

    try:
        converter = ExamConverter(
            input_md=md_path,
            output_tex=Path(args.output_tex),
            title=args.title,
            slug=args.slug,
            enable_issue_detection=not args.no_issue_detection,
            figures_dir=args.figures_dir,
        )
        result = converter.convert()
    except Exception as e:
        print(f"❌ Conversion failed: {e}", file=sys.stderr)
        return 1

    if result.output_path:
        print(f"✅ Generated: {result.output_path} ({len(result.tex.splitlines())} lines)")
    else:
        print("✅ Conversion succeeded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
