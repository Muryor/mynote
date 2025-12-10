#!/usr/bin/env python3
"""
Replace IMAGE_TODO blocks with \examimage or \examimageinline commands.

This script:
1. Finds IMAGE_TODO_START...IMAGE_TODO_END blocks
2. Extracts metadata (path, width, inline)
3. Replaces with \examimage{relative_path}{width_ratio} command

Note: Requires \setexamdir{content/exams/auto/EXAM_NAME} at the top of the file
"""

import re
import sys
from pathlib import Path


def extract_image_filename(path_str: str) -> str:
    """Extract just the filename from the path metadata."""
    # Path is like: /Users/muryor/.../jinan_2025_mock/media/image2.png
    # We want: image2.png
    return Path(path_str).name


def replace_image_todos(tex_content: str, exam_dir: Path, exam_slug: str) -> tuple[str, bool]:
    """
    Replace IMAGE_TODO blocks with \examimage or \examimageinline commands.
    
    Args:
        tex_content: Full LaTeX content
        exam_dir: Path to exam directory (e.g., content/exams/auto/jinan_2025_mock)
        exam_slug: Exam directory name (e.g., jinan_2025_mock)
    
    Returns:
        Tuple of (modified LaTeX content, needs_setexamdir)
        needs_setexamdir = '\\setexamdir' not in tex_content
    
    """
    needs_setexamdir = '\\setexamdir' not in tex_content
    # Pattern to match entire IMAGE_TODO block
    pattern = re.compile(
        r'% IMAGE_TODO_START.*?path=([^\s]+).*?width=(\d+%).*?inline=(true|false).*?\n'
        r'(.*?)'
        r'% IMAGE_TODO_END.*?\n',
        re.DOTALL | re.MULTILINE
    )
    
    def replace_block(match):
        path_str = match.group(1).replace(r'\_', '_').replace(r'\\', '/')
        width = match.group(2)
        inline = match.group(3) == 'true'
        block_content = match.group(4)
        
        # Extract filename from path
        filename = extract_image_filename(path_str)
        
        # Build relative path (relative to exam directory)
        rel_path = f"images/media/{filename}"
        
        # Force default width ratio to 0.30 per current workflow preference
        width_decimal = 0.30
        
        # Build examimage command
        if inline:
            examimage_cmd = f"\\examimageinline{{{rel_path}}}{{{width_decimal:.2f}}}"
        else:
            examimage_cmd = f"\\examimage{{{rel_path}}}{{{width_decimal:.2f}}}"
        
        return examimage_cmd + "\n"
    
    modified_content = pattern.sub(replace_block, tex_content)
    return modified_content, needs_setexamdir


def main():
    if len(sys.argv) != 2:
        print("Usage: python replace_image_todos_with_includes.py <tex_file>")
        print("Example: python replace_image_todos_with_includes.py content/exams/auto/jinan_2025_mock/converted_exam.tex")
        sys.exit(1)
    
    tex_file = Path(sys.argv[1])
    
    if not tex_file.exists():
        print(f"❌ File not found: {tex_file}")
        sys.exit(1)
    
    # Read original content
    with open(tex_file, 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    # Get exam directory (parent of tex file)
    exam_dir = tex_file.parent
    exam_slug = exam_dir.name
    
    # Replace IMAGE_TODO blocks
    modified_content, needs_setexamdir = replace_image_todos(original_content, exam_dir, exam_slug)
    
    # Add \setexamdir if needed (after \examxtitle line)
    if needs_setexamdir:
        # Find first line starting with \examxtitle and add \setexamdir after it
        lines = modified_content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('\\examxtitle'):
                relative_exam_dir = f"content/exams/auto/{exam_slug}"
                lines.insert(i + 1, f"\\setexamdir{{{relative_exam_dir}}}")
                print(f"ℹ️  Added \\setexamdir{{{relative_exam_dir}}}")
                break
        modified_content = '\n'.join(lines)
    
    # Count replacements
    original_count = original_content.count('IMAGE_TODO_START')
    modified_count = modified_content.count('IMAGE_TODO_START')
    replaced_count = original_count - modified_count
    
    # Write back to file
    with open(tex_file, 'w', encoding='utf-8') as f:
        f.write(modified_content)
    
    print(f"✅ Replaced {replaced_count} IMAGE_TODO blocks with \\examimage commands")
    print(f"📄 Modified: {tex_file}")
    
    if modified_count > 0:
        print(f"⚠️  Warning: {modified_count} IMAGE_TODO blocks remain (check for parsing issues)")


if __name__ == '__main__':
    main()
