#!/usr/bin/env python3
"""
Fix common math delimiter issues in converted exam TeX files.
- Convert display math `\[ ... \]` to inline `\(...\)` when inside \explain{} or \answer{}
- Convert `$$...$$` to `\(...\)` inside those macros
- Ensure balanced parentheses for common cases

Usage: python3 tools/fix_converted_math.py path/to/converted_exam.tex
"""
import sys
import re
from pathlib import Path

if len(sys.argv) < 2:
    print("Usage: fix_converted_math.py <file.tex>")
    sys.exit(1)

p = Path(sys.argv[1])
text = p.read_text()

# Helper to replace display math inside a macro argument
def replace_in_macro(content, macro):
    # Find macro occurrences like \explain{...} possibly spanning lines
    pattern = re.compile(r'(\\' + re.escape(macro) + r'\{)(.*?)(\})', re.S)
    def repl(m):
        head, body, tail = m.group(1), m.group(2), m.group(3)
        # Replace $$...$$ with \(...\)
        body = re.sub(r'\$\$(.*?)\$\$', lambda mm: r'\\(' + mm.group(1).strip() + r'\\)', body, flags=re.S)
        # Replace \[ ... \] with \(...\) inside body
        body = re.sub(r'\\\[(.*?)\\\]', lambda mm: r'\\(' + mm.group(1).strip() + r'\\)', body, flags=re.S)
        # Replace leftover single $...$ with \(...\)
        body = re.sub(r'\$(.*?)\$', lambda mm: r'\\(' + mm.group(1).strip() + r'\\)', body, flags=re.S)
        return head + body + tail
    return pattern.sub(repl, content)

# Apply to explain and answer macros
text2 = replace_in_macro(text, 'explain')
text2 = replace_in_macro(text2, 'answer')

# Also, for safety, convert stray instances where a line contains \] followed by text without matching \[
# Replace '\]somechars' -> '\)somechars'
text2 = re.sub(r'\\\](?=\S)', r'\\)', text2)
text2 = re.sub(r'(?<=\S)\\\[', r'\\(', text2)

# Write backup and new file
backup = p.with_suffix('.tex.bak')
backup.write_text(text)
p.write_text(text2)
print(f"Patched {p}; backup saved to {backup}")
