#!/usr/bin/env python3
"""
Test harness for insert_allowbreaks_in_math.py
Runs the fixer on a sample converted tex (uses existing converted_exam.tex)
and checks for balanced braces and absence of duplicate ',\\allowbreak' insertions.
"""
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / 'content' / 'exams' / 'auto' / 'gaokao_2024_national_1' / 'converted_exam.tex'
FIXER = ROOT / 'tools' / 'utils' / 'insert_allowbreaks_in_math.py'


def brace_counts_equal(before: str, after: str) -> bool:
    # Conservative check: ensure number of '{' and '}' are unchanged
    return before.count('{') == after.count('{') and before.count('}') == after.count('}')


def run_test():
    if not SAMPLE.exists():
        print(f"Sample .tex not found: {SAMPLE}", file=sys.stderr)
        return 2
    tmpdir = Path(tempfile.mkdtemp())
    testfile = tmpdir / SAMPLE.name
    shutil.copy(SAMPLE, testfile)
    before_txt = testfile.read_text(encoding='utf-8')
    res = subprocess.run([sys.executable, str(FIXER), str(testfile)], capture_output=True, text=True)
    if res.returncode != 0:
        print('Fixer failed:', res.stderr, file=sys.stderr)
        return 2
    txt = testfile.read_text(encoding='utf-8')
    if not brace_counts_equal(before_txt, txt):
        print('Error: brace counts changed after fixer', file=sys.stderr)
        return 2
    if re.search(r',\\allowbreak\s*,', txt):
        print('Error: duplicate allowbreak insertion detected', file=sys.stderr)
        return 2
    print('Test passed: fixer ran, braces balanced, no duplicate allowbreak patterns.')
    return 0


if __name__ == '__main__':
    sys.exit(run_test())
