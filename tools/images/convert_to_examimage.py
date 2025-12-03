#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
convert_to_examimage.py - 转换图片路径为 \examimage 宏

功能：
1. 将 \begin{center}\includegraphics[...]{path}\end{center} 转为 \examimage{full_path}{width}
2. 复制图片到试卷目录的 images/media/ 下
3. 使用从项目根目录开始的完整路径（如 content/exams/auto/.../images/media/xxx.png）

用法：
    python3 tools/images/convert_to_examimage.py <exam_tex> [--dry-run]

示例：
    # 预览
    python3 tools/images/convert_to_examimage.py \
        content/exams/auto/hubei_enshi_2026_q1/converted_exam.tex --dry-run
    
    # 执行转换
    python3 tools/images/convert_to_examimage.py \
        content/exams/auto/hubei_enshi_2026_q1/converted_exam.tex
"""

import re
import shutil
import argparse
from pathlib import Path


# 匹配 center 包裹的 includegraphics（支持多种格式）
# 格式1: \begin{center}\n\includegraphics...\n\end{center}
# 格式2: \begin{center}\n% IMAGE_TODO...\n\includegraphics...\n% IMAGE_TODO_END...\n\end{center}
# 格式3: \begin{center}\n% PNG: ...\n\includegraphics...\n\end{center}
CENTER_IMG_PATTERN = re.compile(
    r'\\begin\{center\}\s*\n?'
    r'(?:%[^\n]*\n)*'  # 可选的注释行（IMAGE_TODO, PNG 等）
    r'\\includegraphics\[width=([0-9.]+)\\textwidth\]\{([^}]+)\}\s*\n?'
    r'(?:%[^\n]*\n)*'  # 可选的注释行（IMAGE_TODO_END 等）
    r'\\end\{center\}',
    re.MULTILINE
)


def convert_exam_images(tex_path: str, dry_run: bool = False):
    r"""转换试卷中的图片路径为 \examimage 宏"""
    
    tex_file = Path(tex_path)
    if not tex_file.exists():
        print(f"❌ 文件不存在: {tex_path}")
        return 0
    
    exam_dir = tex_file.parent
    
    # 目标图片目录
    images_dir = exam_dir / "images" / "media"
    if not dry_run:
        images_dir.mkdir(parents=True, exist_ok=True)
    
    content = tex_file.read_text(encoding='utf-8')
    original_content = content
    
    print(f"📄 处理试卷: {tex_file}")
    print(f"📂 图片目录: {images_dir}")
    if dry_run:
        print("🔍 预览模式\n")
    else:
        print()
    
    matches = list(CENTER_IMG_PATTERN.finditer(content))
    
    if not matches:
        print("⚠️  未发现需要转换的图片块")
        return 0
    
    converted = 0
    copied = 0
    
    # 计算试卷目录相对于项目根目录的路径
    try:
        exam_rel_dir = exam_dir.relative_to(Path.cwd())
    except ValueError:
        exam_rel_dir = exam_dir
    
    # 反向替换（避免偏移问题）
    for match in reversed(matches):
        width = match.group(1)
        old_path = match.group(2)
        filename = Path(old_path).name
        
        # 新的完整路径（从项目根目录开始）
        new_full_path = f"{exam_rel_dir}/images/media/{filename}"
        full_new_path = exam_dir / "images" / "media" / filename
        
        # 源文件路径
        src_path = Path.cwd() / old_path
        
        print(f"  [{len(matches) - converted}] {filename}")
        print(f"      旧: {old_path}")
        print(f"      新: {new_full_path}")
        
        if not dry_run:
            # 复制图片
            if src_path.exists() and not full_new_path.exists():
                shutil.copy2(src_path, full_new_path)
                print(f"      ✓ 复制图片")
                copied += 1
            elif full_new_path.exists():
                print(f"      ✓ 图片已存在")
            else:
                print(f"      ⚠️  源图片未找到")
            
            # 替换文本
            new_text = f"\\examimage{{{new_full_path}}}{{{width}}}"
            content = content[:match.start()] + new_text + content[match.end():]
        
        converted += 1
    
    if not dry_run and converted > 0:
        # 备份
        bak_file = tex_file.with_suffix('.tex.bak')
        bak_file.write_text(original_content, encoding='utf-8')
        
        # 写入
        tex_file.write_text(content, encoding='utf-8')
        print(f"\n✅ 转换完成: {converted} 处图片")
        print(f"📋 备份: {bak_file}")
        if copied:
            print(f"📁 复制: {copied} 张图片")
    elif dry_run:
        print(f"\n📊 预览: 将转换 {converted} 处图片")
    
    return converted


def main():
    parser = argparse.ArgumentParser(
        description=r'转换图片路径为 \examimage 宏',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'files',
        nargs='+',
        help='要处理的试卷文件'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='预览模式，不修改文件'
    )
    
    args = parser.parse_args()
    
    print("━" * 50)
    print("🖼️  图片路径转换工具 → \\examimage")
    print("━" * 50)
    print()
    
    total = 0
    for tex_file in args.files:
        total += convert_exam_images(tex_file, dry_run=args.dry_run)
        print()
    
    print(f"{'预览' if args.dry_run else '处理'}完成，共 {total} 处")


if __name__ == '__main__':
    main()
