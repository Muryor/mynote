#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
preprocess_shenzhen_format.py - 深圳中学格式 Markdown 预处理脚本

处理深圳中学试卷格式，转换为标准 examx 格式：
1. 【答案】*B* → 【答案】B （移除斜体标记）
2. 【解析】【分析】+ 【解答】 → 【详解】（合并为标准格式）
3. 移除【分析】内容（通常是题目考点说明，非详细解析）
4. 保持其他预处理功能（标题、图片、标点等）

版本：v1.0
日期：2025-12-04
"""

import re
import argparse
from pathlib import Path
from typing import List, Tuple


def convert_shenzhen_answer_format(text: str) -> str:
    """转换深圳中学答案格式
    
    【答案】*B* → 【答案】B
    【答案】*AD* → 【答案】AD
    【答案】*ABD* → 【答案】ABD
    【答案】112 → 【答案】112（不变）
    【答案】$$...$$ → 【答案】$$...$$（不变）
    【答案】解：... → 【答案】\n【详解】解：...（解答题格式）
    """
    lines = text.split('\n')
    result_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        # 模式1：【答案】*X* 或 【答案】*XY* 或 【答案】*XYZ*（单选/多选答案）
        if re.match(r'^【答案】\*([A-Z]+)\*\s*$', stripped):
            match = re.match(r'^【答案】\*([A-Z]+)\*', stripped)
            result_lines.append(f'【答案】{match.group(1)}')
            continue
        
        # 模式2：【答案】*BD.* 等（带句点的）
        if re.match(r'^【答案】\*([A-Z]+)\.\*\s*$', stripped):
            match = re.match(r'^【答案】\*([A-Z]+)\.?\*', stripped)
            result_lines.append(f'【答案】{match.group(1)}')
            continue
        
        # 模式3：【答案】解：...（解答题格式 - 答案即详解）
        if re.match(r'^【答案】解[：:]', stripped):
            explain_content = stripped[len('【答案】'):].strip()
            result_lines.append('【答案】')
            result_lines.append(f'【详解】{explain_content}')
            continue
        
        # 模式4：【答案】证明：...（证明题格式）
        if re.match(r'^【答案】证明[：:]', stripped):
            explain_content = stripped[len('【答案】'):].strip()
            result_lines.append('【答案】')
            result_lines.append(f'【详解】{explain_content}')
            continue
        
        # 模式5：【答案】![...（图片开头的解答题）
        if re.match(r'^【答案】!\[', stripped):
            # 提取图片和后续内容
            img_content = stripped[len('【答案】'):].strip()
            result_lines.append('【答案】')
            result_lines.append(f'【详解】{img_content}')
            continue
        
        # 其他情况保持不变
        result_lines.append(line)
    
    return '\n'.join(result_lines)


def convert_shenzhen_explain_format(text: str) -> str:
    """转换深圳中学解析格式
    
    原格式：
    【解析】【分析】
    本题考查了...（考点说明，丢弃）
    【解答】
    解：...（保留作为详解）
    
    目标格式：
    【详解】解：...
    
    注意：解答题的 【答案】解：... 格式已在 convert_shenzhen_answer_format 中处理
    """
    lines = text.split('\n')
    result_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # 检测 【解析】【分析】 模式
        if stripped.startswith('【解析】【分析】'):
            # 跳过【分析】后的考点说明段落，直到遇到【解答】
            i += 1
            while i < len(lines):
                current = lines[i].strip()
                if current.startswith('【解答】'):
                    # 找到【解答】，提取其后的内容作为详解
                    explain_content = current[len('【解答】'):].strip()
                    result_lines.append(f'【详解】{explain_content}')
                    break
                i += 1
            i += 1
            continue
        
        # 检测独立的 【解析】 行（后面是考点说明，非详解）
        elif stripped == '【解析】' or stripped.startswith('【解析】本题'):
            # 这是考点说明，跳过直到下一个元数据或题目
            i += 1
            while i < len(lines):
                current = lines[i].strip()
                # 遇到新的元数据标记或题目编号，停止跳过
                if current.startswith('【') or re.match(r'^\d+[．.、]', current):
                    break
                i += 1
            continue
        
        else:
            result_lines.append(line)
            i += 1
    
    return '\n'.join(result_lines)


def clean_analysis_section(text: str) -> str:
    """清理【分析】相关的残留内容
    
    深圳中学格式中，【分析】通常包含考点说明，这些内容在转换后应该丢弃，
    只保留【解答】/【详解】中的实际解题过程。
    """
    # 移除独立的 【分析】 段落标记
    text = re.sub(r'^【分析】\s*$', '', text, flags=re.MULTILINE)
    
    # 移除 【解析】后面紧跟的【分析】
    text = re.sub(r'【解析】【分析】', '【解析】', text)
    
    return text


def fix_explain_continuation(text: str) -> str:
    """修复【详解】内容的续行问题
    
    确保【详解】后的多行内容正确连接。
    """
    # 修复【解答】\ 这种续行标记
    text = re.sub(r'【解答】\\?\s*$', '【详解】', text, flags=re.MULTILINE)
    text = re.sub(r'【详解】\\?\s*$', '【详解】', text, flags=re.MULTILINE)
    
    return text


def preprocess_shenzhen_content(text: str) -> str:
    """深圳中学格式预处理主函数
    
    Args:
        text: 原始 markdown 文本
        
    Returns:
        处理后的 markdown 文本
    """
    # 1. 转换答案格式
    text = convert_shenzhen_answer_format(text)
    
    # 2. 转换解析格式（这个需要逐行处理，比较复杂）
    text = convert_shenzhen_explain_format(text)
    
    # 3. 清理【分析】残留
    text = clean_analysis_section(text)
    
    # 4. 修复续行问题
    text = fix_explain_continuation(text)
    
    # 5. 调用通用的 markdown 预处理
    from preprocess_markdown import preprocess_markdown_content
    text = preprocess_markdown_content(text)
    
    return text


def preprocess_shenzhen_file(input_path: Path, output_path: Path) -> None:
    """预处理深圳中学格式的 markdown 文件
    
    Args:
        input_path: 输入文件路径
        output_path: 输出文件路径
    """
    # 读取输入文件
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 预处理
    processed = preprocess_shenzhen_content(content)
    
    # 写入输出文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(processed)
    
    # 统计信息
    input_lines = content.count('\n') + 1
    output_lines = processed.count('\n') + 1
    
    # 统计元数据
    answers = len(re.findall(r'^【答案】', processed, re.MULTILINE))
    explains = len(re.findall(r'^【详解】', processed, re.MULTILINE))
    
    print(f"深圳中学格式预处理完成:")
    print(f"  输入行数: {input_lines}")
    print(f"  输出行数: {output_lines}")
    print(f"  答案数量: {answers}")
    print(f"  详解数量: {explains}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="预处理深圳中学格式的 Markdown 文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
深圳中学格式特点：
  1. 答案带斜体标记：【答案】*B* 
  2. 解析分为【解析】【分析】和【解答】两部分
  3. 【分析】包含考点说明（丢弃）
  4. 【解答】包含实际解题过程（保留）
  5. 无【难度】和【知识点】标记

示例:
  python3 preprocess_shenzhen_format.py input.md output.md
        """
    )
    
    parser.add_argument('input', type=Path, help='输入 markdown 文件')
    parser.add_argument('output', type=Path, help='输出 markdown 文件')
    parser.add_argument('--version', action='version', version='preprocess_shenzhen_format.py v1.0')
    
    args = parser.parse_args()
    
    # 检查输入文件
    if not args.input.exists():
        print(f"❌ 错误: 输入文件不存在: {args.input}")
        return 1
    
    # 确保输出目录存在
    args.output.parent.mkdir(parents=True, exist_ok=True)
    
    # 预处理
    try:
        preprocess_shenzhen_file(args.input, args.output)
        print(f"✅ 成功: {args.output}")
        return 0
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
