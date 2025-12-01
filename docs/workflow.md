# LaTeX 试卷流水线指南 (v4.1)

> **版本**: v4.1（2025-11-28）  
> **更新**: export_image_jobs.py 支持 `--copy-images` 选项，PNG fallback 流程

---

## 快速导航

| 文档 | 用途 |
|------|------|
| 本文档 | 完整流程概览 |
| [REFERENCE.md](REFERENCE.md) | 格式规范速查 |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | 错误诊断指南 |
| [IMAGE_JOBS_FULL.md](IMAGE_JOBS_FULL.md) | 图片任务字段定义 |
| [TIKZ_AGENT_PROMPT.md](TIKZ_AGENT_PROMPT.md) | TikZ 生成 Prompt |
| [EXPLAIN_FULL.md](EXPLAIN_FULL.md) | \exstep 详解格式示例 |
| [dev/IMAGE_PIPELINE_TASKS.md](dev/IMAGE_PIPELINE_TASKS.md) | 图片流水线开发任务 |
| [archive/CHANGELOG.md](archive/CHANGELOG.md) | 完整版本历史 |

---

## 一、核心规范

### 1.1 路径约定

```text
输入 Word:     word_to_tex/input/<name>.docx
输出 Markdown: word_to_tex/output/<prefix>_preprocessed.md
输出 TeX:      content/exams/auto/<prefix>/converted_exam.tex
输出 PDF:      output/wrap-exam-*.pdf
```


注意：在用 PNG 快速替换 `IMAGE_TODO` 占位时，建议保留原始的 `IMAGE_TODO_START` / `IMAGE_TODO_END` 注释块（以及其中的 TikZ `TODO` 占位注释）。
这样可以：
- 立即生成可用 PDF（使用 PNG），
- 同时保留后续由 AI / 手工将该占位替换为 TikZ 的上下文信息。

自动命名构建（避免覆盖）:
- 若希望自动将构建产物按试卷标题命名并避免覆盖，可使用仓库自带的包装脚本：
       `./scripts/build_named_exam.sh <path/to/converted_exam.tex> {teacher|student|both}`。
       该脚本会调用 `./build.sh exam {teacher|student}`，并把生成的 `output/wrap-exam-*.pdf` 复制为
       `output/<examxtitle>（教师版/学生版）.pdf`（如文件已存在，会自动附加 `-1,-2,...` 以避免覆盖）。

### 1.2 元信息映射

| Markdown | LaTeX | 备注 |
|----------|-------|------|
| `【答案】A` | `\answer{A}` | 直接映射 |
| `【难度】0.85` | `\difficulty{0.85}` | 直接映射 |
| `【知识点】`/`【考点】` | `\topics{...}` | 合并 |
| `【详解】`/`【点睛】` | `\explain{...}` | ✅ 主要来源 |
| `【分析】` | **丢弃** | ⚠️ 严禁使用 |

### 1.3 表格格式规范

**重要**：试卷中的表格需要使用竖线边框，以保持清晰的视觉效果。

```tex
% ✅ 正确：带竖线边框的表格
\begin{tabular}{|c|c|c|c|c|}
\hline
$x$ & -2 & -1 & 0 & 1 \\
\hline
$y$ & 5 & 4 & 2 & 1 \\
\hline
\end{tabular}

% ❌ 错误：无竖线边框
\begin{tabular}{ccccc}
...
\end{tabular}
```

**注意事项**：
- 每列之间用 `|` 分隔（如 `{|c|c|c|}`）
- 使用 `\hline` 添加水平线
- 确保 `\end{tabular}` 后有完整的 `}`（OCR 常见错误）

### 1.4 编译命令

```bash
# 带预检查（推荐）
VALIDATE_BEFORE_BUILD=1 ./build.sh exam teacher

# 标准编译
./build.sh exam teacher/student/both
```

---

## 二、标准工作流

### 方式 A：一键转换（推荐）

