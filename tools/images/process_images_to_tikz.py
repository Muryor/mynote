#!/usr/bin/env python3
"""
图片转TikZ处理工具

功能：
1. 扫描所有 converted_exam.tex 文件中的 IMAGE_TODO 标记
2. 将WMF图片转换为PNG（使用LibreOffice或ImageMagick）
3. 生成TikZ代码模板
4. 替换占位符为实际TikZ代码或includegraphics

使用方法：
    # 模式1：转换WMF为PNG并使用\includegraphics
    python tools/process_images_to_tikz.py --mode include
    
    # 模式2：生成TikZ模板供手工填充
    python tools/process_images_to_tikz.py --mode template
    
    # 模式3：仅转换WMF为PNG
    python tools/process_images_to_tikz.py --mode convert
"""

import re
import argparse
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict
import shutil


def find_image_todos(tex_file: Path) -> List[Tuple[int, str, str]]:
    """查找文件中的所有IMAGE_TODO标记
    
    Returns:
        List of (line_number, image_path, width)
    """
    todos = []
    with open(tex_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines, 1):
        match = re.search(r'% IMAGE_TODO: (.+?) \(width=([^)]+)\)', line)
        if match:
            img_path = match.group(1).replace(r'\_', '_')
            width = match.group(2)
            todos.append((i, img_path, width))
    
    return todos


def convert_wmf_to_png(wmf_path: Path, output_dir: Path) -> Path:
    """转换WMF为PNG
    
    尝试使用多种工具：
    1. LibreOffice (soffice)
    2. ImageMagick (convert)
    3. 如果都失败，返回原文件路径
    """
    if not wmf_path.exists():
        print(f"⚠️  文件不存在: {wmf_path}")
        return wmf_path
    
    png_name = wmf_path.stem + '.png'
    png_path = output_dir / png_name
    
    if png_path.exists():
        print(f"✓ 已存在: {png_name}")
        return png_path
    
    # 尝试方法1: LibreOffice
    if shutil.which('soffice'):
        try:
            subprocess.run([
                'soffice', '--headless', '--convert-to', 'png',
                '--outdir', str(output_dir),
                str(wmf_path)
            ], check=True, capture_output=True, timeout=10)
            if png_path.exists():
                print(f"✓ LibreOffice转换: {png_name}")
                return png_path
        except Exception as e:
            print(f"  LibreOffice失败: {e}")
    
    # 尝试方法2: ImageMagick
    if shutil.which('convert'):
        try:
            subprocess.run([
                'convert', str(wmf_path), str(png_path)
            ], check=True, capture_output=True, timeout=10)
            if png_path.exists():
                print(f"✓ ImageMagick转换: {png_name}")
                return png_path
        except Exception as e:
            print(f"  ImageMagick失败: {e}")
    
    # 都失败了，返回原路径
    print(f"✗ 无法转换: {wmf_path.name}")
    return wmf_path


def generate_includegraphics(image_path: Path, width: str) -> str:
    r"""生成\includegraphics代码"""
    # 使用相对路径
    rel_path = str(image_path).replace('/Users/muryor/code/mynote/', '')
    return f"""\\begin{{center}}
\\includegraphics[width={width}\\textwidth]{{{rel_path}}}
\\end{{center}}"""


def generate_tikz_template(image_name: str, width: str) -> str:
    """生成TikZ模板"""
    return f"""\\begin{{center}}
% 图片: {image_name}
\\begin{{tikzpicture}}[scale=1.0]
  % TODO: 根据图片内容绘制
  % 示例：坐标轴
  \\draw[->] (-3,0) -- (3,0) node[right] {{$x$}};
  \\draw[->] (0,-2) -- (0,2) node[above] {{$y$}};
  
  % TODO: 添加具体图形元素
\\end{{tikzpicture}}
\\end{{center}}"""


def process_tex_file(tex_file: Path, mode: str, output_dir: Path):
    """处理单个TeX文件"""
    print(f"\n{'='*60}")
    print(f"处理文件: {tex_file}")
    print(f"{'='*60}")
    
    todos = find_image_todos(tex_file)
    if not todos:
        print("  未找到IMAGE_TODO标记")
        return
    
    print(f"  找到 {len(todos)} 个图片占位符")
    
    # 读取文件内容
    with open(tex_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    replacements = []
    converted_images = []
    
    for line_num, img_path, width in todos:
        img_path_obj = Path(img_path)
        
        if mode == 'convert':
            # 仅转换，不修改TeX文件
            if img_path_obj.suffix.lower() == '.wmf':
                png_path = convert_wmf_to_png(img_path_obj, output_dir)
                converted_images.append((img_path_obj.name, png_path.name))
        
        elif mode == 'include':
            # 转换WMF并替换为\includegraphics
            if img_path_obj.suffix.lower() == '.wmf':
                png_path = convert_wmf_to_png(img_path_obj, output_dir)
                new_code = generate_includegraphics(png_path, width.rstrip('%'))
            else:
                new_code = generate_includegraphics(img_path_obj, width.rstrip('%'))
            
            # 查找并替换整个TikZ块
            pattern = rf'\\begin{{center}}\n% IMAGE_TODO: {re.escape(img_path)}.*?\n\\begin{{tikzpicture}}.*?\\end{{tikzpicture}}\n\\end{{center}}'
            if re.search(pattern, content, re.DOTALL):
                replacements.append((pattern, new_code))
        
        elif mode == 'template':
            # 生成TikZ模板
            new_code = generate_tikz_template(img_path_obj.name, width.rstrip('%'))
            pattern = rf'\\begin{{center}}\n% IMAGE_TODO: {re.escape(img_path)}.*?\n\\begin{{tikzpicture}}.*?\\end{{tikzpicture}}\n\\end{{center}}'
            if re.search(pattern, content, re.DOTALL):
                replacements.append((pattern, new_code))
    
    # 应用替换
    if replacements and mode != 'convert':
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content, flags=re.DOTALL, count=1)
        
        # 备份原文件
        backup_path = tex_file.with_suffix('.tex.bak')
        shutil.copy2(tex_file, backup_path)
        print(f"  ✓ 备份: {backup_path.name}")
        
        # 写入新内容
        with open(tex_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ 替换了 {len(replacements)} 个图片块")
    
    if converted_images:
        print(f"  ✓ 转换了 {len(converted_images)} 个WMF图片")


def main():
    parser = argparse.ArgumentParser(description='处理图片并转换为TikZ')
    parser.add_argument('--mode', choices=['convert', 'include', 'template'],
                       default='include',
                       help='处理模式：convert=仅转换WMF, include=使用includegraphics, template=生成TikZ模板')
    parser.add_argument('--output-dir', type=Path,
                       default=Path('word_to_tex/output/figures/png'),
                       help='PNG输出目录')
    parser.add_argument('--files', nargs='*', type=Path,
                       help='指定要处理的TeX文件（默认处理所有auto目录）')
    
    args = parser.parse_args()
    
    # 确保输出目录存在
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"📸 图片转TikZ处理工具 - 模式: {args.mode}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # 查找要处理的文件
    if args.files:
        tex_files = args.files
    else:
        tex_files = list(Path('content/exams/auto').rglob('converted_exam.tex'))
    
    print(f"找到 {len(tex_files)} 个TeX文件")
    
    for tex_file in tex_files:
        if tex_file.exists():
            process_tex_file(tex_file, args.mode, args.output_dir)
    
    print("\n" + "━"*60)
    print("✅ 处理完成")
    print(f"PNG输出目录: {args.output_dir}")


if __name__ == '__main__':
    main()
