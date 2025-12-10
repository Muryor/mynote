#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/lib - 共享工具库模块

提供试卷和讲义转换器的通用功能：
- math_processing: 数学公式处理 (MathStateMachine + 修复函数)
- text_cleaning: 文本清理和 LaTeX 转义
- meta_extraction: 元数据提取 (【答案】【详解】等)
- latex_utils: LaTeX 环境处理工具
- question_processing: 题目结构处理
- validation: 验证和问题检测
- image_handling: 图片占位符和文件处理
"""

# math_processing - 数学公式处理
from .math_processing import (
    CHINESE_MATH_SEPARATORS,
    TokenType,
    MathStateMachine,
    math_sm,
    fix_array_boundaries,
    fix_broken_set_definitions,
    fix_ocr_specific_errors,
    fix_right_boundary_errors,
    fix_unmatched_close_delimiters,
    balance_array_and_cases_env,
    fix_trig_function_spacing,
    fix_greek_letter_spacing,
    fix_bold_math_symbols,
    fix_overset_arrow_vectors,
    fix_specific_reversed_pairs,
    fix_simple_reversed_inline_pairs,
    collect_reversed_math_samples,
)

# text_cleaning - 文本清理和转义
from .text_cleaning import (
    LATEX_SPECIAL_CHARS,
    escape_latex_special,
    standardize_math_symbols,
    convert_markdown_table_to_latex,
    convert_ascii_table_blocks,
    clean_markdown,
    clean_image_attributes,
    remove_decorative_images,
    clean_residual_image_attrs,
    fix_markdown_bold_residue,
    remove_blank_lines_in_macro_args,
    collapse_consecutive_blank_lines,
    remove_blank_lines_before_meta,
    remove_image_todo_blocks,
    soft_wrap_paragraph,
)

# meta_extraction - 元数据提取
from .meta_extraction import (
    META_PATTERNS,
    ANALYSIS_MARKERS,
    ANALYSIS_START_MARKERS,
    extract_meta_and_images,
)

# latex_utils - LaTeX工具
from .latex_utils import (
    fix_tabular_environments,
    add_table_borders,
    fix_fill_in_blanks,
    remove_par_breaks_in_explain,
    clean_question_environments,
)

# question_processing - 题目结构处理
from .question_processing import (
    fix_merged_questions_structure,
    fix_circled_subquestions_to_nested_enumerate,
    fix_nested_subquestions,
    fix_spurious_items_in_enumerate,
    fix_missing_items_in_enumerate,
    _is_likely_stem,
    fix_keep_questions_together,
    parse_question_structure,
    expand_inline_choices,
    convert_choices,
)

# validation - 验证和检测
from .validation import (
    validate_math_integrity,
    validate_brace_balance,
    validate_latex_output,
    validate_and_fix_image_todo_blocks,
)

# image_handling - 图片处理
from .image_handling import (
    IMAGE_PATTERN,
    IMAGE_PATTERN_WITH_ID,
    IMAGE_PATTERN_NO_ID,
    find_markdown_and_images,
    copy_images_to_output,
    generate_image_todo_block,
    infer_figures_dir,
)

# exam_utils - 试卷专用工具
from .exam_utils import (
    SECTION_MAP,
    split_sections,
    split_questions,
    extract_context_around_image,
)

__all__ = [
    # math_processing
    'CHINESE_MATH_SEPARATORS',
    'TokenType',
    'MathStateMachine',
    'math_sm',
    'fix_array_boundaries',
    'fix_broken_set_definitions',
    'fix_ocr_specific_errors',
    'fix_right_boundary_errors',
    'fix_unmatched_close_delimiters',
    'balance_array_and_cases_env',
    'fix_trig_function_spacing',
    'fix_greek_letter_spacing',
    'fix_bold_math_symbols',
    'fix_overset_arrow_vectors',
    'fix_specific_reversed_pairs',
    'fix_simple_reversed_inline_pairs',
    'collect_reversed_math_samples',
    # text_cleaning
    'LATEX_SPECIAL_CHARS',
    'escape_latex_special',
    'standardize_math_symbols',
    'convert_markdown_table_to_latex',
    'convert_ascii_table_blocks',
    'clean_markdown',
    'clean_image_attributes',
    'remove_decorative_images',
    'clean_residual_image_attrs',
    'fix_markdown_bold_residue',
    'remove_blank_lines_in_macro_args',
    'collapse_consecutive_blank_lines',
    'remove_blank_lines_before_meta',
    'remove_image_todo_blocks',
    'soft_wrap_paragraph',
    # meta_extraction
    'META_PATTERNS',
    'ANALYSIS_MARKERS',
    'ANALYSIS_START_MARKERS',
    'extract_meta_and_images',
    # latex_utils
    'fix_tabular_environments',
    'add_table_borders',
    'fix_fill_in_blanks',
    'remove_par_breaks_in_explain',
    'clean_question_environments',
    # question_processing
    'fix_merged_questions_structure',
    'fix_circled_subquestions_to_nested_enumerate',
    'fix_nested_subquestions',
    'fix_spurious_items_in_enumerate',
    'fix_missing_items_in_enumerate',
    '_is_likely_stem',
    'fix_keep_questions_together',
    'parse_question_structure',
    'expand_inline_choices',
    'convert_choices',
    # validation
    'validate_math_integrity',
    'validate_brace_balance',
    'validate_latex_output',
    'validate_and_fix_image_todo_blocks',
    # image_handling
    'IMAGE_PATTERN',
    'IMAGE_PATTERN_WITH_ID',
    'IMAGE_PATTERN_NO_ID',
    'find_markdown_and_images',
    'copy_images_to_output',
    'generate_image_todo_block',
    'infer_figures_dir',
    # exam_utils
    'SECTION_MAP',
    'split_sections',
    'split_questions',
    'extract_context_around_image',
]
