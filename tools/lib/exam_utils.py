#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
exam_utils.py - Exam-specific conversion utilities

Functions for exam paper structure parsing and conversion that are specific
to the exam format (sections, questions, choices, etc.).
"""

from typing import List, Tuple, Dict, Optional
import re

# ============================================================
# Constants
# ============================================================

SECTION_MAP = {
    "一、单选题": "单选题",
    "二、单选题": "单选题",
    "二、多选题": "多选题",
    "三、填空题": "填空题",
    "四、解答题": "解答题",
}


# ============================================================
# Section and Question Splitting
# ============================================================

def split_sections(text: str) -> List[Tuple[str, str]]:
    """拆分章节（支持 markdown 标题和加粗格式）
    
    支持多种格式：
    1. Markdown 标题：# 一、单选题
    2. 加粗格式：**一、单选题**
    3. 灵活格式：# 一、选择题：本题共8小题... （会被规范化为 一、单选题）
    4. 灵活格式：# 二、选择题：本题共3小题，有多项... （会被规范化为 二、多选题）
    """
    lines = text.splitlines()
    sections = []
    current_title = None
    current_lines = []

    # 定义章节匹配模式（更灵活）
    # 支持：一、选择题/单选题/多选题/填空题/解答题，后面可以有冒号和其他说明
    section_pattern = r"(一|二|三|四)、(选择题|单选题|多选题|填空题|解答题)"
    
    def normalize_section_title(num: str, title: str, full_line: str) -> str:
        """规范化章节标题"""
        # 检查是否是多选题（通过内容判断）
        if title == "选择题":
            # 检查是否包含"多项"、"多选"等关键词
            if "多项" in full_line or "多选" in full_line:
                return f"{num}、多选题"
            # 第一个选择题默认是单选
            elif num == "一":
                return f"{num}、单选题"
            # 第二个选择题如果有"有多项符合"等描述，是多选
            else:
                # 检查上下文，如果有"有多项"等关键词则是多选
                if "多项" in full_line or "部分选对" in full_line:
                    return f"{num}、多选题"
                return f"{num}、单选题"  # 默认单选
        else:
            return f"{num}、{title}"

    for line in lines:
        stripped = line.strip()
        
        # 匹配 markdown 标题格式：# 一、选择题...
        m = re.match(r"^#+\s*" + section_pattern, stripped)
        if m:
            if current_title is not None:
                sections.append((current_title, "\n".join(current_lines).strip()))
                current_lines = []
            current_title = normalize_section_title(m.group(1), m.group(2), stripped)
            continue
            
        # 匹配加粗格式：**一、选择题**... 或 **一、选择题：说明文字**
        # 注意：** 可能紧跟在章节名后，也可能在整行末尾
        m = re.match(r"^\*\*" + section_pattern + r"(?:\*\*|[^*]*\*\*)", stripped)
        if m:
            if current_title is not None:
                sections.append((current_title, "\n".join(current_lines).strip()))
                current_lines = []
            current_title = normalize_section_title(m.group(1), m.group(2), stripped)
            continue
        
        # 匹配纯文本格式：一、选择题...（无markdown标记）
        m = re.match(r"^" + section_pattern, stripped)
        if m:
            if current_title is not None:
                sections.append((current_title, "\n".join(current_lines).strip()))
                current_lines = []
            current_title = normalize_section_title(m.group(1), m.group(2), stripped)
            continue
            
        # 非标题行
        if current_title is not None:
            current_lines.append(line)

    if current_title is not None and current_lines:
        sections.append((current_title, "\n".join(current_lines).strip()))

    return sections


def split_questions(section_body: str) -> List[str]:
    """拆分题目（智能合并相同题号）
    
    🆕 v1.8.5：改进题目拆分逻辑，避免将解答题的小问误识别为新题
    - 只在题号连续递增时才拆分新题
    - 相同题号或题号不连续的行不会被拆分（可能是小问）
    
    修复：连续相同题号的内容会合并到一个题目中
    例如：17. 题干  17. (1)...  17. (2)... → 合并为一题
    """
    lines = section_body.splitlines()
    blocks = []
    current = []
    last_question_num = 0  # 记录上一题的题号，初始为0

    def flush():
        if current:
            blocks.append("\n".join(current).strip())
            current.clear()

    for line in lines:
        stripped = line.strip()
        # 匹配题号：1. 或 1． 或 1、
        match = re.match(r"^(\d+)[\.．、]\s*", stripped)
        if match:
            num = int(match.group(1))
            # 只有在题号连续递增时才认为是新题
            # 或者是第一题（last_question_num == 0）
            if last_question_num == 0 or num == last_question_num + 1:
                flush()
                last_question_num = num
                current.append(line)
            else:
                # 题号不连续（包括相同题号），可能是小问标号，不拆分
                current.append(line)
        else:
            current.append(line)

    flush()
    return blocks


def extract_context_around_image(text: str, img_match_start: int, img_match_end: int,
                                  context_len: int = 50) -> Tuple[str, str]:
    """提取图片前后的上下文文本

    Args:
        text: 完整文本
        img_match_start: 图片匹配的起始位置
        img_match_end: 图片匹配的结束位置
        context_len: 上下文长度（字符数）

    Returns:
        (context_before, context_after) 元组
    """
    # 提取前文
    before_start = max(0, img_match_start - context_len)
    context_before = text[before_start:img_match_start].strip()
    # 清理换行符和多余空格
    context_before = ' '.join(context_before.split())

    # 提取后文
    after_end = min(len(text), img_match_end + context_len)
    context_after = text[img_match_end:after_end].strip()
    context_after = ' '.join(context_after.split())

    return context_before, context_after


# ============================================================
# Export
# ============================================================

__all__ = [
    "SECTION_MAP",
    "split_sections",
    "split_questions",
    "extract_context_around_image",
]
