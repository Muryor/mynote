#!/usr/bin/env python3
"""
生成 TikZ 图形代码辅助工具（向后兼容入口）

🆕 Prompt 4: 此功能已合并到 process_images_to_tikz.py

该脚本现在作为向后兼容的入口点，将调用重定向到主脚本。

旧用法：
    python tools/generate_tikz_from_images.py <converted_exam.tex>

新用法（推荐）：
    python tools/images/process_images_to_tikz.py --mode preview --files <converted_exam.tex>

或者简化为：
    python tools/images/process_images_to_tikz.py --mode preview
"""

import sys
import subprocess
from pathlib import Path


def main():
    print("=" * 60)
    print("⚠️  注意：此脚本的功能已合并到 process_images_to_tikz.py")
    print("=" * 60)
    print()

    if len(sys.argv) < 2:
        print("用法: python generate_tikz_from_images.py <converted_exam.tex>")
        print()
        print("推荐使用新的统一脚本：")
        print("  python tools/images/process_images_to_tikz.py --mode preview")
        print()
        sys.exit(1)

    tex_file = Path(sys.argv[1])

    if not tex_file.exists():
        print(f"错误: 文件不存在: {tex_file}")
        sys.exit(1)

    print(f"正在调用新脚本处理: {tex_file}")
    print()
    print("=" * 60)
    print()

    # 调用新脚本
    cmd = [
        sys.executable,
        'tools/images/process_images_to_tikz.py',
        '--mode', 'preview',
        '--files', str(tex_file)
    ]

    try:
        result = subprocess.run(cmd, check=True)
        sys.exit(result.returncode)
    except subprocess.CalledProcessError as e:
        print(f"\n错误: 调用新脚本失败")
        print(f"命令: {' '.join(cmd)}")
        sys.exit(e.returncode)
    except FileNotFoundError:
        print("\n错误: 找不到 process_images_to_tikz.py")
        print("请确保在项目根目录运行此脚本")
        sys.exit(1)


if __name__ == '__main__':
    main()
