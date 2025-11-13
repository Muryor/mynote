#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 OCR 生成的 *_local.md 转换为 examx.sty 风格的粗 LaTeX 试卷。

功能：
- 清理 markdown 中的页码、span 标签等杂质
- 按 # 一、单选题 / # 二、多选题 / # 三、填空题 / # 四、解答题 切分 section
- 按 1. / 1． / 1、 拆分为每道题
- 抽取元信息：
  - 【答案】 -> \answer{}
  - 【难度】 -> \difficulty{}
  - 【知识点】 -> \topics{}
  - 【详解】 -> \explain{}
  - 【分析】 -> 丢弃
- 识别 A. / B. / C. / D. 选项，生成 choices 环境
- 识别图片 ![](images/xxx.jpg){width=39%}，生成带 IMAGE_TODO 注释的 tikzpicture 占位
- 将部分行内 $...$ 简单替换为 \(...\)
- 输出 examx 结构的 .tex 文件，后续可交给 LLM 精修
"""

import re
import argparse
from pathlib import Path

# 章节标题映射，可按实际需要调整
SECTION_MAP = {
    "一、单选题": "单选题",
    "二、单选题": "单选题",
    "二、多选题": "多选题",
    "三、填空题": "填空题",
    "四、解答题": "解答题",
}

# 元信息字段
META_PATTERNS = {
    "answer": r"^【答案】(.*)$",
    "difficulty": r"^【难度】([\d.]+)",
    "topics": r"^【知识点】(.*)$",
    "analysis": r"^【分析】(.*)$",  # 丢弃用
    "explain": r"^【详解】(.*)$",
}

# markdown 图片
IMAGE_PATTERN = re.compile(
    r"!\[\]\((images/[^)]+)\)\{width=(\d+)%\}"
)


def clean_markdown(text: str) -> str:
    """删除页码 span、过多空行等垃圾内容。"""
    # 删除特定的分页行
    text = re.sub(
        r"<br><span class='markdown-page-line'>.*?</span><br><br>",
        "\n",
        text,
        flags=re.S,
    )
    # 删除 [ 第x页 ] 标签
    text = re.sub(
        r"<span id='page\d+' class='markdown-page-text'>\[.*?\]</span>",
        "",
        text,
    )

    # 统一换行符
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 压缩多行空行
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def split_sections(text: str):
    """
    按 # 一、单选题 等拆分板块。
    返回 list[(raw_title, body_text)]。
    """
    lines = text.splitlines()
    sections = []
    current_title = None
    current_lines = []

    for line in lines:
        stripped = line.strip()
        m = re.match(
            r"^#+\s*(一、单选题|二、单选题|二、多选题|三、填空题|四、解答题)",
            stripped,
        )
        if m:
            # flush 之前的 section
            if current_title is not None:
                sections.append((current_title, "\n".join(current_lines).strip()))
                current_lines = []
            current_title = m.group(1)
        else:
            if current_title is not None:
                current_lines.append(line)

    if current_title is not None and current_lines:
        sections.append((current_title, "\n".join(current_lines).strip()))

    return sections


def split_questions(section_body: str):
    """
    根据题号拆题：1.  1．  1、 等。
    返回 list[str]，每个元素是一个题目的原始文本块。
    """
    lines = section_body.splitlines()
    blocks = []
    current = []

    def flush():
        if current:
            blocks.append("\n".join(current).strip())
            current.clear()

    for line in lines:
        stripped = line.strip()
        # 题号开头
        if re.match(r"^\d+[\.．、]\s*", stripped):
            flush()
            current.append(line)
        else:
            current.append(line)

    flush()
    return blocks


def extract_meta_and_images(block: str):
    """
    从题目块中提取元信息（answer/difficulty/topics/explain）和图片列表。
    返回：(content_without_meta_and_images, meta_dict, images_list)
    images_list: [{"path": ..., "width": ...}, ...]
    """
    meta = {k: "" for k in META_PATTERNS}
    content_lines = []
    images = []

    for line in block.splitlines():
        stripped = line.strip()

        # 先匹配图片
        m_img = IMAGE_PATTERN.search(stripped)
        if m_img:
            images.append(
                {
                    "path": m_img.group(1),
                    "width": int(m_img.group(2)),
                }
            )
            # 不把图片行写入内容
            continue

        # 再匹配元信息
        matched_meta = False
        for key, pat in META_PATTERNS.items():
            m = re.match(pat, stripped)
            if m:
                # 【分析】我们不使用，但先解析出来方便以后扩展
                if key != "analysis":
                    meta[key] = m.group(1).strip()
                matched_meta = True
                break

        if not matched_meta:
            content_lines.append(line)

    content = "\n".join(content_lines).strip()
    return content, meta, images


def normalize_choices_in_content(content: str) -> str:
    """
    把内容里 A. / A． 等选项前缀尽量拆到独立行。
    避免出现：题干和选项混在一行的情况。
    """
    # 常见形式：  A.  B.  C.  D.
    for ch in ["A", "B", "C", "D"]:
        # A. 或 A．
        content = re.sub(rf"\s+{ch}[\.．]\s*", f"\n{ch}. ", content)
    return content


def convert_choices(content: str):
    """
    将题目内容拆分为 (题干, 选项列表)。
    选项格式：A. ... / B. ... / C. ... / D. ...
    """
    content = normalize_choices_in_content(content)
    lines = content.splitlines()

    stem_lines = []
    option_lines = {"A": "", "B": "", "C": "", "D": ""}

    current_key = None
    for line in lines:
        stripped = line.strip()
        m = re.match(r"^(A|B|C|D)[\.．]\s*(.*)$", stripped)
        if m:
            current_key = m.group(1)
            option_lines[current_key] = m.group(2).strip()
        else:
            if current_key is not None:
                # 当前在某个选项内，追加行
                option_lines[current_key] += " " + stripped
            else:
                stem_lines.append(line)

    stem = "\n".join(stem_lines).strip()
    # 去掉题干起始的题号 "1．" 等
    stem = re.sub(r"^\s*\d+[\.．、]\s*", "", stem)

    options = []
    for key in ["A", "B", "C", "D"]:
        if option_lines[key]:
            options.append(option_lines[key])

    return stem, options


def inline_math_to_parens(text: str) -> str:
    """
    将简单的 $...$ 行内公式替换为 \(...\)。
    不处理 $$...$$ 等复杂情况。
    """
    if not text:
        return text
    # 避免 $$...$$ 的冲突：先保护一下
    text = text.replace("$$", "@@MATHDISPLAY@@")
    text = re.sub(r"\$(.+?)\$", r"\\(\1\\)", text)
    text = text.replace("@@MATHDISPLAY@@", "$$")
    return text


def build_question_tex(
    stem: str,
    options,
    meta,
    images,
) -> str:
    """
    根据题干、选项、元信息、图片，生成 examx 的 question 环境。
    """
    stem = inline_math_to_parens(stem)
    explain = inline_math_to_parens(meta.get("explain", ""))

    topics = meta.get("topics", "").strip()
    if topics:
        # 用分号分隔知识点
        topics = topics.replace("、", "；")

    lines = []
    lines.append(r"\begin{question}")
    if stem:
        lines.append(stem)

    # 选择题
    if options:
        lines.append(r"\begin{choices}")
        for opt in options:
            lines.append(f"  \\item {inline_math_to_parens(opt)}")
        lines.append(r"\end{choices}")

    # 图片占位 -> TikZ TODO
    for img in images:
        lines.append(r"\begin{center}")
        lines.append(
            f"% IMAGE_TODO: {img['path']} (width={img['width']}%)"
        )
        lines.append(
            r"\begin{tikzpicture}[scale=1.05,>=Stealth,line cap=round,line join=round]"
        )
        lines.append(
            r"  % TODO: draw this figure in TikZ according to the original image."
        )
        lines.append(r"\end{tikzpicture}")
        lines.append(r"\end{center}")

    if topics:
        lines.append(f"\\topics{{{topics}}}")
    if meta.get("difficulty"):
        lines.append(f"\\difficulty{{{meta['difficulty']}}}")
    if meta.get("answer"):
        lines.append(f"\\answer{{{meta['answer']}}}")
    if explain:
        lines.append(f"\\explain{{{explain}}}")

    lines.append(r"\end{question}")
    return "\n".join(lines)


def guess_exam_title(md_path: Path) -> str:
    """
    如果没有显式给 title，用文件名（去掉后缀）当 title。
    """
    return md_path.stem


def convert_md_to_examx(md_text: str, title: str) -> str:
    """
    从 markdown 文本生成 examx 粗 LaTeX 内容。
    """
    md_text = clean_markdown(md_text)
    sections = split_sections(md_text)

    out_lines = []
    out_lines.append(f"\\examxtitle{{{title}}}")

    for raw_title, body in sections:
        sec_label = SECTION_MAP.get(raw_title, raw_title)
        out_lines.append("")
        out_lines.append(f"\\section{{{sec_label}}}")

        for block in split_questions(body):
            if not block.strip():
                continue
            content, meta, images = extract_meta_and_images(block)
            stem, options = convert_choices(content)
            q_tex = build_question_tex(stem, options, meta, images)
            out_lines.append("")
            out_lines.append(q_tex)

    out_lines.append("")  # 文件末尾空行
    return "\n".join(out_lines)


def main():
    parser = argparse.ArgumentParser(
        description="Convert OCR *_local.md to examx-style rough LaTeX."
    )
    parser.add_argument("input_md", help="Path to *_local.md file.")
    parser.add_argument("output_tex", help="Path to output .tex file.")
    parser.add_argument(
        "--title",
        help="Exam title for \\examxtitle{}. If omitted, use input filename.",
        default=None,
    )

    args = parser.parse_args()
    md_path = Path(args.input_md)
    tex_path = Path(args.output_tex)

    if not md_path.is_file():
        raise FileNotFoundError(f"Input markdown not found: {md_path}")

    md_text = md_path.read_text(encoding="utf-8")
    title = args.title or guess_exam_title(md_path)
    tex_text = convert_md_to_examx(md_text, title)

    tex_path.parent.mkdir(parents=True, exist_ok=True)
    tex_path.write_text(tex_text, encoding="utf-8")
    print(f"[OK] Written: {tex_path}")


if __name__ == "__main__":
    main()
