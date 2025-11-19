#!/usr/bin/env python3
"""
Perform conservative cleaning of converted_exam.tex to remove embedded pandoc image attributes
and stray quote markers that break LaTeX structure.

Actions:
- Remove width="..." and height="..." attributes inside file
- Remove markdown image alt/id markers like ![@@@...](...) and their trailing attribute braces
- Remove stray leading '>' characters at start of choice lines (e.g., "> D．")
- Collapse repeated "> >" sequences

This is conservative; it does NOT change math delimiters.

Usage: python3 tools/clean_extracted_attrs.py path/to/converted_exam.tex
"""
import sys, re
from pathlib import Path

if len(sys.argv) < 2:
    print('Usage: clean_extracted_attrs.py <file.tex>')
    sys.exit(1)

p = Path(sys.argv[1])
s = p.read_text()
backup = p.with_suffix('.tex.clean.bak')
backup.write_text(s)

# Remove width/height attributes: key="..."
s = re.sub(r'\{width="[^"]*"\}', '', s)
s = re.sub(r'width="[^"]*"', '', s)
s = re.sub(r'height="[^"]*"', '', s)
# Remove trailing stray attribute braces leftover like }" or "}
s = re.sub(r'\"\}', '}', s)

# Remove pandoc image inline attribute blocks like  ![...](...){...}
s = re.sub(r'!\[[^\]]*\]\([^\)]*\)\{[^}]*\}', '', s)
# Remove pandoc inline image references without braces
s = re.sub(r'!\[[^\]]*\]\([^\)]*\)', '', s)

# Remove stray > markers at start of lines (often from quote blocks)
s = re.sub(r'^\s*>+\s*', '', s, flags=re.M)
# Collapse duplicated > markers inside lines
s = re.sub(r'>\s*>', '>', s)

p.write_text(s)
print('cleaned', p, 'backup at', backup)
