# 调试与错误诊断指南 (v4.2)

> **文档定位**: 完整的错误排查、质量检查和问题修复手册  
> **配套文档**: [workflow.md](workflow.md), [REFERENCE.md](REFERENCE.md)  
> **更新**: 2025-12-01

---

## 一、预编译检查流程

### 1.1 结构验证（转换完成后立即运行）

**工具**: `tools/core/validate_tex.py`

```bash
python3 tools/core/validate_tex.py content/exams/auto/<slug>/converted_exam.tex
```

**检查项目**:
- ✅ 花括号配对 `{}`（智能忽略数学定界符）
- ✅ 数学定界符配对 `\(...\)` 和 `\[...\]`
- ✅ 环境平衡 `\begin{question}` vs `\end{question}`
- ✅ 题干缺失检测（题目直接从 `\item` 开始）

**处理建议**:
- 如果显示警告，优先修复后再编译
- 花括号/数学定界符警告可能是误报（array 环境中的 `\\`）
- `\explain` 空行是最常见的编译错误，必须修复

### 1.2 数学处理完整性检查（v1.8 新增）

**方式1：A/B 对比测试**（推荐）

```bash
cd tools/testing
python3 math_sm_comparison.py ../../word_to_tex/output/<exam>_preprocessed.md
```

**检查指标**:
- **定界符平衡**: `\(` 与 `\)` 数量差异（目标 = 0）
- **裸 $ 符号**: 未转换的 dollar 符号数量（目标 = 0）
- **文件大小**: 状态机 vs 旧管线大小对比
- **截断片段**: 疑似不完整的数学片段样本

**WARNING 标记**:
- ⚠️ `balance_diff != 0`: 仍有括号不平衡
- ⚠️ `truncation detected`: 发现疑似截断片段
- ⚠️ `stray dollars > 0`: 存在裸 $ 符号

**方式2：直接查看问题日志**

```bash
cat content/exams/auto/<slug>/debug/<slug>_issues.log
```

**日志内容**:
- 数学完整性报告（balance_diff, stray $, truncation samples）
- 元信息一致性警告
- 题干缺失警告
- 【分析】过滤警告

---

## 二、编译错误诊断流程

### 2.1 快速诊断步骤

**Step 1: 查看智能错误摘要**  
build.sh 自动显示错误类型、位置、原因和修复建议。

**Step 2: 查看详细错误日志**

```bash
cat output/last_error.log
# 或使用错误定位工具（更友好）
tools/locate_error.sh output/.aux/wrap-exam-teacher.log
```

**Step 3: 定位问题代码**  
locate_error.sh 会显示：
- 错误类型
- 文件路径和行号
- 前后 5 行上下文
- 常见原因和修复建议

### 2.2 常见错误类型及修复方法

| 错误类型 | 常见原因 | 修复方法 |
|---------|---------|---------|
| Runaway argument | `\explain{}` 中有空行 | 删除空行或用 `%` 注释 |
| Missing $ inserted | 数学模式定界符不匹配 | 检查 `\(...\)` 配对 |
| Undefined control sequence | 拼写错误或缺少宏包 | 检查命令名称 |
| Environment unbalanced | `\begin{question}` 缺少 `\end{question}` | 补充缺失的环境结束标记 |
| Unmatched brace | 花括号不配对 | 检查 `{...}` 是否完整 |

**修复优先级**:
1. 🔴 先修复 TeX 文件中的明显语法错误
2. 🟡 如果是 ocr_to_examx.py 解析问题，修改脚本并重新生成
3. 🟢 最后才考虑修改项目公共配置（preamble.sty 等）

### 2.3 回归测试流程

**何时使用**: 修改了核心脚本或配置文件、准备提交代码前

**运行测试**: `tools/test_compile.sh`

**测试覆盖**: exam/handout × teacher/student（4种组合）

**失败处理**: 查看错误摘要 → 使用 locate_error.sh 定位 → 修复后重测

---

## 三、快速调试命令清单

### 3.1 结构检查

