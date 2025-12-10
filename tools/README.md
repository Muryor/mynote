# Tools 目录说明

本目录包含 Word→LaTeX 转换流程的所有工具脚本（已完成重构）。

## 📁 目录结构

```
tools/
├── core/                    # 核心转换引擎
│   ├── ocr_to_examx.py     # Markdown → examx LaTeX 转换器（主引擎）
│   └── agent_refine.py     # TeX 精修工具（TikZ 占位符处理）
│
├── scripts/                 # 实用脚本工具
│   ├── run_pipeline.py          # 快速转换与校验
│   ├── validate_tex.py          # TeX 预编译校验
│   ├── apply_fixes.py           # 批量应用修复
│   └── fix_*.py                 # 各类修复脚本
│
├── lib/                     # 🆕 共享库模块（重构后）
│   ├── __init__.py         # 模块入口
│   ├── math_processing.py       # 数学公式处理
│   ├── text_cleaning.py         # 文本清理
│   ├── meta_extraction.py       # 元数据提取
│   ├── latex_utils.py           # LaTeX工具
│   ├── question_processing.py   # 题目处理
│   ├── validation.py            # 验证检测
│   └── image_handling.py        # 图片处理
│
├── images/                  # 图片处理工具
│   ├── process_images_to_tikz.py      # WMF → PNG + TikZ 占位符处理
│   ├── generate_tikz_placeholders.py  # 生成 TikZ 占位符
│   └── generate_tikz_from_images.py   # 从图片生成 TikZ 代码
│
├── testing/                 # 测试工具
│   ├── run_batch_tests.py          # 批量转换和编译测试
│   ├── quick_test_changes.py       # 快速功能测试
│   ├── test_ocr_fixes.py           # OCR修复测试
│   └── ocr_blackbox_tests/         # 黑盒测试套件
│
├── utils/                   # 辅助工具
│   ├── preprocess_markdown.py            # Markdown 预处理
│   ├── preprocess_shenzhen_format.py     # 智学网格式预处理
│   ├── clean_extracted_attrs.py          # 清理提取的属性
│   ├── convert_display_math_in_macros.py # 转换显示数学环境
│   └── ...
│
├── docs/                    # 文档
│   ├── refactoring/        # 🆕 重构文档
│   │   ├── REFACTORING_PLAN.md      # 详细重构方案
│   │   ├── REFACTORING_SUMMARY.md   # 工作总结
│   │   ├── REFACTORING_REPORT.md    # 完成报告
│   │   ├── README_REFACTORING.md    # 快速指南
│   │   ├── QUICK_REFERENCE.md       # 快速参考
│   │   └── ...
│   ├── OCR_TO_EXAMX_SUMMARY.md      # ocr_to_examx 功能总结
│   └── V15_IMPLEMENTATION_REPORT.md # v1.5 版本实现报告
│
└── legacy/                  # 旧版脚本（不推荐使用）
```

## 🚀 快速开始

### 一键转换脚本（推荐）

所有一键脚本位于 `word_to_tex/scripts/`:

```bash
# 标准格式转换（南京、常州等）
./word_to_tex/scripts/preprocess_docx.sh input.docx output_name "试卷标题"

# 示例
./word_to_tex/scripts/preprocess_docx.sh nanjing.docx nanjing_2026 "南京2026期末"

# 智学网格式转换（深圳等）
./word_to_tex/scripts/preprocess_zx_docx.sh input.docx output_name "试卷标题"

# 示例
./word_to_tex/scripts/preprocess_zx_docx.sh shenzhen.docx shenzhen_2025 "深圳中学开学试卷"
```

**工作流程**:
1. docx → markdown (pandoc)
2. markdown 预处理
3. markdown → examx LaTeX (ocr_to_examx.py)
4. TikZ 占位符处理 (agent_refine.py)
5. 复制图片到输出目录
6. 验证编译

**输出位置**: `content/exams/auto/{output_name}/converted_exam.tex`

### 手动使用核心脚本

#### 1. OCR to examx Converter

```bash
python3 tools/core/ocr_to_examx.py input.md output.tex \
    --title "试卷标题" \
    --figures-dir path/to/images
```

**功能**: 将预处理的 Markdown 转换为 examx LaTeX 格式

#### 2. Agent Refine

```bash
python3 tools/core/agent_refine.py input.tex output.tex --create-tikz
```

