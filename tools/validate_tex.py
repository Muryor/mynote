#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pre-compilation LaTeX validator

用来在跑 latexmk 之前做一次快速静态检查，尽早发现：
- Runaway argument 的高频根因（explain 中空行 / 括号不平衡）
- 花括号不配对
- 数学定界符不配对
- 环境 begin/end 数量不一致
"""

import re
import sys
from pathlib import Path
from typing import List


class TeXValidator:
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.errors: List[str] = []
        self.warnings: List[str] = []

    # ---------- 工具方法 ----------

    def _read_content(self) -> str:
        try:
            return self.filepath.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # 兜底：有些文件可能是 gbk 或其它编码
            return self.filepath.read_text(errors="ignore")

    # ---------- 具体检查 ----------

    def check_explain_macro(self) -> None:
        """检查 \\explain{...} 中是否出现段落分隔（空行）"""
        content = self._read_content()

        # 尽量只匹配单层 explain {...}，避免贪心
        pattern = re.compile(
            r"\\explain\{((?:[^{}]|(?:\{[^{}]*\}))*)\}",
            re.DOTALL,
        )
        for match in pattern.finditer(content):
            explain_content = match.group(1)
            if "\n\n" in explain_content:
                line_no = content[: match.start()].count("\n") + 1
                self.errors.append(
                    f"Line {line_no}: \\explain macro contains paragraph breaks "
                    f"(double newlines) - this is very likely to cause 'Runaway argument' errors."
                )

    def check_brace_balance(self) -> None:
        """检查全局花括号配对情况（只做粗略统计 + 简单定位）"""
        content = self._read_content()
        stack: List[int] = []

        for i, ch in enumerate(content):
            if ch == "{":
                stack.append(i)
            elif ch == "}":
                if not stack:
                    line_no = content[:i].count("\n") + 1
                    self.errors.append(f"Line {line_no}: Unmatched closing brace '}}'")
                else:
                    stack.pop()

        # 报告剩余未闭合的若干 '{'
        for pos in stack[-5:]:
            line_no = content[:pos].count("\n") + 1
            self.errors.append(f"Line {line_no}: Unmatched opening brace '{{'")

    def check_math_delimiters(self) -> None:
        """检查数学环境定界符配对（粗略计数）"""
        content = self._read_content()

        inline_open = len(re.findall(r"\\\(", content))
        inline_close = len(re.findall(r"\\\)", content))
        if inline_open != inline_close:
            self.warnings.append(
                f"Inline math delimiters mismatch: {inline_open} '\\(' vs {inline_close} '\\)'"
            )

        display_open = len(re.findall(r"\\\[", content))
        display_close = len(re.findall(r"\\\]", content))
        if display_open != display_close:
            self.warnings.append(
                f"Display math delimiters mismatch: {display_open} '\\[' vs {display_close} '\\]'"
            )

    def check_environment_balance(self) -> None:
        """检查 \\begin{env} / \\end{env} 数量是否一致（按 env 名计数）"""
        content = self._read_content()

        begin_pattern = re.compile(r"\\begin\{([\w*]+)\}")
        end_pattern = re.compile(r"\\end\{([\w*]+)\}")

        env_counts = {}

        for m in begin_pattern.finditer(content):
            env_counts[m.group(1)] = env_counts.get(m.group(1), 0) + 1

        for m in end_pattern.finditer(content):
            env_counts[m.group(1)] = env_counts.get(m.group(1), 0) - 1

        for env, count in env_counts.items():
            if count != 0:
                kind = "extra \\begin" if count > 0 else "extra \\end"
                self.errors.append(
                    f"Environment '{env}' is unbalanced: {abs(count)} {kind}"
                )

    # ---------- 主入口 ----------

    def validate(self) -> bool:
        print(f"🔍 Validating {self.filepath} ...")

        if not self.filepath.is_file():
            print(f"❌ File not found: {self.filepath}")
            return False

        self.check_explain_macro()
        self.check_brace_balance()
        self.check_math_delimiters()
        self.check_environment_balance()

        if self.errors:
            print(f"\n❌ Found {len(self.errors)} error(s):")
            for err in self.errors:
                print("  •", err)

        if self.warnings:
            print(f"\n⚠️  Found {len(self.warnings)} warning(s):")
            for warn in self.warnings:
                print("  •", warn)

        if not self.errors and not self.warnings:
            print("✅ No obvious issues found")

        return len(self.errors) == 0


def main(argv: list) -> int:
    if len(argv) < 2:
        print("Usage: python validate_tex.py <tex_file>")
        return 1
    validator = TeXValidator(argv[1])
    ok = validator.validate()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
