#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
meta_extraction.py - 元数据提取模块 - 答案、解析、知识点等

从 ocr_to_examx.py 提取的共享工具函数，供 exam 和 handout 转换器使用。

生成时间: 自动提取
源文件: tools/core/ocr_to_examx.py
"""

from typing import List, Dict, Tuple, Optional
import re

# Image patterns and helpers
from tools.lib.image_handling import (
    IMAGE_PATTERN,
    IMAGE_PATTERN_WITH_ID,
    IMAGE_PATTERN_NO_ID,
)
# Context helper for image extraction
from tools.lib.exam_utils import extract_context_around_image

# ============================================================
# 元数据提取模块 - 答案、解析、知识点等
# ============================================================

META_PATTERNS = {
    "answer": r"^【答案】(.*)$",
    "difficulty": r"^【难度】([\d.]+)",
    "topics": r"^【知识点】(.*)$",
    "analysis": r"^【分析】(.*)$",
    "explain": r"^【详解】(.*)$",
    "diangjing": r"^【点睛】(.*)$",
    "dianjing_alt": r"^【点评】(.*)$",
}


ANALYSIS_MARKERS = [
    '根据', '由题意', '因为', '所以', '故选', '答案',
    '分析', '详解', '解答', '证明', '计算可得',
    '显然', '易知', '可知', '不难看出', '由此可得',
    '综上', '故', '即', '则', '可得'
]


ANALYSIS_START_MARKERS = [
    '根据', '由题意', '因为', '所以', '故选', '答案',
    '分析', '详解', '解答', '证明', '计算可得',
    '显然', '易知', '可知', '不难看出', '由此可得', '综上'
]


def extract_meta_and_images(block: str, question_index: int = 0, slug: str = "") -> Tuple[str, Dict, List, List]:
    r"""提取元信息、图片与附件（状态机重构：防止跨题累积）

    🆕 v1.9: 新增附件识别与提取
    🆕 新增参数：question_index 和 slug 用于生成图片 ID

    目标：避免上一题的多行【详解】/【分析】错误吞并下一题题干。
    关键边界：
      - 新的 meta 开始（答案/难度/知识点/详解/分析）
      - 题号开始：^\s*>?\s*(?:\d+[\.．、]\s+|（\d+）\s+|\d+\)\s+)
      - 章节标题：^#{1,6}\s*(第?[一二三四五六七八九十]+[、．.].*)$
      - 空行 + lookahead 为题号时，作为安全边界（若上一行像环境续行则跳过该空行边界）
      - 引述空行 ^>\s*$ 忽略
      - 🆕 附件标记：^附[:：]、^附表、^参考数据表

    Returns:
        (content, meta, images, attachments) 四元组
        attachments: List[Dict] 包含 kind, lines 字段
    """
    # 规范化并切分行
    lines = block.splitlines()

    # 结果容器
    meta = {k: "" for k in META_PATTERNS}
    # 🆕 修复：analysis 单独存在，后续会被丢弃
    meta_alias_map = {
        "analysis": "analysis",  # analysis 单独存在，后面会被丢弃
        "explain": "explain",
        "answer": "answer",
        "difficulty": "difficulty",
        "topics": "topics",
    }

    content_lines: List[str] = []
    images: List[Dict] = []
    attachments: List[Dict] = []  # 🆕 附件列表

    # 编译边界正则（增强版：支持更多题号格式和章节标题）
    question_start_perm = re.compile(r"^\s*>?\s*(?:\d{1,3}[\.．、]\s+|（\d{1,3}）\s+|\d{1,3}\)\s+)")
    section_header = re.compile(r"^#{1,6}\s*(第?[一二三四五六七八九十]+[、．.].*)$")
    quote_blank = re.compile(r"^>\s*$")
    env_cont_hint = re.compile(r"(\\\\\s*$)|\\begin\{|\\left|\\right")

    # 🆕 v1.9: 附件标记正则
    attachment_start = re.compile(r"^(附[:：]|附表|参考数据表)")
    markdown_table_line = re.compile(r"^\s*\|.*\|.*$")  # Markdown 表格行
    box_drawing_chars = re.compile(r"[│─┌┐└┘┼├┤┬┴]")  # Box-drawing 字符

    # 🆕 修复：将 META_PATTERNS 编译，分离 analysis 和 explain
    # 🆕 v1.9.9: 添加【解析】支持（图片 OCR 试卷常用）
    meta_starts = [
        ("answer", re.compile(r"^【\s*答案\s*】[:：]?\s*(.*)$")),
        ("difficulty", re.compile(r"^【\s*难度\s*】[:：]?\s*([\d.]+).*")),
        ("topics", re.compile(r"^【\s*(知识点|考点)\s*】[:：]?\s*(.*)$")),
        ("analysis", re.compile(r"^【\s*分析\s*】[:：]?\s*(.*)$")),
        ("explain", re.compile(r"^【\s*(详解|解析)\s*】[:：]?\s*(.*)$")),  # 🆕 支持【解析】
        ("diangjing", re.compile(r"^【\s*点睛\s*】[:：]?\s*(.*)$")),
        ("dianjing_alt", re.compile(r"^【\s*点评\s*】[:：]?\s*(.*)$")),
    ]

    # 状态
    state = "NORMAL"  # or "IN_META" or "IN_ATTACHMENT"
    current_meta_key: Optional[str] = None
    current_meta_lines: List[str] = []

    # 🆕 v1.9: 附件状态
    current_attachment_lines: List[str] = []
    current_attachment_kind: Optional[str] = None  # "table", "text", "figure"

    def flush_meta():
        nonlocal current_meta_key, current_meta_lines
        if current_meta_key is None:
            return
        # 归一化到别名键
        key = meta_alias_map.get(current_meta_key, current_meta_key)
        # 🆕 修复：遇到 analysis/diangjing/dianjing_alt 时直接丢弃
        if key in ("analysis", "diangjing", "dianjing_alt"):
            # 说明这是【分析】/【点睛】/【点评】段，直接舍弃，不写入 meta 字典
            current_meta_key = None
            current_meta_lines = []
            return
        # 合并清理
        text = "\n".join(current_meta_lines)
        # 去掉可能残留的标签前缀
        text = re.sub(r"^【?(?:答案|难度|知识点|考点|详解|分析)】?[:：]?\s*", "", text)
        # 对于 explain 字段，保留原始格式（不折叠空行），让后续 remove_par_breaks_in_explain 处理
        # 其他字段压缩空行
        if key != "explain":
            text = re.sub(r"\n\s*\n+", "\n", text)
        # 合并：若已有 explain，则追加一行
        if key == "explain" and meta.get("explain"):
            meta["explain"] = (meta["explain"] + "\n" + text.strip()).strip()
        else:
            meta[key] = text.strip()
        # 重置
        current_meta_key = None
        current_meta_lines = []

    def flush_attachment():
        """🆕 v1.9: 刷新附件缓冲区"""
        nonlocal current_attachment_lines, current_attachment_kind
        if not current_attachment_lines or current_attachment_kind is None:
            current_attachment_lines = []
            current_attachment_kind = None
            return

        # 添加到附件列表
        attachments.append({
            "kind": current_attachment_kind,
            "lines": current_attachment_lines.copy()
        })

        # 重置
        current_attachment_lines = []
        current_attachment_kind = None

    def is_question_start(s: str) -> bool:
        return bool(question_start_perm.match(s))

    def is_section_header(s: str) -> bool:
        return bool(section_header.match(s))

    def image_match(s: str):
        # 优先匹配带ID的图片
        m = IMAGE_PATTERN_WITH_ID.search(s)
        if m:
            return ('with_id', m)
        # 然后匹配无ID的图片
        m = IMAGE_PATTERN_NO_ID.search(s)
        if m:
            return ('no_id', m)
        # 最后尝试旧版简单格式
        m = IMAGE_PATTERN.search(s)
        if m:
            return ('simple', m)
        return None

    # 查找上一条非空行（用于环境续行判断）
    def find_prev_nonempty(idx: int) -> Optional[str]:
        j = idx - 1
        while j >= 0:
            if lines[j].strip():
                return lines[j]
            j -= 1
        return None

    # 查找下一条非空行（用于 blank+lookahead 判断）
    def find_next_nonempty(idx: int) -> Optional[str]:
        j = idx + 1
        while j < len(lines):
            if lines[j].strip():
                return lines[j]
            j += 1
        return None

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # 🆕 v1.6.2：图片行识别增强 - 区分独立图片块 vs 内联公式图片
        # 只有当图片"独占一行"且是完整匹配时，才提取为图片块
        # 内联图片（如 "已知集合![](image2.wmf)，则..."）保留在文本中
        # 🆕 Prompt 3: 统一处理所有图片（独立和内联）
        # 检查整行是否包含图片标记
        img_result = image_match(line)  # 注意：使用完整行而非stripped
        if img_result:
            img_type, m_img = img_result
            # 检查是否为独立图片行：整行只有一个图片标记
            is_standalone = (m_img.group(0).strip() == stripped)

            # 🆕 生成图片 ID 和提取上下文
            img_counter = len(images) + 1
            generated_id = f"{slug}-Q{question_index}-img{img_counter}" if slug else f"Q{question_index}-img{img_counter}"

            # 提取上下文
            full_text = "\n".join(lines)
            img_start = full_text.find(m_img.group(0))
            img_end = img_start + len(m_img.group(0))
            context_before, context_after = extract_context_around_image(full_text, img_start, img_end)

            if is_standalone:
                # 独立图片块：提取到images列表
                if img_type == 'with_id':
                    # ![@@@id](path){...}
                    img_id = m_img.group(1)
                    path = m_img.group(2).strip()
                    images.append({
                        "path": path,
                        "width": 60,
                        "id": generated_id,
                        "inline": False,
                        "question_index": question_index,
                        "sub_index": 1,
                        "context_before": context_before,
                        "context_after": context_after
                    })
                elif img_type == 'no_id':
                    # ![](path){...}
                    path = m_img.group(1).strip()
                    images.append({
                        "path": path,
                        "width": 60,
                        "id": generated_id,
                        "inline": False,
                        "question_index": question_index,
                        "sub_index": 1,
                        "context_before": context_before,
                        "context_after": context_after
                    })
                else:
                    # 简单格式: ![](images/...)
                    path = m_img.group(1)
                    width = int(m_img.group(2)) if m_img.group(2) else 60
                    images.append({
                        "path": path,
                        "width": width,
                        "id": generated_id,
                        "inline": False,
                        "question_index": question_index,
                        "sub_index": 1,
                        "context_before": context_before,
                        "context_after": context_after
                    })
                i += 1
                continue
            else:
                # 内联图片：替换为占位符，记录到images列表
                if img_type == 'with_id':
                    img_id = m_img.group(1)
                    path = m_img.group(2).strip()
                    images.append({
                        "path": path,
                        "width": 60,
                        "id": generated_id,
                        "inline": True,
                        "question_index": question_index,
                        "sub_index": 1,
                        "context_before": context_before,
                        "context_after": context_after
                    })
                elif img_type == 'no_id':
                    path = m_img.group(1).strip()
                    images.append({
                        "path": path,
                        "width": 60,
                        "id": generated_id,
                        "inline": True,
                        "question_index": question_index,
                        "sub_index": 1,
                        "context_before": context_before,
                        "context_after": context_after
                    })
                else:
                    path = m_img.group(1)
                    width = int(m_img.group(2)) if m_img.group(2) else 60
                    images.append({
                        "path": path,
                        "width": width,
                        "id": generated_id,
                        "inline": True,
                        "question_index": question_index,
                        "sub_index": 1,
                        "context_before": context_before,
                        "context_after": context_after
                    })

                # 替换图片标记为占位符（使用新的 ID 格式）
                line = line.replace(m_img.group(0), f"<<IMAGE_INLINE:{generated_id}>>")
                # 继续处理该行（fallthrough）

        # 引述空行：丢弃
        if quote_blank.match(stripped):
            i += 1
            continue

        if state == "NORMAL":
            # 🆕 v1.9: 检测附件开始
            if attachment_start.match(stripped):
                # 进入附件状态
                state = "IN_ATTACHMENT"
                current_attachment_lines = [line]
                # 判断附件类型（初步）
                if "表" in stripped or markdown_table_line.match(stripped):
                    current_attachment_kind = "table"
                elif box_drawing_chars.search(stripped):
                    current_attachment_kind = "table"
                else:
                    current_attachment_kind = "text"
                i += 1
                continue

            # 新的 meta 开始？
            started = False
            for key, pat in meta_starts:
                m = pat.match(stripped)
                if m:
                    state = "IN_META"
                    current_meta_key = key
                    seed = m.group(m.lastindex or 1) if m.groups() else ""
                    current_meta_lines = [seed.strip()] if seed.strip() else []
                    started = True
                    break
            if started:
                i += 1
                continue

            # 普通内容
            content_lines.append(line)
            i += 1
            continue

        elif state == "IN_META":
            # state == IN_META
            # 1) 新 meta 开始 -> 刷新并切换
            started = False
            for key, pat in meta_starts:
                m = pat.match(stripped)
                if m:
                    flush_meta()
                    state = "IN_META"
                    current_meta_key = key
                    seed = m.group(m.lastindex or 1) if m.groups() else ""
                    current_meta_lines = [seed.strip()] if seed.strip() else []
                    started = True
                    break
            if started:
                i += 1
                continue

            # 2) 确认题号或章节边界 -> 结束 meta，保留该行给题干
            if is_question_start(stripped) or is_section_header(stripped):
                flush_meta()
                state = "NORMAL"
                content_lines.append(line)
                i += 1
                continue

            # 3) 空行 + lookahead 为题号 -> 安全地结束 meta
            if stripped == "":
                next_ne = find_next_nonempty(i)
                if next_ne and is_question_start(next_ne.strip()):
                    prev_ne = find_prev_nonempty(i)
                    # 若上一非空行看起来是环境续行，则不要在此空行切断
                    if prev_ne and env_cont_hint.search(prev_ne):
                        # 继续把空行也并入 meta（保持原样）
                        current_meta_lines.append(line)
                        i += 1
                        continue
                    # 否则切断 meta（不消费空行）
                    flush_meta()
                    state = "NORMAL"
                    i += 1  # 跳过该空行，下一轮看到题号行会进入 NORMAL 流程
                    continue

            # 4) 继续累积 meta 内容
            current_meta_lines.append(line)
            i += 1
            continue

        elif state == "IN_ATTACHMENT":
            # 附件状态处理
            # 1) 新 meta 开始 -> 刷新附件并切换到 meta
            started = False
            for key, pat in meta_starts:
                m = pat.match(stripped)
                if m:
                    flush_attachment()
                    state = "IN_META"
                    current_meta_key = key
                    seed = m.group(m.lastindex or 1) if m.groups() else ""
                    current_meta_lines = [seed.strip()] if seed.strip() else []
                    started = True
                    break
            if started:
                i += 1
                continue

            # 2) 确认题号或章节边界 -> 结束附件，保留该行给题干
            if is_question_start(stripped) or is_section_header(stripped):
                flush_attachment()
                state = "NORMAL"
                content_lines.append(line)
                i += 1
                continue

            # 3) 空行 - 可能结束附件
            if stripped == "":
                next_ne = find_next_nonempty(i)
                # 如果下一行是题号、meta标记或章节标题，则结束附件
                if next_ne and (is_question_start(next_ne.strip()) or
                               is_section_header(next_ne.strip()) or
                               any(pat.match(next_ne.strip()) for _, pat in meta_starts)):
                    flush_attachment()
                    state = "NORMAL"
                    i += 1
                    continue
                # 否则继续累积（可能是附件内的空行）
                current_attachment_lines.append(line)
                i += 1
                continue

            # 4) 继续累积附件内容
            # 动态更新附件类型
            if markdown_table_line.match(stripped):
                current_attachment_kind = "table"
            elif box_drawing_chars.search(stripped):
                current_attachment_kind = "table"

            current_attachment_lines.append(line)
            i += 1
            continue

    # 循环结束，若还在 meta 或 attachment 状态则刷新
    if state == "IN_META":
        flush_meta()
    elif state == "IN_ATTACHMENT":
        flush_attachment()

    content = "\n".join(content_lines).strip()
    return content, meta, images, attachments





# ============================================================
# 导出列表
# ============================================================

__all__ = [
    'META_PATTERNS',
    'ANALYSIS_MARKERS',
    'ANALYSIS_START_MARKERS',
    'extract_meta_and_images',
]
