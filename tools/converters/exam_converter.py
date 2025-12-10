#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ExamConverter - exam Markdown → examx LaTeX converter.

Phase-B: begins using tools.lib modular functions while maintaining
compatibility with legacy core converter.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

# Import modular libs
from tools.lib import (
    split_sections,
    split_questions,
    SECTION_MAP,
    clean_markdown,
    extract_meta_and_images,
    math_sm,
    fix_right_boundary_errors,
    fix_unmatched_close_delimiters,
    balance_array_and_cases_env,
    validate_and_fix_image_todo_blocks,
    fix_specific_reversed_pairs,
    fix_simple_reversed_inline_pairs,
    fix_tabular_environments,
    add_table_borders,
    fix_trig_function_spacing,
    fix_bold_math_symbols,
    fix_greek_letter_spacing,
    fix_overset_arrow_vectors,
    fix_markdown_bold_residue,
    fix_merged_questions_structure,
    fix_nested_subquestions,
    fix_spurious_items_in_enumerate,
    fix_circled_subquestions_to_nested_enumerate,
    fix_keep_questions_together,
    remove_par_breaks_in_explain,
    remove_blank_lines_in_macro_args,
    collapse_consecutive_blank_lines,
    remove_blank_lines_before_meta,
    remove_image_todo_blocks,
    convert_choices,
)

# Still import from legacy for not-yet-migrated functions
from tools.core.ocr_to_examx import (
    build_question_tex,
    init_issue_log,
    detect_question_issues,
    append_issue_log,
    fix_undefined_symbols,
    split_long_lines_in_explain,
    fix_left_pipe_without_right,
    fix_angle_bracket_notation,
    balance_left_right_delimiters,
    collect_reversed_math_samples,
    cleanup_remaining_image_markers,
    cleanup_guxuan_in_macros,
    _fix_equation_system_arrows,
    process_text_for_latex,
    postprocess_inline_math,
)

from .base_converter import BaseConverter, ConversionResult


