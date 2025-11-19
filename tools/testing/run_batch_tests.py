#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_batch_tests.py — Safe batch tester for DOCX→examx pipeline with compile

Features:
- Auto-discovers DOCX in word_to_tex/input or accepts explicit files
- Runs preprocess pipeline (preprocess_docx.sh) with per-task timeouts
- Compiles refined TeX via build.sh (teacher) with timeout
- Captures stdout/stderr into log files per exam
- Generates a concise markdown report with issues and structural risks

Usage:
  python3 tools/run_batch_tests.py                 # discover all input/*.docx
  python3 tools/run_batch_tests.py path1.docx ...  # run only specific files

Environment: macOS + zsh; uses Python subprocess timeouts (no external deps)
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional

ROOT = Path(__file__).resolve().parents[2]  # tools/testing/ -> tools/ -> mynote/
WORD_TO_TEX = ROOT / "word_to_tex"
INPUT_DIR = WORD_TO_TEX / "input"
OUTPUT_DIR = WORD_TO_TEX / "output"
AUTO_DIR = ROOT / "content" / "exams" / "auto"
SCRIPTS_DIR = WORD_TO_TEX / "scripts"
TOOLS_DIR = ROOT / "tools"
BUILD_SH = ROOT / "build.sh"
PREPROCESS_SH = SCRIPTS_DIR / "preprocess_docx.sh"
METADATA_TEX = ROOT / "settings" / "metadata.tex"


def slugify_from_path(p: Path) -> str:
    stem = p.stem
    h = hashlib.md5(stem.encode("utf-8")).hexdigest()[:6]
    return f"auto_{h}"


@dataclass
class PipelineResult:
    docx: Path
    slug: str
    title: str
    preprocess_ok: bool
    preprocess_err: Optional[str]
    refined_path: Optional[Path]
    question_count: int
    tikz_files: int
    compile_ok: bool
    compile_err: Optional[str]
    pdf_path: Optional[Path]
    missing_chars: List[str]
    undefined_refs: int
    chinese_in_math: int
    because_count: int
    therefore_count: int
    residual_guxuan: int
    refine_placeholders_found: bool
    # 🆕 图片标记统计
    markdown_images_found: int
    markdown_images_paths: List[str]


def run_with_timeout(cmd: List[str], cwd: Path, timeout: int, log_file: Path) -> subprocess.CompletedProcess:
    with log_file.open("w", encoding="utf-8", errors="ignore") as lf:
        lf.write("$ "+" ".join(cmd)+"\n\n")
        try:
            cp = subprocess.run(
                cmd,
                cwd=str(cwd),
                stdout=lf,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=timeout,
                check=False,
            )
            return cp
        except subprocess.TimeoutExpired as e:
            lf.write(f"\n[timeout] Command exceeded {timeout}s and was terminated.\n")
            raise


def extract_counts(refined_tex: Path) -> tuple[int, int, int, int, int, int, bool, int, List[str]]:
    text = refined_tex.read_text(encoding="utf-8")
    q = len(re.findall(r"\\begin\{question\}", text))
    # residual '故选'
    guxuan = text.count("故选")
    # Chinese in math
    rx_math = re.compile(r"\\\\\((.*?)\\\\\)", re.DOTALL)
    zh = re.compile(r"[\u4e00-\u9fff]")
    chinese_in_math = 0
    for m in rx_math.finditer(text):
        if zh.search(m.group(1)):
            chinese_in_math += 1
    because_count = text.count("∵")
    therefore_count = text.count("∴")
    # agent_refine placeholders: expects IMAGE_TODO pattern. If not found, false.
    refine_placeholders_found = "% IMAGE_TODO:" in text
    # tikz files existing alongside
    tikz_dir = refined_tex.parent / "figures" / "tikz"
    tikz_files = len(list(tikz_dir.glob("*.tikz"))) if tikz_dir.exists() else 0
    
    # 🆕 统计残留的 Markdown 图片标记
    # 匹配 ![...](...)... 形式
    md_img_pattern = re.compile(r"!\[.*?\]\([^)]+\)")
    md_images = md_img_pattern.findall(text)
    md_img_count = len(md_images)
    # 提取路径（仅显示前5个）
    md_img_paths = [m for m in md_images[:5]]
    
    return q, tikz_files, chinese_in_math, because_count, therefore_count, guxuan, refine_placeholders_found, md_img_count, md_img_paths


