#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convert loosely formatted TeX/Markdown-like exam text into project format:
- Split by numbered questions: "1." / "1．"
- Options like "A. xxx" / "A．xxx" / "A、xxx"
- Meta tags: 【答案】, 【难度】, 【知识点】, 【详解】, 【分析】
Output blocks use exam-zh's `question/choices` plus unified metadata
(\topics, \difficulty, \explain).
"""
import re, sys, io, pathlib

def convert_block_to_question(block: str) -> str:
    b = block.strip()
    if not b:
        return ""
    opt_pat = re.compile(r"(?m)^[\sA．、\.]*([ABCD])[\.．、]\s*(.+)$")
    options = [(m.group(1), m.group(2).strip()) for m in opt_pat.finditer(b)]
    stem = opt_pat.sub("", b).strip()

    def get_meta(tag):
        m = re.search(rf"\s*([^\n\r]+)", b)
        return m.group(1).strip() if m else ""

    ans   = get_meta("答案")
    diff  = get_meta("难度") or "0.5"
    topics= (get_meta("知识点") or "").replace("、", "；")
    exp1  = re.search(r"【详解】\s*([\s\S]+?)(?=【|$)", b)
    exp2  = re.search(r"【分析】\s*([\s\S]+?)(?=【|$)", b)
    explain = ""
    if exp2: explain += exp2.group(1).strip() + "\n\n"
    if exp1: explain += exp1.group(1).strip()
    explain = explain.strip()
    if ans:
        explain = (explain + ("\n\n" if explain else "") + f"本题答案：{ans}。").strip()

    stem = re.sub(r"【(答案|难度|知识点|详解|分析)】[\s\S]*", "", stem).strip()

    parts = [r"\begin{question}", stem]
    if options:
        parts += [r"\begin{choices}"] + [rf"\choice {t}" for _, t in options] + [r"\end{choices}"]
    if topics:
        parts.append(rf"\topics{{{topics}}}")
    parts.append(rf"\difficulty{{{diff}}}")
    if explain:
        parts.append(r"\explain{")
        parts.append(explain)
        parts.append("}")
    parts.append(r"\end{question}")
    return "\n".join(parts)

def convert_text(src: str) -> str:
    parts = re.split(r"(?m)^\s*(\d+)[\.．]\s*", src)
    qs = []
    for i in range(1, len(parts), 2):
        block = parts[i+1]
        tex = convert_block_to_question(block)
        if tex:
            qs.append(tex)
    header = r"\section*{Ⅰ. 单选题（自动转换）}"
    return header + "\n\n" + "\n\n".join(qs)

def main():
    if len(sys.argv) != 3:
        print("Usage: convert_tex_exam.py in.tex out.tex")
        sys.exit(1)
    inp, outp = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    text = inp.read_text(encoding="utf-8", errors="ignore")
    out = convert_text(text)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(out, encoding="utf-8")
    print(f"✅ Wrote {outp}")

if __name__ == "__main__":
    main()
