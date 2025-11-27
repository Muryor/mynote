#!/usr/bin/env python3
"""
图片转TikZ处理工具（支持新旧IMAGE_TODO格式）

功能：
1. 扫描所有 converted_exam.tex 文件中的 IMAGE_TODO 标记
2. 将WMF图片转换为PNG（使用LibreOffice或ImageMagick）
3. 生成TikZ代码模板
4. 替换占位符为实际TikZ代码或includegraphics

支持格式：
- 新格式（推荐）：% IMAGE_TODO_START id=xxx path=xxx width=60% ...
- 旧格式（兼容）：% IMAGE_TODO: /path/to/image.png (width=60%)

使用方法：
    # 预览模式：查看所有图片TODO和模板示例（不修改文件）
    python tools/images/process_images_to_tikz.py --mode preview --files content/exams/auto/*/converted_exam.tex
    
    # 模式1：转换WMF为PNG并使用\includegraphics
    python tools/images/process_images_to_tikz.py --mode include --files content/exams/auto/*/converted_exam.tex
    
    # 模式2：生成TikZ模板供手工填充
    python tools/images/process_images_to_tikz.py --mode template --files content/exams/auto/*/converted_exam.tex
    
    # 模式3：仅转换WMF为PNG
    python tools/images/process_images_to_tikz.py --mode convert --files content/exams/auto/*/converted_exam.tex

示例（新格式）：
    输入TeX:
        % IMAGE_TODO_START id=exam-Q1-img1 path=/path/to/image.png width=60% inline=false
        % CONTEXT_BEFORE: 题目内容
        % CONTEXT_AFTER: 选项内容
        \\begin{tikzpicture}[scale=0.8]
          % TODO: AI_AGENT_REPLACE_ME
        \\end{tikzpicture}
        % IMAGE_TODO_END id=exam-Q1-img1
    
    输出（include模式）：
        \\begin{center}
        \\includegraphics[width=0.6\\textwidth]{path/to/image.png}
        \\end{center}
"""

import re
import argparse
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict
import shutil


def find_image_todos(tex_file: Path) -> List[Tuple[int, str, str, str]]:
    """查找文件中的所有IMAGE_TODO标记（支持新旧格式）
    
    新格式（优先）：
        % IMAGE_TODO_START id=exam-Q1-img1 path=/path/to/image.png width=60% inline=true question_index=1
    
    旧格式（兼容）：
        % IMAGE_TODO: /path/to/image.png (width=60%)
    
    Returns:
        List of (line_number, id, image_path, width)
        - 新格式：(行号, id, path, width)
        - 旧格式：(行号, "legacy-N", path, width)
    """
    todos = []
    legacy_counter = 1
    
    with open(tex_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines, 1):
        # 优先匹配新格式
        new_match = re.search(
            r'% IMAGE_TODO_START\s+id=(\S+)\s+path=(\S+)\s+width=(\d+)%',
            line
        )
        if new_match:
            img_id = new_match.group(1)
            img_path = new_match.group(2).replace(r'\_', '_')
            width = new_match.group(3) + '%'
            todos.append((i, img_id, img_path, width))
            continue
        
        # 兼容旧格式
        old_match = re.search(r'% IMAGE_TODO: (.+?) \(width=([^)]+)\)', line)
        if old_match:
            img_path = old_match.group(1).replace(r'\_', '_')
            width = old_match.group(2)
            img_id = f"legacy-{legacy_counter}"
            legacy_counter += 1
            todos.append((i, img_id, img_path, width))
    
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


def generate_includegraphics(image_path: Path, width: str, project_root: Path = None) -> str:
    r"""生成\includegraphics代码

    🆕 Prompt 5: 移除硬编码路径，使用相对路径

    Args:
        image_path: 图片路径
        width: 宽度设置
        project_root: 项目根目录（如果未提供，使用当前工作目录）

    Returns:
        LaTeX includegraphics 代码
    """
    if project_root is None:
        project_root = Path.cwd()

    # 尝试计算相对路径
    try:
        rel_path = image_path.relative_to(project_root)
    except ValueError:
        # 如果路径不在项目根目录下，使用绝对路径
        rel_path = image_path

    # 使用 POSIX 风格路径（LaTeX 兼容）
    rel_path_str = rel_path.as_posix()

    return f"""\\begin{{center}}
\\includegraphics[width={width}\\textwidth]{{{rel_path_str}}}
\\end{{center}}"""