```bash
# 验证 TeX 结构完整性
python3 tools/core/validate_tex.py content/exams/auto/<slug>/converted_exam.tex

# 数学公式 A/B 对比
cd tools/testing && python3 math_sm_comparison.py ../../word_to_tex/output/<exam>_preprocessed.md

# 查看问题日志
cat content/exams/auto/<slug>/debug/<slug>_issues.log
```

### 3.2 编译相关

```bash
# 带预检查的编译
VALIDATE_BEFORE_BUILD=1 ./build.sh exam teacher

# 查看编译错误
cat output/last_error.log
tools/locate_error.sh output/.aux/wrap-exam-teacher.log

# 回归测试
tools/test_compile.sh
```

### 3.3 图片处理

```bash
# 导出图片任务
python tools/images/export_image_jobs.py \
    --files "content/exams/auto/<slug>/converted_exam.tex" \
    --output "content/exams/auto/<slug>/image_jobs.jsonl"

# 应用 TikZ 代码
python tools/images/apply_tikz_snippets.py \
    --tex-file content/exams/auto/<slug>/converted_exam.tex

# 从 JSONL 写入 TikZ
python3 tools/images/write_snippets_from_jsonl.py \
    --jobs-file content/exams/auto/<slug>/image_jobs.jsonl \
    --tikz-file generated_tikz.jsonl
```

### 3.4 清理与重置

```bash
# 清理 LaTeX 临时文件
latexmk -C

# 清理所有输出（包括 PDF）
rm -rf output/
```

---

## 四、常见问题详解（按类别）

> **自动化状态说明**:  
> ✅ 已自动化（MathStateMachine v1.8 自动修复）  
> ⚠️ 半自动化（工具检测 + 人工修复）  
> ❌ 需人工检查

---

### 4.1 Meta 区域问题

#### 问题 1: 元信息字段缺失或格式错误 ⚠️

**错误现象**:
- `【答案】`、`【难度】`、`【知识点】`、`【详解】` 缺失或拼写错误
- 元信息未独立成行（与题干/选项混在一起）
- 使用了非标记词（如"难易度"、"解析"、"正确答案"）

**根本原因**:
- Word 原文档格式不规范
- Pandoc 转换时合并了多行
- OCR 识别错误

**检测方法**:
```bash
# 查看元信息一致性警告
cat content/exams/auto/<slug>/debug/<slug>_issues.log | grep "meta"
```

**修复方法**:
1. 打开 `word_to_tex/output/<exam>_raw.md`
2. 搜索题号（如 `1.`），检查其后是否有 `【答案】` 等标记
3. 如缺失，手动补充：
   ```markdown
   1. 题干内容...
   
   【答案】A
   【难度】中等
   【知识点】函数与导数
   【详解】详细解释...
   ```
4. 如格式错误（如 `【 答案 】`），修正为标准格式
5. 重新运行 `ocr_to_examx.py`

**预防措施**:
- 转换前先检查 Word 文档，确保元信息独立成行
- 使用标准标记词（答案/难度/知识点/详解）

---

#### 问题 2: 【分析】内容未被过滤（高频，~100%） ❌

**错误现象**:
- TeX 文件的 `\explain{}` 中包含 `【分析】` 的内容
- 编译后的 PDF 显示了不应出现的解析步骤

**根本原因**:
- `ocr_to_examx.py` 的 `META_PATTERNS["analysis"]` 未正确匹配
- `parse_question_structure()` 未将【分析】内容排除

**检测方法**:
```bash
# 搜索 TeX 文件中的"分析"字样
grep -n "分析" content/exams/auto/<slug>/converted_exam.tex
```

**修复方法**:
1. 检查 `tools/core/ocr_to_examx.py` 的 `META_PATTERNS`:
   ```python
   META_PATTERNS = {
       "analysis": re.compile(r"【分析】.*", re.DOTALL)  # 确保匹配到行尾
   }
   ```
2. 在 `parse_question_structure()` 中确保【分析】内容不被加入 `\explain{}`
3. 修改后重新运行脚本
4. **必须记录到问题清单**

