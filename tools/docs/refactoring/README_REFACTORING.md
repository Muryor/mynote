# OCR 脚本重构指南

## 概述

本指南帮助你将 `tools/core/ocr_to_examx.py` (7000+ 行) 重构为模块化结构，以支持：
- **试卷 (Exam)**: 使用 `question`、`choices` 环境
- **讲义 (Handout)**: 使用 `definitionx`、`propertyx`、`examplex` 环境

## 文件说明

### 1. `REFACTORING_PLAN.md`
- **内容**: 完整的重构方案设计文档
- **包含**: 模块划分、代码位置、时间表、风险评估
- **用途**: 理解重构架构和整体规划

### 2. `extract_modules.py`
- **内容**: 自动化代码提取脚本
- **功能**: 从 `ocr_to_examx.py` 提取函数到各个模块
- **用途**: 自动生成模块文件，减少手动复制粘贴

### 3. `tools/lib/__init__.py` (已存在)
- **内容**: 库模块的导入入口
- **状态**: 已创建，需要在提取后更新

## 快速开始

### 步骤1: 阅读重构计划
```bash
cat tools/REFACTORING_PLAN.md
```

这会帮助你理解：
- 为什么要重构
- 模块如何划分
- 每个模块包含什么
- 代码在原文件的哪里

### 步骤2: 运行代码提取脚本
```bash
cd /Users/muryor/code/mynote
python tools/extract_modules.py
```

脚本会：
1. 读取 `tools/core/ocr_to_examx.py`
2. 查找每个函数/类/常量的定义
3. 提取完整的代码（包括注释和文档字符串）
4. 生成7个模块文件到 `tools/lib/`：
   - `math_processing.py` - 数学处理 (~2000行)
   - `text_cleaning.py` - 文本清理 (~800行)
   - `meta_extraction.py` - 元数据提取 (~400行)
   - `latex_utils.py` - LaTeX工具 (~500行)
   - `question_processing.py` - 题目处理 (~900行)
   - `validation.py` - 验证函数 (~400行)
   - `image_handling.py` - 图片处理 (~300行)

### 步骤3: 检查生成的文件
```bash
# 查看生成的文件列表
ls -lh tools/lib/*.py

# 查看某个模块的结构
head -50 tools/lib/math_processing.py

# 检查导出列表
grep -A 20 "__all__" tools/lib/math_processing.py
```

### 步骤4: 更新导入语句
编辑 `tools/lib/__init__.py`，确保导入所有模块：

```python
# 示例（脚本会自动生成）
from .math_processing import MathStateMachine, math_sm, fix_array_boundaries, ...
from .text_cleaning import escape_latex_special, clean_markdown, ...
from .meta_extraction import extract_meta_and_images, ...
# ... 等等
```

### 步骤5: 运行测试
```bash
# 确保现有功能不受影响
cd /Users/muryor/code/mynote
python tools/testing/quick_test_changes.py

# 或者运行完整测试
python -m pytest tools/testing/
```

### 步骤6: 更新主脚本
编辑 `tools/core/ocr_to_examx.py`，将函数调用改为从模块导入：

```python
# 旧方式（7000行都在一个文件）
def main():
    text = math_sm.process(text)  # 直接调用
    text = fix_array_boundaries(text)
    ...

# 新方式（从模块导入）
from tools.lib import math_sm, fix_array_boundaries, ...

def main():
    text = math_sm.process(text)
    text = fix_array_boundaries(text)
    ...
```

## 模块功能说明

### `math_processing.py` - 数学处理核心
- **MathStateMachine**: ~900行的状态机，处理所有数学定界符
- **16个修复函数**: 修复各种OCR数学错误
- **用途**: 试卷和讲义都需要数学公式处理

**关键函数**:
- `math_sm.process()` - 主处理入口
- `fix_array_boundaries()` - 修复矩阵边界
- `fix_trig_function_spacing()` - 修复三角函数空格

