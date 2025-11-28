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

### 1.2 元信息映射

| Markdown | LaTeX | 备注 |
|----------|-------|------|
| `【答案】A` | `\answer{A}` | 直接映射 |
| `【难度】0.85` | `\difficulty{0.85}` | 直接映射 |
| `【知识点】`/`【考点】` | `\topics{...}` | 合并 |
| `【详解】`/`【点睛】` | `\explain{...}` | ✅ 主要来源 |
| `【分析】` | **丢弃** | ⚠️ 严禁使用 |

### 1.3 编译命令

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

# 4. 编译
./build.sh exam teacher
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

### 流程概览

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
# 导出图片任务
python3 tools/images/export_image_jobs.py --files converted_exam.tex

# 导出图片任务 + 复制图片到 content/exams（作为 PNG fallback）
python3 tools/images/export_image_jobs.py --files converted_exam.tex --copy-images

# 应用 TikZ 代码
python3 tools/images/apply_tikz_snippets.py --tex-file converted_exam.tex

# 快速用 includegraphics 替代（调试用）
python3 tools/images/process_images_to_tikz.py --mode include --files converted_exam.tex
```

### PNG Fallback 流程

当没时间画 TikZ 时，可直接使用 PNG 图片：

1. 导出时添加 `--copy-images` 参数，图片会复制到 `<exam_dir>/images/`
2. 在 TeX 中用 `\includegraphics{images/<filename>.png}` 替代 TikZ 占位符
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