def generate_tikz_template(image_name: str, width: str) -> str:
    """生成TikZ模板（智能版）

    🆕 Prompt 4: 合并 generate_tikz_from_images.py 的智能模板生成逻辑
    """
    img_name_lower = image_name.lower()

    # 根据常见模式提供不同的模板
    if 'graph' in img_name_lower or 'plot' in img_name_lower:
        return f"""\\begin{{center}}
% {image_name}: 函数图像
\\begin{{tikzpicture}}[scale=1.0]
  % 坐标轴
  \\draw[->] (-3,0) -- (3,0) node[right] {{$x$}};
  \\draw[->] (0,-2) -- (0,2) node[above] {{$y$}};

  % TODO: 绘制函数曲线
  % \\draw[domain=-2:2, smooth, variable=\\x, blue] plot ({{\\x}}, {{\\x*\\x}});

  % TODO: 标注关键点
  % \\fill (1,1) circle (2pt) node[above right] {{$(1,1)$}};
\\end{{tikzpicture}}
\\end{{center}}"""

    elif 'circle' in img_name_lower:
        return f"""\\begin{{center}}
% {image_name}: 圆形/圆相关图形
\\begin{{tikzpicture}}[scale=1.0]
  % 坐标轴
  \\draw[->] (-2,0) -- (2,0) node[right] {{$x$}};
  \\draw[->] (0,-2) -- (0,2) node[above] {{$y$}};

  % TODO: 绘制圆
  % \\draw (0,0) circle (1.5cm);

  % TODO: 标注圆心和半径
  % \\fill (0,0) circle (2pt) node[below left] {{$O$}};
\\end{{tikzpicture}}
\\end{{center}}"""

    elif 'triangle' in img_name_lower:
        return f"""\\begin{{center}}
% {image_name}: 三角形
\\begin{{tikzpicture}}[scale=1.0]
  % TODO: 定义顶点
  \\coordinate (A) at (0,0);
  \\coordinate (B) at (4,0);
  \\coordinate (C) at (2,3);

  % TODO: 绘制三角形
  \\draw (A) -- (B) -- (C) -- cycle;

  % TODO: 标注顶点
  \\node[below left] at (A) {{$A$}};
  \\node[below right] at (B) {{$B$}};
  \\node[above] at (C) {{$C$}};
\\end{{tikzpicture}}
\\end{{center}}"""

    else:
        return f"""\\begin{{center}}
% {image_name}: 通用图形
\\begin{{tikzpicture}}[scale=1.0]
  % TODO: 根据实际图片内容绘制
  % 示例：坐标轴
  % \\draw[->] (-2,0) -- (2,0) node[right] {{$x$}};
  % \\draw[->] (0,-2) -- (0,2) node[above] {{$y$}};

  % 示例：点
  % \\fill (1,1) circle (2pt) node[above] {{$P$}};

  % 示例：线段
  % \\draw[thick] (0,0) -- (2,1);

  % 示例：曲线
  % \\draw[domain=0:2, smooth, variable=\\x] plot ({{\\x}}, {{sin(\\x r)}});
\\end{{tikzpicture}}
\\end{{center}}"""


def print_tikz_snippets():
    """🆕 Prompt 4: 打印常用 TikZ 代码片段（来自 generate_tikz_from_images.py）"""
    print()
    print("=" * 60)
    print("常用 TikZ 代码片段：")
    print("=" * 60)
    print("""
1. 坐标轴：
   \\draw[->] (-3,0) -- (3,0) node[right] {$x$};
   \\draw[->] (0,-2) -- (0,2) node[above] {$y$};

2. 网格：
   \\draw[help lines] (-2,-2) grid (2,2);

3. 函数曲线：
   \\draw[domain=-2:2, smooth, variable=\\x, blue, thick]
         plot ({\\x}, {\\x*\\x - 1});

4. 圆：
   \\draw (0,0) circle (1.5cm);
   \\draw[fill=blue!20] (0,0) circle (1cm);

5. 点：
   \\fill (1,1) circle (2pt) node[above right] {$P(1,1)$};

6. 箭头向量：
   \\draw[->, thick] (0,0) -- (2,1) node[midway, above] {$\\vec{v}$};

7. 角度标记：
   \\draw (1,0) arc (0:45:1cm) node[midway, right] {$\\theta$};

8. 阴影区域：
   \\fill[blue!20, opacity=0.5] (0,0) -- (2,0) -- (2,2) -- cycle;
""")


