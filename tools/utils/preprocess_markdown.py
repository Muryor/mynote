#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
preprocess_markdown.py - 安全的 Markdown 预处理脚本

替代 sed 命令，提供更可靠的预处理功能：
1. 章节标题转换：**一、单选题** → # 一、单选题
2. 保留图片引用（markdown 格式）
3. 规范化标点符号
4. 清理多余空行
5. 保护特殊字符
6. 修复 Pandoc 转换产生的问题

版本：v1.1
作者：Claude
日期：2025-11-28
"""

import re
import argparse
from pathlib import Path
from typing import List


def preprocess_markdown_content(text: str) -> str:
    """预处理 markdown 内容
    
    Args:
        text: 原始 markdown 文本
        
    Returns:
        处理后的 markdown 文本
    """
    lines = []
    in_image = False
    
    for line in text.splitlines():
        stripped = line.strip()
        
        # 1. 转换章节标题：**一、单选题** → # 一、单选题
        # 匹配：**开头 + 中文数字 + 顿号 + 任意文字 + **结尾
        if re.match(r'^\*\*([一二三四五六七八九十]、[^*]+)\*\*$', stripped):
            title = re.match(r'^\*\*([^*]+)\*\*$', stripped).group(1)
            lines.append(f"# {title}")
            continue
        
        # 2. 保护图片引用
        # 格式: ![alt](path){width="..."}
        if re.search(r'!\[.*?\]\(.*?\)', line):
            lines.append(line)
            in_image = True
            continue
        
        # 如果上一行是图片，这一行可能是图片属性，也保留
        if in_image and ('{width=' in line or '{height=' in line):
            lines.append(line)
            in_image = False
            continue
        
        in_image = False
        
        # 3. 规范化常见标点
        # 全角逗号 → 中文逗号（保持）
        # 英文句号 → 中文句号（在中文语境中）
        processed_line = line
        
        # 保留原始行，不做过度处理
        # 只处理明显的标点问题
        
        # 4. 清理行尾空格
        processed_line = processed_line.rstrip()
        
        lines.append(processed_line)
    
    # 5. 清理多余空行（连续3个以上空行 → 2个空行）
    result = '\n'.join(lines)
    result = re.sub(r'\n{4,}', '\n\n\n', result)

    # 6. 🆕 清理孤立的 $$ 标记（P2 修复）
    # 移除空的 $$ 对
    result = re.sub(r'\$\$\s*\n\s*\$\$', '', result)
    # 移除行首/行尾的孤立 $$（即只有 $$ 没有内容的行）
    result = re.sub(r'^\$\$\s*$', '', result, flags=re.MULTILINE)
    # 注意：不要使用 \s+\$\$\s+ 模式，会错误地移除正常数学公式的 $$

    # 7. 🆕 修复 \right.\ $$ 模式（导致数学模式断裂）
    # 将 \right.\ $$ 替换为 \right.$$（移除多余的反斜杠空格）
    # 注意：\\ 在 raw string 中表示一个反斜杠，再加空格匹配 "\ "
    result = re.sub(r'\\right\.\\ \$\$', r'\\right.$$', result)
    # 同样修复 \left 的情况
    result = re.sub(r'\$\$ \\left', r'$$\\left', result)

    # 8. 🆕 修复 Pandoc 产生的希腊字母问题
    # \text{π} → \pi, \text{α} → \alpha 等
    greek_map = {
        'π': r'\\pi',
        'α': r'\\alpha',
        'β': r'\\beta',
        'γ': r'\\gamma',
        'δ': r'\\delta',
        'θ': r'\\theta',
        'φ': r'\\varphi',
        'ω': r'\\omega',
        'λ': r'\\lambda',
        'μ': r'\\mu',
        'σ': r'\\sigma',
        'τ': r'\\tau',
    }
    for greek, latex in greek_map.items():
        # 匹配 \text{π} 或 \text{π,} 等（保留后面的标点）
        result = re.sub(rf'\\text\{{{greek}([,;.]*)\}}', latex + r'\1', result)

    # 9. 🆕 修复 Pandoc 产生的斜体残留（选项标记和数学变量）
    # *A*、*B.* → \(A\)、\(B.\)（选项标记）
    # *AB*、*BF* → \(AB\)、\(BF\)（数学变量，仅大写字母组合）
    # 注意：只处理纯大写字母组合，避免误伤正常斜体
    # 模式：*后跟1-4个大写字母（可选句点），再跟*
    result = re.sub(r'\*([A-Z]{1,4}\.?)\*', r'\\(\1\\)', result)

    # 10. 🆕 修复 Pandoc 产生的斜体变量+标点模式（保守方案）
    # 例如：*BD．* → BD．（斜体变量后跟中文标点）
    # 只处理：*1-3个大写字母+中文标点*  这种明确的模式
    # 保守：只处理句号、逗号结尾的情况
    result = re.sub(r'\*([A-Z]{1,3}[．。，,；;])\*', r'\\(\1\\)', result)
    
    # 11. 🆕 修复单独的斜体数学变量（小写，如 *a*, *b*, *c*, *n*）
    # 只处理单个小写字母，避免误伤正常斜体文本
    result = re.sub(r'\*([a-z])\*', r'\\(\1\\)', result)

    return result


def preprocess_markdown_file(input_path: Path, output_path: Path) -> None:
    """预处理 markdown 文件
    
    Args:
        input_path: 输入文件路径
        output_path: 输出文件路径
    """
    # 读取输入文件
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 预处理
    processed = preprocess_markdown_content(content)
    
    # 写入输出文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(processed)
    
    # 统计信息
    input_lines = content.count('\n') + 1
    output_lines = processed.count('\n') + 1
    
    # 统计章节数
    sections = len(re.findall(r'^# [一二三四五六七八九十]、', processed, re.MULTILINE))
    
    # 统计图片数
    images = len(re.findall(r'!\[.*?\]\(.*?\)', processed))
    
    print(f"预处理完成:")
    print(f"  输入行数: {input_lines}")
    print(f"  输出行数: {output_lines}")
    print(f"  章节数量: {sections}")
    print(f"  图片数量: {images}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="预处理 Pandoc 生成的 Markdown 文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本用法
  python3 preprocess_markdown.py input.md output.md
  
  # 查看帮助
  python3 preprocess_markdown.py --help
        """
    )
    
    parser.add_argument('input', type=Path, help='输入 markdown 文件')
    parser.add_argument('output', type=Path, help='输出 markdown 文件')
    parser.add_argument('--version', action='version', version='preprocess_markdown.py v1.0')
    
    args = parser.parse_args()
    
    # 检查输入文件
    if not args.input.exists():
        print(f"❌ 错误: 输入文件不存在: {args.input}")
        return 1
    
    # 确保输出目录存在
    args.output.parent.mkdir(parents=True, exist_ok=True)
    
    # 预处理
    try:
        preprocess_markdown_file(args.input, args.output)
        print(f"✅ 成功: {args.output}")
        return 0
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