**预防措施**:
- 转换前手动删除 Word 文档中的【分析】内容
- 在 `ocr_to_examx.py` 中增加单元测试覆盖【分析】过滤

---

### 4.2 数学公式问题

#### 问题 3: 定界符不平衡（中频，~15%） ✅

**错误现象**:
- 编译报错 `Missing $ inserted` 或 `Extra }, or forgotten $`
- 数学公式显示异常

**根本原因**:
- `\(` 与 `\)` 数量不匹配
- 公式内嵌套了未转义的括号

**检测方法**:
```bash
# 运行数学完整性检查
cd tools/testing
python3 math_sm_comparison.py ../../word_to_tex/output/<exam>_preprocessed.md
# 查看 balance_diff 是否为 0
```

**修复方法**:
- **v1.8 已自动化**: MathStateMachine 自动修复大部分不平衡问题
- 如仍有残留，手动检查 TeX 文件中的公式，补充缺失的 `\)`

**预防措施**:
- 使用 v1.8+ 版本的 `ocr_to_examx.py`
- 转换前检查 Markdown 中的数学公式格式

---

#### 问题 4: 裸 $ 符号残留（中频，~10%） ✅

**错误现象**:
- TeX 文件中存在单独的 `$` 符号（未转换为 `\(...\)`）
- 编译报错或公式格式错误

**根本原因**:
- Pandoc 转换时保留了原 Word 文档中的 `$` 符号
- `preprocess_markdown.py` 未完全转换

**检测方法**:
```bash
# 搜索裸 $ 符号
grep -n '\$' word_to_tex/output/<exam>_preprocessed.md
```

**修复方法**:
- **v1.8 已自动化**: MathStateMachine 自动将 `$...$` 转换为 `\(...\)`
- 如仍有残留，手动替换：
  ```bash
  sed -i '' 's/\$\(.*\)\$/\\(\1\\)/g' word_to_tex/output/<exam>_preprocessed.md
  ```

**预防措施**:
- 使用 v1.8+ 版本的转换流程

---

#### 问题 5: 数学片段截断（低频，~5%） ⚠️

**错误现象**:
- 公式显示不完整（如 `\(x^2 + y`，缺少 `\)`）
- 编译报错 `Runaway argument`

**根本原因**:
- OCR 识别时截断了长公式
- Markdown 转换时丢失了部分内容

**检测方法**:
```bash
# 查看截断样本
cd tools/testing
python3 math_sm_comparison.py ../../word_to_tex/output/<exam>_preprocessed.md
# 查看 truncation_samples
```

**修复方法**:
1. 定位截断位置（根据 truncation_samples）
2. 对照原 Word 文档，手动补全公式
3. 重新运行 `ocr_to_examx.py`

**预防措施**:
- 转换前检查 Word 文档中的长公式是否完整
- 使用高质量的 Pandoc 转换参数

---

#### 问题 6: 双重定界符包裹（低频，~3%） ✅

**错误现象**:
- TeX 文件中出现 `\(\(...\)\)` 或 `\[\[...\]\]`
- 公式显示异常或编译报错

**根本原因**:
- 旧版本转换脚本重复添加了定界符
- 手动修改时误操作

**检测方法**:
```bash
# 搜索双重定界符
grep -n '\\(\\(' content/exams/auto/<slug>/converted_exam.tex
grep -n '\\[\\[' content/exams/auto/<slug>/converted_exam.tex
```

**修复方法**:
- **v1.8 已自动化**: 去重逻辑自动移除外层定界符
- 手动修复：
  ```bash
  sed -i '' 's/\\(\\(/\\(/g' content/exams/auto/<slug>/converted_exam.tex
  sed -i '' 's/\\)\\)/\\)/g' content/exams/auto/<slug>/converted_exam.tex
  ```

**预防措施**:
- 使用 v1.8+ 版本的 `ocr_to_examx.py`

---

### 4.3 括号与定界符问题

#### 问题 7: 花括号不配对（中频，~12%） ⚠️

**错误现象**:
- 编译报错 `Missing } inserted` 或 `Extra }`
- 环境结构错位

**根本原因**:
- 手动编辑时误删了 `{` 或 `}`
- OCR 识别错误