def process_tex_file(tex_file: Path, mode: str, output_dir: Path, project_root: Path = None):
    """处理单个TeX文件（支持新旧格式）

    🆕 支持 IMAGE_TODO_START/END 新格式
    🆕 Prompt 4: 支持 preview 模式
    🆕 Prompt 5: 支持自定义项目根目录
    """
    if project_root is None:
        project_root = Path.cwd()
    print(f"\n{'='*60}")
    print(f"处理文件: {tex_file}")
    print(f"{'='*60}")

    todos = find_image_todos(tex_file)
    if not todos:
        print("  未找到IMAGE_TODO标记")
        return

    print(f"  找到 {len(todos)} 个图片占位符")

    # preview 模式 - 列出所有图片并显示模板示例
    if mode == 'preview':
        print()
        for line_num, img_id, img_path, width in todos:
            print(f"  行 {line_num}: ID={img_id}, {Path(img_path).name} (width={width})")

        print()
        print("=" * 60)
        print("TikZ 代码模板示例：")
        print("=" * 60)

        # 显示前3个模板示例
        for i, (line_num, img_id, img_path, width) in enumerate(todos[:3], 1):
            print(f"\n{'=' * 60}")
            print(f"示例 {i} - 行 {line_num}: {Path(img_path).name}")
            print(f"{'=' * 60}\n")
            print(generate_tikz_template(Path(img_path).name, width.rstrip('%')))

        if len(todos) > 3:
            print(f"\n... (还有 {len(todos) - 3} 个图片)")

        print_tikz_snippets()
        return
    
    # 读取文件内容
    with open(tex_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    replacements = []
    converted_images = []
    
    for line_num, img_id, img_path, width in todos:
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
                new_code = generate_includegraphics(png_path, width.rstrip('%'), project_root)
            else:
                new_code = generate_includegraphics(img_path_obj, width.rstrip('%'), project_root)
            
            # 匹配新格式（优先）
            if img_id.startswith('legacy-'):
                # 旧格式兼容
                pattern = rf'\\begin{{center}}\n% IMAGE_TODO: {re.escape(img_path)}.*?\n\\begin{{tikzpicture}}.*?\\end{{tikzpicture}}\n\\end{{center}}'
            else:
                # 新格式：匹配完整的 IMAGE_TODO_START ... IMAGE_TODO_END 块
                escaped_id = re.escape(img_id)
                pattern = (
                    rf'% IMAGE_TODO_START\s+id={escaped_id}\s+.*?\n'
                    rf'(?:% CONTEXT_BEFORE:.*?\n)?'
                    rf'(?:% CONTEXT_AFTER:.*?\n)?'
                    rf'\\begin{{tikzpicture}}.*?\\end{{tikzpicture}}\s*\n'
                    rf'% IMAGE_TODO_END\s+id={escaped_id}'
                )
            
            if re.search(pattern, content, re.DOTALL):
                replacements.append((pattern, new_code, img_id))
        
        elif mode == 'template':
            # 生成TikZ模板
            new_code = generate_tikz_template(img_path_obj.name, width.rstrip('%'))
            
            # 匹配新格式（优先）
            if img_id.startswith('legacy-'):
                pattern = rf'\\begin{{center}}\n% IMAGE_TODO: {re.escape(img_path)}.*?\n\\begin{{tikzpicture}}.*?\\end{{tikzpicture}}\n\\end{{center}}'
            else:
                escaped_id = re.escape(img_id)
                pattern = (
                    rf'% IMAGE_TODO_START\s+id={escaped_id}\s+.*?\n'
                    rf'(?:% CONTEXT_BEFORE:.*?\n)?'
                    rf'(?:% CONTEXT_AFTER:.*?\n)?'
                    rf'\\begin{{tikzpicture}}.*?\\end{{tikzpicture}}\s*\n'
                    rf'% IMAGE_TODO_END\s+id={escaped_id}'
                )
            
            if re.search(pattern, content, re.DOTALL):
                replacements.append((pattern, new_code, img_id))
    
    # 应用替换
    if replacements and mode != 'convert':
        for pattern, replacement, img_id in replacements:
            # 使用 lambda 函数避免反斜杠转义问题（Python 3.14+）
            content = re.sub(pattern, lambda m: replacement, content, flags=re.DOTALL, count=1)
        
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
    parser = argparse.ArgumentParser(
        description='处理图片并转换为TikZ',
        epilog="""
🆕 Prompt 4: 合并了 generate_tikz_from_images.py 的功能

模式说明：
  convert  - 仅转换WMF为PNG，不修改TeX文件
  include  - 转换WMF并替换为\\includegraphics（默认）
  template - 生成智能TikZ模板供手工填充
  preview  - 列出所有图片占位符并显示模板示例（不修改文件）

使用示例：
  # 预览模式：查看所有图片TODO和模板示例
  python tools/images/process_images_to_tikz.py --mode preview

  # 转换模式：使用includegraphics
  python tools/images/process_images_to_tikz.py --mode include

  # 模板模式：生成TikZ模板
  python tools/images/process_images_to_tikz.py --mode template
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--mode', choices=['convert', 'include', 'template', 'preview'],
                       default='include',
                       help='处理模式（详见下方说明）')
    parser.add_argument('--output-dir', type=Path,
                       default=Path('word_to_tex/output/figures/png'),
                       help='PNG输出目录')
    parser.add_argument('--files', nargs='*', type=Path,
                       help='指定要处理的TeX文件（默认处理所有auto目录）')
    parser.add_argument('--project-root', type=Path,
                       default=None,
                       help='项目根目录（用于计算相对路径，默认为当前工作目录）')

    args = parser.parse_args()

    # 🆕 Prompt 5: 设置项目根目录
    if args.project_root is None:
        args.project_root = Path.cwd()
    else:
        args.project_root = args.project_root.resolve()

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
            process_tex_file(tex_file, args.mode, args.output_dir, args.project_root)

    print("\n" + "━"*60)
    print("✅ 处理完成")
    print(f"PNG输出目录: {args.output_dir}")
    print(f"项目根目录: {args.project_root}")


if __name__ == '__main__':
    main()