class ExamConverter(BaseConverter):
    """Exam-style Markdown → examx LaTeX converter.

    Phase-B: uses modular tools.lib functions where available,
    falls back to legacy core for complex question-building logic.
    """

    def __init__(self, input_md: Path, output_tex: Path, *, title: str = "", slug: str = "", enable_issue_detection: bool = True, figures_dir: str = ""):
        super().__init__(input_md, output_tex, title=title, slug=slug, enable_issue_detection=enable_issue_detection, figures_dir=figures_dir)

    def convert_text(self, md_text: str) -> ConversionResult:
        """Convert markdown text to examx LaTeX using modular pipeline."""
        
        # Clean markdown
        md_text = clean_markdown(md_text)
        
        # Split into sections
        sections = split_sections(md_text)

        # Initialize issue log if enabled
        if self.enable_issue_detection and self.slug:
            init_issue_log(self.slug)

        out_lines = []
        out_lines.append(f"\\examxtitle{{{self.title}}}")

        q_index = 0  # Global question counter
        for raw_title, body in sections:
            sec_label = SECTION_MAP.get(raw_title, raw_title)
            out_lines.append("")
            out_lines.append(f"\\section{{{sec_label}}}")

            for block in split_questions(body):
                if not block.strip():
                    continue

                q_index += 1
                raw_block = block  # Save original Markdown fragment

                try:
                    # Extract meta and images
                    content, meta, images, attachments = extract_meta_and_images(
                        block, question_index=q_index, slug=self.slug
                    )

                    # Convert choices (still uses legacy)
                    stem, options, extracted_analysis = convert_choices(content)

                    # Merge extracted analysis with meta
                    if extracted_analysis and not meta.get('explain'):
                        meta['explain'] = extracted_analysis
                    elif extracted_analysis:
                        meta['explain'] = meta['explain'] + '\n' + extracted_analysis

                    # Build question TeX (still uses legacy)
                    q_tex = build_question_tex(
                        stem, options, meta, images, attachments, sec_label,
                        question_index=q_index, slug=self.slug
                    )

                    # Detect issues if enabled
                    if self.enable_issue_detection and self.slug:
                        issues = detect_question_issues(
                            slug=self.slug,
                            q_index=q_index,
                            raw_block=raw_block,
                            tex_block=q_tex,
                            meta=meta,
                            section_label=sec_label,
                        )
                        append_issue_log(
                            slug=self.slug,
                            q_index=q_index,
                            raw_block=raw_block,
                            tex_block=q_tex,
                            issues=issues,
                            meta=meta,
                            section_label=sec_label,
                        )

                    # Validate generated TeX
                    if r'\begin{question}' in q_tex and r'\end{question}' not in q_tex:
                        print(f"⚠️  Q{q_index} 缺少 \\end{{question}}，自动补全")
                        q_tex += "\n\\end{question}"

                    out_lines.append("")
                    out_lines.append(q_tex)
                except Exception as e:
                    import traceback
                    print(f"⚠️  Q{q_index} ({sec_label}) 转换失败: {str(e)}")
                    print(f"   {traceback.format_exc()}")
                    out_lines.append("")
                    out_lines.append(r"\begin{question}")
                    out_lines.append(f"% ERROR: Q{q_index} 转换失败 - {str(e)}")
                    out_lines.append(r"\end{question}")

        out_lines.append("")

        # Final processing: cleanup and apply modular fixes
        result = "\n".join(out_lines)
        # 保留图片占位符，后续可按需手动移除；空白折叠在占位符保留后进行
        result = collapse_consecutive_blank_lines(result, max_blank_lines=1)
        result = remove_blank_lines_before_meta(result)
        result = remove_blank_lines_in_macro_args(result)
        result = split_long_lines_in_explain(result, max_length=800)
        result = remove_par_breaks_in_explain(result)

        # Convert display math to inline (skip comments)
        import re
        def convert_display_math_skip_comments(text: str) -> str:
            lines = text.split('\n')
            result_lines = []
            for line in lines:
                if line.strip().startswith('%'):
                    result_lines.append(line)
                else:
                    line = re.sub(r'\$\$\s*(.+?)\s*\$\$', r'\\(\1\\)', line)
                    result_lines.append(line)
            return '\n'.join(result_lines)
        
        result = convert_display_math_skip_comments(result)
        result = _fix_equation_system_arrows(result)

        # Clean remaining $$ and image markers
        lines = result.split('\n')
        result = '\n'.join(
            line if line.strip().startswith('%') else line.replace('$$', '')
            for line in lines
        )
        result = cleanup_remaining_image_markers(result)

        # Clean guxuan remnants
        result = cleanup_guxuan_in_macros(result)
        result = re.sub(r'故选[:：][ABCD]+\.?[^\n}]*', '', result)
        result = re.sub(r'故答案为[:：]?[ABCD]*\.?', '', result)

        # Apply modular fixes
        result = fix_merged_questions_structure(result)
        result = fix_right_boundary_errors(result)
        result = fix_unmatched_close_delimiters(result)
        result = validate_and_fix_image_todo_blocks(result)
        result = balance_array_and_cases_env(result)
        result = fix_specific_reversed_pairs(result)
        result = fix_simple_reversed_inline_pairs(result)
        result = fix_left_pipe_without_right(result)
        result = fix_angle_bracket_notation(result)
        result = balance_left_right_delimiters(result)

        # Collect reversed math samples if slug provided
        if self.slug:
            collect_reversed_math_samples(result, self.slug)

        # Additional fixes
        result = fix_tabular_environments(result)
        result = add_table_borders(result)
        result = fix_trig_function_spacing(result)
        result = fix_undefined_symbols(result)
        result = fix_markdown_bold_residue(result)
        result = fix_bold_math_symbols(result)
        result = fix_greek_letter_spacing(result)
        result = fix_overset_arrow_vectors(result)
        result = fix_nested_subquestions(result)
        result = fix_spurious_items_in_enumerate(result)
        result = fix_circled_subquestions_to_nested_enumerate(result)
        result = fix_keep_questions_together(result)

        return ConversionResult(tex=result)