**检测方法**:
```bash
# 运行结构验证
python3 tools/core/validate_tex.py content/exams/auto/<slug>/converted_exam.tex
# 查看 brace balance 警告
```

**修复方法**:
1. 根据 validate_tex.py 报告定位行号
2. 手动检查该行及上下文，补充缺失的 `}` 或删除多余的 `{`
3. 注意区分：
   - 命令参数：`\command{arg}`
   - 环境：`\begin{env} ... \end{env}`
   - 数学：`\(...\)` 内的花括号通常不需要配对检查

**预防措施**:
- 编辑 TeX 文件时使用支持括号高亮的编辑器
- 每次修改后运行 validate_tex.py

---

#### 问题 8: 大括号 `\{` 与小括号混淆（低频，~2%） ❌

**错误现象**:
- 集合符号显示为普通括号（如 `{x|x>0}` 应为 `\{x|x>0\}`）
- 编译报错 `Missing $ inserted`

**根本原因**:
- OCR 未识别转义符号
- 手动输入时遗漏 `\`

**检测方法**:
```bash
# 搜索未转义的集合符号
grep -n '{[a-zA-Z]' content/exams/auto/<slug>/converted_exam.tex
```

**修复方法**:
手动检查数学公式中的 `{}`，如表示集合，改为 `\{\}`：
```latex
\( A = \{x \mid x > 0\} \)
```

**预防措施**:
- 转换前检查 Word 文档中的集合符号是否正确

---

### 4.4 环境结构问题

#### 问题 9: 题目缺少题干（高频，~20%） ⚠️

**错误现象**:
- 题目直接从 `\item` 开始，无题干描述
- `\begin{question}` 后紧跟 `\begin{choices}`

**根本原因**:
- Word 原文档格式不规范（题号后直接跟选项）
- OCR 识别时将题干误识别为选项

**检测方法**:
```bash
# 运行结构验证
python3 tools/core/validate_tex.py content/exams/auto/<slug>/converted_exam.tex
# 查看 "missing statement" 警告
```

**修复方法**:
1. 对照原 Word 文档，确认是否确实缺少题干
2. 如缺失，在 `\begin{question}` 后、`\begin{choices}` 前补充题干：
   ```latex
   \begin{question}
   \topics{函数}
   \difficulty{中等}
   \answer{A}
   
   已知函数 \(f(x) = x^2 + 1\)，求...  % 补充的题干
   
   \begin{choices}
   ...
   \end{choices}
   \end{question}
   ```

**预防措施**:
- 转换前检查 Word 文档，确保每道题都有题干
- 在 `ocr_to_examx.py` 中增加题干缺失检测

---

#### 问题 10: `\explain{}` 中包含空行（高频，~50%） ⚠️

**错误现象**:
- 编译报错 `Runaway argument` 或 `Paragraph ended before \explain was complete`
- PDF 生成失败

**根本原因**:
- `\explain{}` 宏不允许参数中包含空行
- OCR 转换时保留了原文档的段落分隔

**检测方法**:
```bash
# 运行结构验证
python3 tools/core/validate_tex.py content/exams/auto/<slug>/converted_exam.tex
# 查看 "empty line in \explain{}" 警告
```

**修复方法**:
1. 定位 `\explain{}` 的位置（根据 validate_tex.py 报告）
2. 删除 `{}` 内的空行，或用 `%` 注释掉：
   ```latex
   \explain{
   第一段解释...
   %
   第二段解释...
   }
   ```

**预防措施**:
- 在 `ocr_to_examx.py` 中自动将 `\explain{}` 内的空行替换为 `%`

---

#### 问题 11: 环境未闭合（中频，~8%） ⚠️

**错误现象**:
- 编译报错 `\begin{question} ended by \end{document}`
- PDF 生成失败或内容错位

**根本原因**:
- 手动编辑时误删了 `\end{question}` 或 `\end{choices}`
- OCR 识别错误

**检测方法**:
```bash
# 运行结构验证
python3 tools/core/validate_tex.py content/exams/auto/<slug>/converted_exam.tex
# 查看 "environment not closed" 警告
```

**修复方法**:
1. 根据报告定位缺失的 `\end{...}`
2. 手动补充：
   ```latex
   \begin{question}
   ...
   \end{question}  % 确保每个 \begin 都有对应的 \end
   ```

**预防措施**:
- 使用编辑器的自动补全功能
- 每次修改后运行 validate_tex.py

---

### 4.5 图片问题

#### 问题 12: 图片路径错误（中频，~10%） ⚠️

**错误现象**:
- 编译报错 `File not found`
- PDF 中图片显示为占位框

**根本原因**:
- Pandoc 提取的图片路径与 TeX 中的 `\includegraphics` 不匹配
- 图片文件未正确复制到目标目录

**检测方法**:
```bash
# 检查图片是否存在
ls word_to_tex/output/figures/<image_name>.png
# 对比 TeX 文件中的路径
grep includegraphics content/exams/auto/<slug>/converted_exam.tex
```

**修复方法**:
1. 确认图片位于 `word_to_tex/output/figures/` 或其子目录
2. 修正 TeX 文件中的路径：
   ```latex
   \includegraphics[width=0.5\textwidth]{figures/<image_name>.png}
   ```
3. 如图片为 WMF 格式，先转换为 PNG：
   ```bash
   python tools/images/process_images_to_tikz.py --mode convert --files <tex_file>
   ```

**预防措施**:
- 使用 `process_images_to_tikz.py` 自动处理图片路径

---

#### 问题 13: TikZ 占位符格式错误（低频，~5%） ⚠️

**错误现象**:
- 编译报错 `Undefined control sequence`
- 图片无法显示

**根本原因**:
- `IMAGE_TODO` 块格式不符合规范（缺少必需字段）
- 手动编辑时语法错误

**检测方法**:
```bash
# 检查 IMAGE_TODO 格式
grep -A 10 'IMAGE_TODO_START' content/exams/auto/<slug>/converted_exam.tex
```

**修复方法**:
1. 对照 [REFERENCE.md § 2](REFERENCE.md) 检查必需字段
2. 补充缺失字段：
   ```latex
   % IMAGE_TODO_START
   % id: <slug>-Q<num>-img<idx>
   % exam: <exam_name>
   % question: <num>
   % image_index: <idx>
   % description: <desc>
   % IMAGE_TODO_END
   ```

**预防措施**:
- 使用 `process_images_to_tikz.py --mode template` 自动生成标准占位符

---

### 4.6 文本格式问题

#### 问题 14: 中英文混排空格（低频，~3%） ❌

**错误现象**:
- 中英文之间缺少空格，排版拥挤
- 或多余空格导致间距过大

**根本原因**:
- Word 原文档格式不统一
- Pandoc 转换时未处理空格

**检测方法**:
手动浏览 PDF，检查中英文混排处

**修复方法**:
手动调整 TeX 文件中的空格：
```latex
函数 \(f(x)\) 的定义域为... % 中文与公式之间保留空格
```

**预防措施**:
- 转换前统一 Word 文档格式
- 考虑编写自动化脚本处理空格

---

#### 问题 15: 特殊字符未转义（低频，~2%） ❌

**错误现象**:
- 编译报错 `Missing $ inserted` 或 `Undefined control sequence`
- 特殊符号（如 `%`、`&`、`#`）显示异常