def parse_compile_log(log: Path) -> tuple[List[str], int]:
    if not log.exists():
        return [], 0
    s = log.read_text(encoding="utf-8", errors="ignore")
    # Missing character summaries
    # Collect unique lines containing "Missing character:" and symbol if any
    missing = []
    for line in s.splitlines():
        if "Missing character:" in line:
            missing.append(line.strip())
    # Undefined refs
    undef = len(re.findall(r"Reference `[^']+' .* undefined", s))
    return sorted(set(missing)), undef


def compile_exam(refined_tex: Path, timeout: int, log_dir: Path) -> tuple[bool, Optional[str], Optional[Path]]:
    # Temporarily rewrite metadata to point to refined_tex
    meta = METADATA_TEX.read_text(encoding="utf-8")
    pattern = re.compile(r"\\newcommand\{\\examSourceFile\}\{[^}]*\}")
    replaced = pattern.sub(lambda m: f"\\newcommand{{\\examSourceFile}}{{{refined_tex.as_posix()}}}", meta)
    METADATA_TEX.write_text(replaced, encoding="utf-8")
    try:
        cp = run_with_timeout(["bash", str(BUILD_SH), "exam", "teacher"], ROOT, timeout, log_dir/"compile.log")
        # latexmk may return non-zero but still produce PDF; check PDF
        pdf = ROOT / "output" / "wrap-exam-teacher.pdf"
        ok = pdf.exists()
        err = None if ok else f"latexmk exited {cp.returncode} and PDF missing"
        return ok, err, (pdf if ok else None)
    except subprocess.TimeoutExpired:
        return False, f"compile timeout after {timeout}s", None
    finally:
        # Restore metadata
        METADATA_TEX.write_text(meta, encoding="utf-8")


def run_pipeline(docx: Path, slug: str, title: str, time_pre: int, time_comp: int, base_log: Path) -> PipelineResult:
    log_dir = base_log / slug
    log_dir.mkdir(parents=True, exist_ok=True)
    pre_log = log_dir / "preprocess.log"

    preprocess_ok = False
    preprocess_err = None
    refined_path: Optional[Path] = None
    question_count = 0
    tikz_files = 0
    chinese_in_math = because_count = therefore_count = residual_guxuan = 0
    refine_placeholders_found = False
    markdown_images_found = 0
    markdown_images_paths: List[str] = []

    try:
        run_with_timeout(["bash", str(PREPROCESS_SH), str(docx), slug, title], ROOT, time_pre, pre_log)
        preprocess_ok = True
    except subprocess.TimeoutExpired:
        preprocess_err = f"preprocess timeout after {time_pre}s"
    except Exception as e:
        preprocess_err = f"preprocess error: {e}"

    # If preprocessing succeeded, collect refined tex path
    if preprocess_ok:
        refined_path = AUTO_DIR / slug / "converted_exam.tex"
        if refined_path.exists():
            question_count, tikz_files, chinese_in_math, because_count, therefore_count, residual_guxuan, refine_placeholders_found, markdown_images_found, markdown_images_paths = extract_counts(refined_path)

    # Compile
    compile_ok = False
    compile_err = None
    pdf_path: Optional[Path] = None
    if refined_path and refined_path.exists():
        compile_ok, compile_err, pdf_path = compile_exam(refined_path, time_comp, log_dir)

    # Parse compile log
    missing_chars: List[str] = []
    undefined_refs = 0
    comp_log = log_dir/"compile.log"
    if comp_log.exists():
        missing_chars, undefined_refs = parse_compile_log(comp_log)

    return PipelineResult(
        docx=docx,
        slug=slug,
        title=title,
        preprocess_ok=preprocess_ok,
        preprocess_err=preprocess_err,
        refined_path=refined_path,
        question_count=question_count,
        tikz_files=tikz_files,
        compile_ok=compile_ok,
        compile_err=compile_err,
        pdf_path=pdf_path,
        missing_chars=missing_chars,
        undefined_refs=undefined_refs,
        chinese_in_math=chinese_in_math,
        because_count=because_count,
        therefore_count=therefore_count,
        residual_guxuan=residual_guxuan,
        refine_placeholders_found=refine_placeholders_found,
        markdown_images_found=markdown_images_found,
        markdown_images_paths=markdown_images_paths,
    )


