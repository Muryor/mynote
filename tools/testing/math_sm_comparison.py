#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""math_sm_comparison.py — 状态机 vs 旧管线 A/B 对比测试工具

目的：
1. 对同一原始 Markdown 文件运行两套数学处理：
   - 新：MathStateMachine (当前默认)
   - 旧：legacy 正则管线 (smart_inline_math + fix_double_wrapped_math + fix_inline_math_glitches)
2. 输出关键质量指标与差异统计，帮助确认可以安全移除旧函数。

使用示例：
    python3 tools/testing/math_sm_comparison.py \
        word_to_tex/output/nanjing_2026_sep_raw.md \
        --title "南京调研" --slug test_nanjing

输出：
    - new_output.tex 与 legacy_output.tex （临时存放在同级 test_out/）
    - 对比报告：math_sm_comparison_report.md

注意：该脚本不会修改主代码，只在内存中 monkeypatch process_text_for_latex。
"""

from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
TOOLS_CORE = ROOT / "tools" / "core"
sys.path.insert(0, str(TOOLS_CORE))

import ocr_to_examx as core  # type: ignore

# ---------------- 验证器 ----------------

def check_math_balance(text: str) -> Tuple[int, int, int]:
    """检查行内数学定界符配对情况
    返回: (opens, closes, diff)
    """
    opens = text.count(r"\(")
    closes = text.count(r"\)")
    return opens, closes, opens - closes


def find_stray_dollars(text: str) -> int:
    """检测裸露的美元符号数量（排除被转义与成对 $$ 已被移除后的残留）"""
    # 已统一为 \( \)，所以非转义 $ 应该不存在
    return len(re.findall(r"(?<!\\)\$", text))


def detect_empty_math(text: str) -> int:
    """统计空数学块 \(\) 或 \[\]"""
    return len(re.findall(r"\\\(\s*\\\)", text)) + len(re.findall(r"\\\[\s*\\\]", text))


def detect_right_boundary_glitches(text: str) -> int:
    """检测 OCR 遗留的 \right. $$ 或 \right.\\) 等畸形模式"""
    patterns = [r"\\right\.\s*\$\$", r"\\right\.\\\\\)"]
    c = 0
    for p in patterns:
        c += len(re.findall(p, text))
    return c


def detect_double_wrapped(text: str) -> int:
    """检测双重包裹模式 $$\( ... \)$$ 或 $\( ... \)$ 等"""
    patterns = [r"\$\$\s*\\\(.*?\\\)\s*\$\$", r"\$\s*\\\(.*?\\\)\s*\$"]
    c = 0
    for p in patterns:
        c += len(re.findall(p, text, flags=re.DOTALL))
    return c


def summarize(text: str) -> Dict[str, int]:
    return {
        "length": len(text),
        "questions": text.count("\\begin{question}"),
        "math_opens": text.count(r"\("),
        "math_closes": text.count(r"\)"),
        "balance_diff": check_math_balance(text)[2],
        "stray_dollars": find_stray_dollars(text),
        "empty_math": detect_empty_math(text),
        "right_boundary_glitches": detect_right_boundary_glitches(text),
        "double_wrapped": detect_double_wrapped(text),
        "unicode_because": text.count("∵"),
        "unicode_therefore": text.count("∴"),
        "residual_guxuan": text.count("故选"),
    }


# ---------------- 旧管线模拟 ----------------

def legacy_process_text(text: str, is_math_heavy: bool = False) -> str:
    """模拟旧版数学处理流程（精简版）
    保留：强调清理 + 故选清理 + smart_inline_math + fix_double_wrapped_math + fix_inline_math_glitches
    不使用：wrap_math_variables / sanitize_math （避免破坏比较稳定性）
    """
    if not text:
        return text
    # 前置与现行一致
    text = re.sub(r"\*\s*(\$[^$]+\$)\s*\*", r"\1", text)
    text = re.sub(r"\*([A-Za-z0-9])\*", r"\\emph{\1}", text)
    text = re.sub(r"[,，。\.;；]\s*故选[:：][ABCD]+[.。]?\s*$", "", text)
    text = re.sub(r"\n+故选[:：][ABCD]+[.。]?\s*$", "", text)
    text = re.sub(r"^\s*故选[:：][ABCD]+[.。]?\s*", "", text)
    text = re.sub(r"\n+故答案为[:：]", "", text)
    text = re.sub(r"^\s*故选[:：][ABCD]+[.。]?\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"[，,]?\s*故选[:：]\s*[ABCD]+[。．.]*\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^【?详解】?[:：]?\s*", "", text)
    if '∵' in text or '∴' in text:
        text = text.replace('∵', '$\\because$').replace('∴', '$\\therefore$')
    if not is_math_heavy:
        text = core.escape_latex_special(text, in_math_mode=False)
    # 旧数学转换
    text = core.smart_inline_math(text)
    text = core.fix_double_wrapped_math(text)
    text = core.fix_inline_math_glitches(text)
    return text


def run_conversion(md_path: Path, title: str, slug: str, use_legacy: bool = False) -> str:
    md_text = md_path.read_text(encoding='utf-8')
    # Monkeypatch process_text_for_latex
    original = core.process_text_for_latex
    try:
        if use_legacy:
            def _legacy_wrapper(t: str, is_math_heavy: bool = False):
                return legacy_process_text(t, is_math_heavy=is_math_heavy)
            core.process_text_for_latex = _legacy_wrapper  # type: ignore
        tex = core.convert_md_to_examx(md_text, title=title, slug=slug, enable_issue_detection=False)
        # Fallback: 若未识别任何 question（可能因为原始文件没有 # 章节标题），
        # 直接对全文做数学处理以获得统计意义。
        if tex.count("\\begin{question}") == 0:
            processed = core.process_text_for_latex(md_text, is_math_heavy=True)
            tex = ("% Fallback raw processing (no sections detected)\n" + processed)
        return tex
    finally:
        core.process_text_for_latex = original  # restore


def diff_basic(a: str, b: str) -> Dict[str, int]:
    """简单字符级差异统计"""
    return {
        "len_a": len(a),
        "len_b": len(b),
        "delta_len": len(b) - len(a),
        "questions_a": a.count('\\begin{question}'),
        "questions_b": b.count('\\begin{question}'),
    }


def write_report(path: Path, new_stats: Dict[str, int], legacy_stats: Dict[str, int], diff_stats: Dict[str, int]):
    lines: List[str] = []
    lines.append("# Math State Machine Comparison Report\n")
    lines.append("## 新管线统计\n")
    for k, v in new_stats.items():
        if k == 'balance_diff' and v != 0:
            lines.append(f"- {k}: {v}  (WARNING: imbalance)")
        else:
            lines.append(f"- {k}: {v}")
    lines.append("\n## 旧管线统计\n")
    for k, v in legacy_stats.items():
        if k == 'balance_diff' and v != 0:
            lines.append(f"- {k}: {v}  (WARNING: imbalance)")
        else:
            lines.append(f"- {k}: {v}")
    lines.append("\n## 基本差异\n")
    for k, v in diff_stats.items():
        lines.append(f"- {k}: {v}")
    # 重点对比
    improvements = []
    if legacy_stats['double_wrapped'] and not new_stats['double_wrapped']:
        improvements.append("双重包裹已消除")
    if legacy_stats['stray_dollars'] > new_stats['stray_dollars']:
        improvements.append("裸 $ 符号减少")
    if new_stats['balance_diff'] == 0 and legacy_stats['balance_diff'] != 0:
        improvements.append("数学括号配对修复")
    if improvements:
        lines.append("\n## 改进亮点\n")
        for item in improvements:
            lines.append(f"- {item}")
    path.write_text("\n".join(lines), encoding='utf-8')


def main() -> int:
    ap = argparse.ArgumentParser(description="Compare MathStateMachine with legacy regex pipeline")
    ap.add_argument("md", help="原始 Markdown 文件路径")
    ap.add_argument("--title", default="Untitled Exam", help="试卷标题")
    ap.add_argument("--slug", default="comparison", help="输出 slug")
    ap.add_argument("--outdir", default="tools/testing/test_out", help="输出目录")
    args = ap.parse_args()

    md_path = Path(args.md).resolve()
    if not md_path.exists():
        print(f"❌ Missing markdown file: {md_path}")
        return 2

    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    # Run new pipeline
    new_tex = run_conversion(md_path, args.title, slug=args.slug + "_new", use_legacy=False)
    legacy_tex = run_conversion(md_path, args.title, slug=args.slug + "_legacy", use_legacy=True)

    (outdir / "new_output.tex").write_text(new_tex, encoding='utf-8')
    (outdir / "legacy_output.tex").write_text(legacy_tex, encoding='utf-8')

    new_stats = summarize(new_tex)
    legacy_stats = summarize(legacy_tex)
    diff_stats = diff_basic(legacy_tex, new_tex)

    report_path = outdir / "math_sm_comparison_report.md"
    write_report(report_path, new_stats, legacy_stats, diff_stats)

    print(f"✅ 完成对比: {report_path}")
    print(f"   新输出: {outdir/'new_output.tex'}")
    print(f"   旧输出: {outdir/'legacy_output.tex'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
