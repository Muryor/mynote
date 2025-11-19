# LaTeX 试卷流水线测试 Prompt

## 角色定位
你是一名**本地 LaTeX 试卷流水线工程师**，负责用一个示例 Word 试卷文件跑通整个流水线，并记录过程中发现的所有问题。

本项目分为两个阶段：

1. **阶段一**：原始文本 & 结构流水线（Word → Pandoc → Markdown → ocr_to_examx.py → TeX → PDF）
2. **阶段二**：图片 → TikZ 自动化流水线（IMAGE_TODO → image_jobs.jsonl → AI 画图 → 回填 TikZ）

---

## 流水线总览

### 总体数据流

```text
Word → Pandoc → Markdown
     → ocr_to_examx.py → examx TeX（含 IMAGE_TODO 占位）
     → export_image_jobs.py → image_jobs.jsonl
     → AI Agent（看图生成 TikZ） → tikz_snippets/{id}.tex
     → apply_tikz_snippets.py → examx TeX（已回填 TikZ）
     → build.sh → PDF
```

**图片处理脚本辅助使用**：
- `process_images_to_tikz.py`：用于 WMF→PNG 转换、批量检查、预览 IMAGE_TODO
- （可选）历史脚本 `generate_tikz_from_images.py` / `generate_tikz_placeholders.py` 将逐步被新流程替代

---

---

## 一、项目核心规范（文本 & 结构部分）

### 1.1 文件结构

```text
mynote/
├── tools/
│   ├── core/
│   │   └── ocr_to_examx.py       # Markdown → examx TeX
│   └── images/
│       ├── process_images_to_tikz.py     # 图片处理主工具
│       ├── export_image_jobs.py          # 新增：导出 image_jobs.jsonl
│       ├── apply_tikz_snippets.py        # 新增：回填 TikZ 片段
│       ├── generate_tikz_placeholders.py # 历史脚本（逐步替代）
│       └── generate_tikz_from_images.py  # 历史脚本（逐步替代）
├── word_to_tex/
│   ├── scripts/
│   │   └── preprocess_docx.sh    # 完整转换流程封装
│   ├── input/                     # 存放待转换的 DOCX
│   └── output/                    # 转换输出
├── content/exams/auto/            # 生成的试卷存放位置
│   └── <exam_slug>/
│       ├── converted_exam.tex     # 带 IMAGE_TODO 占位的 TeX
│       ├── image_jobs.jsonl       # 图片任务列表
│       └── tikz_snippets/         # AI 生成的 TikZ 片段
│           └── {id}.tex
├── settings/
│   └── metadata.tex               # 编译配置（指定试卷源）
├── build.sh                       # 编译脚本
└── output/                        # PDF 输出目录
```

### 1.2 关键工具说明

#### `ocr_to_examx.py`

**输入**：Pandoc 生成的 Markdown（含题号、选项、元信息标记）  
**输出**：examx 风格 TeX 文件（含 IMAGE_TODO 占位符）

**功能**：

- 按章节分类（单选题/多选题/填空题/解答题）
- 识别题号、题干、选项
- 解析元信息：`【答案】`、`【难度】`、`【知识点】`、`【详解】`
- 文本清洗：数学公式、中文标点、"故选"等
- **图片处理**：所有 Markdown 图片转换为 IMAGE_TODO_START/END 占位块
- 生成 examx 结构

**使用**：

```bash
python3 tools/core/ocr_to_examx.py <input.md或文件夹> <output目录或.tex>
```

**关键参数**：

- `input`：输入路径（.md 文件或包含 `*_local.md` 的文件夹）
- `output`：输出路径（目录或 .tex 文件）
- `--title`：试卷标题（可选，默认从输入路径推断）

#### `export_image_jobs.py`（新增）

**输入**：包含 IMAGE_TODO_START/END 的 TeX 文件  
**输出**：`image_jobs.jsonl`（图片任务列表）

**使用**：

```bash
python tools/images/export_image_jobs.py --files <tex文件> --output <jsonl路径>
```

#### `apply_tikz_snippets.py`（新增）

**输入**：TeX 文件 + tikz_snippets 目录  
**输出**：回填 TikZ 后的 TeX 文件

**使用**：

```bash
python tools/images/apply_tikz_snippets.py \
    --tex-file <tex文件> \
    --snippets-dir <tikz_snippets目录> \
    --output <输出文件>
```

#### `process_images_to_tikz.py`

