#!/usr/bin/env python3
"""Convert display math delimiters `\[ ... \]` to inline `\(...\)` inside
specific macros such as \explain{...} and \answer{...} to avoid LaTeX
macro-argument parsing issues.

Usage: python3 tools/convert_display_math_in_macros.py path/to/file.tex
It edits the file in-place and creates a .bak copy.
"""
import sys
from pathlib import Path


def find_matching_brace(s, start):
    # start is index at the opening brace '{'
    i = start
    depth = 0
    while i < len(s):
        ch = s[i]
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def convert_between(s):
    # Replace \[ and \] with \( and \)
    s = s.replace('\\[', '\\(')
    s = s.replace('\\]', '\\)')
    return s


def process(content, macros=('\\explain{', '\\answer{')):
    i = 0
    out = []
    while i < len(content):
        found = False
        for macro in macros:
            if content.startswith(macro, i):
                found = True
                out.append(macro[:-1])  # append '\explain' without '{'
                brace_start = i + len(macro) - 1
                # find matching brace for this argument
                match = find_matching_brace(content, brace_start)
                if match == -1:
                    # fallback: append rest and return
                    out.append(content[brace_start:])
                    return ''.join(out)
                arg = content[brace_start+1:match]
                new_arg = convert_between(arg)
                out.append('{' + new_arg + '}')
                i = match + 1
                break
        if not found:
            out.append(content[i])
            i += 1
    return ''.join(out)


def main():
    if len(sys.argv) < 2:
        print('Usage: convert_display_math_in_macros.py file.tex')
        sys.exit(2)
    p = Path(sys.argv[1])
    if not p.exists():
        print('File not found', p)
        sys.exit(2)
    content = p.read_text(encoding='utf8')
    backup = p.with_suffix(p.suffix + '.displaybak')
    backup.write_text(content, encoding='utf8')
    new = process(content)
    p.write_text(new, encoding='utf8')
    print('converted', p)


if __name__ == '__main__':
    main()
