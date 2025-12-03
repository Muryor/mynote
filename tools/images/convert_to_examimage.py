#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
convert_to_examimage.py - 转换图片为相对路径 + \setexamdir

功能：
1. 在试卷开头插入 \setexamdir{试卷目录}
2. 将 \includegraphics 转换为 \examimage{相对路径}{宽度}
3. 图片使用相对于试卷目录的路径（如 images/media/image1.png）

优势：
- 移动整个试卷目录后仍能正常编译
- 组卷时只需更新 \setexamdir 即可

用法：
    python3 tools/images/convert_to_examimage.py [--dry-run] <tex_file>...

示例：
    # 预览
    python3 tools/images/convert_to_examimage.py --dry-run \
        content/exams/auto/hubei_enshi_2026_q1/converted_exam.tex

    # 执行转换
    python3 tools/images/convert_to_examimage.py \
        content/exams/auto/*/converted_exam.tex
"""

import re
import sys
import shutil
from pathlib import Path


def get_project_root() -> Path:
    """获取项目根目录（包含 build.sh 的目录）"""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "build.sh").exists():
            return current
        current = current.parent
    return Path.cwd()


# 匹配 center 包裹的 includegraphics（支持多种格式）
CENTER_IMG_PATTERN = re.compile(
    r'\\begin\{center\}\s*\n?'
    r'(?:%[^\n]*\n)*'  # 可选的注释行（IMAGE_TODO, PNG 等）
    r'\\includegraphics\[width=([0-9.]+)\\textwidth\]\{([^}]+)\}\s*\n?'
    r'(?:%[^\n]*\n)*'  # 可选的注释行（IMAGE_TODO_END 等）
    r'\\end\{center\}',
    re.MULTILINE
)


def extract_relative_path(img_path: str) -> str:
    """从完整路径提取相对路径（images/media/xxx.png）"""
    if "images/media/" in img_path:
        idx = img_path.find("images/media/")
        return img_path[idx:]
    elif "images/" in img_path:
        idx = img_path.find("images/")
        return img_path[idx:]
    else:
        # 只保留文件名，放到 images/media/ 下
        filename = Path(img_path).name
        return f"images/media/{filename}"


def convert_exam_images(tex_path: str, dry_run: bool = False) -> int:
    r"""转换试卷中的图片路径为相对路径 + \setexamdir"""

    tex_file = Path(tex_path).resolve()
    if not tex_file.exists():
        print(f"❌ 文件不存在: {tex_path}")
        return 0

    content = tex_file.read_text(encoding='utf-8')
    original_content = content
    exam_dir = tex_file.parent
    root = get_project_root()

    # 计算试卷目录相对于项目根的路径
    try:
        exam_dir_relative = str(exam_dir.relative_to(root))
    except ValueError:
        exam_dir_relative = str(exam_dir)

    print(f"📄 处理: {tex_file.name}")
    print(f"   目录: {exam_dir_relative}")
    if dry_run:
        print("   🔍 预览模式\n")

    matches = list(CENTER_IMG_PATTERN.finditer(content))

    if not matches and '\\setexamdir' in content:
        print("   ✓ 已转换，跳过\n")
        return 0

    converted = 0

    # 反向替换（避免偏移问题）
    for match in reversed(matches):
        width = match.group(1)
        old_path = match.group(2)
        rel_path = extract_relative_path(old_path)

        print(f"   [{len(matches) - converted}] {Path(old_path).name}")
        print(f"       旧: {old_path}")
        print(f"       新: {rel_path}")

        if not dry_run:
            new_text = f"\\examimage{{{rel_path}}}{{{width}}}"
            content = content[:match.start()] + new_text + content[match.end():]

        converted += 1

    # 插入 \setexamdir（如果没有）
    need_setexamdir = '\\setexamdir' not in original_content and converted > 0

    if need_setexamdir:
        setexamdir_line = f"\\setexamdir{{{exam_dir_relative}}}\n\n"

        if not dry_run:
            # 在 \examxtitle 之前插入
            if '\\examxtitle' in content:
                content = content.replace('\\examxtitle', setexamdir_line + '\\examxtitle')
            else:
                # 在文件开头插入
                content = setexamdir_line + content

        print(f"   + 插入: \\setexamdir{{{exam_dir_relative}}}")

    if not dry_run and (converted > 0 or need_setexamdir):
        # 备份
        bak_file = tex_file.with_suffix('.tex.bak')
        bak_file.write_text(original_content, encoding='utf-8')

        # 写入
        tex_file.write_text(content, encoding='utf-8')
        print(f"\n   ✅ 转换完成: {converted} 处")
        print(f"   📋 备份: {bak_file.name}")
    elif dry_run and converted > 0:
        print(f"\n   📊 预览: 将转换 {converted} 处")

    print()
    return converted


def main():
    args = sys.argv[1:]
    dry_run = '--dry-run' in args
    files = [a for a in args if a != '--dry-run']

    if not files:
        print(__doc__)
        sys.exit(1)

    print("━" * 50)
    print("🖼️  图片路径转换工具（相对路径版）")
    print("━" * 50)
    print()

    total = 0
    for tex_file in files:
        total += convert_exam_images(tex_file, dry_run)

    print(f"{'预览' if dry_run else '处理'}完成，共 {total} 处转换")


if __name__ == '__main__':
    main()