**输入**：包含 `% IMAGE_TODO:` 标记的 TeX 文件  
**输出**：处理后的 TeX（包含 TikZ 代码或 `\includegraphics`）

**三种模式**：

```bash
# 模式1：转换WMF为PNG并使用\includegraphics（推荐用于快速验证）
python tools/images/process_images_to_tikz.py --mode include --files <tex文件>

# 模式2：生成TikZ模板供手工填充
python tools/images/process_images_to_tikz.py --mode template --files <tex文件>

# 模式3：仅转换WMF为PNG
python tools/images/process_images_to_tikz.py --mode convert --files <tex文件>
```

**注意**：

- WMF 转换需要系统安装 LibreOffice (`soffice`) 或 ImageMagick (`convert`)
- `--files` 可以指定多个文件或使用通配符
- 如果没有 `--files`，默认处理 `content/exams/auto/*/converted_exam.tex`
- **此工具将逐步被 export_image_jobs.py + apply_tikz_snippets.py 替代**

#### `preprocess_docx.sh`（推荐）

**完整流程封装**，自动执行 Pandoc → ocr_to_examx.py → agent_refine.py

**使用**：

```bash
word_to_tex/scripts/preprocess_docx.sh \
    <输入DOCX路径> \
    <输出前缀名> \
    <试卷标题>
```

**示例**：

```bash
word_to_tex/scripts/preprocess_docx.sh \
    "word_to_tex/input/江苏省南京市2026届高三上学期9月学情调研数学试题.docx" \
    "nanjing_2026_sep" \
    "江苏省南京市2026届高三上学期9月学情调研数学试题"
```

**输出**：

- `word_to_tex/output/<前缀>_raw.md` - Pandoc 原始输出
- `word_to_tex/output/<前缀>_preprocessed.md` - 预处理后的 Markdown
- `word_to_tex/output/<前缀>_examx.tex` - examx 风格 TeX
- `content/exams/auto/<前缀>/converted_exam.tex` - 精炼后的最终版本（含 IMAGE_TODO 占位）
- `word_to_tex/output/figures/` - 提取的图片（如果有）

### 1.3 元信息映射规则（⚠️ 核心规范）

| Markdown 标记 | examx 命令 | 处理规则 |
|--------------|-----------|---------|
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

### 1.4 编译规范

**步骤**：
1. 修改 `settings/metadata.tex`，设置：
   ```latex
   \newcommand{\examSourceFile}{content/exams/auto/<前缀>/converted_exam.tex}
   ```

2. 运行编译：
   ```bash
   ./build.sh exam teacher    # 生成教师版（含答案和解析）
   ./build.sh exam student    # 生成学生版（无答案）
   ./build.sh exam both       # 同时生成两个版本
   ```

3. 检查输出：
   - PDF 位于 `output/wrap-exam-teacher.pdf` 或 `output/wrap-exam-student.pdf`
   - 如果编译失败，查看 `output/last_error.log`
   - 日志保存在 `output/build.log`

**build.sh 特性**（v2.0 已改进）：

- ✅ 自动提取并显示错误上下文
- ✅ 智能区分真实错误和引用警告
- ✅ 自动清理失败的中间文件
- ✅ 对 `LastPage` 未定义等警告自动强制完成编译
- ✅ 保存错误摘要到 `output/last_error.log`

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

## 三、操作步骤（推荐流程）

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

## 四、验证标准

### 4.1 TeX 结构验证
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

### 4.2 关键检查项
- [ ] PDF 成功生成且可打开
- [ ] 题目结构完整（题干、选项、答案、解析）
- [ ] 元信息正确对应
- [ ] **TeX 和 PDF 中完全没有"【分析】"字样或其内容**
- [ ] 数学公式渲染正确
- [ ] 至少一张图片正确显示（TikZ 或 includegraphics）

## 五、输出要求

### 5.1 执行记录
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

## 六、常见问题与解决方案

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

## 七、成功标准

完成以下所有项即视为测试成功：

- [ ] PDF 文件成功生成并可正常打开
- [ ] PDF 中所有题目结构完整
- [ ] 所有元信息（答案、难度、知识点、解析）正确显示
- [ ] **TeX 源文件和 PDF 中完全不包含`【分析】`及其内容**
- [ ] `\explain{}` 中的内容全部来自`【详解】`
- [ ] 至少一张图片正确显示（TikZ 或图片）
- [ ] 产出完整的"OCR 脚本问题清单"（至少 3 个问题）
- [ ] 执行记录清晰完整

## 八、附录

### 常用路径速查
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

### 关键脚本位置

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