```bash
# 1. 放置 Word 文件
cp exam.docx word_to_tex/input/

# 2. 运行转换脚本
word_to_tex/scripts/preprocess_docx.sh \
    "word_to_tex/input/exam.docx" \
    "exam_2025" \
    "2025年试卷"

# 3. 修改 metadata.tex 指向生成的文件
# \newcommand{\examSourceFile}{content/exams/auto/exam_2025/converted_exam.tex}

# 4. ⚠️ 插入图片（重要！）
# 复制图片到试卷目录
mkdir -p content/exams/auto/exam_2025/images/media
cp word_to_tex/output/figures/exam_2025/media/*.png content/exams/auto/exam_2025/images/media/

# 将 IMAGE_TODO 替换为 \includegraphics
# 找到所有 IMAGE_TODO 位置：
grep -n "IMAGE_TODO_START" content/exams/auto/exam_2025/converted_exam.tex
# 手动替换 TikZ 占位为：
# \includegraphics[width=0.4\textwidth]{content/exams/auto/exam_2025/images/media/imageN.png}

# 5. 编译 + 自动重命名（推荐，使用 build.sh 统一入口）
EXAM_TEX=content/exams/auto/exam_2025/converted_exam.tex ./build.sh exam both

# 或者直接调用重命名脚本（功能相同）：
# ./scripts/build_named_exam.sh content/exams/auto/exam_2025/converted_exam.tex both
```

### 方式 B：分步执行（调试用）

```bash
# Step 1: Word → Markdown
pandoc input.docx -o output_raw.md --extract-media=figures

# Step 2: 预处理 Markdown（可选）
python3 tools/utils/preprocess_markdown.py raw.md preprocessed.md

# Step 3: Markdown → examx TeX
python3 tools/core/ocr_to_examx.py \
    preprocessed.md \
    converted_exam.tex \
    --title "试卷标题" \
    --figures-dir figures

# Step 4: 验证
python3 tools/validate_tex.py converted_exam.tex

# Step 5: 编译
./build.sh exam teacher
```

---

## 三、质量保证

### 3.1 预编译检查

```bash
python3 tools/validate_tex.py <tex_file>
```

### 可选：通过 `build.sh` 一步完成编译并自动重命名

如果希望使用统一入口进行编译并让输出按 `\examxtitle{}` 自动命名（并避免覆盖），可以在调用 `build.sh` 时设置环境变量 `EXAM_TEX` 指向 `converted_exam.tex`：

```bash
# 一键编译并自动重命名（teacher 版本）
EXAM_TEX=content/exams/auto/exam_2025/converted_exam.tex ./build.sh exam teacher

# 同时生成 teacher + student 并自动命名
EXAM_TEX=content/exams/auto/exam_2025/converted_exam.tex ./build.sh exam both
```

该机制为保守设计：
- 仅在 `EXAM_TEX` 被设置时才会调用 `scripts/build_named_exam.sh`；
- 如果重命名脚本不存在或失败，`build.sh` 只会打印警告并继续，不会中止构建；
- 生成的文件名保持原有的中文符号（脚本会使用 `tools/utils/get_exam_title.py` 提取标题）。


**检查内容**：
- `\explain{}` 中的空行（Runaway argument 主因）
- 花括号/数学定界符配对
- 环境平衡 `\begin{question}` vs `\end{question}`
- 反向定界符 `\)...\(`
- 重复 meta 命令

### 3.2 黑箱测试（开发用）

```bash
# 运行单个测试
python3 tools/testing/ocr_blackbox_tests/run_tests.py <preprocessed.md>

# 分析所有结果
python3 tools/testing/ocr_blackbox_tests/analyze_results.py
```

**18 项测试覆盖**：
- T001-T007: 结构正确性（题目、选项、答案、解析）
- T008: 定界符平衡
- T009: 反向定界符
- T010-T015: 格式规范
- T016-T020: 特殊情况处理

### 3.3 自测命令

```bash
# ocr_to_examx.py 自测
python3 tools/core/ocr_to_examx.py --selftest

# 回归测试
tools/test_compile.sh
```

---

## 四、错误诊断

### 常见错误速查