**根本原因**:
- LaTeX 特殊字符未添加反斜杠转义
- OCR 识别时保留了原始符号

**检测方法**:
```bash
# 搜索未转义的特殊字符
grep -n '[%&#]' content/exams/auto/<slug>/converted_exam.tex | grep -v '^%'
```

**修复方法**:
手动添加转义符：
```latex
% 原文：使用 % 表示百分比
% 修正：使用 \% 表示百分比
```

**预防措施**:
- 在 `ocr_to_examx.py` 中增加特殊字符自动转义

---

### 4.7 LaTeX 编译错误

#### 问题 16: Undefined control sequence（中频，~10%） ❌

**错误现象**:
- 编译报错 `Undefined control sequence`
- 指向某个自定义命令或宏包命令

**根本原因**:
- 拼写错误（如 `\beign` 而非 `\begin`）
- 缺少宏包引入
- 使用了未定义的自定义命令

**检测方法**:
查看 `output/last_error.log`，定位错误行

**修复方法**:
1. 检查拼写：确认命令名称正确
2. 检查宏包：确认 `preamble.sty` 中已引入必要的宏包
3. 检查自定义命令：确认 `styles/examx.sty` 中已定义该命令

**预防措施**:
- 使用编辑器的自动补全和语法检查
- 新增自定义命令时及时更新样式文件

