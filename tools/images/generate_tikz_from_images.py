#!/usr/bin/env python3
"""
生成 TikZ 图形代码辅助工具

由于 WMF 图片无法直接查看，此脚本提供以下功能：
1. 列出所有需要 TikZ 代码的图片占位符
2. 生成待填充的 TikZ 模板文件
3. 为常见几何图形提供 TikZ 代码示例

使用方法：
    python tools/generate_tikz_from_images.py <converted_exam.tex>
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple


def extract_image_todos(tex_file: Path) -> List[Tuple[int, str, str]]:
    """提取文件中所有的 IMAGE_TODO 占位符
    
    Args:
        tex_file: LaTeX 文件路径
        
    Returns:
        列表，每项为 (行号, 图片路径, width设置)
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


def generate_tikz_template(img_path: str, width: str) -> str:
    """生成 TikZ 代码模板
    
    Args:
        img_path: 图片路径
        width: 宽度设置
        
    Returns:
        TikZ 代码模板字符串
    """
    img_name = Path(img_path).stem
    
    # 根据常见模式提供不同的模板
    if 'graph' in img_name.lower() or 'plot' in img_name.lower():
        return f"""% {img_name}: 函数图像
\\begin{{tikzpicture}}[scale=1.0]
  % 坐标轴
  \\draw[->] (-3,0) -- (3,0) node[right] {{$x$}};
  \\draw[->] (0,-2) -- (0,2) node[above] {{$y$}};
  
  % TODO: 绘制函数曲线
  % \\draw[domain=-2:2, smooth, variable=\\x, blue] plot ({{\\x}}, {{\\x*\\x}});
  
  % TODO: 标注关键点
  % \\fill (1,1) circle (2pt) node[above right] {{$(1,1)$}};
\\end{{tikzpicture}}"""
    
    elif 'circle' in img_name.lower():
        return f"""% {img_name}: 圆形/圆相关图形
\\begin{{tikzpicture}}[scale=1.0]
  % 坐标轴
  \\draw[->] (-2,0) -- (2,0) node[right] {{$x$}};
  \\draw[->] (0,-2) -- (0,2) node[above] {{$y$}};
  
  % TODO: 绘制圆
  % \\draw (0,0) circle (1.5cm);
  
  % TODO: 标注圆心和半径
  % \\fill (0,0) circle (2pt) node[below left] {{$O$}};
\\end{{tikzpicture}}"""
    
    elif 'triangle' in img_name.lower():
        return f"""% {img_name}: 三角形
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
\\end{{tikzpicture}}"""
    
    else:
        return f"""% {img_name}: 通用图形
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
\\end{{tikzpicture}}"""


def main():
    if len(sys.argv) < 2:
        print("用法: python generate_tikz_from_images.py <converted_exam.tex>")
        sys.exit(1)
    
    tex_file = Path(sys.argv[1])
    
    if not tex_file.exists():
        print(f"错误: 文件不存在: {tex_file}")
        sys.exit(1)
    
    print(f"扫描文件: {tex_file}")
    print()
    
    todos = extract_image_todos(tex_file)
    
    if not todos:
        print("未找到需要处理的图片占位符")
        return
    
    print(f"找到 {len(todos)} 个图片占位符：")
    print()
    
    for line_num, img_path, width in todos:
        print(f"行 {line_num}: {Path(img_path).name} (width={width})")
    
    print()
    print("=" * 60)
    print("TikZ 代码模板示例：")
    print("=" * 60)
    print()
    
    # 显示前3个模板示例
    for i, (line_num, img_path, width) in enumerate(todos[:3], 1):
        print(f"\n{'=' * 60}")
        print(f"示例 {i} - 行 {line_num}: {Path(img_path).name}")
        print(f"{'=' * 60}\n")
        print(generate_tikz_template(img_path, width))
    
    if len(todos) > 3:
        print(f"\n... (还有 {len(todos) - 3} 个图片)")
    
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


if __name__ == '__main__':
    main()
