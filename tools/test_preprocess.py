#!/usr/bin/env python3
"""快速测试 preprocess_markdown.py 功能"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from preprocess_markdown import preprocess_markdown_content

# 测试用例
test_input = """**一、单选题**

1．已知$$x = 1$$

![](images/test.png){width="50%"}

**二、多选题**

2．集合$$(A) = \\{x\\}$$



"""

print("输入:")
print(test_input)
print("\n" + "="*60 + "\n")

result = preprocess_markdown_content(test_input)

print("输出:")
print(result)
print("\n" + "="*60 + "\n")

# 验证
checks = [
    ("章节转换", "# 一、单选题" in result),
    ("保留数学", "$$x = 1$$" in result),
    ("保留图片", "![](images/test.png)" in result),
]

print("验证结果:")
for name, passed in checks:
    status = "✅" if passed else "❌"
    print(f"  {status} {name}")

all_passed = all(p for _, p in checks)
print(f"\n{'✅ 全部通过' if all_passed else '❌ 部分失败'}")
sys.exit(0 if all_passed else 1)