**功能**: 创建 TikZ 图片占位符，优化格式

#### 3. 快速转换与校验（开发调试）

```bash
# 转换 + 校验（默认）
python3 tools/scripts/run_pipeline.py input.md --slug exam-2025

# 只转换，不校验
python3 tools/scripts/run_pipeline.py input.md --slug exam-2025 --no-validate

# 指定输出路径和标题
python3 tools/scripts/run_pipeline.py input.md \
    --slug exam-2025 \
    --title "2025年期末试卷" \
    --out-tex output/result.tex
```

## 🔧 开发使用

### Python 模块导入

重构后的共享库可以直接导入：

```python
# 导入共享库模块
from tools.lib import (
    math_sm,                    # 数学状态机
    escape_latex_special,       # LaTeX转义
    extract_meta_and_images,    # 元数据提取
    validate_math_integrity,    # 验证
)

# 或导入特定模块
from tools.lib.math_processing import MathStateMachine, fix_array_boundaries
from tools.lib.text_cleaning import clean_markdown
from tools.lib.question_processing import fix_merged_questions_structure
```

### 测试

```bash
# 重构功能测试
python3 tools/docs/refactoring/test_refactoring.py

# 快速测试
python3 tools/testing/quick_test_changes.py

# 运行所有测试
python -m pytest tools/testing/
```

## 📚 重要文档

### 重构文档

重构相关文档位于 `tools/docs/refactoring/`:

- **REFACTORING_REPORT.md** - 重构完成报告（推荐先看这个）
- **README_REFACTORING.md** - 快速上手指南
- **REFACTORING_PLAN.md** - 详细重构方案
- **QUICK_REFERENCE.md** - 快速参考卡片

### 功能文档

- **OCR_TO_EXAMX_SUMMARY.md** - ocr_to_examx.py 功能总结
- **V15_IMPLEMENTATION_REPORT.md** - v1.5 版本实现报告

## 🎯 脚本路径说明

### 一键脚本如何找到工具

`word_to_tex/scripts/` 中的脚本使用以下方式定位：

```bash
# 在 preprocess_docx.sh 中
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
TOOLS_DIR="$ROOT_DIR/tools"

# 然后引用
python3 "$TOOLS_DIR/core/ocr_to_examx.py" ...
python3 "$TOOLS_DIR/utils/preprocess_markdown.py" ...
```

这样无论从哪里运行脚本，都能正确找到工具位置。

## 🔨 维护指南

### 添加新工具脚本

1. **核心转换器**: 放在 `tools/core/`
2. **共享库函数**: 放在 `tools/lib/`（跨项目复用）
3. **工具脚本**: 放在 `tools/utils/`
4. **图片处理**: 放在 `tools/images/`
5. **测试**: 放在 `tools/testing/`

### 更新共享库

如果修改了 `tools/lib/` 中的模块：

1. 确保更新 `tools/lib/__init__.py` 的导出列表
2. 运行测试: `python3 tools/docs/refactoring/test_refactoring.py`
3. 更新相关文档

### 更新一键脚本

如果修改了工具脚本路径，需要同步更新：

- `word_to_tex/scripts/preprocess_docx.sh`
- `word_to_tex/scripts/preprocess_zx_docx.sh`

## 🎉 重构成果

### 代码模块化

- ✅ 从 7013行单文件 → 7个独立模块
- ✅ 54个函数/类/常量全部成功提取
- ✅ 所有测试通过（单元测试 + 集成测试）

### 模块列表

| 模块 | 大小 | 功能 |
|------|------|------|
| `math_processing.py` | 60KB | 数学公式处理 |
| `text_cleaning.py` | 17KB | 文本清理 |
| `meta_extraction.py` | 18KB | 元数据提取 |
| `latex_utils.py` | 11KB | LaTeX工具 |
| `question_processing.py` | 23KB | 题目处理 |
| `validation.py` | 14KB | 验证检测 |
| `image_handling.py` | 8KB | 图片处理 |

详见 `tools/docs/refactoring/REFACTORING_REPORT.md`

## 📞 获取帮助

- 查看重构文档: `cat tools/docs/refactoring/README_REFACTORING.md`
- 快速参考: `cat tools/docs/refactoring/QUICK_REFERENCE.md`
- 运行测试验证: `python3 tools/docs/refactoring/test_refactoring.py`
