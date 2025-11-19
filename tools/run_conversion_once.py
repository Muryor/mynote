#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from pathlib import Path

# Usage: python3 tools/run_conversion_once.py input_md output_tex "Title"

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 tools/run_conversion_once.py input_md output_tex 'Title'")
        sys.exit(1)
    input_md = Path(sys.argv[1])
    output_tex = Path(sys.argv[2])
    title = sys.argv[3]

    if not input_md.exists():
        print(f"Input not found: {input_md}")
        sys.exit(2)

    sys.path.insert(0, str(Path(__file__).parent))
    from ocr_to_examx import convert_md_to_examx

    md_text = input_md.read_text(encoding='utf-8')
    tex = convert_md_to_examx(md_text, title)
    output_tex.parent.mkdir(parents=True, exist_ok=True)
    output_tex.write_text(tex, encoding='utf-8')
    print(f"Wrote: {output_tex}")
