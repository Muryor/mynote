#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TXT/Markdown → LaTeX converter for MyMathLectureNotes exams.

Features:
- Detects questions, multi-line choices, and solution/answer markers.
- Supports sub-questions (1), (2), ... within a problem.
- Parses metadata tags: [difficulty=中], [tags=函数,极限], etc.
- Recognizes Markdown images: ![alt](path){width=0.4\linewidth} -> \includegraphics
- Emits LaTeX using the project's semantic macros (no layout commands).

Input conventions (example):
-----------------------------------------------------
# Ⅰ. 单选题
1. 复数 (1+5i)i 的虚部为（） {points=5} [difficulty=易]
A. -1
B. 0
C. 1
D. 6
Answer: C

# Ⅱ. 填空题
1. \int_0^1 x^2 dx = ____ {points=4}
Answer: 1/3

# Ⅲ. 解答题
1. 证明...（可插入图片）
![示意图](figs/demo.png){width=0.35\linewidth}
Solution: ...
Answer: 结果表达式
-----------------------------------------------------

Usage:
    python tools/txtmd_to_tex.py input.txt --out content/exams/exam02.tex

Notes:
- This script does not inject layout; keep content semantic.
- Compile with build.sh after import.

"""
import re, sys, argparse, io, os, textwrap
from pathlib import Path

SECTION_RE = re.compile(r'^\s*#\s*(.+)$')
QSTART_RE  = re.compile(r'^\s*(\d+)\.\s+(.*)$')
SUBQ_RE    = re.compile(r'^\s*[\(（](\d+)[\)）]\s*(.*)$')
OPT_RE     = re.compile(r'^\s*([A-D])[\.\)]\s+(.*)$')
KV_RE      = re.compile(r'\{([^}]+)\}')
IMG_RE     = re.compile(r'!\[(.*?)\]\((.*?)\)(?:\{(.*?)\})?')
META_KV_RE = re.compile(r'(\w+)\s*=\s*([^,]+)')

def parse_meta_braces(text):
    m = KV_RE.search(text or '')
    meta = {}
    if m:
        for k, v in META_KV_RE.findall(m.group(1)):
            meta[k.strip()] = v.strip()
    return meta

def strip_meta(text):
    return KV_RE.sub('', text).strip()

def to_latex_image(alt, path, opt):
    opt = opt.strip() if opt else ''
    width = None
    if 'width=' in opt:
        width = opt.split('width=')[1].split('}')[0]
    wopt = f'[width={width}]' if width else ''
    return f'\\begin{{center}}\\includegraphics{wopt}{{{path}}}\\end{{center}}'

def emit_header():
    return ""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('input')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    lines = Path(args.input).read_text(encoding='utf-8').splitlines()

    out = io.StringIO()
    current_section = None
    in_choices = False
    pending_opts = {}
    pending_q = None

    def flush_question():
        nonlocal pending_q, pending_opts, in_choices
        if not pending_q:
            return
        # Write question stem
        out.write("\\item " + pending_q['stem'])
        if pending_q.get('points'):
            out.write(f" \\points{{{pending_q['points']}}}")
        out.write("\n\n")
        # Choices
        if pending_q.get('choices'):
            out.write("\\begin{choices}\n")
            for key in ['A','B','C','D']:
                if key in pending_q['choices']:
                    out.write("\\choice " + pending_q['choices'][key] + "\n\n")
            out.write("\\end{choices}\n\n")
        # Image(s)
        for img in pending_q.get('images', []):
            out.write(img + "\n\n")
        # Solution / Answer
        if pending_q.get('solution'):
            out.write("\\begin{solutionbox}\n" + pending_q['solution'] + "\n\\end{solutionbox}\n\n")
        if pending_q.get('answer'):
            # Let grouping default via environment; caller may set [type]
            atext = pending_q['answer']
            out.write(f"\\answer{{{atext}}}\n\n")
        pending_q = None
        pending_opts = {}
        in_choices = False

    for raw in lines:
        line = raw.rstrip()

        # Section
        s = SECTION_RE.match(line)
        if s:
            flush_question()
            current_section = s.group(1).strip()
            out.write(f"\\section*{{{current_section}}}\n\n")
            if '单选' in current_section:
                out.write("\\begin{enumerate}\n\n")
            continue

        # Question start
        q = QSTART_RE.match(line)
        if q:
            flush_question()
            idx, rest = q.groups()
            meta = parse_meta_braces(rest)
            stem = strip_meta(rest)
            pending_q = {
                'index': int(idx),
                'stem': stem.strip(),
                'points': meta.get('points')
            }
            pending_q['choices'] = {}
            pending_q['images'] = []
            continue

        # Options
        o = OPT_RE.match(line)
        if o and pending_q is not None:
            k, v = o.groups()
            pending_q['choices'][k] = v.strip()
            continue

        # Images
        im = IMG_RE.search(line)
        if im and pending_q is not None:
            alt, path, opt = im.groups()
            pending_q.setdefault('images', []).append(to_latex_image(alt, path, opt))
            continue

        # Solution / Answer markers
        if line.strip().lower().startswith('solution:'):
            if pending_q is not None:
                pending_q['solution'] = line.split(':',1)[1].strip()
            continue
        if line.strip().lower().startswith('answer:'):
            if pending_q is not None:
                pending_q['answer'] = line.split(':',1)[1].strip()
            continue

        # Sub-questions within a problem
        sub = SUBQ_RE.match(line)
        if sub and pending_q is not None:
            k, v = sub.groups()
            pending_q['stem'] += f"\\\\（{k}）{v}"
            continue

        # Accumulate long lines into stem or solution if in block
        if pending_q is not None:
            if 'solution' in pending_q and pending_q['solution'] and not line.lower().startswith(('solution:','answer:')):
                pending_q['solution'] += "\n" + line
            else:
                pending_q['stem'] += "\n" + line

    # Flush last
    flush_question()

    # Close enumerate if last section was single-choice
    if current_section and '单选' in current_section:
        out.write("\\end{enumerate}\n")

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(out.getvalue(), encoding='utf-8')

if __name__ == "__main__":
    main()
