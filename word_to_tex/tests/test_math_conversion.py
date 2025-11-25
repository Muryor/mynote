#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ocr_to_examx.py 的单元测试"""

import unittest
import sys
import os

# Add tools/core to path
test_dir = os.path.dirname(os.path.abspath(__file__))
word_to_tex_dir = os.path.dirname(test_dir)
tools_core_dir = os.path.join(os.path.dirname(word_to_tex_dir), 'tools', 'core')
sys.path.insert(0, tools_core_dir)

from ocr_to_examx import MathStateMachine, standardize_math_symbols

class TestMathStateMachine(unittest.TestCase):
    """测试数学状态机"""

    def setUp(self):
        self.sm = MathStateMachine()

    def test_double_dollar_merge(self):
        """测试双美元符号合并不丢失内容"""
        # 合并后应保留两个公式的内容
        result = self.sm.preprocess_multiline_math('$$C$$：$$x^{2}$$')
        self.assertIn('x^{2}', result, "第二个公式内容不应丢失")

    def test_right_boundary_with_punctuation(self):
        """测试 \\right. 后跟中文标点"""
        result = self.sm.process(r'$$\left\{ x \right.$$，然后')
        # 中文标点不应在数学模式内
        self.assertNotIn(r'\(，', result)

    def test_preserve_text_i(self):
        """测试虚数单位保持 \\text{i} 格式"""
        result = standardize_math_symbols(r'\text{i}')
        # 应保持原样，不转换为 \mathrm{i}
        self.assertEqual(result, r'\text{i}')

class TestImageProcessing(unittest.TestCase):
    """测试图片处理"""

    def test_remove_tiny_images(self):
        """测试移除极小装饰性图片"""
        from ocr_to_examx import remove_decorative_images

        text = '![](/path/img.png){width="1.38e-2in" height="1.38e-2in"}'
        result = remove_decorative_images(text)
        self.assertEqual(result, '', "极小图片应被移除")

if __name__ == '__main__':
    unittest.main()
