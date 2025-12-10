# 试卷工作流 (v4.8)

> **快速参考** | [详细规范](REFERENCE.md) | [问题排查](TROUBLESHOOTING.md) | [更新日志](archive/CHANGELOG.md) | [工具文档](../tools/README.md)

## 快速开始

### 一键转换

```bash
# 标准格式
./word_to_tex/scripts/preprocess_docx.sh input.docx exam_name "试卷标题"

# 智学网格式- 详见 WORKFLOW_ZHIXUE.md
./word_to_tex/scripts/preprocess_zx_docx.sh input.docx exam_name "试卷标题"
```

**输出**: `content/exams/auto/<exam_name>/converted_exam.tex`

### 完整流程

```bash
# 1. 转换 Word → LaTeX
./word_to_tex/scripts/preprocess_docx.sh <docx> <name> "<title>"

# 2. 插入图片（必须）
python3 tools/images/process_images_to_tikz.py --mode include \
    --files content/exams/auto/<name>/converted_exam.tex

# 3. 配置编译 (编辑 settings/metadata.tex)
\newcommand{\examSourceFile}{content/exams/auto/<name>/converted_exam.tex}

# 4. 编译测试
VALIDATE_BEFORE_BUILD=1 ./build.sh exam teacher

# 5. 正式输出
RENAME_OUTPUT=1 ./build.sh exam both
```

---

## 核心命令

| 命令 | 功能 |
|------|------|
| `preprocess_docx.sh <docx> <name> "<title>"` | Word → LaTeX 转换 |
| `process_images_to_tikz.py --mode include` | 插入图片 ⚠️ 必须 |
| `VALIDATE_BEFORE_BUILD=1 ./build.sh exam teacher` | 预检查编译 |
| `RENAME_OUTPUT=1 ./build.sh exam both` | 输出最终 PDF |
| `tools/scripts/validate_tex.py <tex>` | TeX 结构验证 |

---

## 路径约定

```
输入:  word_to_tex/input/<name>.docx
输出:  content/exams/auto/<name>/converted_exam.tex
图片:  content/exams/auto/<name>/images/media/
PDF:   output/<试卷名>（教师版/学生版）.pdf
```

---

## 元信息映射

| Markdown | LaTeX | 说明 |
|----------|-------|------|
| 【答案】 | `\answer{}` | 直接映射 |
| 【难度】 | `\difficulty{}` | 小数 0-1 |
| 【知识点】/【考点】 | `\topics{}` | 分号分隔 |
| 【详解】/【点睛】 | `\explain{}` | 合并为详解 |
| 【分析】 | — | ⚠️ 丢弃 |

---

## 故障排查

```bash
# 查看错误日志
cat output/last_error.log

# TeX 结构检查
python3 tools/scripts/validate_tex.py <tex_file>
```

详见 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## 图片与 TikZ

**PNG 图片** (自动):
```bash
python3 tools/images/process_images_to_tikz.py --mode include --files <tex>
```

**TikZ 图形** (手动):
- 流程: [TIKZ_WORKFLOW.md](TIKZ_WORKFLOW.md)
- 提示词: [TIKZ_AGENT_PROMPT.md](TIKZ_AGENT_PROMPT.md)

---

## 工具架构

### 核心组件
- `tools/core/ocr_to_examx.py` - Markdown → LaTeX 主引擎
- `tools/core/agent_refine.py` - TeX 精修工具
- `tools/lib/` - 7个共享库模块（重构完成）

### 重构成果 (v4.8)
- ✅ 7013行 → 7个模块（54个导出项）
- ✅ 100% 测试通过
- ✅ 向后兼容

详见: [重构报告](../tools/docs/refactoring/REFACTORING_REPORT.md) | [工具文档](../tools/README.md)

---

## VS Code 任务

`Cmd+Shift+B` 或 `Cmd+Shift+P` → "Run Task":
- **Build: Exam (both)** - 默认构建
- **Build: Exam (auto-rename)** - 自动重命名
- **Build with Validation** - 带预检查
    │   └── test_refactoring.py         # 重构测试
    ├── OCR_TO_EXAMX_SUMMARY.md         # 功能总结
    └── V15_IMPLEMENTATION_REPORT.md
```

### 一键脚本工作流

```mermaid
word_to_tex/scripts/preprocess_docx.sh
    ↓
1. pandoc (docx → markdown)
    ↓
2. tools/utils/preprocess_markdown.py (预处理)
    ↓
3. tools/core/ocr_to_examx.py (markdown → examx)
    ↓  使用 tools/lib/ 共享库:
    ↓  - math_processing.py (数学处理)
    ↓  - text_cleaning.py (文本清理)
    ↓  - meta_extraction.py (元数据提取)
    ↓  - question_processing.py (题目处理)
    ↓  - validation.py (完整性验证)
    ↓
4. tools/core/agent_refine.py (TikZ 占位符)
    ↓
5. 复制图片到 content/exams/auto/<name>/images/
```

### 重构成果

| 模块 | 大小 | 导出项 | 功能 |
|------|------|--------|------|
| `math_processing.py` | 60KB | 17 | 数学公式、状态机、OCR修复 |
| `text_cleaning.py` | 17KB | 10 | LaTeX转义、文本清理 |
| `meta_extraction.py` | 18KB | 4 | 答案/难度/知识点提取 |
| `latex_utils.py` | 11KB | 5 | 填空题、表格边框 |
| `question_processing.py` | 23KB | 7 | 题目合并、结构处理 |
| `validation.py` | 14KB | 4 | 数学完整性检查 |
| `image_handling.py` | 8KB | 7 | 图片路径处理 |

### 测试验证

```bash
# 重构测试套件（5/5 通过）
python3 tools/docs/refactoring/test_refactoring.py

# 快速功能测试（3/3 通过）
python3 tools/testing/quick_test_changes.py

# 完整转换测试（683行, 19题）
python3 tools/core/ocr_to_examx.py test.md test.tex
```

详见：
- 完整报告：[tools/docs/refactoring/REFACTORING_REPORT.md](../tools/docs/refactoring/REFACTORING_REPORT.md)
- 快速指南：[tools/docs/refactoring/README_REFACTORING.md](../tools/docs/refactoring/README_REFACTORING.md)
- 工具文档：[tools/README.md](../tools/README.md)

---

## 九、VS Code 任务

按 `Cmd+Shift+B` 运行默认编译，或 `Cmd+Shift+P` → "Run Task"：
- Build: Exam (both) - 默认
- Build: Exam (auto-rename) - 编译并重命名
- Build: Exam (teacher/student)