| 错误类型 | 常见原因 | 修复方法 |
|---------|---------|---------|
| Runaway argument | `\explain{}` 有空行 | 删除空行 |
| Missing $ inserted | 定界符不匹配 | 检查 `\(...\)` |
| Environment unbalanced | 缺少 `\end{question}` | 补充结束标记 |
| Undefined control sequence | 命令拼写错误 | 检查命令名 |
| `\pir` 等希腊字母连写 | OCR 识别问题 | 改为 `\pi r`（加空格） |
| `*\(R\)*` 格式错误 | Pandoc 粗体转换问题 | 改为 `\(\mathbf{R}\)` |
| 18、19题进入17题答案框 | 解答题未正确分隔 | 检查 `> N．` 引用前缀 |

### 常见手动修复项

转换后常需手动检查的问题：

1. **希腊字母与变量连写**：如 `\pir` → `\pi r`，`\alphax` → `\alpha x`
2. **实数集粗体**：`*\(R\)*` → `\(\mathbf{R}\)`
3. **解答题小问分隔**：确保每个小问有独立的 `\item`
4. **Markdown 引用符号**：检查是否有 `>` 符号导致的内容合并

### 诊断流程

```bash
# 1. 查看错误摘要
cat output/last_error.log

# 2. 详细定位
tools/locate_error.sh output/.aux/wrap-exam-teacher.log

# 3. 修复后重新验证
VALIDATE_BEFORE_BUILD=1 ./build.sh exam teacher
```

---

## 五、图片流水线

### ⭐ 推荐策略：PNG 优先

**最佳实践**：优先使用 PNG 图片，有时间再转换为 TikZ。

理由：
- ✅ **快速交付**：直接使用 PNG 图片可立即编译出完整试卷
- ✅ **质量保证**：保留原始图片所有细节，避免 TikZ 绘制误差
- ✅ **灵活转换**：后续有时间可逐步替换为 TikZ，不影响现有工作
- ⚠️ **TikZ 耗时**：手工绘制或 AI 生成 TikZ 都需要大量时间和调试

### PNG 快速流程（推荐）

```bash
# 方式 1：转换时已有图片（推荐）
# 图片已在 <exam_dir>/images/media/ 目录中

# 直接在 TeX 中使用（手动替换 IMAGE_TODO）
# 注意：使用从项目根目录的完整路径
\begin{center}
\includegraphics[width=0.40\textwidth]{content/exams/auto/changzhou_2026_midterm/images/media/image2.png}
\end{center}

# 方式 2：批量替换所有 IMAGE_TODO 为 includegraphics（调试用）
python3 tools/images/process_images_to_tikz.py --mode include --files converted_exam.tex
```

### TikZ 完整流程（时间充裕时）

```text
DOCX → Pandoc → Markdown + media/
       ↓
ocr_to_examx.py → IMAGE_TODO 占位
       ↓
export_image_jobs.py → image_jobs.jsonl
       ↓
AI Agent 生成 TikZ → generated_tikz.jsonl
       ↓
write_snippets_from_jsonl.py → tikz_snippets/*.tex
       ↓
apply_tikz_snippets.py → 回填到 TeX
       ↓
build.sh → 最终 PDF
```

### IMAGE_TODO 格式

```tex
% IMAGE_TODO_START id=exam-Q3-img1 path=figures/image1.png width=60% inline=false question_index=3
% CONTEXT_BEFORE: 函数图像如下所示：
% CONTEXT_AFTER: 则下列结论正确的是
\begin{tikzpicture}
  % TODO: AI_AGENT_REPLACE_ME
\end{tikzpicture}
% IMAGE_TODO_END id=exam-Q3-img1
```

### 图片处理命令

```bash
# === PNG 快速方案（推荐） ===
# 手动替换 IMAGE_TODO 为 \includegraphics{images/media/<filename>.png}
# 示例见上方"PNG 快速流程"

# === TikZ 流程（时间充裕时） ===
# 导出图片任务
python3 tools/images/export_image_jobs.py --files converted_exam.tex

# 应用 TikZ 代码
python3 tools/images/apply_tikz_snippets.py --tex-file converted_exam.tex

# 批量替换为 includegraphics（调试/临时方案）
python3 tools/images/process_images_to_tikz.py --mode include --files converted_exam.tex
```

