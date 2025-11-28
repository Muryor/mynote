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
        self._content: str = None
        self._content_no_comments: str = None

    # ---------- 工具方法 ----------

    def _read_content(self) -> str:
        if self._content is None:
            try:
                self._content = self.filepath.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                self._content = self.filepath.read_text(errors="ignore")
        return self._content

    def _get_content_no_comments(self) -> str:
        """获取去除注释的内容（带缓存）"""
        if self._content_no_comments is None:
            content = self._read_content()
            self._content_no_comments = re.sub(r'(?<!\\)%[^\n]*', '', content)
        return self._content_no_comments

    # ---------- 具体检查 ----------

    def check_explain_macro(self) -> None:
        """检查 \\explain{...} 中是否出现段落分隔（空行）"""
        content = self._read_content()

        # 使用栈算法提取 \explain{...} 内容，支持任意嵌套深度
        i = 0
        while i < len(content):
            idx = content.find(r'\explain{', i)
            if idx == -1:
                break

            line_no = content[:idx].count('\n') + 1
            start = idx + len(r'\explain{')
            depth = 1
            j = start

            while j < len(content) and depth > 0:
                backslash_count = 0
                k = j - 1
                while k >= 0 and content[k] == '\\':
                    backslash_count += 1
                    k -= 1

                is_escaped = (backslash_count % 2 == 1)

                if content[j] == '{' and not is_escaped:
                    depth += 1
                elif content[j] == '}' and not is_escaped:
                    depth -= 1
                j += 1

            if depth == 0:
                explain_content = content[start:j-1]
                if "\n\n" in explain_content:
                    self.errors.append(
                        f"Line {line_no}: \\explain macro contains paragraph breaks "
                        f"(double newlines) - this is very likely to cause 'Runaway argument' errors."
                    )

            i = j

    def check_brace_balance(self) -> None:
        """检查全局花括号配对情况（移除数学定界符后再检查，避免误报）"""
        content_cleaned = self._get_content_no_comments()

        # 移除数学定界符，避免误报 \left\{ 和 \right\} 等
        content_cleaned = re.sub(r'\\left\\{', '', content_cleaned)
        content_cleaned = re.sub(r'\\right\\}', '', content_cleaned)
        content_cleaned = re.sub(r'\\left\\\[', '', content_cleaned)
        content_cleaned = re.sub(r'\\right\\\]', '', content_cleaned)
        content_cleaned = re.sub(r'\\left\\\(', '', content_cleaned)
        content_cleaned = re.sub(r'\\right\\\)', '', content_cleaned)
        content_cleaned = re.sub(r'\\right\\\\.', '', content_cleaned)
        content_cleaned = re.sub(r'\\left\\\\.', '', content_cleaned)

        # 移除转义的花括号
        content_cleaned = content_cleaned.replace(r'\{', '@@ESC_OPEN@@')
        content_cleaned = content_cleaned.replace(r'\}', '@@ESC_CLOSE@@')

        stack: List[int] = []

        for i, ch in enumerate(content_cleaned):
            if ch == "{":
                stack.append(i)
            elif ch == "}":
                if not stack:
                    line_no = content_cleaned[:i].count("\n") + 1
                    self.errors.append(f"Line {line_no}: Unmatched closing brace '}}'")
                else:
                    stack.pop()

        # 报告剩余未闭合的若干 '{'
        for pos in stack[-5:]:
            line_no = content_cleaned[:pos].count("\n") + 1
            self.errors.append(f"Line {line_no}: Unmatched opening brace '{{'")

    def check_math_delimiters(self) -> None:
        """检查数学环境定界符配对（总数 + 顺序合理性）"""
        content_no_comments = self._get_content_no_comments()

        # 原有逻辑：检查总数
        inline_open = len(re.findall(r"\\\(", content_no_comments))
        inline_close = len(re.findall(r"\\\)", content_no_comments))
        if inline_open != inline_close:
            self.warnings.append(
                f"Inline math delimiters mismatch: {inline_open} '\\(' vs {inline_close} '\\)'"
            )

        display_open = len(re.findall(r"\\\[", content_no_comments))
        display_close = len(re.findall(r"\\\]", content_no_comments))
        if display_open != display_close:
            self.warnings.append(
                f"Display math delimiters mismatch: {display_open} '\\[' vs {display_close} '\\]'"
            )

        # 新增：顺序合理性检查（行内数学）
        pattern_inline = re.compile(r"\\\(|\\\)")
        balance = 0
        for m in pattern_inline.finditer(content_no_comments):
            token = m.group(0)
            line_no = content_no_comments[: m.start()].count("\n") + 1
            if token == r"\(":
                balance += 1
            else:
                balance -= 1
                if balance < 0:
                    self.errors.append(
                        f"Line {line_no}: Found '\\)' before any opening '\\(' "
                        f"(inline math delimiters out of order)."
                    )
                    balance = 0

        # 新增：顺序合理性检查（行间数学）
        pattern_display = re.compile(r"\\\[|\\\]")
        balance_display = 0
        for m in pattern_display.finditer(content_no_comments):
            token = m.group(0)
            line_no = content_no_comments[: m.start()].count("\n") + 1
            if token == r"\[":
                balance_display += 1
            else:
                balance_display -= 1
                if balance_display < 0:
                    self.errors.append(
                        f"Line {line_no}: Found '\\]' before any opening '\\[' "
                        f"(display math delimiters out of order)."
                    )
                    balance_display = 0

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

    def check_question_missing_stem(self) -> None:
        """检查题目是否缺少题干（直接从 \\item 开始）"""
        content = self._read_content()

        # 检测 \begin{question} 后直接跟 \item 的情况
        pattern = re.compile(
            r"\\begin\{question\}\s*\n\s*\\item",
            re.MULTILINE
        )

        for match in pattern.finditer(content):
            line_no = content[:match.start()].count("\n") + 1
            self.errors.append(
                f"Line {line_no}: Question starts with \\item (missing stem) - "
                f"题目缺少题干，直接从小问开始"
            )

    def check_reversed_math_delimiters(self) -> None:
        """语义化检测真正次序错误的数学定界符。

        旧版本基于单行正则 \\)...\\( 导致大量误报：句子结束后紧跟下一公式属正常。
        新逻辑：全局扫描 token 流，维护深度；仅当出现 depth < 0 时报告真正的逆序错误。
        另外检测大段中文被放入单个行内公式中，给出警告以提示排版改进。
        """
        content_no_comments = self._get_content_no_comments()

        tokens = list(re.finditer(r"\\\(|\\\)|\\\[|\\\]", content_no_comments))
        inline_depth = 0
        display_depth = 0
        for m in tokens:
            tok = m.group(0)
            line_no = content_no_comments[: m.start()].count("\n") + 1
            if tok == r"\(":
                inline_depth += 1
            elif tok == r"\)":
                inline_depth -= 1
                if inline_depth < 0:
                    self.errors.append(
                        rf"Line {line_no}: '\)' without preceding '\(' (inline math order error)."
                    )
                    inline_depth = 0
            elif tok == r"\[":
                display_depth += 1
            else:  # tok == \]
                display_depth -= 1
                if display_depth < 0:
                    self.errors.append(
                        rf"Line {line_no}: '\]' without preceding '\[' (display math order error)."
                    )
                    display_depth = 0

        # 检测大段中文包裹在单个 \( ... \) 中
        for blk in re.finditer(r"\\\((.+?)\\\)", content_no_comments, flags=re.DOTALL):
            inner = blk.group(1)
            if len(inner) < 20:
                continue
            cjk_chars = re.findall(r"[\u4e00-\u9fff]", inner)
            if cjk_chars:
                ratio = len(cjk_chars) / max(1, len(inner))
                if ratio > 0.4:
                    line_no = content_no_comments[: blk.start()].count("\n") + 1
                    self.warnings.append(
                        f"Line {line_no}: Large inline math with {len(cjk_chars)} CJK chars (~{ratio:.0%}). Consider moving text outside math or using \text{{}}."
                    )

    def check_duplicate_meta_commands(self) -> None:
        """检查同一题目中是否有重复的元信息命令"""
        content_no_comments = self._get_content_no_comments()

        # 切分所有 question 环境
        question_pattern = re.compile(
            r"\\begin\{question\}(.*?)\\end\{question\}",
            re.DOTALL
        )

        meta_commands = ["explain", "topics", "answer", "difficulty"]

        for q_index, match in enumerate(question_pattern.finditer(content_no_comments), 1):
            q_content = match.group(1)
            base_line = content_no_comments[:match.start()].count("\n") + 1

            for cmd in meta_commands:
                # 查找所有该命令出现的位置
                cmd_pattern = re.compile(rf"\\{cmd}\s*\{{")
                matches = list(cmd_pattern.finditer(q_content))

                if len(matches) > 1:
                    # 第二次出现就是重复
                    first_dup_pos = matches[1].start()
                    dup_line = base_line + q_content[:first_dup_pos].count("\n")
                    self.errors.append(
                        f"Line {dup_line}: Question {q_index} has duplicated '\\{cmd}' "
                        f"({len(matches)} times) inside one question environment."
                    )

    def check_left_right_balance(self) -> None:
        """检查 \\left 和 \\right 配对"""
        content = self._read_content()

        pattern = re.compile(r"\\(left|right)")
        stack = []

        for match in pattern.finditer(content):
            token = match.group(1)
            line_no = content[:match.start()].count("\n") + 1

            if token == "left":
                stack.append((line_no, "\\left"))
            else:  # token == "right"
                if stack:
                    stack.pop()
                else:
                    self.errors.append(
                        f"Line {line_no}: '\\right' appears without matching '\\left' "
                        f"in previous lines."
                    )

        # 报告未闭合的 \left（只取最后10个）
        for line_no, _ in stack[-10:]:
            self.errors.append(
                f"Line {line_no}: '\\left' does not have a matching '\\right'."
            )

    def check_enumerate_structure(self) -> None:
        """检查 enumerate 环境中是否有非 \\item 开头的实质内容"""
        content = self._read_content()

        enum_pattern = re.compile(
            r"\\begin\{enumerate\}(.*?)\\end\{enumerate\}",
            re.DOTALL
        )

        for block_index, match in enumerate(enum_pattern.finditer(content), 1):
            block = match.group(1)
            base_line = content[:match.start()].count("\n") + 1
            lines = block.splitlines()

            for offset, raw_line in enumerate(lines):
                line = raw_line.strip()

                # 跳过空行、注释、\item 开头的行
                if not line or line.startswith('%') or line.startswith(r'\item'):
                    continue

                # 跳过 enumerate 可选参数行 (例如 [label=(\arabic*)])
                if line.startswith('[') and line.endswith(']'):
                    continue

                # 跳过纯 LaTeX 环境标记（如 \begin, \end）
                if line.startswith(r'\begin') or line.startswith(r'\end'):
                    continue

                # 其他实质内容视为可能的问题
                line_no = base_line + offset
                self.warnings.append(
                    f"Line {line_no}: Non-\\item content inside enumerate environment "
                    f"(block {block_index}) - please check if this should be '\\item ...'."
                )

    def check_dollar_sign_residual(self) -> None:
        """检查 $$ 残留"""
        content = self._get_content_no_comments()
        if '$$' in content:
            count = content.count('$$')
            self.errors.append(f'检测到 {count} 个残留的 $$ 定界符')

    def check_choices_environment(self) -> None:
        """检查选项是否有 choices 环境"""
        content = self._get_content_no_comments()
        question_pattern = re.compile(r'\\begin\{question\}(.*?)\\end\{question\}', re.DOTALL)
        for match in question_pattern.finditer(content):
            q_content = match.group(1)
            if r'\item' in q_content:
                if r'\begin{choices}' not in q_content and r'\begin{enumerate}' not in q_content:
                    line_no = content[:match.start()].count('\n') + 1
                    self.warnings.append(f'Line {line_no}: 选项缺少 choices 环境')

    def check_markdown_residual(self) -> None:
        """检查 Markdown 格式残留"""
        content = self._get_content_no_comments()
        if re.search(r'!\[.*?\]\(.*?\)', content):
            self.errors.append('检测到 Markdown 图片格式残留')
        if re.search(r'\*[A-Za-z]+\*', content):
            self.warnings.append('检测到 Markdown 斜体格式残留')

    def check_math_symbol_standardization(self, warn_text_i: bool = False) -> None:
        """检查数学符号标准化

        Args:
            warn_text_i: 是否对 \\text{i} 发出警告（默认 False，因为范本使用 \\text{i}）
        """
        content = self._read_content()

        # \text{i} 检查 - 可选，因为范本中使用的就是 \text{i}
        if warn_text_i and r'\text{i}' in content:
            self.warnings.append('检测到 \\text{i}，建议检查是否应转为 \\mathrm{i}')

        if r'\text{π}' in content:
            self.warnings.append('检测到未转换的 \\text{π}')
        if re.search(r'(?<!\\)π', self._get_content_no_comments()):
            self.warnings.append('检测到未转换的 π')

    def check_answer_format(self) -> None:
        """检查答案格式是否正确"""
        content = self._get_content_no_comments()

        # 检测当前所在的 section
        current_section = ""

        for match in re.finditer(r'\\answer\{([^}]*)\}', content):
            answer = match.group(1).strip()
            line_no = content[:match.start()].count('\n') + 1

            # 查找这个答案之前最近的 section
            text_before = content[:match.start()]
            section_matches = list(re.finditer(r'\\section\{([^}]+)\}', text_before))
            if section_matches:
                current_section = section_matches[-1].group(1)

            # 根据 section 类型检查答案格式
            if '单选' in current_section:
                if not re.match(r'^[A-D]$', answer):
                    self.warnings.append(
                        f"Line {line_no}: 单选题答案格式可能不正确: '{answer}'（应为 A/B/C/D）"
                    )
            elif '多选' in current_section:
                if not re.match(r'^[A-D]{2,4}$', answer):
                    self.warnings.append(
                        f"Line {line_no}: 多选题答案格式可能不正确: '{answer}'（应为 AB/ABC/ABCD 等）"
                    )

    def check_difficulty_range(self) -> None:
        """检查难度值是否在有效范围内 [0, 1]"""
        content = self._get_content_no_comments()

        for match in re.finditer(r'\\difficulty\{([^}]*)\}', content):
            value_str = match.group(1).strip()
            line_no = content[:match.start()].count('\n') + 1

            try:
                value = float(value_str)
                if not (0 <= value <= 1):
                    self.warnings.append(
                        f"Line {line_no}: 难度值 {value} 超出有效范围 [0, 1]"
                    )
            except ValueError:
                self.errors.append(
                    f"Line {line_no}: 难度值格式错误: '{value_str}'（应为 0-1 之间的小数）"
                )

    def check_choices_count(self) -> None:
        """检查选择题选项数量"""
        content = self._get_content_no_comments()

        for q_match in re.finditer(r'\\begin\{question\}(.*?)\\end\{question\}', content, re.DOTALL):
            q_content = q_match.group(1)
            base_line = content[:q_match.start()].count('\n') + 1

            # 查找 choices 环境
            choices_match = re.search(r'\\begin\{choices\}(.*?)\\end\{choices\}', q_content, re.DOTALL)
            if choices_match:
                choices_content = choices_match.group(1)
                # Count both \item and \choice (which is often aliased to \item)
                item_count = len(re.findall(r'\\(?:item|choice)\b', choices_content))

                if item_count < 2:
                    line_no = base_line + q_content[:choices_match.start()].count('\n')
                    self.errors.append(
                        f"Line {line_no}: choices 环境只有 {item_count} 个选项（至少需要 2 个）"
                    )
                elif item_count != 4:
                    # 只是警告，因为有些题目可能确实不是4个选项
                    line_no = base_line + q_content[:choices_match.start()].count('\n')
                    self.warnings.append(
                        f"Line {line_no}: choices 环境包含 {item_count} 个选项（通常为 4 个）"
                    )

    def check_chinese_punctuation_in_math(self) -> None:
        """检查数学模式内的中文标点（使用栈算法正确处理嵌套括号）"""
        content = self._get_content_no_comments()
        issues = []

        # 使用栈算法提取数学块
        i = 0
        while i < len(content):
            # 查找 \(
            idx = content.find(r'\(', i)
            if idx == -1:
                break

            # 从 \( 开始，找到匹配的 \)
            depth = 1
            j = idx + 2
            while j < len(content) - 1 and depth > 0:
                if content[j:j+2] == r'\(':
                    depth += 1
                    j += 2
                elif content[j:j+2] == r'\)':
                    depth -= 1
                    if depth == 0:
                        break
                    j += 2
                else:
                    j += 1

            if depth == 0:
                inner = content[idx+2:j]
                chinese_punct = re.findall(r'[，。；：、！？]', inner)
                if chinese_punct:
                    line_no = content[:idx].count('\n') + 1
                    issues.append(f'Line {line_no}: 数学模式内包含中文标点 {chinese_punct}')

            i = j + 2 if depth == 0 else j

        if issues:
            self.warnings.append(f'发现 {len(issues)} 处数学模式内的中文标点')
            for issue in issues[:5]:  # 只显示前5个
                self.warnings.append(f'  {issue}')

    def check_image_todo_trailing_text(self) -> None:
        """检查 IMAGE_TODO_END 注释行是否有尾随文本"""
        content = self._read_content()
        lines = content.splitlines()

        pattern = re.compile(r"^%.*IMAGE_TODO_END(?P<tail>.*)$")

        for i, line in enumerate(lines, 1):
            match = pattern.match(line)
            if match:
                tail = match.group("tail")
                # 检查 tail 是否只包含 id=xxx 格式（这是正常的）
                # 如果有其他非空白内容，则报错
                tail_stripped = tail.strip()
                if tail_stripped and not tail_stripped.startswith('id='):
                    # 进一步检查：去掉 id=xxx 后是否还有其他内容
                    tail_after_id = re.sub(r'id=\S+', '', tail_stripped).strip()
                    if tail_after_id:
                        self.errors.append(
                            f"Line {i}: IMAGE_TODO_END comment line has trailing text "
                            f"('{tail_after_id}') which should probably be moved to the next line."
                        )

    # ---------- 主入口 ----------

    def validate(self, warn_text_i: bool = False, quiet: bool = False) -> bool:
        if not quiet:
            print(f"🔍 Validating {self.filepath} ...")

        if not self.filepath.is_file():
            if not quiet:
                print(f"❌ File not found: {self.filepath}")
            return False

        self.check_explain_macro()
        self.check_brace_balance()
        self.check_math_delimiters()
        self.check_environment_balance()
        self.check_question_missing_stem()

        # 新增检查
        self.check_reversed_math_delimiters()
        self.check_duplicate_meta_commands()
        self.check_left_right_balance()
        self.check_enumerate_structure()
        self.check_image_todo_trailing_text()

        # 🆕 改进的检查
        self.check_dollar_sign_residual()
        self.check_choices_environment()
        self.check_markdown_residual()
        self.check_math_symbol_standardization(warn_text_i=warn_text_i)
        self.check_chinese_punctuation_in_math()

        # 🆕 新增功能检查
        self.check_answer_format()
        self.check_difficulty_range()
        self.check_choices_count()

        if self.errors:
            print(f"\n❌ Found {len(self.errors)} error(s):")
            for err in self.errors:
                print("  •", err)

        if self.warnings and not quiet:
            print(f"\n⚠️  Found {len(self.warnings)} warning(s):")
            for warn in self.warnings:
                print("  •", warn)

        if not self.errors and not self.warnings and not quiet:
            print("✅ No obvious issues found")

        return len(self.errors) == 0


def main(argv: list) -> int:
    import argparse

    parser = argparse.ArgumentParser(description='LaTeX 文件验证工具')
    parser.add_argument('tex_file', help='要验证的 TeX 文件路径')
    parser.add_argument('--strict', action='store_true',
                        help='严格模式：将警告也视为错误')
    parser.add_argument('--warn-text-i', action='store_true',
                        help='对 \\text{i} 发出警告')
    parser.add_argument('--quiet', action='store_true',
                        help='安静模式：只输出错误')

    args = parser.parse_args(argv[1:])

    validator = TeXValidator(args.tex_file)
    ok = validator.validate(
        warn_text_i=args.warn_text_i,
        quiet=args.quiet
    )

    if args.strict and validator.warnings:
        return 1

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
