#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试反向定界符检测和修复功能

测试 v1.8.8 新增的两个函数：
1. fix_simple_reversed_inline_pairs - 极度保守的自动修复
2. collect_reversed_math_samples - 检测并记录问题
"""

import sys
from pathlib import Path

# 添加路径以导入核心模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.ocr_to_examx import fix_simple_reversed_inline_pairs


def test_fix_simple_reversed_inline_pairs():
    """测试极度保守的反向定界符修复"""
    
    print("=" * 80)
    print("测试 fix_simple_reversed_inline_pairs")
    print("=" * 80)
    
    # 测试用例 1：应该被修复的简单例子（中间只有空白和标点）
    test_cases_should_fix = [
        ("求点\\) \\(X_2 所有可能的坐标", "求点\\( \\)X_2 所有可能的坐标"),
        ("其中\\) ，\\(x_i", "其中\\( ，\\)x_i"),
        ("函数\\)  \\(f(x)", "函数\\(  \\)f(x)"),
        ("已知\\)。\\(a > 0", "已知\\(。\\)a > 0"),
        ("设\\) : \\(m", "设\\( : \\)m"),
        ("因此\\)、\\(x", "因此\\(、\\)x"),
    ]
    
    print("\n应该被修复的例子：")
    for i, (input_text, expected) in enumerate(test_cases_should_fix, 1):
        result = fix_simple_reversed_inline_pairs(input_text)
        status = "✅" if result == expected else "❌"
        print(f"{status} 测试 {i}:")
        print(f"  输入: {input_text}")
        print(f"  期望: {expected}")
        print(f"  结果: {result}")
        if result != expected:
            print(f"  错误: 不匹配！")
        print()
    
    # 测试用例 2：不应该被修复的例子（中间包含字母/数字/反斜杠）
    test_cases_should_not_fix = [
        "函数\\)f(x)\\(在区间",  # 中间有字母
        "已知\\)2x+3\\(等于",    # 中间有数字和字母
        "设\\)\\alpha\\(为锐角",  # 中间有反斜杠（LaTeX命令）
        "其中\\)a_1, a_2\\(为常数",  # 中间有字母、数字、下划线
    ]
    
    print("\n不应该被修复的例子（保持原样）：")
    for i, input_text in enumerate(test_cases_should_not_fix, 1):
        result = fix_simple_reversed_inline_pairs(input_text)
        status = "✅" if result == input_text else "❌"
        print(f"{status} 测试 {i}:")
        print(f"  输入: {input_text}")
        print(f"  结果: {result}")
        if result != input_text:
            print(f"  错误: 不应该被修改！")
        print()
    
    # 测试用例 3：边界情况
    edge_cases = [
        ("", ""),  # 空字符串
        ("没有数学公式的文本", "没有数学公式的文本"),  # 无数学定界符
        ("正常的\\(x + y\\)公式", "正常的\\(x + y\\)公式"),  # 正常顺序
    ]
    
    print("\n边界情况：")
    for i, (input_text, expected) in enumerate(edge_cases, 1):
        result = fix_simple_reversed_inline_pairs(input_text)
        status = "✅" if result == expected else "❌"
        print(f"{status} 测试 {i}:")
        print(f"  输入: {input_text}")
        print(f"  结果: {result}")
        if result != expected:
            print(f"  错误: 不匹配！")
        print()


def test_with_real_files():
    """用实际文件测试（如果可用）"""
    
    print("=" * 80)
    print("测试实际文件")
    print("=" * 80)
    
    output_dir = Path("word_to_tex/output")
    if not output_dir.exists():
        print("\n⚠️  word_to_tex/output 目录不存在，跳过实际文件测试")
        return
    
    tex_files = list(output_dir.glob("*_examx.tex"))
    if not tex_files:
        print("\n⚠️  未找到 *_examx.tex 文件，跳过实际文件测试")
        return
    
    print(f"\n找到 {len(tex_files)} 个文件，测试前 3 个：")
    
    for tex_file in tex_files[:3]:
        print(f"\n处理: {tex_file.name}")
        
        try:
            content = tex_file.read_text(encoding='utf-8')
            
            # 统计反向定界符
            import re
            inline_reversed = len(re.findall(r'\\\)([^\n]*?)\\\(', content))
            display_reversed = len(re.findall(r'\\\]([^\n]*?)\\\[', content))
            
            print(f"  发现反向定界符：")
            print(f"    行内数学 \\)...\\(: {inline_reversed}")
            print(f"    显示数学 \\]...\\[: {display_reversed}")
            
            # 测试修复
            fixed = fix_simple_reversed_inline_pairs(content)
            
            # 统计修复后的情况
            inline_reversed_after = len(re.findall(r'\\\)([^\n]*?)\\\(', fixed))
            display_reversed_after = len(re.findall(r'\\\]([^\n]*?)\\\[', fixed))
            
            fixed_count = (inline_reversed - inline_reversed_after) + (display_reversed - display_reversed_after)
            
            print(f"  修复后剩余：")
            print(f"    行内数学 \\)...\\(: {inline_reversed_after}")
            print(f"    显示数学 \\]...\\[: {display_reversed_after}")
            print(f"  修复数量: {fixed_count}")
            
        except Exception as e:
            print(f"  ❌ 处理失败: {e}")


if __name__ == "__main__":
    test_fix_simple_reversed_inline_pairs()
    print("\n" + "=" * 80)
    test_with_real_files()
    print("\n" + "=" * 80)
    print("测试完成！")
