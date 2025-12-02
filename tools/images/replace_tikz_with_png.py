#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
replace_tikz_with_png.py

扫描 TeX 文件中的 IMAGE_TODO / TikZ 占位块，并将其替换为 \includegraphics 指令。
- 优先从 `ORIGINAL_IMAGE` 注释中取原始图片路径
- 回退到 IMAGE_TODO 的 `path=` 字段
- 使用 `width=NN%` 转为 `0.NN\\textwidth`，默认 0.30\\textwidth
- 备份原文件为 `<file>.bak`

用法：
    python3 tools/images/replace_tikz_with_png.py <tex_file> [...]

注意：在替换前请确保原始图片文件存在于仓库中。
"""

import re
import sys
from pathlib import Path

BLOCK_RE = re.compile(r"\\begin\{center\}.*?% IMAGE_TODO_START(?P<meta>.*?)% IMAGE_TODO_END.*?\\end\{center\}", re.DOTALL)
ORIG_RE = re.compile(r"%\s*ORIGINAL_IMAGE:\s*(?P<p>\S+)")
PATH_RE = re.compile(r"path=(?P<p>\S+)")
WIDTH_PCT_RE = re.compile(r"width\s*=\s*([0-9]+)%")
WIDTH_TEX_RE = re.compile(r"width\s*=\s*([0-9.]+)\\\\textwidth")


def make_includegraphics_line(img_path: str, width_str: str) -> str:
    return f"\\begin{{center}}\n\\includegraphics[width={width_str}]{{{img_path}}}\n\\end{{center}}\n"


def replace_in_text(text: str) -> (str, int):
    replaced = 0
    new_text = text
    matches = list(BLOCK_RE.finditer(text))
    if not matches:
        return text, 0
    for m in reversed(matches):
        block = m.group(0)
        meta = m.group('meta')
        img_path = None
        # search ORIGINAL_IMAGE first
        mo = ORIG_RE.search(block)
        if mo:
            img_path = mo.group('p')
        else:
            mo = PATH_RE.search(block)
            if mo:
                img_path = mo.group('p')
        if not img_path:
            print("[WARN] no path found for IMAGE_TODO block; skipping replacement")
            continue
        # cleanup braces
        img_path = img_path.strip()
        if img_path.startswith('{') and img_path.endswith('}'):
            img_path = img_path[1:-1]
        # find width
        w = WIDTH_PCT_RE.search(block)
        if w:
            pct = int(w.group(1))
            width_str = f"{pct/100.0:.2f}\\textwidth"
        else:
            w2 = WIDTH_TEX_RE.search(block)
            if w2:
                width_str = f"{float(w2.group(1)):.2f}\\textwidth"
            else:
                width_str = "0.30\\textwidth"
        repl = make_includegraphics_line(img_path, width_str)
        new_text = new_text[:m.start()] + repl + new_text[m.end():]
        replaced += 1
    return new_text, replaced


def replace_file(path: Path) -> int:
    text = path.read_text(encoding='utf-8')
    new_text, count = replace_in_text(text)
    if count > 0:
        bak = path.with_suffix(path.suffix + '.bak')
        bak.write_text(text, encoding='utf-8')
        path.write_text(new_text, encoding='utf-8')
        print(f"Replaced {count} blocks in {path}; backup at {bak}")
    else:
        print(f"No IMAGE_TODO/TikZ blocks replaced in {path}")
    return count


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: replace_tikz_with_png.py <tex_file> [...]")
        sys.exit(1)
    total = 0
    for arg in sys.argv[1:]:
        p = Path(arg)
        if not p.exists():
            print(f"[ERR] file not found: {p}")
            continue
        total += replace_file(p)
    print(f"Total replaced: {total}")
