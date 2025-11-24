# LaTeX 试卷流水线测试与开发指南 (v3.5)

> **文档版本**：v3.5（2025-11-24）  
> **核心特性**：
> - 🔥 MathStateMachine 状态机数学处理（v1.8）
> - 🆕 反向定界符检测与自动修复（v1.8.8）
> - 🆕 方程组 \left\{ 智能补全（v1.8.9）
> - ✅ Meta 重复检测 + 【分析】强制过滤
> - ✅ 智能预编译检查 + 错误诊断工具链
> - ✅ IMAGE_TODO 统一占位符 + TikZ 自动化流水线

---

## 📚 配套文档导航

### 核心必读（按顺序）

1. **本文档（workflow.md）** - 完整流程概览与快速入门
2. **[REFERENCE.md](REFERENCE.md)** - 格式规范速查手册
   - 元信息映射、IMAGE_TODO 格式、image_jobs.jsonl 字段、\exstep 语法
3. **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - 错误诊断与修复指南
   - 预编译检查、编译错误诊断、常见问题详解（8 大类）

### 深度参考（按需查阅）

- **[IMAGE_JOBS_FULL.md](IMAGE_JOBS_FULL.md)** - image_jobs.jsonl 完整字段定义
- **[EXPLAIN_FULL.md](EXPLAIN_FULL.md)** - \exstep 详解格式详细示例
- **[TIKZ_AGENT_PROMPT.md](TIKZ_AGENT_PROMPT.md)** - AI 生成 TikZ 的标准 Prompt

### 归档与开发

- **[archive/CHANGELOG.md](archive/CHANGELOG.md)** - 版本历史（v3.0-v3.5）
- **[dev/IMAGE_PIPELINE_TASKS.md](dev/IMAGE_PIPELINE_TASKS.md)** - 图片流水线开发任务清单（Tasks A/B/C/D）

---

## 角色定位

你是一名**本地 LaTeX 试卷流水线工程师**，负责执行和验证整个考试流水线，并能根据需要自动调用脚本、定位错误、修复格式，并产出稳定的 examx 结构化 TeX + PDF。

本文档涵盖：
1. **阶段一**：文本 & 结构流水线（Word → Markdown → examx TeX → PDF）
2. **阶段二**：图片 → TikZ 自动化流水线（详见第九章及 dev/IMAGE_PIPELINE_TASKS.md）
3. **质量保证**：预编译检查、智能错误分析、回归测试（详见 TROUBLESHOOTING.md）

---

## 一、核心规范速查

### 1.1 文件路径约定

| 文件类型 | 路径模板 | 示例 |
|---------|---------|------|
| 输入 Word | `word_to_tex/input/<name>.docx` | `2023-math-final.docx` |
| Markdown | `word_to_tex/output/<前缀>_raw.md` | `2023_math_final_raw.md` |
| 转换后 TeX | `content/exams/auto/<前缀>/converted_exam.tex` | `2023_math_final/converted_exam.tex` |
| 输出 PDF | `output/wrap-exam-*.pdf` | `wrap-exam-teacher.pdf` |

### 1.2 元信息映射规范

| Markdown | LaTeX | 备注 |
|----------|-------|------|
| `【答案】A` | `\answer{A}` | 直接映射 |
| `【难度】0.85` | `\difficulty{0.85}` | 直接映射 |
| `【知识点】...` 或 `【考点】...` | `\topics{...}` | 合并为一个 |
| `【详解】...` | `\explain{...}` | **唯一来源** |
| `【分析】...` | **舍弃** | ⚠️ **严禁使用** |

**⚠️ 强制规则（不可违反）**：

1. **【分析】必须完全舍弃**：
   - 不进入 `\explain{}`
   - 不写入任何其他 LaTeX 命令
   - 不作为注释保留
   - 最终 TeX 中不能出现`【分析】`及其内容

2. **【详解】是 `\explain{}` 的唯一来源**：
   - 只有`【详解】`之后的内容才能进入 `\explain{}`
   - 如果某题只有`【分析】`而无`【详解】`，该题视为"无详解"
   - 可以不输出 `\explain`，或输出空的 `\explain{}`

3. **验证方法**：
   - 在生成的 TeX 中搜索"分析"二字
   - 检查 `\explain{}` 内容是否全部来自`【详解】`
   - 对比原始 Markdown 确认`【分析】`内容未被使用

### 1.3 编译规范

**步骤**：

1. 修改 `settings/metadata.tex`：`\newcommand{\examSourceFile}{content/exams/auto/<前缀>/converted_exam.tex}`

2. 运行编译：
   ```bash
   # 带预检查（推荐）
   VALIDATE_BEFORE_BUILD=1 ./build.sh exam teacher
   
   # 标准编译
   ./build.sh exam teacher/student/both
   ```

3. 检查输出：`output/wrap-exam-*.pdf`、`output/last_error.log`、`output/build.log`

**build.sh 特性**：预编译检查集成、智能错误分析、跨平台兼容、自动错误定位

---

## 二、阶段一：文本流水线测试任务目标

使用一个示例 Word 文件，完整跑通**文本 + 结构**流水线并产出两份文档：

### 2.1 执行记录

记录所有关键命令和操作步骤。

### 2.2 OCR 脚本问题清单（⚠️ 重点）
每个问题使用以下格式：

```markdown
### 问题 N：<简短标题>

**现象**：
<LaTeX 编译错误或异常表现>

**定位**：
- 原始 Markdown 片段（题号行前后 5 行）：
  ```markdown
  <粘贴相关 Markdown>
  ```
- 生成的错误 TeX 片段（问题行前后 5 行）：
  ```latex
  <粘贴相关 TeX>
  ```

**原因分析**：
<初步判断是哪个解析环节的问题>

**临时修复**：
<本次为绕过问题做的临时处理>

**改进建议**：
<长期改进方向，供脚本作者参考>
```

**问题类型示例**：
- 题号识别失败（导致题目合并或断裂）
- 选项解析错误（单行选项未展开、选项内容截断）
- 元信息提取错位（答案/难度/知识点对应到错误题目）
- `【分析】`内容混入 `\explain{}`
- 数学公式处理问题（双重包裹、转义错误）
- 环境未闭合（`\begin{question}` 没有对应 `\end{question}`）
- 图片标记识别失败或格式不统一

---

## 三、v3.3 调试与质量保证流程

### 3.1 预编译检查流程（推荐）

**何时使用**：在任何 LaTeX 编译之前

```bash
# 方式1：集成到编译命令（推荐）
VALIDATE_BEFORE_BUILD=1 ./build.sh exam teacher

# 方式2：单独运行检查
python3 tools/validate_tex.py content/exams/auto/<slug>/converted_exam.tex
```

**检查内容**：

- ✅ `\explain{}` 中的空行（Runaway argument 主要根因）
- ✅ 花括号配对 `{}`（智能忽略数学定界符）
- ✅ 数学定界符配对 `\(...\)` 和 `\[...\]`
- ✅ 🆕 v1.8.8：反向定界符检测 `\)...\(`（记录日志）
- ✅ 🆕 v1.8.8：重复 meta 命令检测（`\answer`, `\explain`, `\topics`, `\difficulty`）
- ✅ 环境平衡 `\begin{question}` vs `\end{question}`
- ✅ 题干缺失检测（题目直接从 `\item` 开始）
- ✅ `\left`/`\right` 配对检测
- ✅ enumerate 环境结构检查

**处理建议**：

- 如果显示警告，优先修复后再编译
- 反向定界符和 meta 重复会记录到 `word_to_tex/output/debug/` 日志
- `\explain` 空行是最常见的编译错误，必须修复

### 3.2 ocr_to_examx.py 自动修复功能（v1.8.8/v1.8.9）

**新增自动修复**：

1. **反向定界符修复**（v1.8.8）：
   - 检测：`\) <标点/空白> \(` 模式
   - 修复：仅当中间只有空白和常见标点时，自动反转为 `\( <标点/空白> \)`
   - 日志：所有反向定界符案例记录到 `{slug}_reversed_delimiters.log`

2. **方程组 \left\{ 补全**（v1.8.9）：
   - 检测：`\begin{array}` 或 `\begin{cases}` 配合 `\right.` 但缺少 `\left\{`
   - 修复：在 `\begin{array}/\begin{cases}` 前插入 `\left\{`
   - 条件：前 50 个字符内无 `\left` 或 `\{`
   - 效果：避免 left/right 不平衡导致的降级处理

3. **Meta 重复检测**（v1.8.8）：
   - 检测：同一题目中多次出现 `\answer`, `\explain`, `\topics`, `\difficulty`
   - 日志：记录到 `{slug}_meta_duplicates.log`
   - 行为：不修改输出，仅记录供人工审查

**查看日志**：

```bash
ls -lh word_to_tex/output/debug/{slug}_*.log
cat word_to_tex/output/debug/{slug}_reversed_delimiters.log
cat word_to_tex/output/debug/{slug}_meta_duplicates.log
```

### 3.3 数学处理完整性检查（v1.8）

**何时使用**：转换完成后验证数学内容质量

**方式1：A/B 对比测试**（推荐）

```bash
cd tools/testing
python3 math_sm_comparison.py ../../word_to_tex/output/<exam>_preprocessed.md
```

**检查指标**：

- **定界符平衡**：`\(` 与 `\)` 数量差异（目标 = 0）
- **裸 $ 符号**：未转换的 dollar 符号数量（目标 = 0）
- **文件大小**：状态机 vs 旧管线大小对比
- **截断片段**：疑似不完整的数学片段样本

**WARNING 标记**：

- ⚠️ `balance_diff != 0`：仍有括号不平衡
- ⚠️ `truncation detected`：发现疑似截断片段
- ⚠️ `stray dollars > 0`：存在裸 $ 符号

**方式2：直接查看问题日志**

```bash
cat content/exams/auto/<slug>/debug/<slug>_issues.log
```

**日志内容**：

- 数学完整性报告（balance_diff, stray $, truncation samples）
- 元信息一致性警告
- 题干缺失警告
- 【分析】过滤警告

---

### 3.4 编译错误诊断流程

当 PDF 编译失败时，按以下步骤诊断：

#### Step 1：查看智能错误摘要

build.sh 自动显示错误类型、位置、原因和修复建议。

#### Step 2：查看详细错误日志

```bash
cat output/last_error.log
# 或使用错误定位工具（更友好）
tools/locate_error.sh output/.aux/wrap-exam-teacher.log
```

#### Step 3：定位问题代码

locate_error.sh 会显示：
- 错误类型
- 文件路径和行号
- 前后 5 行上下文
- 常见原因和修复建议

#### Step 4：修复问题

**常见问题类型及修复方法**：

| 错误类型 | 常见原因 | 修复方法 |
|---------|---------|---------|
| Runaway argument | `\explain{}` 中有空行 | 删除空行或用 `%` 注释 |
| Missing $ inserted | 数学模式定界符不匹配 | 检查 `\(...\)` 配对 |
| Undefined control sequence | 拼写错误或缺少宏包 | 检查命令名称 |
| Environment unbalanced | `\begin{question}` 缺少 `\end{question}` | 补充缺失的环境结束标记 |
| Unmatched brace | 花括号不配对 | 检查 `{...}` 是否完整 |

**修复优先级**：
1. 🔴 先修复 TeX 文件中的明显语法错误
2. 🟡 如果是 ocr_to_examx.py 解析问题，修改脚本并重新生成
3. 🟢 最后才考虑修改项目公共配置（preamble.sty 等）

#### Step 5：重新编译验证

```bash
VALIDATE_BEFORE_BUILD=1 ./build.sh exam teacher
```

### 3.5 核心功能自测（v1.8.8/v1.8.9）

**何时使用**：修改 `ocr_to_examx.py` 后、提交代码前

**运行自测**：

```bash
python3 tools/core/ocr_to_examx.py --selftest
```

**测试覆盖**（12项）：

1. 【分析】段过滤
2. 【详解】保留到 `\explain{}`
3. `*$x$*` 模式修复
4. 全角括号统一
5. 空 `$$` 清理
6. 内联图片处理（旧版）
7. IMAGE_TODO_START/END 占位块
8. 🆕 反向定界符简单修复（v1.8.8）
9. 🆕 Meta 重复检测（v1.8.8）
10. 🆕 array 环境 `\left\{` 补全（v1.8.9）
11. 🆕 cases 环境 `\left\{` 补全（v1.8.9）
12. 🆕 已有 `\left` 不重复补全（v1.8.9）

**期望结果**：

```
✅ 所有测试通过！
```

**失败处理**：

- 查看失败的具体测试项
- 检查相关函数逻辑：`fix_simple_reversed_inline_pairs()`, `_fix_array_left_braces()`, `build_question_tex()`
- 修复后重新运行 `--selftest`

### 3.6 编译回归测试流程

**何时使用**：修改了核心脚本或配置文件、准备提交代码前

**运行测试**：`tools/test_compile.sh`

**测试覆盖**：exam/handout × teacher/student（4种组合）

**失败处理**：查看错误摘要 → 使用 locate_error.sh 定位 → 修复后重测

### 3.7 快速转换与校验（开发/调试）

**工具**：`tools/run_pipeline.py`

**何时使用**：开发调试阶段，快速验证 Markdown → TeX 转换结果

**基本用法**：

```bash
# 转换 + 校验（默认）
python3 tools/run_pipeline.py input.md --slug exam-2025

# 只转换，不校验
python3 tools/run_pipeline.py input.md --slug exam-2025 --no-validate

# 指定输出路径
python3 tools/run_pipeline.py input.md --slug exam-2025 --out-tex output/result.tex

# 自定义标题
python3 tools/run_pipeline.py input.md --slug exam-2025 --title "2025年期末试卷"
```

**退出码**：
- `0`：成功（转换成功 + 校验通过，或仅转换成功）
- `1`：转换失败
- `2`：转换成功但校验失败

**优势**：
- ✅ 一条命令完成转换和校验
- ✅ 适合 CI/CD 集成
- ✅ 清晰的退出码便于脚本判断
- ✅ 无需手动运行两个工具

### 3.8 完整工作流验证

**使用**：`tools/workflow_validate.sh content/exams/auto/<slug>/converted_exam.tex`

**验证步骤**：文件检查 → 预编译 → 教师版/学生版编译 → PDF 验证

**成功标准**：所有步骤✅、PDF可打开、文件大小合理（>50KB）

---

## 四、操作步骤（推荐流程）

### 方式A：使用 preprocess_docx.sh（推荐）

**适用场景**：标准流程，最小化手动操作

```bash
# 步骤1：准备输入文件
# 将 Word 文件放到 word_to_tex/input/ 目录

# 步骤2：一键转换
word_to_tex/scripts/preprocess_docx.sh \
    "word_to_tex/input/<文件名>.docx" \
    "<输出前缀>" \
    "<试卷标题>"

# 步骤3：处理图片（如果有）
python tools/images/process_images_to_tikz.py \
    --mode include \
    --files "content/exams/auto/<输出前缀>/converted_exam.tex"

# 步骤4：编译
# 1) 确认 settings/metadata.tex 中 \examSourceFile 已指向生成的文件
# 2) 运行编译
./build.sh exam teacher

# 步骤5：检查结果
# PDF 位于 output/wrap-exam-teacher.pdf
# 如有错误，查看 output/last_error.log
```

### 方式B：分步执行（用于调试或特殊情况）

#### Step 1：Word → Markdown
```bash
pandoc "word_to_tex/input/<文件名>.docx" \
  -o "word_to_tex/output/<前缀>_raw.md" \
  --extract-media="word_to_tex/output/figures"
```

**检查点**：
- 题号格式：`1.` / `1．` / `1、`
- 选项格式：`A．` / `A.` 等
- 元信息是否在独立行：`【答案】`、`【难度】`、`【知识点】`、`【详解】`、`【分析】`

**轻微修正**（如需要）：
- 统一题号格式
- 修正元信息标记的空格
- **不要**大规模重写内容

#### Step 2：Markdown → examx TeX
```bash
python3 tools/core/ocr_to_examx.py \
    "word_to_tex/output/<前缀>_raw.md" \
    "content/exams/auto/<前缀>/converted_exam.tex" \
    --title "<试卷标题>"
```

**检查点**：
- ✅ 结构正确：`\section{单选题}` → `\begin{question}` ... `\end{question}`
- ✅ 元信息正确：`\topics{}`、`\difficulty{}`、`\answer{}`、`\explain{}`
- ⚠️ **关键检查**：搜索"分析"二字，确保`【分析】`内容未出现在 TeX 中
- ✅ 数学公式：`\(...\)` 或 `\[...\]`，无双重包裹
- ✅ 选项格式：`\begin{choices}` → `\item` （每个选项单独一行）

**如发现【分析】内容混入**：
1. 检查 `ocr_to_examx.py` 中的元信息解析逻辑
2. 确认 `META_PATTERNS` 中 `"analysis"` 的正则正确
3. 确认 `parse_question_structure()` 不会将`【分析】`内容加入 `\explain{}`
4. 修改后重新运行脚本
5. **记录到"OCR 脚本问题清单"**

#### Step 3：图片处理
```bash
# 方式1：简单替换为 \includegraphics（推荐用于快速验证）
python tools/images/process_images_to_tikz.py \
    --mode include \
    --files "content/exams/auto/<前缀>/converted_exam.tex"

# 方式2：生成 TikZ 模板（用于后续手工绘制）
python tools/images/process_images_to_tikz.py \
    --mode template \
    --files "content/exams/auto/<前缀>/converted_exam.tex"

# 方式3：仅转换 WMF 为 PNG
python tools/images/process_images_to_tikz.py \
    --mode convert \
    --files "content/exams/auto/<前缀>/converted_exam.tex"
```

**检查点**：
- 所有 `% IMAGE_TODO:` 标记已被处理
- WMF 图片已转换为 PNG（位于 `word_to_tex/output/figures/png/`）
- TikZ 占位符语法正确（至少不导致编译失败）

**手动绘制一张图**（可选但推荐）：
- 选择一张简单的图（如坐标轴、几何图形）
- 编写基本 TikZ 代码替换占位符
- 证明 TikZ 路径可行

#### Step 4：编译 PDF
```bash
# 1. 备份 metadata.tex
cp settings/metadata.tex settings/metadata.tex.bak

# 2. 修改 metadata.tex
# 将 \newcommand{\examSourceFile}{...} 改为：
# \newcommand{\examSourceFile}{content/exams/auto/<前缀>/converted_exam.tex}

# 3. 编译
./build.sh exam teacher

# 4. 恢复 metadata.tex（如需要）
mv settings/metadata.tex.bak settings/metadata.tex
```

**编译失败处理**：
1. 查看终端输出的错误摘要
2. 检查 `output/last_error.log` 获取详细错误
3. 定位错误类型：
   - 结构错误（环境未闭合）→ 检查 `\begin{}` / `\end{}`
   - 数学公式错误 → 检查 `\(...\)` / `\[...\]`
   - TikZ 错误 → 简化或临时注释掉问题图
   - 未定义引用（`LastPage`）→ build.sh 会自动处理
4. **如果问题源于 ocr_to_examx.py**，记录到问题清单
5. 做最小修改后重新编译

**修改优先级**：
1. 修正 TeX 文件中的明显语法错误
2. 如是脚本解析问题，修改 `ocr_to_examx.py` 并重新生成
3. 最后才考虑修改项目公共配置（`preamble.sty` 等）

---

## 五、验证标准

### 5.1 TeX 结构验证
```latex
\examxtitle{试卷标题}

\section{单选题}

\begin{question}
题干内容……
\begin{choices}
  \item A 选项
  \item B 选项
  \item C 选项
  \item D 选项
\end{choices}
\topics{知识点1；知识点2}
\difficulty{0.85}
\answer{A}
\explain{
  这里的内容必须全部来自【详解】，
  不能包含【分析】的内容。
}
\end{question}
```

### 5.2 关键检查项
- [ ] PDF 成功生成且可打开
- [ ] 题目结构完整（题干、选项、答案、解析）
- [ ] 元信息正确对应
- [ ] **TeX 和 PDF 中完全没有"【分析】"字样或其内容**
- [ ] 数学公式渲染正确
- [ ] 至少一张图片正确显示（TikZ 或 includegraphics）

## 六、输出要求

### 6.1 执行记录
简短记录（Markdown 格式）：

```markdown
## 执行记录

**输入文件**：`word_to_tex/input/<文件名>.docx`

**关键命令**：
1. Pandoc 转换：
   ```bash
   <实际命令>
   ```
2. TeX 生成：
   ```bash
   <实际命令>
   ```
3. 图片处理：
   ```bash
   <实际命令>
   ```
4. 编译：
   ```bash
   <实际命令>
   ```

**中途修改**：
- 修改点1：<描述>
- 修改点2：<描述>

**最终结果**：
- ✅ PDF 生成成功：`output/wrap-exam-teacher.pdf`
- 题目数量：X 道
- 图片数量：Y 个
```

### 5.2 OCR 脚本问题清单
详细记录所有发现的问题（使用第二章格式）。

**最低要求**：
- 至少记录 3 个实际遇到的问题
- 每个问题包含完整的五要素（现象、定位、分析、修复、建议）
- 优先记录与`【分析】/【详解】`解析相关的问题

## 七、常见问题与解决方案

### Q1：Pandoc 输出的 Markdown 格式异常
**现象**：题号、选项格式不符合预期  
**解决**：
- 检查 Word 文档的原始格式（是否使用了特殊样式）
- 尝试在 Word 中另存为更标准的格式
- 手动调整 Markdown 中的格式标记

### Q2：ocr_to_examx.py 运行失败
**现象**：脚本报错或输出为空  
**解决**：
- 检查输入路径是否正确
- 确认 Markdown 文件编码为 UTF-8
- 查看脚本输出的详细错误信息
- 检查 Python 版本（需要 3.6+）

### Q3：【分析】内容混入 \explain{}
**现象**：生成的 TeX 中 `\explain{}` 包含`【分析】`的内容  
**解决**：
1. 定位问题题目的原始 Markdown
2. 检查 `ocr_to_examx.py` 中 `META_PATTERNS` 的 `"analysis"` 正则
3. 检查 `parse_question_structure()` 中处理`【分析】`的逻辑
4. 确保`【分析】`被识别但不写入任何输出
5. 重新运行脚本并验证

### Q4：图片占位符无法识别
**现象**：`process_images_to_tikz.py` 找不到 `IMAGE_TODO`  
**解决**：
- 检查 TeX 中图片标记格式：`% IMAGE_TODO: <路径> (width=XX%)`
- 确认路径中的下划线是否被转义为 `\_`
- 查看 `ocr_to_examx.py` 中图片标记的生成逻辑

### Q5：编译时 LastPage 未定义
**现象**：`Reference 'LastPage' on page X undefined`  
**解决**：
- 这是正常的首次编译警告
- build.sh v2.0 会自动使用 `-f` 强制完成编译
- 如果仍然失败，手动运行第二次编译

### Q6：数学公式双重包裹
**现象**：`$$\(...\)$$` 或类似嵌套  
**解决**：
- 检查 `ocr_to_examx.py` v1.5 的 `fix_double_wrapped_math()` 是否生效
- 手动搜索并替换：`$$\(...\)$$` → `\(...\)`
- 记录到问题清单供脚本作者改进

## 八、成功标准（v3.0 严格版）

完成以下所有项即视为测试成功：

**文本与结构（阶段一）**：
- [ ] PDF 文件成功生成并可正常打开
- [ ] PDF 中所有题目结构完整
- [ ] 所有元信息（答案、难度、知识点、解析）正确显示
- [ ] **TeX 源文件和 PDF 中完全不包含`【分析】`及其内容**
- [ ] `\explain{}` 中的内容全部来自`【详解】`
- [ ] 预编译检查通过（或仅有非致命警告）
- [ ] 回归测试全部通过（test_compile.sh）

**图片处理（阶段二）**：
- [ ] 所有图片都有对应的 IMAGE_TODO_START/END 块
- [ ] image_jobs.jsonl 包含所有图片的完整元信息
- [ ] 至少一张图片成功转换为 TikZ 或 includegraphics
- [ ] TikZ 图片渲染正确且符合数学语义

**质量保证（v3.0 新增）**：
- [ ] 问题日志完整生成（debug/<slug>_issues.log）
- [ ] 问题日志包含 meta summary
- [ ] ocr_to_examx.py 自测通过（--selftest）
- [ ] 产出完整的"OCR 脚本问题清单"（至少 3 个问题）
- [ ] 执行记录清晰完整

**编译健壮性**：
- [ ] 教师版和学生版都能成功编译
- [ ] PDF 文件大小合理（通常 >50KB）
- [ ] 没有致命的 LaTeX 错误
- [ ] LastPage 等引用警告已自动处理

---

## 九、最佳实践与提示

### 8.1 开发流程建议

1. **先保证文本流水线稳定**
   - 完成 Word → Markdown → TeX → PDF 全流程
   - 确保所有题目、答案、解析正确
   - 验证【分析】过滤完全生效
   
2. **再引入图片流水线**
   - 先用 includegraphics 快速验证图片位置
   - 再逐步替换为 TikZ
   - 优先绘制简单图形（坐标轴、几何图形）
   
3. **持续验证质量**
   - 每次修改 ocr_to_examx.py 后运行 --selftest
   - 每次修改构建脚本后运行 test_compile.sh
   - 使用 VALIDATE_BEFORE_BUILD=1 作为默认编译方式

### 8.2 调试技巧

**快速诊断命令**：
```bash
# 预检查 + 错误过滤
VALIDATE_BEFORE_BUILD=1 ./build.sh exam teacher 2>&1 | grep -A 5 "Found.*error"

# 详细错误定位
tools/locate_error.sh output/.aux/wrap-exam-teacher.log

# 检查问题日志
cat word_to_tex/output/debug/*_issues.log | grep "CRITICAL\|ERROR"
```

**常见检查**：explain 空行、【分析】残留、括号配对、题目统计（参见 KNOWN_ISSUES.md）

### 8.3 版本控制建议

**提交前检查清单**：
```bash
# 1. 运行自测
python3 tools/core/ocr_to_examx.py --selftest

# 2. 运行回归测试
tools/test_compile.sh

# 3. 验证示例文件
tools/workflow_validate.sh content/exams/auto/<slug>/converted_exam.tex

# 4. 检查问题日志
ls -lh word_to_tex/output/debug/*.log
```

**Git 提交规范**：
```bash
# 功能改进
git commit -m "feat(ocr): 增强 meta 自检和【分析】过滤"

# Bug 修复
git commit -m "fix(build): 修复 BSD grep 兼容性问题"

# 文档更新
git commit -m "docs(workflow): 更新 v3.0 调试流程说明"

# 测试用例
git commit -m "test(validate): 添加 explain 空行检测测试"
```

### 8.4 性能优化

**加速编译**：
```bash
# 跳过预检查（仅当确信 TeX 无误时）
./build.sh exam teacher

# 并行编译多个版本
./build.sh exam both  # 教师版和学生版同时生成
```

**减少问题日志大小**：
- 修复高频问题（如公式格式）
- 在 ocr_to_examx.py 中调整 issue 阈值
- 定期清理 debug/ 目录

### 8.5 团队协作

**角色分工**：
1. **OCR 工程师**：维护 ocr_to_examx.py，处理文本解析问题
2. **TikZ 绘图师**：根据 image_jobs.jsonl 绘制 TikZ 图形
3. **测试工程师**：运行回归测试，记录问题清单
4. **流程集成师**：优化 build.sh 和工作流脚本

**文档维护**：
- 每次发现新问题类型，更新"常见问题"章节
- 每次优化脚本，更新"工具说明"章节
- 每个版本发布，更新"更新日志"

### 9.9 附录速查

**常用路径**：
```
输入文件：word_to_tex/input/<文件名>.docx
输出 Markdown：word_to_tex/output/<前缀>_raw.md
生成 TeX：content/exams/auto/<前缀>/converted_exam.tex
图片目录：word_to_tex/output/figures/
编译配置：settings/metadata.tex
最终 PDF：output/wrap-exam-teacher.pdf
错误日志：output/last_error.log
构建日志：output/build.log
```

**关键脚本位置**：

```text
转换脚本：tools/core/ocr_to_examx.py
图片处理（历史）：tools/images/process_images_to_tikz.py
图片任务导出（新）：tools/images/export_image_jobs.py
TikZ 回填（新）：tools/images/apply_tikz_snippets.py
完整流程：word_to_tex/scripts/preprocess_docx.sh
编译脚本：./build.sh
```

### 元信息标记参考

```markdown
【答案】A
【难度】0.85
【知识点】函数的性质；导数的应用
【考点】函数的单调性；极值点
【分析】根据题意可知…… （⚠️ 此部分必须丢弃）
【详解】由题可得…… （✅ 此部分写入 \explain{}）
```

### 图片占位符示例

```tex
% IMAGE_TODO_START id=nanjing2026-Q3-img1 path=word_to_tex/output/figures/media/image1.png width=60% inline=false question_index=3 sub_index=1
% CONTEXT_BEFORE: 已知函数 f(x) 在区间 [0,1] 上单调递增，其图像如下所示：
% CONTEXT_AFTER: 则下列结论中正确的是（    ）。
\begin{tikzpicture}
  % TODO: AI_AGENT_REPLACE_ME (id=nanjing2026-Q3-img1)
\end{tikzpicture}
% IMAGE_TODO_END id=nanjing2026-Q3-img1
```

---

**最后提醒**：

1. **【详解】是 \explain{} 唯一来源**
2. 每次遇到 ocr_to_examx.py 导致的问题都要详细记录
3. 优先使用 `preprocess_docx.sh` 简化流程
4. 编译失败时先查看 `output/last_error.log`
5. 问题清单的质量比数量更重要

**祝测试顺利！🚀**

---

## 十、阶段二：图片 → TikZ 自动化流水线

这一部分是新增内容，用于指导 Agent 逐步改造图片处理流程。

### 9.1 图片子流水线概览

```text
[DOCX/Word]
    │
    ▼
[Pandoc] → Markdown + media/*.wmf/png
    │
    ▼
[ocr_to_examx.py]
    ├─ 解析题干/选项/答案等文本
    └─ 所有图片 → IMAGE_TODO_START/END 占位（带 id/path/width/inline/question_index）
        ↓
   converted_exam.tex
        │
        ├──────────────┐
        │              │
        ▼              ▼
[export_image_jobs.py]   （可先编译一次, 图为空）
    │
    ▼
image_jobs.jsonl  +  media/*.png
  （包含 exam_prefix, exam_dir, tikz_snippets_dir 等字段，详见 IMAGE_JOBS_FORMAT.md）
    │
    ▼
[AI Agent]
(读取 image_jobs + 图片)
(生成 TikZ 环境，输出 id + tikz_code)
    │
    ▼
generated_tikz.jsonl
    │
    ▼
[write_snippets_from_jsonl.py / utils.write_tikz_snippet]
    │
    ▼
content/exams/auto/<exam_prefix>/tikz_snippets/{id}.tex
  （由 utils.get_tikz_snippets_dir 统一推断，不允许硬编码目录）
    │
    ▼
[apply_tikz_snippets.py]
  （默认使用 tex_file 所在目录的 tikz_snippets）
    │
    ▼
converted_exam_tikz.tex
    │
    ▼
[pdflatex / build.sh]
    │
    ▼
最终试卷 PDF（全部为 TikZ 图）
```

### 9.2 IMAGE_TODO_START/END 注释格式规范

#### 基本格式

每张图片在 TeX 中必须被包装成如下结构（示例）：

```tex
\begin{center}
% IMAGE_TODO_START id=nanjing2026-Q3-img1 path=word_to_tex/output/figures/media/image1.png width=60% inline=false question_index=3 sub_index=1
% CONTEXT_BEFORE: 已知函数 f(x) 在区间 [0,1] 上单调递增，其图像如下所示：
% CONTEXT_AFTER: 则下列结论中正确的是（    ）。
\begin{tikzpicture}
  % TODO: AI_AGENT_REPLACE_ME (id=nanjing2026-Q3-img1)
\end{tikzpicture}
% IMAGE_TODO_END id=nanjing2026-Q3-img1
\end{center}
```

#### 字段含义

- **`id`**（必选）：**全局唯一**图片 ID  
  建议命名：`<slug>-Q<题号>-img<序号>`，例如：`nanjing2026-Q3-img1`

- **`path`**（必选）：原始图片文件的相对路径  
  一般来自 Pandoc 导出的 `media/*.wmf` / `*.png`。后续流水线会基于这个路径加载图片供 AI 识别。

- **`width`**（必选）：推荐宽度百分比，例如 `60%`  
  可以从 Markdown 中 `{width=60%}` 提取，没有则默认 `60%`

- **`inline`**（必选）：此图片是否来自行内位置  
  行内图片：`inline=true`；独立成行图片：`inline=false`

- **`question_index`**（建议）：题号（整数）

- **`sub_index`**（建议）：小问序号或该题下图片序号（从 1 开始）

- **`CONTEXT_BEFORE` / `CONTEXT_AFTER`**（可选但推荐）：  
  分别是一行简短的题干上下文，用来帮助 AI 理解图像用途

> **注意**：即使后续填入了真实 TikZ 代码，`IMAGE_TODO_START/END` 注释也建议保留不删，以便后续重新导出或替换图片。

### 9.3 `image_jobs.jsonl` 字段定义（schema）

#### JSONL 单行示例

> **完整字段说明与推断规则详见：[IMAGE_JOBS_FULL.md](IMAGE_JOBS_FULL.md)**

每一行是一个 JSON 对象，代表一个图片任务（image_job）。以下为简化示例（实际导出包含更多字段）：

```json
{
  "id": "nanjing_2026_sep-Q3-img1",
  "exam_slug": "nanjing_2026_sep",
  "exam_prefix": "nanjing_2026_sep",
  "exam_dir": "content/exams/auto/nanjing_2026_sep",
  "tikz_snippets_dir": "content/exams/auto/nanjing_2026_sep/tikz_snippets",
  "tex_file": "content/exams/auto/nanjing_2026_sep/converted_exam.tex",
  "question_index": 3,
  "sub_index": 1,
  "path": "word_to_tex/output/figures/media/image1.png",
  "width_pct": 60,
  "inline": false,
  "context_before": "已知函数 f(x) 在区间 [0,1] 上单调递增，其图像如下所示：",
  "context_after": "则下列结论中正确的是（    ）。",
  "todo_block_start_line": 241,
  "todo_block_end_line": 250
}
```

**关键字段**：
- `exam_prefix` / `exam_dir` / `tikz_snippets_dir`：由 `export_image_jobs.py` 自动推断并填充，确保下游 Agent 可直接使用。
- 完整字段说明、目录推断逻辑（唯一真理）、使用示例请参阅 **[IMAGE_JOBS_FULL.md](IMAGE_JOBS_FULL.md)**。

#### 字段说明

- **`id`** *(string, required)*  
  与 TeX 中 `IMAGE_TODO_START` 的 `id` 完全一致，唯一标识一张图片

- **`exam_slug`** *(string, required)*  
  试卷 slug，例如 `nanjing2026`。可由 `tex_file` 路径或 `id` 前缀推断

- **`tex_file`** *(string, required)*  
  源 TeX 文件相对路径，例如 `content/exams/auto/nanjing2026/converted_exam.tex`

- **`question_index`** *(integer, optional)*  
  题号（如第 3 题）

- **`sub_index`** *(integer, optional)*  
  该题中的小问编号或图片序号，从 1 开始

- **`path`** *(string, required)*  
  图片文件路径，与 `IMAGE_TODO_START` 中的 path 一致

- **`width_pct`** *(integer, required)*  
  推荐宽度百分比，去掉 `%`，例如 `60`

- **`inline`** *(boolean, required)*  
  图片是否来自行内位置：`true` / `false`

- **`context_before` / `context_after`** *(string, optional)*  
  来自 `CONTEXT_BEFORE` / `CONTEXT_AFTER` 注释，一般是一两句题干文字

- **`todo_block_start_line` / `todo_block_end_line`** *(integer, optional)*  
  对应 TeX 文件中 `IMAGE_TODO_START` / `IMAGE_TODO_END` 行号（1-based），用于快速定位和替换

> **推荐**：允许未来新增字段，但尽量不要删除上述字段，便于流水线演进。

### 9.4 给 AI 画 TikZ 的标准系统 Prompt 模板

> 完整 Prompt 模板参见：**[TIKZ_AGENT_PROMPT.md](TIKZ_AGENT_PROMPT.md)**

**核心要求**：

1. **输入**：image_job JSON 对象 + 对应图片
2. **输出**：纯 TikZ 代码（`\begin{tikzpicture}...\end{tikzpicture}`）
3. **风格**：使用标准 tikz/pgfplots，避免中文标签，优先数学语义正确
4. **鲁棒性**：复杂图可适当简化，禁止输出空 tikzpicture

### 9.5 给代码 Agent 的开发任务（可直接复制当成子任务）

#### 任务 A：改造 `ocr_to_examx.py`，输出统一的 IMAGE_TODO_START/END

> 按照上文第 9.2 节的格式规范，修改 `tools/core/ocr_to_examx.py`：
>
> 1. 所有 Markdown 图片（独立行 + 内联）都在 Markdown→TeX 阶段转换为带 `id/path/width/inline/question_index/sub_index` 的 `IMAGE_TODO_START/END` 占位块
> 2. 内联图片在文本中用占位符替换，并在生成 TeX 时展开为对应的 IMAGE_TODO 块
> 3. `id` 统一命名为 `<slug>-Q<题号>-img<序号>`
> 4. 在 `run_self_tests()` 中新增测试用例，覆盖"同时存在行内/独立图片"的情况，确保 TeX 中不再出现 `![](...)` 这样的 Markdown 图片语法

#### 任务 B：新增 `export_image_jobs.py` 生成 `image_jobs.jsonl`

> 按照上文第 9.3 节的 schema，在 `tools/images/export_image_jobs.py` 中实现：
>
> 1. 从一个或多个 `converted_exam.tex` 中解析所有 `IMAGE_TODO_START/END`
> 2. 生成 `image_jobs.jsonl`，每个 IMAGE_TODO 对应一行 JSON
> 3. 支持命令行参数：
>    - `--files` 指定一个或多个 TeX 文件
>    - `--output` 指定 jsonl 输出路径
> 4. 对字段缺失/格式错误的 IMAGE_TODO，要打印警告并跳过，而不是崩溃

#### 任务 C：新增 `apply_tikz_snippets.py` 回填 TikZ

> 该脚本已完成实现，功能说明如下：

**输入**：
- `--tex-file`：待回填的 TeX 文件（例如 `converted_exam.tex`）
- `--snippets-dir`（可选）：TikZ 片段目录；若未提供，默认使用 `tex_file` 所在目录的 `tikz_snippets` 子目录。
- `--output`（可选）：输出文件路径；若未提供，覆盖原文件（会自动备份为 `.tex.bak`）。

**使用示例**：

```bash
# 默认用 tex 所在目录的 tikz_snippets
python tools/images/apply_tikz_snippets.py \
    --tex-file content/exams/auto/nanjing_2026_sep/converted_exam.tex

# 也可以显式指定 snippets 目录（覆盖默认值）
python tools/images/apply_tikz_snippets.py \
    --tex-file content/exams/auto/nanjing_2026_sep/converted_exam.tex \
    --snippets-dir content/exams/auto/nanjing_2026_sep/tikz_snippets \
    --output content/exams/auto/nanjing_2026_sep/converted_exam_tikz.tex
```

**运行时输出**：
- 打印实际使用的 snippets 目录（绝对路径）：
  ```
  Snippets 目录: /full/path/to/content/exams/auto/nanjing_2026_sep/tikz_snippets
  ```
- 列出缺少 snippet 的图片 id（若存在）。
- 统计信息：总 TODO 数量、成功替换、跳过（缺失 snippet）。

#### 任务 D（新增）：使用 `write_snippets_from_jsonl.py` 落地 TikZ

> **作用**：读取 AI 生成的 `tikz_code` 并统一写入规范目录。

该脚本已实现，负责衔接 AI 生成的 TikZ 与文件系统写入。

**输入**：
- `--jobs-file`：`export_image_jobs.py` 生成的 `image_jobs.jsonl`（包含目录推断所需字段）
- `--tikz-file`：AI 输出的 `generated_tikz.jsonl`（每行包含 `{"id": "...", "tikz_code": "..."}`）
- `--dry-run`（可选）：仅预览写入计划，不实际创建文件
- `--snippets-dir`（可选）：强制所有 snippet 写入该目录（调试用，正常情况下不要提供）

**使用示例**：

```bash
# 实际写入（推荐）
python3 tools/images/write_snippets_from_jsonl.py \
  --jobs-file content/exams/auto/nanjing_2026_sep/image_jobs.jsonl \
  --tikz-file generated_tikz.jsonl

# 预览模式（dry-run）
python3 tools/images/write_snippets_from_jsonl.py \
  --jobs-file content/exams/auto/nanjing_2026_sep/image_jobs.jsonl \
  --tikz-file generated_tikz.jsonl \
  --dry-run
```

**日志格式示例**：

```text
[TikZ] write snippet: id=nanjing_2026_sep-Q8-img1  ->  content/exams/auto/nanjing_2026_sep/tikz_snippets/nanjing_2026_sep-Q8-img1.tex
[TikZ] write snippet: id=nanjing_2026_sep-Q14-img1  ->  content/exams/auto/nanjing_2026_sep/tikz_snippets/nanjing_2026_sep-Q14-img1.tex
...

结果：
  ✓ 成功写入: 5
  ✗ 写入错误: 0
  ☐ 缺少 tikz_code: 0
```

**设计要点**：
- 每条 job 的目标目录由 `utils.get_tikz_snippets_dir(job)` 推断（唯一真理）。
- 对缺失 `tikz_code` 的 id 不会写入，仅统计与警告。
- 支持 `--dry-run` 方便预检查路径。

**AI Agent 使用场景**：

如果 Agent 可以直接 import 仓库代码，建议调用：

```python
from pathlib import Path
import json
from tools.images.utils import get_tikz_snippets_dir, write_tikz_snippet_to_dir

jobs = [json.loads(line) for line in Path("image_jobs.jsonl").read_text().splitlines() if line.strip()]
for job in jobs:
    tikz_dir = get_tikz_snippets_dir(job)
    tikz_code = generate_tikz_for_image(job)  # AI 生成逻辑
    write_tikz_snippet_to_dir(job['id'], tikz_code, tikz_dir)
```

如果 Agent 无法 import，可输出 `generated_tikz.jsonl`，然后使用本脚本。

---

## 十一、阶段二测试流程建议

1. **先完成任务 A**：改造 `ocr_to_examx.py`，确保生成的 TeX 包含统一的 IMAGE_TODO 块
2. **运行一次完整转换**：从 Word → Markdown → TeX，检查 IMAGE_TODO 格式是否正确
3. **实现任务 B**：开发 `export_image_jobs.py`，从 TeX 导出 `image_jobs.jsonl`
4. **手工创建一两个 TikZ 片段**：在 `tikz_snippets/` 目录下创建测试文件
5. **实现任务 C**：开发 `apply_tikz_snippets.py`，测试 TikZ 回填功能
6. **集成测试**：运行完整流水线 Word → TeX → export → AI 生成 → apply → 编译 PDF
7. **记录问题**：将发现的所有问题补充到"OCR 脚本问题清单"

---

**阶段二最后提醒**：

1. 保证 IMAGE_TODO 格式的一致性和完整性
2. 阶段一先保证文本 & 结构流水线稳定，再逐步引入阶段二的图片 → TikZ 流水线
3. 对于每次改造（任务 A/B/C），都要在本地用一个小样本 Word 试卷跑完整条流程
4. 把发现的问题补充到"问题清单"里

**祝测试与重构顺利！🚀**

---

## 附录：版本历史

> **📖 完整版本历史**：详细更新日志、测试结果和性能指标请参阅 **[archive/CHANGELOG.md](archive/CHANGELOG.md)**  
> 以下为核心功能点速查（适合快速了解新特性）

### v3.5（2025-11-24）- 智能修复与回归测试增强

**🆕 核心更新**：

- **方程组 `\left\{` 智能补全**（v1.8.9）
  - 自动为 `\begin{array}` 和 `\begin{cases}` 补全缺失的 `\left\{`
  - 保守策略：检查 50 字符上下文，避免误补
  
- **反向定界符自动修复**（v1.8.8）
  - 检测 `\)...\(` 反向模式并记录日志
  - 简单场景（仅标点/空白）自动修复
  
- **Meta 命令重复检测**（v1.8.8）
  - 检测题内 `\answer`、`\explain` 等命令重复
  
- **回归测试扩展**
  - `run_self_tests()` 新增 5 个测试用例（总计 12 项）
  - 覆盖所有 v1.8.8/v1.8.9 新功能

**详细信息**：[CHANGELOG.md - v3.5](archive/CHANGELOG.md)

---

### v3.4（2025-11-21）- 精准数学定界符修复

**🔧 核心更新**：
- 数学定界符统计忽略注释（改善 67%）
- 检测反向数学定界符模式
- 极窄自动修复特定反向模式
- 收紧 `fix_right_boundary_errors` 行为（改善 83%）

**详细信息**：[CHANGELOG.md - v3.4](archive/CHANGELOG.md)

---

### v3.3（2025-11-20）- MathStateMachine 状态机

**🚀 重大升级**：
- 实现 MathStateMachine 状态机数学处理管线
- 完美数学定界符平衡（balance_diff = 0）
- 新增截断检测功能
- 添加 A/B 对比测试工具

**详细信息**：[CHANGELOG.md - v3.3](archive/CHANGELOG.md)

---

### v3.2（2025-11-19）- 表格美化环境

- 新增统一表格美化环境 `examtableboxed`（试卷带竖线）
- 新增 `examtable`（讲义 booktabs 风格）

---

### v3.1（2025-11-18）- ocr_to_examx.py v1.7

- 题干缺失检测
- 图片属性残留清理
- 小问编号格式统一
- IMAGE_TODO 块优化

---

### v3.0（2025-11-17）- 质量保证工具链

- 集成 meta 自检系统
- 新增预编译验证工具（`validate_tex.py`）
- 新增智能错误分析（`locate_error.sh`）
- 新增回归测试（`test_compile.sh`）

---

> **🔍 查看更早版本**：完整历史记录请参阅 [archive/CHANGELOG.md](archive/CHANGELOG.md)