---

#### 问题 17: Runaway argument（高频，~30%） ⚠️

**错误现象**:
- 编译报错 `Runaway argument`
- 通常指向 `\explain{}` 或其他宏

**根本原因**:
- 宏参数中包含空行（LaTeX 不允许）
- 花括号不配对

**检测方法**:
```bash
# 运行结构验证
python3 tools/core/validate_tex.py content/exams/auto/<slug>/converted_exam.tex
```

**修复方法**:
参见 [问题 10: `\explain{}` 中包含空行](#问题-10-explain-中包含空行高频-50-️)

**预防措施**:
- 在 `ocr_to_examx.py` 中自动处理空行

---

### 4.8 题目结构问题

#### 问题 18: 选项编号错误（中频，~8%） ⚠️

**错误现象**:
- 选项编号显示为 `1. 2. 3. 4.` 而非 `A. B. C. D.`
- 或编号缺失

**根本原因**:
- `\begin{choices}` 环境未正确使用
- 选项未使用 `\item` 标记

**检测方法**:
手动浏览 PDF，检查选项编号

**修复方法**:
确保选项使用标准格式：
```latex
\begin{choices}
\item 选项 A 内容
\item 选项 B 内容
\item 选项 C 内容
\item 选项 D 内容
\end{choices}
```

**预防措施**:
- 在 `ocr_to_examx.py` 中确保选项正确解析为 `\item`

---

#### 问题 19: 多选题/填空题格式不统一（低频，~5%） ❌

**错误现象**:
- 多选题未使用 `\begin{multichoice}` 环境
- 填空题未使用 `\fillin{}` 命令

**根本原因**:
- 转换脚本未识别题目类型
- 手动编辑时未统一格式

**检测方法**:
手动浏览 PDF，检查题目类型是否正确

**修复方法**:
1. 多选题：
   ```latex
   \begin{multichoice}
   \item 选项 A
   \item 选项 B
   \item 选项 C
   \item 选项 D
   \end{multichoice}
   ```
2. 填空题：
   ```latex
   已知 \fillin{答案} ...
   ```

**预防措施**:
- 在 `ocr_to_examx.py` 中增加题目类型识别逻辑

---

## 五、完整工作流验证

### 5.1 验证脚本

```bash
tools/workflow_validate.sh content/exams/auto/<slug>/converted_exam.tex
```

**验证步骤**:
1. 文件检查（TeX 文件是否存在）
2. 预编译验证（结构检查、数学完整性）
3. 教师版编译
4. 学生版编译
5. PDF 验证（文件大小、可打开性）

**成功标准**:
- 所有步骤显示 ✅
- PDF 可正常打开
- 文件大小合理（>50KB）

### 5.2 问题追踪

**记录问题到清单**:
- 新发现的问题类型记录到本文档
- OCR 脚本问题单独记录到开发日志
- 统计高频问题，优先自动化修复

---

## 六、参考链接

- **格式规范**: [REFERENCE.md](REFERENCE.md)
- **完整流程**: [workflow.md](workflow.md)
- **图片处理详解**: [IMAGE_JOBS_FULL.md](IMAGE_JOBS_FULL.md)
- **解释格式详解**: [EXPLAIN_FULL.md](EXPLAIN_FULL.md)
- **TikZ 生成指南**: [TIKZ_AGENT_PROMPT.md](TIKZ_AGENT_PROMPT.md)

---

**版本**: v3.4  
**最后更新**: 2025-01-XX
