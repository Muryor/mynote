#!/usr/bin/env python3
"""Convert all display math \\[ ... \\] to inline math \\( ... \\) in a file."""
import sys
from pathlib import Path

if len(sys.argv) < 2:
    print('Usage: convert_display_to_inline.py file.tex')
    sys.exit(1)

p = Path(sys.argv[1])
if not p.exists():
    print(f'File not found: {p}')
    sys.exit(1)

# Read content
content = p.read_text(encoding='utf8')

# Backup
backup = p.with_suffix(p.suffix + '.bak_inline')
backup.write_text(content, encoding='utf8')

# Replace display math with inline math
content = content.replace('\\[', '\\(')
content = content.replace('\\]', '\\)')

# Write back
p.write_text(content, encoding='utf8')

print(f'Converted {p}')
print(f'Backup saved to {backup}')
