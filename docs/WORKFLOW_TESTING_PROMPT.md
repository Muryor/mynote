# LaTeX 试卷流水线测试 Prompt

## 角色定位
你是一名**本地 LaTeX 试卷流水线工程师**，负责用一个示例 Word 试卷文件跑通整个流水线，并记录过程中发现的所有问题。

## 流水线概览
```
Word → Pandoc → Markdown 
     → ocr_to_examx.py → examx TeX 
     → process_images_to_tikz.py → TikZ/图片处理 
     → build.sh → PDF
```

## 一、项目核心规范

### 1.1 文件结构
```
mynote/
├── tools/
│   ├── core/
│   │   └── ocr_to_examx.py       # Markdown → examx TeX
│   └── images/
│       ├── process_images_to_tikz.py  # 图片处理主工具
│       ├── generate_tikz_placeholders.py
│       └── generate_tikz_from_images.py
├── word_to_tex/
│   ├── scripts/
│   │   └── preprocess_docx.sh    # 完整转换流程封装
│   ├── input/                     # 存放待转换的 DOCX
│   └── output/                    # 转换输出
├── content/exams/auto/            # 生成的试卷存放位置
├── settings/
│   └── metadata.tex               # 编译配置（指定试卷源）
├── build.sh                       # 编译脚本
└── output/                        # PDF 输出目录
```

### 1.2 关键工具说明

#### `ocr_to_examx.py`
**输入**：Pandoc 生成的 Markdown（含题号、选项、元信息标记）  
**输出**：examx 风格 TeX 文件

**功能**：
- 按章节分类（单选题/多选题/填空题/解答题）
- 识别题号、题干、选项
- 解析元信息：`【答案】`、`【难度】`、`【知识点】`、`【详解】`
- 文本清洗：数学公式、中文标点、"故选"等
- 生成 examx 结构

**使用**：
```bash
python3 tools/core/ocr_to_examx.py <input.md或文件夹> <output目录或.tex>
```

**关键参数**：
- `input`：输入路径（.md 文件或包含 `*_local.md` 的文件夹）
- `output`：输出路径（目录或 .tex 文件）
- `--title`：试卷标题（可选，默认从输入路径推断）

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
- `content/exams/auto/<前缀>/converted_exam.tex` - 精炼后的最终版本
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

## 二、测试任务目标

使用一个示例 Word 文件，完整跑通流水线并产出两份文档：

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
```
转换脚本：tools/core/ocr_to_examx.py
图片处理：tools/images/process_images_to_tikz.py
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

---

**最后提醒**：
1. 始终遵守"【分析】全部舍弃，【详解】是 \explain{} 唯一来源"的核心规范
2. 每次遇到 ocr_to_examx.py 导致的问题都要详细记录
3. 优先使用 `preprocess_docx.sh` 简化流程
4. 编译失败时先查看 `output/last_error.log`
5. 问题清单的质量比数量更重要

**祝测试顺利！🚀**