### `text_cleaning.py` - 文本清理
- **LaTeX转义**: 处理特殊字符 `&`, `%`, `#` 等
- **Markdown清理**: 移除粗体残留、图片属性等
- **用途**: 通用文本预处理

**关键函数**:
- `escape_latex_special()` - 转义特殊字符
- `clean_markdown()` - 清理Markdown残留
- `standardize_math_symbols()` - 标准化符号

### `meta_extraction.py` - 元数据提取
- **提取答案**: 【答案】部分
- **提取解析**: 【详解】【分析】部分
- **提取知识点**: 【知识点】部分
- **用途**: 主要用于试卷，讲义可能不需要

**关键函数**:
- `extract_meta_and_images()` - 主提取函数

### `latex_utils.py` - LaTeX工具
- **环境处理**: tabular, question, enumerate
- **格式化**: 添加表格边框、填空题横线
- **用途**: 通用LaTeX辅助

**关键函数**:
- `fix_fill_in_blanks()` - 添加填空题横线
- `fix_tabular_environments()` - 修复表格环境

### `question_processing.py` - 题目结构处理
- **结构修复**: 合并题目、嵌套子题
- **格式化**: 题干识别、小问编号
- **用途**: 主要用于试卷，讲义的例题可能需要调整

**关键函数**:
- `fix_merged_questions_structure()` - 修复合并题目
- `_is_likely_stem()` - 判断是否是题干

### `validation.py` - 验证检测
- **语法检查**: 括号平衡、数学定界符
- **错误检测**: 未闭合环境、畸形结构
- **用途**: 通用验证

**关键函数**:
- `validate_math_integrity()` - 验证数学定界符
- `validate_latex_output()` - 全局LaTeX验证

### `image_handling.py` - 图片处理
- **路径处理**: 查找、复制图片文件
- **占位符**: 生成 IMAGE_TODO 块
- **用途**: 通用图片处理

**关键函数**:
- `find_markdown_and_images()` - 查找图片
- `generate_image_todo_block()` - 生成TODO块

## 常见问题

### Q1: 提取后原文件怎么办？
保留 `ocr_to_examx.py`，逐步移除已提取的函数，最终只保留主流程代码。

### Q2: 如何确保功能不变？
运行现有测试用例，对比重构前后的输出文件是否一致。

### Q3: 发现某个函数没有被提取怎么办？
1. 检查 `MODULE_FUNCTIONS` 字典是否包含该函数名
2. 手动添加到相应模块
3. 更新 `__all__` 列表

### Q4: 导入循环怎么办？
- 确保模块之间没有相互导入
- 如果有依赖，考虑将共同依赖提取到单独的 `utils.py`

### Q5: 性能会受影响吗？
模块化导入不会显著影响性能。Python会缓存已导入的模块。

## 下一步

完成模块提取后，你可以：

1. **创建 HandoutConverter** (讲义转换器)
   - 继承 `BaseConverter`
   - 复用 `tools/lib` 中的函数
   - 实现讲义特有的逻辑

2. **优化现有代码**
   - 添加类型注解
   - 改进错误处理
   - 增加单元测试

3. **扩展新功能**
   - 支持其他文档类型（练习册、作业等）
   - 添加新的验证规则
   - 改进OCR错误检测

## 参考资料

- **重构计划**: `tools/REFACTORING_PLAN.md`
- **原始代码**: `tools/core/ocr_to_examx.py`
- **测试用例**: `tools/testing/`
- **样式文件**: `styles/examx.sty`, `styles/handoutx.sty`
- **文档**: `docs/workflow.md`, `docs/EXPLAIN_FULL.md`

## 联系与反馈

如果在重构过程中遇到问题：
1. 检查 `REFACTORING_PLAN.md` 的详细说明
2. 查看提取脚本的输出日志
3. 运行测试确认功能正常
4. 必要时回滚到原始版本

祝重构顺利！🚀
