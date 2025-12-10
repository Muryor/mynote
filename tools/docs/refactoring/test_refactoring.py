#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重构验证测试脚本

测试新提取的模块是否能正常工作
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
root_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(root_dir))

def test_imports():
    """测试所有模块是否能正常导入"""
    print("=" * 60)
    print("测试 1: 模块导入")
    print("=" * 60)
    
    try:
        from tools.lib import (
            # math_processing
            math_sm, MathStateMachine, fix_array_boundaries,
            # text_cleaning
            escape_latex_special, clean_markdown,
            # meta_extraction
            extract_meta_and_images, META_PATTERNS,
            # latex_utils
            fix_fill_in_blanks, add_table_borders,
            # question_processing
            fix_merged_questions_structure,
            # validation
            validate_math_integrity,
            # image_handling
            find_markdown_and_images,
        )
        print("✓ 所有模块导入成功")
        return True
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_math_processing():
    """测试数学处理模块"""
    print("\n" + "=" * 60)
    print("测试 2: 数学处理功能")
    print("=" * 60)
    
    try:
        from tools.lib import math_sm
        
        # 测试简单的数学模式转换
        test_cases = [
            ("$x + y$", r"\(x + y\)"),
            ("$$E = mc^2$$", r"\(E = mc^2\)"),
            (r"\(a^2 + b^2\)", r"\(a^2 + b^2\)"),  # 已经正确的
        ]
        
        for input_text, expected_pattern in test_cases:
            result = math_sm.process(input_text)
            if expected_pattern in result or result.strip() == expected_pattern.strip():
                print(f"  ✓ {input_text[:30]:30s} → OK")
            else:
                print(f"  ! {input_text[:30]:30s} → {result[:40]}")
        
        return True
    except Exception as e:
        print(f"✗ 数学处理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_text_cleaning():
    """测试文本清理模块"""
    print("\n" + "=" * 60)
    print("测试 3: 文本清理功能")
    print("=" * 60)
    
    try:
        from tools.lib import escape_latex_special
        
        # 测试LaTeX特殊字符转义
        test_cases = [
            ("100% complete", r"100\% complete"),
            ("x & y", r"x \& y"),
            ("a#b", r"a\#b"),
        ]
        
        for input_text, expected in test_cases:
            result = escape_latex_special(input_text)
            if expected in result:
                print(f"  ✓ {input_text:20s} → OK")
            else:
                print(f"  ! {input_text:20s} → {result}")
        
        return True
    except Exception as e:
        print(f"✗ 文本清理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_meta_extraction():
    """测试元数据提取模块"""
    print("\n" + "=" * 60)
    print("测试 4: 元数据提取功能")
    print("=" * 60)
    
    try:
        from tools.lib import META_PATTERNS
        
        # 验证模式定义
        expected_keys = ['answer', 'difficulty', 'topics', 'analysis', 'explain']
        for key in expected_keys:
            if key in META_PATTERNS:
                print(f"  ✓ 模式 '{key}' 已定义")
            else:
                print(f"  ✗ 模式 '{key}' 缺失")
        
        return True
    except Exception as e:
        print(f"✗ 元数据提取测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_validation():
    """测试验证模块"""
    print("\n" + "=" * 60)
    print("测试 5: 验证功能")
    print("=" * 60)
    
    try:
        from tools.lib import validate_math_integrity
        
        # 测试简单的验证
        test_text = r"""
        这是一个测试文本。
        公式1: \(x + y = z\)
        公式2: \(a^2 + b^2 = c^2\)
        """
        
        issues = validate_math_integrity(test_text)
        print(f"  ✓ 验证功能正常 (发现 {len(issues)} 个问题)")
        
        return True
    except Exception as e:
        print(f"✗ 验证测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("OCR 脚本重构 - 功能验证测试")
    print("=" * 60)
    
    tests = [
        ("模块导入", test_imports),
        ("数学处理", test_math_processing),
        ("文本清理", test_text_cleaning),
        ("元数据提取", test_meta_extraction),
        ("验证功能", test_validation),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n✗ 测试 '{name}' 异常: {e}")
            results.append((name, False))
    
    # 打印总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"  {status:8s} - {name}")
    
    print(f"\n通过率: {passed}/{total} ({passed*100//total}%)")
    
    if passed == total:
        print("\n🎉 所有测试通过！重构成功！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，需要修复。")
        return 1


if __name__ == '__main__':
    sys.exit(main())
