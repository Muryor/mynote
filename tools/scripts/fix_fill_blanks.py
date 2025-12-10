#!/usr/bin/env python3
r"""
Auto-insert \fillin{} placeholders for fill-in questions where the blank vanished
(e.g., Word underlines lost during docx->md). It operates only inside the
"填空题" section and skips questions that already contain \fillin or \choices.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

QUESTION_RE = re.compile(r"(\\begin\{question\}.*?\\end\{question\})", re.DOTALL)


def fix_block(block: str) -> tuple[str, bool]:
    # Skip if already has fillin or is a choice question.
    if "\\fillin" in block or "\\choices" in block:
        return block, False

    topics_idx = block.find(r"\topics")
    if topics_idx == -1:
        return block, False

    before_topics = block[:topics_idx]
    dot_idx = before_topics.rfind("\uff0e")
    if dot_idx == -1:
        return block, False

    # Avoid double inserting immediately before the dot.
    if before_topics[max(0, dot_idx - 10):dot_idx].find("\\fillin") != -1:
        return block, False

    new_before = before_topics[:dot_idx] + r"\fillin{}" + before_topics[dot_idx:]
    new_block = new_before + block[topics_idx:]
    return new_block, True


def fix_text(text: str) -> tuple[str, int]:
    start = text.find("\\section{填空题}")
    if start == -1:
        return text, 0
    end = text.find(r"\section{", start + 1)
    if end == -1:
        end = len(text)

    prefix, body, suffix = text[:start], text[start:end], text[end:]

    changed = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal changed
        block = match.group(1)
        new_block, touched = fix_block(block)
        if touched:
            changed += 1
        return new_block

    body = QUESTION_RE.sub(repl, body)
    return prefix + body + suffix, changed


def process_file(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    new_text, changed = fix_text(text)
    if changed:
        path.write_text(new_text, encoding="utf-8")
    return changed


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: fix_fill_blanks.py <tex_file> [more.tex]", file=sys.stderr)
        return 1
    total = 0
    for arg in argv[1:]:
        p = Path(arg)
        if not p.exists():
            print(f"[skip] not found: {p}")
            continue
        changed = process_file(p)
        print(f"[ok] {p} - inserted {changed} fillin placeholder(s)")
        total += changed
    return 0 if total >= 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
