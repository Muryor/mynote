#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validation.py - 验证模块 - LaTeX语法检查、错误检测

从 ocr_to_examx.py 提取的共享工具函数，供 exam 和 handout 转换器使用。

生成时间: 自动提取
源文件: tools/core/ocr_to_examx.py
"""

from typing import List, Dict, Tuple, Optional
import re

# ============================================================
# 验证模块 - LaTeX语法检查、错误检测
# ============================================================

def validate_math_integrity(tex: str) -> List[str]:
    r"""分析最终 TeX 数学完整性问题并返回警告列表（扩展版）

    检查项：
    - 行内数学定界符数量差异（opens vs closes）- 🆕 v1.8.7：忽略注释中的定界符
    - 裸露美元符号
    - 双重包裹残留
    - 右边界畸形（\right. $$ 等）
    - 空数学块
    - 🆕 截断/未闭合的数学片段（收集前若干样本）
      典型来源：图片占位符或 explain 合并时跨行被截断，导致缺失 \)
    - 🆕 v1.8.7：检测 \) 在 \( 前面的反向模式
    """
    issues: List[str] = []
    tex_no_comments_lines: List[str] = []
    for raw_line in tex.splitlines():
        tex_no_comments_lines.append(raw_line.split('%', 1)[0])
    tex_no_comments = "\n".join(tex_no_comments_lines)

    # 🆕 v1.8.7：统计时忽略注释中的定界符
    opens = 0
    closes = 0
    left_total = 0
    right_total = 0
    left_right_samples: List[str] = []
    reversed_pairs: List[Tuple[int, str]] = []  # (line_num, line_content)

    for lineno, code_part in enumerate(tex_no_comments_lines, start=1):
        line_opens = code_part.count('\\(')
        line_closes = code_part.count('\\)')
        line_left = code_part.count('\\left')
        line_right = code_part.count('\\right')
        opens += line_opens
        closes += line_closes
        left_total += line_left
        right_total += line_right

        if line_left != line_right and (line_left or line_right):
            snippet = code_part.strip()
            if len(snippet) > 80:
                snippet = snippet[:77] + '...'
            left_right_samples.append(
                f"Line {lineno}: \\left={line_left}, \\right={line_right} → {snippet}"
            )

        if line_opens >= 1 and line_closes >= 1:
            idx_open = code_part.find(r'\(')
            idx_close = code_part.find(r'\)')
            if idx_close < idx_open:
                display_line = code_part.strip()
                if len(display_line) > 80:
                    display_line = display_line[:77] + '...'
                reversed_pairs.append((lineno, display_line))

    if opens != closes:
        issues.append(f"Math delimiter imbalance: opens={opens} closes={closes} diff={opens - closes}")
    if left_total != right_total:
        issues.append(f"\\left/\\right imbalance: left={left_total}, right={right_total}")
        if left_right_samples:
            issues.extend(left_right_samples[:5])

    stray = len(re.findall(r'(?<!\\)\$', tex_no_comments))
    if stray:
        issues.append(f"Stray dollar signs detected: {stray}")

    double_wrapped = (
        len(re.findall(r'\$\s*\\\(.*?\\\)\s*\$', tex_no_comments, flags=re.DOTALL)) +
        len(re.findall(r'\$\$\s*\\\(.*?\\\)\s*\$\$', tex_no_comments, flags=re.DOTALL))
    )
    if double_wrapped:
        issues.append(f"Double-wrapped math segments: {double_wrapped}")

    right_glitch = (
        len(re.findall(r'\\right\.\s*\$\$', tex_no_comments)) +
        len(re.findall(r'\\right\.\\\\\)', tex_no_comments))
    )
    if right_glitch:
        issues.append(f"Right boundary glitches: {right_glitch}")

    empty_math = (
        len(re.findall(r'\\\(\s*\\\)', tex_no_comments)) +
        len(re.findall(r'\\\[\s*\\\]', tex_no_comments))
    )
    if empty_math:
        issues.append(f"Empty math blocks: {empty_math}")

    unmatched_open_positions: List[int] = []
    unmatched_close_positions: List[int] = []

    token_iter = list(re.finditer(r'(\\\(|\\\))', tex_no_comments))
    stack: List[int] = []
    for m in token_iter:
        tok = m.group(0)
        pos = m.start()
        if tok == '\\(':
            stack.append(pos)
        else:
            if stack:
                stack.pop()
            else:
                unmatched_close_positions.append(pos)
    unmatched_open_positions.extend(stack)

    def _sample_at(pos: int, direction: str = 'forward', span: int = 140) -> str:
        if direction == 'forward':
            raw = tex_no_comments[pos:pos+span]
        else:
            start = max(0, pos-span)
            raw = tex_no_comments[start:pos+10]
        end_delim = raw.find('\\)')
        if end_delim != -1:
            raw = raw[:end_delim+2]
        raw = re.sub(r'\s+', ' ', raw).strip()
        return raw

    def _get_line_number(pos: int) -> int:
        return tex_no_comments[:pos].count('\n') + 1

    def _has_priority_keywords(sample: str) -> bool:
        """检查样本是否包含优先关键词（\\right.、array、cases、题号标记等）"""
        priority_patterns = [
            r'\\right\.',
            r'\\begin\{array\}',
            r'\\end\{array\}',
            r'\\begin\{cases\}',
            r'\\end\{cases\}',
            r'\(\d+\)',  # (1) (2) 等小问标记
            r'[①②③④⑤⑥⑦⑧⑨⑩]',  # 圆圈数字
        ]
        return any(re.search(pat, sample) for pat in priority_patterns)

    # 🆕 v1.8.6：进一步甄别"疑似截断"，优先输出包含关键词的样本
    truncated_open_samples: List[str] = []
    priority_open_samples: List[str] = []

    for p in unmatched_open_positions:
        segment = tex_no_comments[p:p+300]
        if '\\)' not in segment:  # 明显没有闭合
            sample = _sample_at(p, 'forward')
            line_num = _get_line_number(p)
            sample_with_line = f"Line {line_num}: {sample}"

            if _has_priority_keywords(sample):
                priority_open_samples.append(sample_with_line)
            else:
                truncated_open_samples.append(sample_with_line)
        else:
            # 可能闭括号远在超过 120 之后，也认为可疑
            close_rel = segment.find('\\)')
            if close_rel > 120:
                sample = _sample_at(p, 'forward')
                line_num = _get_line_number(p)
                sample_with_line = f"Line {line_num}: {sample}"

                if _has_priority_keywords(sample):
                    priority_open_samples.append(sample_with_line)
                else:
                    truncated_open_samples.append(sample_with_line)

        # 限制总数
        if len(priority_open_samples) + len(truncated_open_samples) >= 10:
            break

    # 优先展示包含关键词的样本，然后是普通样本
    final_open_samples = priority_open_samples[:5] + truncated_open_samples[:max(0, 5 - len(priority_open_samples))]

    truncated_close_samples: List[str] = []
    priority_close_samples: List[str] = []

    for p in unmatched_close_positions[:10]:
        sample = _sample_at(p, 'backward')
        line_num = _get_line_number(p)
        sample_with_line = f"Line {line_num}: {sample}"

        if _has_priority_keywords(sample):
            priority_close_samples.append(sample_with_line)
        else:
            truncated_close_samples.append(sample_with_line)

    final_close_samples = priority_close_samples[:5] + truncated_close_samples[:max(0, 5 - len(priority_close_samples))]

    if final_open_samples:
        issues.append(
            "Unmatched opens (samples): " +
            '; '.join(final_open_samples)
        )
    if final_close_samples:
        issues.append(
            "Unmatched closes (samples): " +
            '; '.join(final_close_samples)
        )

    # 针对图片占位符附近的截断：\( ... IMAGE_TODO_START 未闭合
    image_trunc = re.findall(r'\\\([^\\)]{0,200}?% IMAGE_TODO_START', tex_no_comments)
    if image_trunc:
        issues.append(f"Potential image-adjacent truncated math segments: {len(image_trunc)}")

    # 🆕 v1.8.7：报告反向模式（\) 在 \( 前面）
    if reversed_pairs:
        issues.append(f"Reversed inline math pairs detected: {len(reversed_pairs)} lines")
        for lineno, line_content in reversed_pairs[:5]:  # 只显示前5个
            issues.append(f"  Line {lineno}: {line_content}")

    return issues




def validate_brace_balance(tex: str) -> List[str]:
    """🆕 v1.8.6：全局花括号检查 - 忽略 \\{ \\} 和注释，只统计裸 { }

    返回形如：
    - "Line 555: extra '}' (brace balance went negative)"
    - "Global brace imbalance at EOF: balance=..."
    """
    issues: List[str] = []
    balance = 0

    for lineno, raw_line in enumerate(tex.splitlines(), start=1):
        # 去掉注释
        line = raw_line.split('%', 1)[0]
        # 去掉转义的 \{ \}
        line_wo_esc = re.sub(r'\\[{}]', '', line)

        for ch in line_wo_esc:
            if ch == '{':
                balance += 1
            elif ch == '}':
                balance -= 1
                if balance < 0:
                    issues.append(f"Line {lineno}: extra '}}' (brace balance went negative)")
                    balance = 0

    if balance != 0:
        issues.append(f"Global brace imbalance at EOF: balance={balance}")

    return issues




def validate_latex_output(tex_content: str) -> List[str]:
    """
    🆕 v1.3 新增：验证LaTeX输出，返回警告列表
    🆕 v1.6.3：增加【分析】残留检查

    Args:
        tex_content: 生成的LaTeX内容

    Returns:
        警告信息列表
    """
    warnings = []

    # 去除注释内容，避免 IMAGE_TODO 的 CONTEXT 注释触发误报
    tex_no_comments_lines: List[str] = []
    for line in tex_content.splitlines():
        tex_no_comments_lines.append(line.split('%', 1)[0])
    tex_no_comments = "\n".join(tex_no_comments_lines)

    # 🆕 检查0：【分析】meta 段残留
    analysis_meta = re.findall(r'【\s*分析\s*】', tex_no_comments)
    if analysis_meta:
        warnings.append(f"❌ 发现 {len(analysis_meta)} 处【分析】meta 段残留（应已被丢弃）")

    # 检查1：残留的 $ 符号
    dollar_matches = re.findall(r'(?<!\\)\$[^\$]+\$', tex_no_comments)
    if dollar_matches:
        warnings.append(f"⚠️  发现 {len(dollar_matches)} 处残留的 $ 格式")
        for i, match in enumerate(dollar_matches[:3], 1):  # 只显示前3个
            warnings.append(f"     示例{i}: {match}")

    # 检查2：残留的"故选"
    guxuan_matches = re.findall(r'故选[:：][ABCD]+', tex_no_comments)
    if guxuan_matches:
        warnings.append(f"⚠️  发现 {len(guxuan_matches)} 处残留的'故选'")

    # 检查3：中文括号
    chinese_paren = re.findall(r'[（）]', tex_no_comments)
    if chinese_paren:
        warnings.append(f"⚠️  发现 {len(chinese_paren)} 处中文括号")

    # 检查4：环境闭合
    begin_count = tex_content.count(r'\begin{question}')
    end_count = tex_content.count(r'\end{question}')
    if begin_count != end_count:
        warnings.append(f"❌ question 环境不匹配: {begin_count} 个 begin, {end_count} 个 end")

    begin_choices = tex_content.count(r'\begin{choices}')
    end_choices = tex_content.count(r'\end{choices}')
    if begin_choices != end_choices:
        warnings.append(f"❌ choices 环境不匹配: {begin_choices} 个 begin, {end_choices} 个 end")

    # 检查5：空行在宏参数中
    problematic_macros = []
    for macro in ['explain', 'topics', 'answer']:
        pattern = rf'\\{macro}\{{[^}}]*\n\s*\n[^}}]*\}}'
        if re.search(pattern, tex_content):
            problematic_macros.append(macro)
    if problematic_macros:
        warnings.append(f"⚠️  以下宏参数中可能有空行: {', '.join(problematic_macros)}")

    return warnings


# ==================== 主函数 ====================



def validate_and_fix_image_todo_blocks(text: str) -> str:
    """🆕 v1.8.5：验证并修复 IMAGE_TODO 块格式错误

    检查并修复：
    1. IMAGE_TODO_END 后的多余花括号
    2. IMAGE_TODO_START 参数格式错误
    3. 缺失的必需参数

    示例：
        输入：% IMAGE_TODO_END id=xxx{
        输出：% IMAGE_TODO_END id=xxx
    """
    if not text:
        return text

    issues = []

    # 修复1：IMAGE_TODO_END 后的多余字符（花括号或其他）
    # 匹配：% IMAGE_TODO_END id=xxx{ 或 % IMAGE_TODO_END id=xxx {
    pattern = r'(% IMAGE_TODO_END id=[a-zA-Z0-9_-]+)\s*\{[^}]*\}'
    matches = list(re.finditer(pattern, text))
    for match in matches:
        line_num = text[:match.start()].count('\n') + 1
        issues.append(f"Line {line_num}: IMAGE_TODO_END has extra brace")

    # 执行修复
    text = re.sub(pattern, r'\1', text)

    # 修复2：IMAGE_TODO_END 后的单个花括号（无配对）
    text = re.sub(
        r'(% IMAGE_TODO_END id=[a-zA-Z0-9_-]+)\s*\{',
        r'\1',
        text
    )

    # 修复3：IMAGE_TODO_START 行末的多余字符
    text = re.sub(
        r'(% IMAGE_TODO_START[^\n]+)\s*\{[^}]*\}',
        r'\1',
        text
    )

    # 修复4：IMAGE_TODO_END 与正文同处一行，自动拆分
    # 🔧 v1.9.9：修复正则表达式错误截断 ID 的问题
    # 原正则 r'(% IMAGE_TODO_END id=[^\n]+)([^\n]+)' 会错误地将 ID 末尾的数字
    # （如 img2 的 2）当作"尾随内容"拆分到下一行
    # 修复：ID 格式为 slug-QN-imgN，以字母数字结尾，后面必须有非字母数字字符才算尾随内容
    def _split_image_end(match: re.Match) -> str:
        trailing = match.group(2)
        if not trailing.strip():
            return match.group(1)
        return f"{match.group(1)}\n{trailing.lstrip()}"

    text = re.sub(
        r'(% IMAGE_TODO_END id=[a-zA-Z0-9_-]+)([^a-zA-Z0-9_\n-][^\n]*)',
        _split_image_end,
        text
    )

    # 静默修复 IMAGE_TODO 格式错误
    return text





# ============================================================
# 导出列表
# ============================================================

__all__ = [
    'validate_math_integrity',
    'validate_brace_balance',
    'validate_latex_output',
    'validate_and_fix_image_todo_blocks',
]