## 九、阶段二：图片 → TikZ 自动化流水线

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
    │
    ▼
[AI Agent]
(读取 image_jobs + 图片)
(生成 TikZ 环境)
    │
    ▼
tikz_snippets/{id}.tex
    │
    ▼
[apply_tikz_snippets.py]
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

每一行是一个 JSON 对象，代表一个图片任务（image_job）：

```json
{
  "id": "nanjing2026-Q3-img1",
  "exam_slug": "nanjing2026",
  "tex_file": "content/exams/auto/nanjing2026/converted_exam.tex",
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

> 这个 Prompt 是给"看图生成 TikZ"大模型 / Agent 用的，可以直接放到它的 System 区 / 说明文档里。

```markdown
你是一名专业的 LaTeX TikZ 绘图助手，专门为高中数学试卷生成严谨、可编译的 TikZ 代码。

你的任务：根据给定的 **image_job** 元数据和对应的图片内容，生成一段完整的 `tikzpicture` 环境，用于替换试卷中的图片。

---

## 输入信息

你将获得两部分信息：

1. 一个 JSON 对象 `image_job`（结构示例）：

```json
{
  "id": "nanjing2026-Q3-img1",
  "exam_slug": "nanjing2026",
  "tex_file": "content/exams/auto/nanjing2026/converted_exam.tex",
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

2. 对应的图片内容，由外部工具加载 `image_job.path` 所指向的图片文件。

你可以假设外部工具已经把这张图片展示给你，你"看得见"图中的坐标轴、图像、线段、点、注记等。

---

## 生成 TikZ 的要求

1. **输出格式**
   - 只输出一段完整的 TikZ 环境：
     ```tex
     \begin{tikzpicture}
       ...
     \end{tikzpicture}
     ```
   - 不要输出解释、注释或 Markdown 文本
   - 不要包含 `\documentclass`、`\begin{document}` 等内容

2. **风格与规范**
   - 使用标准 `tikz`（和必要的 `pgfplots`）语法，避免依赖冷门宏包
   - 文字标签尽量使用英文字母或数学模式，例如 `$A$`、`$f(x)$`，不要输出中文
   - 坐标轴、网格、曲线要清晰、可读，优先保持数学结构正确，而非像素级完全一致
   - 如果图像是函数图像或统计图，尽量用解析式或关键点来绘制，而不是硬编码大量离散点

3. **坐标与大小**
   - 结合 `image_job.width_pct` 决定图像的相对尺寸，但你不需要直接使用这个百分比
   - 推荐使用 `scale` 或 `axis` 的 `width`/`height` 控制整体大小，例如：
     ```tex
     \begin{tikzpicture}[scale=1.0]
     ...
     \end{tikzpicture}
     ```
   - 坐标轴范围请根据图像内容合理设置，例如 `-1` 到 `4`，`0` 到 `5` 等

4. **保持数学语义**
   - 你的目标是让试卷中的图像在数学意义上与原图一致：
     - 若原图是一次函数、二次函数、绝对值函数、指数函数等，请按正确的函数形状绘制
     - 若原图是几何图形（如三角形、圆、扇形），请尽量保留角度和相对位置关系
   - 不需要完全还原所有装饰性细节（如细小刻度、阴影），优先保证可读和易于编译

5. **鲁棒性**
   - 如果图片极其复杂（比如多子图、复杂统计图），可以适当简化，只画最关键的部分，让学生能够使用这幅图解题
   - 禁止输出空的 `tikzpicture`；如果你实在看不清某部分，可以根据题目上下文做合理推断

---

## 最重要的一点

**始终只输出纯 TikZ 代码**，不要添加任何额外说明文字。
你的输出会被直接写入 LaTeX 源文件并编译成试卷。
```

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

> 按照上文第 9.1 子流水线设计，在 `tools/images/apply_tikz_snippets.py` 中实现：
>
> 1. 读取 `--tex-file` 指定的 TeX 文件
> 2. 扫描 `--snippets-dir` 中所有 `{id}.tex`，建立 TikZ 片段映射
> 3. 遍历 TeX 行：
>    - 遇到 `IMAGE_TODO_START id=...`：
>      - 若存在对应 `{id}.tex`：
>        - 保留 START/END 注释
>        - 用 snippet 内容替换原来的 `tikzpicture` 占位环境
>      - 若不存在 snippet：
>        - 保留整个占位块，并在控制台打印告警
> 4. 支持 `--output` 参数决定是否覆盖原文件

---

## 十、阶段二测试流程建议

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
