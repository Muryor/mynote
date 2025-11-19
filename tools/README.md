# Tools 目录说明

本目录包含 Word→LaTeX 转换流程的所有工具脚本。

## 📁 目录结构

```
tools/
├── core/                    # 核心转换引擎
│   ├── ocr_to_examx.py     # Markdown → examx LaTeX 转换器（主引擎）
│   └── agent_refine.py     # TeX 精修工具（TikZ 占位符处理）
│
├── images/                  # 图片处理工具
│   ├── process_images_to_tikz.py      # WMF → PNG + TikZ 占位符处理
│   ├── generate_tikz_placeholders.py  # 生成 TikZ 占位符
│   └── generate_tikz_from_images.py   # 从图片生成 TikZ 代码
│
├── testing/                 # 测试工具
│   ├── run_batch_tests.py          # 批量转换和编译测试
│   └── quick_test_changes.py       # 快速功能测试
│
├── utils/                   # 辅助工具
│   ├── preprocess_markdown.py            # Markdown 预处理
│   ├── clean_extracted_attrs.py          # 清理提取的属性
│   ├── convert_display_math_in_macros.py # 转换显示数学环境
│   ├── convert_display_to_inline.py      # 转换数学环境格式
│   └── fix_converted_math.py             # 修复数学转换问题
│
├── legacy/                  # 旧版脚本（不推荐使用）
│   ├── run_conversion_once.py      # 单次转换（已废弃）
│   └── final_reconvert.zsh         # 旧版重新转换脚本
│
└── docs/                    # 文档
    ├── OCR_TO_EXAMX_SUMMARY.md          # ocr_to_examx 功能总结
    └── V15_IMPLEMENTATION_REPORT.md     # v1.5 版本实现报告
```

## 🚀 使用方法

### 批量转换测试

```bash
# 从项目根目录运行
./build.sh test-batch

# 或直接调用
python3 tools/testing/run_batch_tests.py

# 指定特定文件
python3 tools/testing/run_batch_tests.py word_to_tex/input/exam1.docx
```

### 单个文档转换

```bash
# 使用主流程脚本
bash word_to_tex/scripts/preprocess_docx.sh input.docx output_name "试卷标题"
```

### 图片处理

```bash
# 处理 IMAGE_TODO 占位符（转为 \includegraphics）
python3 tools/images/process_images_to_tikz.py --mode include

# 生成 TikZ 模板
python3 tools/images/process_images_to_tikz.py --mode template

# 仅转换 WMF 到 PNG
python3 tools/images/process_images_to_tikz.py --mode convert
```

## 🔧 脚本说明

### 核心引擎

- **ocr_to_examx.py**: 将 Markdown 格式的试卷转换为 examx LaTeX 格式
  - 支持题干、选项、答案、解析的自动识别
  - 自动处理数学公式（`\(...\)` 格式）
  - 处理图片占位符

- **agent_refine.py**: 精修 TeX 输出
  - 生成 TikZ 占位符供 AI 填充
  - 清理格式问题
  - 优化宏命令结构

### 图片工具

- **process_images_to_tikz.py**: 一站式图片处理
  - `--mode convert`: 转换 WMF → PNG
  - `--mode include`: 使用 `\includegraphics` 引入图片
  - `--mode template`: 生成 TikZ 代码模板

### 测试工具

- **run_batch_tests.py**: 完整流程测试
  - 自动发现 `word_to_tex/input/*.docx`
  - 运行完整转换流程
  - 编译 PDF 并生成测试报告

## 📝 工作流程

```
DOCX 文件
   ↓
[Pandoc] → Markdown
   ↓
[preprocess_markdown.py] → 预处理的 Markdown
   ↓
[ocr_to_examx.py] → examx LaTeX
   ↓
[agent_refine.py] → 精修的 TeX（带 TikZ 占位符）
   ↓
[process_images_to_tikz.py] → 处理图片
   ↓
[XeLaTeX] → PDF
```

## ⚙️ 依赖要求

- Python 3.8+
- Pandoc（用于 DOCX → Markdown）
- XeLaTeX（用于 PDF 编译）
- 可选：ImageMagick 或 LibreOffice（用于 WMF 图片转换）

## 🔍 故障排查

### 导入错误

所有脚本已更新为使用子目录结构。如果遇到导入错误：

```python
# 在脚本顶部添加
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

### 路径问题

- 确保从项目根目录 (`mynote/`) 运行脚本
- 使用相对路径时注意当前工作目录

### __pycache__ 清理

```bash
cd tools
rm -rf __pycache__
find . -type d -name "__pycache__" -exec rm -rf {} +
```

## 📦 版本历史

- **v1.6**: 目录结构重组（2024-11-19）
  - 分离核心、工具、测试、文档
  - 更新所有导入路径
  - 添加 .gitignore

- **v1.5**: 数学公式和选项格式自动修复
- **v1.4**: TikZ 占位符支持
- **v1.3**: 初始批量测试工具
