#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Generate TikZ placeholders for Markdown-style image markers in LaTeX files.

Usage:
  python generate_tikz_placeholders.py input.tex [output.tex]

- If only input is provided, the file will be overwritten in place.
- Replaces image markers of the form:
    1) With ID:  ![@@@some-uuid](path/to/image.png)
    2) No ID:    ![](path/to/image.jpg)
  Optional trailing attribute blocks like {width="..." height="..."} are tolerated and removed.
- Outputs a TikZ placeholder block at each image location:

        \\begin{center}
        \\begin{tikzpicture}
            \\node[draw, minimum width=6cm, minimum height=4cm] {图略（图 ID: <LABEL>）};
        \\end{tikzpicture}
        \\end{center}

Only Python standard library is used.
"""

import re
import sys
from pathlib import Path
import os
from typing import Callable

# Patterns:
# 1) With ID (starts with @@@, contains alnum and hyphen)
PATTERN_WITH_ID = re.compile(
    r"!\[@@@([0-9A-Za-z\-]+)\]\(([^)]+)\)(?:\s*\{.*?\})?",
    re.MULTILINE | re.DOTALL,
)
# 2) Without ID
PATTERN_NO_ID = re.compile(
    r"!\[\]\(([^)]+)\)(?:\s*\{.*?\})?",
    re.MULTILINE | re.DOTALL,
)


def _make_placeholder(label: str) -> str:
    """Create a TikZ placeholder block with the given label.
    Use double braces to emit literal braces in f-strings.
    """
    label = label.strip() or "image"
    return (
        f"""\\begin{{center}}
\\begin{{tikzpicture}}
  \\node[draw, minimum width=6cm, minimum height=4cm] {{图略（图 ID: {label}）}};
\\end{{tikzpicture}}
\\end{{center}}"""
    )


def replace_images(text: str) -> str:
    """Replace Markdown image markers with TikZ placeholders.

    Supports two forms:
      - With ID: ![@@@ID](path)
      - Without ID: ![](path)
    Accepts optional trailing attribute blocks after the close parenthesis.
    """
    if not text:
        return text

    # First handle ID form to avoid double-processing
    def repl_with_id(match: re.Match) -> str:
        _id = match.group(1)
        # path = match.group(2)  # not currently used, but keep for future
        return _make_placeholder(_id)

    out = PATTERN_WITH_ID.sub(repl_with_id, text)

    # Then handle plain form
    def repl_no_id(match: re.Match) -> str:
        path = match.group(1).strip()
        # Normalize path separators and extract basename
        base = os.path.basename(path)
        label = base if base else "image"
        return _make_placeholder(label)

    out = PATTERN_NO_ID.sub(repl_no_id, out)

    return out


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python generate_tikz_placeholders.py input.tex [output.tex]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        sys.exit(2)

    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])
    else:
        output_path = input_path  # overwrite

    content = input_path.read_text(encoding="utf-8")
    new_content = replace_images(content)

    # Only write if changed to avoid unnecessary touches
    if new_content != content:
        output_path.write_text(new_content, encoding="utf-8")
    else:
        # Still write if output path differs from input
        if output_path != input_path:
            output_path.write_text(new_content, encoding="utf-8")


if __name__ == "__main__":
    main()
