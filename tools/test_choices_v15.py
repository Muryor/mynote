#!/usr/bin/env python3
"""Test choices expansion and $$ cleanup with v1.5."""
import sys
sys.path.insert(0, '/Users/muryor/code/mynote/tools')
from ocr_to_examx import convert_md_to_examx

test_md = open('/Users/muryor/code/mynote/tools/test_choices_nanjing.md').read()
result = convert_md_to_examx(test_md, 'Test')
print(result)
print()
print("=" * 60)
if '\\begin{choices}' in result:
    print("✅ choices environment generated")
else:
    print("❌ NO choices environment found!")

if '$$' in result:
    print("❌ Residual $$ found!")
else:
    print("✅ No residual $$")

if '> A' in result or '> B' in result:
    print("❌ Residual quoted options found!")
else:
    print("✅ No residual quote blocks")
