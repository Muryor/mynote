#!/usr/bin/env python3
"""
Batch-fix common OCR LaTeX math delimiter artifacts.
Patterns handled (conservative):
 1. \(，\)  -> \)，\(
 2. Nested heading colon: \(X\(：\) -> \(X\)：\(
 3. Missing close before Chinese semantic markers (的 / 到 / 与 / 和 / 在 / 为)
 4. Command glued to CJK: \(\therefore直线 -> \(\therefore\)直线
 5. Trailing lone '}' after sentence punctuation
 6. ChineseChar + Capital + \) -> ChineseChar\(Capital\)
Creates <file>.before_fix backup.
Usage: python tools/fix_ocr_math.py <tex_file>
"""
import re, sys, shutil, pathlib

TARGET_MARKERS = "的到与和在为"  # heuristic set
CJK = "\u4e00-\u9fff"

def fix(content: str) -> str:
    # 1. \(，\) -> \)，\(
    content = re.sub(r"\\\\\(，\\\\\)", r"\\)，\\(", content)
    # 2. Nested heading colon \(X\(：\) -> \(X\)：\(
    content = re.sub(r"\\\\\(([^\\(\n]{1,30})\\\\\(：\\\\\)", r"\\(\1\\)：\\(", content)
    # 3. Missing close before Chinese semantic marker
    content = re.sub(r"\\\\\(([^{\n]{1,40}?)([" + TARGET_MARKERS + "])", r"\\(\1\\)\2", content)
    # 4. Command glued to CJK: \(\cmd直 -> \(\cmd\)直
    content = re.sub(r"\\\\\(\\\\([a-zA-Z]+)([" + CJK + "])", r"\\(\\\1\\)\2", content)
    # 5. Trailing lone } after sentence punctuation
    content = re.sub(r"([。，“”，；:,])}\s*$", r"\1", content, flags=re.MULTILINE)
    # 6. ChineseChar + Capital + \) -> ChineseChar\(Capital\)
    content = re.sub(r"([" + CJK + "])([A-Z])\\\\\)", r"\1\\(\2\\)", content)
    return content

def main():
    if len(sys.argv) != 2:
        print("Usage: python tools/fix_ocr_math.py <tex_file>")
        sys.exit(1)
    tex_path = pathlib.Path(sys.argv[1])
    if not tex_path.exists():
        print(f"File not found: {tex_path}")
        sys.exit(1)
    original = tex_path.read_text(encoding="utf-8")
    fixed = fix(original)
    backup = tex_path.with_suffix(tex_path.suffix + ".before_fix")
    shutil.copyfile(tex_path, backup)
    tex_path.write_text(fixed, encoding="utf-8")
    print("✅ OCR math cleanup complete")
    print(f"   Backup: {backup.name}")
    print(f"   Delta chars: {len(fixed) - len(original)}")

if __name__ == "__main__":
    main()
