#!/usr/bin/env python3
"""
Conservative fixer: inside \explain{...} blocks, for each {...} that contains
multiple comma-separated items, replace commas with ',\\allowbreak ' so TeX
may break lines at those commas.

Usage:
  python3 tools/utils/insert_allowbreaks_in_math.py path/to/converted_exam.tex

This only modifies \explain{...} regions to minimize risk. It writes a .bak
backup next to the original file on first modification.
"""
import io
import re
import sys
from pathlib import Path


def find_explain_spans(s: str):
    spans = []
    start_pat = r'\\explain\{'
    for m in re.finditer(start_pat, s):
        i = m.end()
        depth = 1
        while i < len(s) and depth > 0:
            if s[i] == '{':
                depth += 1
            elif s[i] == '}':
                depth -= 1
            i += 1
        if depth == 0:
            spans.append((m.start(), i))
    return spans


def fix_brace_content(content: str) -> str:
    # replace commas inside {...} groups that look math-like with ',\allowbreak '
    def repl(m):
        inner = m.group(1)
        # conservative check: only modify if inner contains digits or k/m/+/− and at least one comma
        if inner.count(',') >= 1 and re.search(r'[0-9kKmM\+\-\\]', inner):
            # avoid double-inserting
            inner = inner.replace(',\\allowbreak', ',\\allowbreak')
            # insert allowbreak after comma only when not already present
            inner = re.sub(r',\s*(?!\\allowbreak)', ',\\allowbreak ', inner)
        return '{' + inner + '}'
    return re.sub(r'\{([^}]*)\}', repl, content)


def process_text(txt: str):
    spans = find_explain_spans(txt)
    if not spans:
        return txt, 0
    out = []
    last = 0
    changes = 0
    for a, b in spans:
        out.append(txt[last:a])
        block = txt[a:b]  # includes \explain{ ... }
        prefix = r'\\explain{'
        if not block.startswith(prefix):
            # unexpected; skip
            out.append(block)
            last = b
            continue
        inner = block[len(prefix):-1]  # drop trailing '}'
        fixed_inner = fix_brace_content(inner)
        if fixed_inner != inner:
            changes += 1
        out.append(prefix + fixed_inner + '}')
        last = b
    out.append(txt[last:])
    return ''.join(out), changes


def main(path: str):
    p = Path(path)
    if not p.exists():
        print(f"File not found: {path}", file=sys.stderr)
        return 2
    txt = p.read_text(encoding='utf-8')
    newtxt, changes = process_text(txt)
    if changes == 0:
        print("No changes needed.")
        return 0
    bak = str(p) + '.bak'
    # write backup only if not exists
    if not Path(bak).exists():
        io.open(bak, 'w', encoding='utf-8').write(txt)
    p.write_text(newtxt, encoding='utf-8')
    print(f"Updated {path}, explain blocks modified: {changes}, backup at {bak}")
    return 0


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: insert_allowbreaks_in_math.py path/to/converted_exam.tex", file=sys.stderr)
        sys.exit(1)
    sys.exit(main(sys.argv[1]))