def write_report(results: List[PipelineResult], report_path: Path):
    lines: List[str] = []
    lines.append("# Word→TeX Pipeline Batch Report\n")
    lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 🆕 添加总体统计
    total_docs = len(results)
    total_success = sum(1 for r in results if r.compile_ok)
    total_md_images = sum(r.markdown_images_found for r in results)
    total_unicode_symbols = sum(r.because_count + r.therefore_count for r in results)
    
    lines.append(f"## 总体统计\n")
    lines.append(f"- 处理文档数: {total_docs}")
    lines.append(f"- 编译成功: {total_success}/{total_docs}")
    lines.append(f"- 残留 Markdown 图片标记: {total_md_images} 处")
    lines.append(f"- 残留 Unicode 符号 (∵/∴): {total_unicode_symbols} 处")
    lines.append("")
    
    for r in results:
        lines.append(f"## {r.docx.name} → `{r.slug}`\n")
        lines.append(f"- Preprocess: {'OK' if r.preprocess_ok else 'FAIL'}{'' if not r.preprocess_err else ' — '+r.preprocess_err}")
        if r.refined_path:
            lines.append(f"- Refined TeX: `{r.refined_path}`")
        lines.append(f"- Questions: {r.question_count}  | TikZ files: {r.tikz_files}")
        lines.append(f"- Compile: {'OK' if r.compile_ok else 'FAIL'}{'' if not r.compile_err else ' — '+r.compile_err}")
        if r.pdf_path:
            lines.append(f"- PDF: `{r.pdf_path}`")
        
        # 🆕 图片处理统计
        if r.markdown_images_found > 0:
            lines.append(f"- **图片处理**: 检测到 {r.markdown_images_found} 个 Markdown 图片标记")
            if r.markdown_images_paths:
                lines.append("  - 示例路径:")
                for path in r.markdown_images_paths:
                    lines.append(f"    - `{path}`")
        
        # Issues
        issues: List[str] = []
        if r.missing_chars:
            issues.append(f"Missing characters: {len(r.missing_chars)} line(s)")
        if r.undefined_refs:
            issues.append(f"Undefined refs: {r.undefined_refs}")
        if r.chinese_in_math:
            issues.append(f"Chinese-in-math segments: {r.chinese_in_math}")
        if r.because_count or r.therefore_count:
            issues.append(f"Unicode ∵: {r.because_count}, ∴: {r.therefore_count}")
        if r.residual_guxuan:
            issues.append(f"Residual '故选': {r.residual_guxuan}")
        if not r.refine_placeholders_found:
            issues.append("Agent placeholder not recognized (no % IMAGE_TODO block)")
        if issues:
            lines.append("- Issues: ")
            for item in issues:
                lines.append(f"  - {item}")
        lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Batch test DOCX→examx pipeline and compile with timeouts")
    ap.add_argument("docx", nargs="*", help="DOCX files to process; default is all under word_to_tex/input")
    ap.add_argument("--pre-timeout", type=int, default=240, help="Timeout seconds for preprocess stage (default 240)")
    ap.add_argument("--comp-timeout", type=int, default=300, help="Timeout seconds for compile stage (default 300)")
    args = ap.parse_args(argv)

    if not PREPROCESS_SH.exists():
        print(f"Missing {PREPROCESS_SH}", file=sys.stderr)
        return 2
    if not BUILD_SH.exists():
        print(f"Missing {BUILD_SH}", file=sys.stderr)
        return 2

    docx_files: List[Path]
    if args.docx:
        docx_files = [Path(p).resolve() for p in args.docx]
    else:
        docx_files = sorted(INPUT_DIR.glob("*.docx"))

    log_root = OUTPUT_DIR / "test_logs"
    log_root.mkdir(parents=True, exist_ok=True)
    results: List[PipelineResult] = []
    for docx in docx_files:
        if not docx.exists():
            print(f"Skip missing: {docx}")
            continue
        slug = slugify_from_path(docx)
        title = docx.stem
        print(f"[run] {docx.name} → {slug}")
        res = run_pipeline(docx, slug, title, args.pre_timeout, args.comp_timeout, log_root)
        results.append(res)

    report = OUTPUT_DIR / "TEST_COMPILE_REPORT.md"
    write_report(results, report)
    print(f"\n✅ Report written: {report}")
    print(f"   Logs under: {log_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
