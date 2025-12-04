#!/usr/bin/env python3
"""测试 split_sections 函数的改动是否正确"""

import sys
sys.path.insert(0, 'tools/core')
from ocr_to_examx import split_sections

def test_split_sections():
    """测试 split_sections 函数"""
    
    # 测试用例: (输入文本, 期望的章节标题)
    test_cases = [
        # 原始支持的格式 - 加粗格式
        ('**一、单选题**\n题目1', '一、单选题'),
        ('**二、多选题**\n题目2', '二、多选题'),
        ('**三、填空题**\n题目3', '三、填空题'),
        ('**四、解答题**\n题目4', '四、解答题'),
        
        # Markdown 标题格式
        ('# 一、单选题\n题目1', '一、单选题'),
        ('## 二、多选题\n题目2', '二、多选题'),
        ('### 三、填空题\n题目3', '三、填空题'),
        ('# 四、解答题\n题目4', '四、解答题'),
        
        # 新增格式：选择题（需要根据上下文判断）
        ('# 一、选择题：本题共8小题\n题目1', '一、单选题'),
        ('# 二、选择题：本题共3小题，有多项符合题目\n题目2', '二、多选题'),
        ('**一、选择题**\n题目1', '一、单选题'),
        ('**二、选择题：本题有多项正确**\n题目2', '二、多选题'),
        
        # 纯文本格式
        ('一、单选题\n题目1', '一、单选题'),
        ('二、多选题\n题目2', '二、多选题'),
        ('三、填空题\n题目3', '三、填空题'),
        ('四、解答题\n题目4', '四、解答题'),
    ]

    print('测试 split_sections 函数:')
    print('=' * 60)
    
    all_passed = True
    for text, expected_title in test_cases:
        sections = split_sections(text)
        if sections:
            actual_title = sections[0][0]
            status = '✅' if actual_title == expected_title else '❌'
            if actual_title != expected_title:
                all_passed = False
            print(f'{status} 输入: {repr(text[:50])}...')
            print(f'   期望: {expected_title}, 实际: {actual_title}')
        else:
            print(f'❌ 输入: {repr(text[:50])}... 未匹配到任何章节')
            all_passed = False
        print()

    print('=' * 60)
    if all_passed:
        print('✅ 全部通过')
        return 0
    else:
        print('❌ 存在失败')
        return 1

if __name__ == '__main__':
    sys.exit(test_split_sections())