### 图片路径说明

转换后的图片位置：
```
content/exams/auto/<exam_name>/
├── converted_exam.tex
└── images/
    └── media/
        ├── image1.png
        ├── image2.png
        └── ...
```

TeX 中引用方式（从项目根目录的相对路径）：
```tex
% ✅ 正确：从项目根目录的完整路径
\includegraphics[width=0.40\textwidth]{content/exams/auto/changzhou_2026_midterm/images/media/image2.png}

% ❌ 错误：相对于 converted_exam.tex 的路径（编译时找不到文件）
\includegraphics[width=0.40\textwidth]{images/media/image2.png}
```
3. 之后有时间再逐步替换为 TikZ

---

## 六、关键脚本说明

### tools/core/ocr_to_examx.py (v1.9.5)

**主要功能**：
- Markdown → examx TeX 结构化转换
- MathStateMachine 状态机处理数学公式
- 自动修复反向定界符、方程组 `\left\{` 补全
- 【分析】强制过滤、Meta 重复检测

**关键函数**：
- `MathStateMachine`: 数学模式状态机
- `fix_simple_reversed_inline_pairs()`: 反向定界符修复
- `_fix_array_left_braces()`: 方程组补全
- `_smart_replace_because_therefore()`: ∴/∵ 智能处理

### tools/utils/preprocess_markdown.py (v1.1)

**功能**：
- 章节标题转换：`**一、单选题**` → `# 一、单选题`
- 清理孤立 `$$` 标记
- 修复 `\right.\ $$` 模式

### tools/validate_tex.py

**检查项**：
- 花括号/定界符配对
- 环境平衡
- `\explain{}` 空行
- 答案格式、难度范围

---

## 七、成功标准

### 文本流水线
- [ ] PDF 成功生成并可打开
- [ ] 题目结构完整（题干、选项、答案、解析）
- [ ] TeX 中不包含【分析】
- [ ] 预编译检查通过
- [ ] 回归测试通过

### 图片流水线
- [ ] IMAGE_TODO 块格式正确
- [ ] image_jobs.jsonl 包含所有图片
- [ ] TikZ 渲染正确

---

## 八、最佳实践

### 开发流程

1. **先稳定文本流水线**：Word → Markdown → TeX → PDF
2. **再引入图片流水线**：先用 includegraphics，再逐步换 TikZ
3. **持续验证**：每次修改后运行 `--selftest` 和 `test_compile.sh`

### 调试技巧

```bash
# 快速诊断
VALIDATE_BEFORE_BUILD=1 ./build.sh exam teacher 2>&1 | grep -A 5 "error"

# 检查问题日志
cat word_to_tex/output/debug/*_issues.log | grep "CRITICAL\|ERROR"

# 数学处理对比
python3 tools/testing/math_sm_comparison.py preprocessed.md
```

### 提交检查清单

```bash
python3 tools/core/ocr_to_examx.py --selftest  # 自测
tools/test_compile.sh                           # 回归测试
python3 tools/validate_tex.py <tex_file>        # 验证
```

---

## 附录：版本历史

### v4.0 (2025-11-28)
- ocr_to_examx.py v1.9.5：智能 ∴/∵ 处理、array/cases 环境保护
- preprocess_markdown.py 修复：正则表达式错误、孤立 $$ 处理
- 18 项黑箱测试：17/18 达到 100% 通过率

### v3.9 (2025-11-27)
- 两批 12 项 OCR 修复
- 测试套件完善

### v3.5 (2025-11-24)
- 方程组 `\left\{` 智能补全
- 反向定界符自动修复
- Meta 命令重复检测

### v3.3 (2025-11-20)
- MathStateMachine 状态机实现
- 完美数学定界符平衡

> 完整历史参见 [archive/CHANGELOG.md](archive/CHANGELOG.md)

---

**祝使用顺利！🚀**
