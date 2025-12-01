#!/usr/bin/env python3
"""
Extract a LaTeX exam title from a converted_exam.tex file.
Prints a sanitized filename-safe string to stdout.

Usage:
  python3 tools/utils/get_exam_title.py path/to/converted_exam.tex
"""
import re
import sys
from pathlib import Path
import unicodedata


def sanitize(name: str) -> str:
    # Normalize using NFC (preserves characters like Ⅰ, Ⅱ, Ⅲ)
    # Note: NFKC would convert Ⅰ→I, Ⅱ→II which is undesirable
    name = unicodedata.normalize('NFC', name).strip()
    # Remove braces and awkward punctuation
    name = re.sub(r'[{}]+', '', name)
    # Remove characters not allowed in filenames on macOS/Unix
    name = re.sub(r'[\\/:*?"<>|]+', '', name)
    # Replace whitespace sequences with underscore
    name = re.sub(r'\s+', '_', name)
    # Truncate to a safe length
    return name[:240]


def get_title(tex_path: Path) -> str:
    txt = tex_path.read_text(encoding='utf-8', errors='ignore')
    m = re.search(r'\\examxtitle\{(.+?)\}', txt, re.S)
    if m:
        return sanitize(m.group(1))
    # fallback to \title{...}
    m2 = re.search(r'\\title\{(.+?)\}', txt, re.S)
    if m2:
        return sanitize(m2.group(1))
    # final fallback: file stem
    return sanitize(tex_path.stem)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: get_exam_title.py /path/to/converted_exam.tex", file=sys.stderr)
        sys.exit(2)
    p = Path(sys.argv[1])
    if not p.is_file():
        print("", file=sys.stderr)
        sys.exit(2)
    print(get_title(p))


if __name__ == '__main__':
    main()
