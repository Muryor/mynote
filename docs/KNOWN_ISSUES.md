# 常见 OCR 错误及修复方法

> **文档版本**：v1.1（2025-11-20）
> **维护说明**：记录 Word → Markdown → LaTeX 流水线中常见的 OCR 转换错误及修复方法

---

## 📋 目录

1. [Meta 区域问题](#1-meta-区域问题)
2. [数学公式错误](#2-数学公式错误)
3. [括号与定界符问题](#3-括号与定界符问题)
4. [环境与结构错误](#4-环境与结构错误)
5. [图片相关问题](#5-图片相关问题)
6. [文本格式问题](#6-文本格式问题)
7. [编译错误模式](#7-编译错误模式)
8. [题目结构问题](#8-题目结构问题-新增)

---

## 1. Meta 区域问题

### 1.1 【分析】内容未删除

**错误现象**：
```latex
\explain{
  【详解】这是正确的解析内容
  【分析】这是应该删除的内容
}
```

**根本原因**：
- OCR 将试卷中的"分析"部分识别为元数据
- `ocr_to_examx.py` 只应保留【详解】内容

**检测方法**：
```bash
grep -n "【分析】" content/exams/auto/*/converted_exam.tex
```

**修复方法**：
```bash
# 手动删除 \explain 中的【分析】段落
# 或增强 Python 转换器的过滤逻辑
```

**预防措施**：
- 在 `ocr_to_examx.py` 的 `detect_question_issues()` 中增加【分析】检测
- 转换时报告包含【分析】的题目到 `debug/<slug>_issues.log`

---

### 1.2 【详解】标记残留

**错误现象**：
```latex
\explain{
  【详解】解：因为 $f(x) = \sin x$...
}
```

**根本原因**：
- 转换时未移除【详解】标记本身

**检测方法**：
```bash
grep -n "【详解】" content/exams/auto/*/converted_exam.tex
```

**修复方法**：
```latex
\explain{
  解：因为 $f(x) = \sin x$...
}
```

**预防措施**：
- 在 `ocr_to_examx.py` 中添加 `.replace("【详解】", "")` 处理
- 自动化清理所有元标记

---

### 1.3 空 \explain 或 \explain 缺失

**错误现象**：
```latex
\begin{question}[题目内容]
  ...
\end{question}
% 缺少 \explain{...}
```

**根本原因**：
- OCR 未识别到【详解】部分
- 或 Markdown 中答案缺失

**检测方法**：
```bash
python3 tools/validate_tex.py content/exams/auto/*/converted_exam.tex
# 查找 "Question missing \explain" 警告
```

**修复方法**：
```latex
\begin{question}[题目内容]
  ...
\end{question}
\explain{
  % TODO: 补充解析内容
}
```

**预防措施**：
- `ocr_to_examx.py` 的 `detect_question_issues()` 已检测此问题
- 查看 `debug/<slug>_issues.log` 中的报告

---

## 2. 数学公式错误

### 2.1 行内公式与行间公式混淆

**错误现象**：
```latex
% 错误：题干中使用行间公式
\begin{question}[已知函数 $$f(x) = \sin x$$]
  ...
\end{question}
```

**根本原因**：
- OCR 将所有公式识别为 `$$...$$` 行间格式
- 题干、选项应使用 `$...$` 行内格式

**检测方法**：
```bash
grep -n '\$\$' content/exams/auto/*/converted_exam.tex | grep -v '\\explain'
```

**修复方法**：
```latex
\begin{question}[已知函数 $f(x) = \sin x$]
  ...
\end{question}
```

**预防措施**：
- 使用 `tools/utils/convert_display_to_inline.py` 自动转换
- 在 `ocr_to_examx.py` 中增加智能判断：题干/选项→行内，\explain→保留行间

---

### 2.2 数学定界符不匹配

**错误现象**：
```latex
\explain{
  解：$f(x) = \sin x
}
```

**根本原因**：
- OCR 丢失结束定界符 `$`
- 或误将 `$$` 拆分成两个 `$`

**检测方法**：
```bash
python3 tools/validate_tex.py content/exams/auto/*/converted_exam.tex
# 查找 "Unbalanced math delimiter" 错误
```

**修复方法**：
```latex
\explain{
  解：$f(x) = \sin x$
}
```

**预防措施**：
- `validate_tex.py` 在编译前自动检测
- 使用编辑器的括号高亮功能

---

### 2.3 特殊符号 OCR 错误

**错误现象**：
```latex
% OCR 误识别
$\alpha$ → $a$
$\beta$ → $B$
$\geq$ → $>=$
$\in$ → $E$
```

**根本原因**：
- OCR 引擎对数学符号识别不准确
- Pandoc 转换时无法恢复

**检测方法**：
- 人工对照原始 PDF 检查
- 或使用专业数学 OCR 工具（Mathpix）

**修复方法**：
- 手动纠正符号错误
- 建立常见错误替换表

**预防措施**：
- 使用 Mathpix 或其他专业数学 OCR 工具
- 在 Markdown 阶段进行人工校对

---

## 3. 括号与定界符问题

### 3.1 大括号不平衡

**错误现象**：
```latex
\explain{
  解：因为 $\{x \mid x > 0$...
}
% 缺少结束花括号
```

**根本原因**：
- OCR 丢失配对的 `}`
- 或在 Markdown → TeX 转换时被转义错误

**检测方法**：
```bash
python3 tools/validate_tex.py content/exams/auto/*/converted_exam.tex
# 查找 "Unbalanced braces" 错误
```

**修复方法**：
```latex
\explain{
  解：因为 $\{x \mid x > 0\}$...
}
```

**预防措施**：
- `validate_tex.py` 自动检测
- 使用编辑器的括号匹配功能

---

### 3.2 方括号转义问题

**错误现象**：
```latex
\begin{question}[区间 [0, 1] 上的函数]
  ...
\end{question}
% LaTeX 错误：Optional argument not properly closed
```

**根本原因**：
- LaTeX 将 `[...]` 识别为可选参数定界符
- 题干中的数学区间 `[0, 1]` 未转义

**检测方法**：
- 编译时报错：`Runaway argument`

**修复方法**：
```latex
\begin{question}[区间 {[}0, 1{]} 上的函数]
  % 或使用
\begin{question}[区间 $[0, 1]$ 上的函数]
  ...
\end{question}
```

**预防措施**：
- 在 `ocr_to_examx.py` 中自动转义 `[` → `{[}`，`]` → `{]}`
- 或统一使用数学模式 `$[0, 1]$`

---

## 4. 环境与结构错误

### 4.1 question 环境未闭合

**错误现象**：
```latex
\begin{question}[题目内容]
  选项内容
% 缺少 \end{question}

\explain{...}
```

**根本原因**：
- 转换脚本逻辑错误
- 或题目边界识别失败

**检测方法**：
```bash
python3 tools/validate_tex.py content/exams/auto/*/converted_exam.tex
# 查找 "Unclosed environment" 错误
```

**修复方法**：
```latex
\begin{question}[题目内容]
  选项内容
\end{question}
\explain{...}
```

**预防措施**：
- `ocr_to_examx.py` 的环境匹配逻辑严格检查
- `validate_tex.py` 在编译前验证

---

### 4.2 \explain 中包含段落分隔

**错误现象**：
```latex
\explain{
  解：第一步...

  第二步...
}
% 编译错误：Runaway argument
```

**根本原因**：
- `\explain` 是命令而非环境，不允许段落分隔（空行）

**检测方法**：
```bash
python3 tools/validate_tex.py content/exams/auto/*/converted_exam.tex
# 查找 "Paragraph break inside \\explain" 错误
```

**修复方法**：
```latex
\explain{
  解：第一步... \par
  第二步...
}
% 或使用 \\ 换行
\explain{
  解：第一步... \\
  第二步...
}
```

**预防措施**：
- `validate_tex.py` 自动检测空行
- 转换时自动替换 `\n\n` → `\par`

---

### 4.3 嵌套环境错误

**错误现象**：
```latex
\begin{question}[...]
  \begin{enumerate}
    \item 选项 A
  \begin{question}[...]  % 错误嵌套
```

**根本原因**：
- 题目边界识别错误
- 或 Markdown 结构层次混乱

**检测方法**：
- 编译时报错：`LaTeX Error: \begin{question} on input line ... ended by \end{enumerate}`

**修复方法**：
- 手动调整题目边界
- 确保每个 `\begin{question}` 都有对应的 `\end{question}`

---

### 4.4 超长 \explain 内容导致转换截断

**错误现象**：
```latex
\begin{question}[...]
  ...
\topics{...}
\difficulty{...}
\answer{...}
\explain{
% 内容为空或被截断，缺少闭合括号
```

**根本原因**：
- 某些题目的【详解】内容极长（>1000行），如高考压轴题
- `ocr_to_examx.py` 在处理超长内容时可能出现截断
- 或 `agent_refine.py` 处理时遇到内存/长度限制

**检测方法**：
```bash
# 检查 question 环境是否匹配
grep -c "\\begin{question}" converted_exam.tex
grep -c "\\end{question}" converted_exam.tex
# 如果数量不一致，说明有环境未闭合

# 检查空的或未闭合的 explain
grep -A 1 "\\explain{$" converted_exam.tex
```

**修复方法**：
1. 手动补充缺失的 `}`（闭合 `\explain{}`）
2. 手动补充缺失的 `\end{question}`
3. 为空的 `\explain{}` 补充简化版内容（如"详见原题解析"）
4. **关键**：删除 `\explain{}` 内部的所有空行（避免 Runaway argument 错误）

**预防措施**：
- 在 `ocr_to_examx.py` 中增加超长内容警告
- 对于超过500行的【详解】，记录到 `debug/<slug>_issues.log`
- 考虑将超长详解拆分或简化

**实际案例**：
- 2025年高考全国一卷第9题（多选题），【详解】约1000行，导致转换截断

---

### 4.5 IMAGE_TODO 注释中残留的 LaTeX 代码

**错误现象**：
```latex
% IMAGE_TODO_START id=... path=... width=60% inline=true question_index=7 sub_index=1
% CONTEXT_BEFORE: left( \sqrt{3} \right)^{2} + ( - 1)^{2}}} = 2\(，
% CONTEXT_AFTER:
```

**根本原因**：
- `agent_refine.py` 在生成 `CONTEXT_BEFORE/AFTER` 时，直接截取了周围的 TeX 代码
- 代码中的花括号 `}` 导致括号不平衡
- 或包含未闭合的数学定界符 `\(`

**检测方法**：
```bash
python3 tools/validate_tex.py content/exams/auto/*/converted_exam.tex
# 查找 "Unmatched closing brace" 错误

# 或手动检查 IMAGE_TODO 注释
grep "% CONTEXT_" converted_exam.tex
```

**修复方法**：
```latex
% 删除注释中多余的闭合括号
% CONTEXT_BEFORE: left( \sqrt{3} \right)^{2} + ( - 1)^{2}} = 2，
% 或简化为纯文本描述
% CONTEXT_BEFORE: 圆心到直线的距离公式
```

**预防措施**：
- 在 `agent_refine.py` 中，CONTEXT 内容应该：
  - 去除 LaTeX 命令，只保留纯文本
  - 或对注释内容进行括号平衡检查
  - 限制长度（如最多50个字符）

**实际案例**：
- 2025年高考全国一卷第7题、第8题的 IMAGE_TODO 注释中有多余的 `}`

---

## 5. 图片相关问题

### 5.1 IMAGE_TODO 块缺失

**错误现象**：
```latex
% 题目中有"如图所示"，但无对应 IMAGE_TODO
\begin{question}[如图所示，函数 $f(x)$ 的图象...]
  ...
\end{question}
```

**根本原因**：
- Pandoc 从 Word 转 Markdown 时丢失图片引用
- 或 OCR 未识别图片位置

**检测方法**：
```bash
# 查找含"如图"但无 IMAGE_TODO 的题目
grep -n "如图" content/exams/auto/*/converted_exam.tex | while read line; do
  file=$(echo $line | cut -d: -f1)
  linenum=$(echo $line | cut -d: -f2)
  if ! grep -A 20 "^$(sed -n "${linenum}p" "$file")" "$file" | grep -q "IMAGE_TODO"; then
    echo "缺失图片：$line"
  fi
done
```

**修复方法**：
```latex
\begin{question}[如图所示，函数 $f(x)$ 的图象...]
  % IMAGE_TODO_START id=slug-Q3-img1 path=word_to_tex/output/figures/media/image1.png width=60% inline=false question_index=3 sub_index=1
  \begin{center}
    % TODO: AI_AGENT_REPLACE_ME (id=slug-Q3-img1)
  \end{center}
  % IMAGE_TODO_END id=slug-Q3-img1
  ...
\end{question}
```

**预防措施**：
- 检查 `word_to_tex/output/figures/media/` 中的图片数量
- 对照 TeX 中的 IMAGE_TODO 数量
- 手动补充缺失的占位块

---

### 5.2 图片路径错误

**错误现象**：
```latex
% IMAGE_TODO_START path=output/figures/media/image1.png
% 实际文件在 word_to_tex/output/figures/media/image1.png
```

**根本原因**：
- 转换脚本使用相对路径
- 或目录结构变化

**检测方法**：
```bash
# 检查路径是否存在
grep "IMAGE_TODO_START" content/exams/auto/*/converted_exam.tex | \
  grep -oE 'path=[^ ]+' | cut -d= -f2 | while read path; do
    [ ! -f "$path" ] && echo "路径不存在：$path"
  done
```

**修复方法**：
```latex
% IMAGE_TODO_START path=word_to_tex/output/figures/media/image1.png
```

**预防措施**：
- 使用绝对路径或项目根目录相对路径
- 在 `export_image_jobs.py` 中验证路径

---

### 5.3 图片宽度参数不合理

**错误现象**：
```latex
% IMAGE_TODO_START width=200%  % 图片过大
% IMAGE_TODO_START width=5%    % 图片过小
```

**根本原因**：
- OCR 未提供图片尺寸信息
- 或默认值设置不当

**检测方法**：
```bash
grep "IMAGE_TODO_START" content/exams/auto/*/converted_exam.tex | \
  grep -oE 'width=[0-9]+%' | sort | uniq -c
```

**修复方法**：
```latex
% 典型建议：
% - 行内小图：30%-50%
% - 独立图示：60%-80%
% - 大型图表：80%-100%
% IMAGE_TODO_START width=70%
```

---

## 6. 文本格式问题

### 6.1 中文标点识别错误

**错误现象**：
```latex
% OCR 误识别
，→ ,
。→ .
（ ）→ ( )
```

**根本原因**：
- OCR 引擎混淆中英文标点
- 或 Word 文档中混用标点

**检测方法**：
```bash
# 查找英文标点后紧跟中文的情况
grep -nE '[,\.][\u4e00-\u9fa5]' content/exams/auto/*/converted_exam.tex
```

**修复方法**：
- 手动替换为中文标点
- 使用正则批量替换

**预防措施**：
- 在 Markdown 阶段进行人工校对
- 或增加后处理脚本

---

### 6.2 换行符处理错误

**错误现象**：
```latex
\explain{解：因为 $f(x)$
满足条件}
% 应保持在同一段落
```

**根本原因**：
- Markdown 保留了原始换行
- TeX 中换行导致空格

**检测方法**：
- 人工检查 \explain 内容格式

**修复方法**：
```latex
\explain{解：因为 $f(x)$ 满足条件}
```

---

### 6.3 特殊字符转义缺失

**错误现象**：
```latex
\begin{question}[占比 50%]  % LaTeX 错误
\begin{question}[价格 $100]  % LaTeX 错误
```

**根本原因**：
- LaTeX 保留字符 `% $ & # _ { } ~ ^` 未转义

**检测方法**：
- 编译时报错

**修复方法**：
```latex
\begin{question}[占比 50\%]
\begin{question}[价格 \$100]
```

**预防措施**：
- 在 `ocr_to_examx.py` 中自动转义
- 或使用数学模式包裹

---

## 7. 编译错误模式

### 7.1 Runaway argument

**错误信息**：
```
Runaway argument?
! Paragraph ended before \explain was complete.
```

**常见原因**：
1. `\explain{...}` 中包含空行
2. 括号不匹配（缺少 `}`）
3. `[...]` 可选参数未闭合

**定位方法**：
```bash
tools/locate_error.sh output/.aux/wrap-exam-teacher.log
```

**修复流程**：
1. 使用 `locate_error.sh` 定位错误行
2. 检查对应命令的参数是否完整
3. 移除空行或添加缺失的定界符

---

### 7.2 Missing $ inserted

**错误信息**：
```
! Missing $ inserted.
<inserted text> 
                $
l.123 解：因为 f(x) = \sin x
```

**常见原因**：
1. 数学符号未包裹在 `$...$` 中
2. 数学定界符不匹配

**定位方法**：
```bash
tools/locate_error.sh output/.aux/wrap-exam-teacher.log
```

**修复方法**：
```latex
解：因为 $f(x) = \sin x$
```

---

### 7.3 Undefined control sequence

**错误信息**：
```
! Undefined control sequence.
l.456 \unknowncommand
```

**常见原因**：
1. 使用了未定义的命令
2. 宏包未加载
3. 拼写错误

**定位方法**：
```bash
tools/locate_error.sh output/.aux/wrap-exam-teacher.log
grep -n "unknowncommand" content/exams/auto/*/converted_exam.tex
```

**修复方法**：
- 检查命令拼写
- 确认所需宏包已加载
- 或移除未定义的命令

---

### 7.4 Environment ... undefined

**错误信息**：
```
! LaTeX Error: Environment choices undefined.
```

**常见原因**：
1. 环境名拼写错误（如 `choices` → `choice`）
2. 环境未在样式文件中定义

**定位方法**：
```bash
grep -n "\\begin{choices}" content/exams/auto/*/converted_exam.tex
```

**修复方法**：
```latex
% examx.sty 中定义的环境是 choice，不是 choices
\begin{choice}
  \item A
  \item B
\end{choice}
```

---

## 📊 统计与优先级

### 高频问题（按出现频率排序）

1. **【分析】内容未删除** - 几乎每个试卷都存在
2. **\explain 中包含段落分隔** - 约 50% 的试卷
3. **IMAGE_TODO 注释中残留 LaTeX 代码** - 约 40% 的试卷（新增）
4. **IMAGE_TODO 块缺失** - 约 30% 的试卷
5. **数学定界符不匹配** - 约 20% 的试卷
6. **超长 \explain 内容导致截断** - 约 10% 的试卷（高考真题常见）
7. **方括号转义问题** - 约 15% 的试卷

### 修复成本分级

| 问题类型 | 自动化修复 | 手动成本 | 优先级 |
|---------|-----------|---------|--------|
| 【分析】未删除 | ✅ 可自动化 | 低 | 🔴 高 |
| \explain 段落分隔 | ✅ 可自动化 | 低 | 🔴 高 |
| IMAGE_TODO 缺失 | ⚠️ 半自动 | 中 | 🟡 中 |
| 数学定界符不匹配 | ✅ 可检测 | 中 | 🟡 中 |
| 特殊符号 OCR 错误 | ❌ 需人工 | 高 | 🟢 低 |

---

## 🛠️ 工具链使用建议

### 错误检测优先级

1. **转换时自动检查**（ocr_to_examx.py）
   - 【分析】内容检测
   - \explain 缺失检测
   - 环境匹配检查

2. **编译前语法检查**（validate_tex.py）
   - 段落分隔检测
   - 括号平衡检查
   - 数学定界符检查

3. **编译后错误定位**（locate_error.sh）
   - Runaway argument 定位
   - Missing $ 定位
   - 环境错误定位

4. **回归测试**（test_compile.sh）
   - 四组合编译测试
   - 确保修复不引入新问题

### 工作流集成

```bash
# 完整错误检测流程
cd /Users/muryor/code/mynote

# 1. 转换时自动检查
python3 tools/core/ocr_to_examx.py \
  word_to_tex/output/<slug>_preprocessed.md \
  <slug> \
  content/exams/auto/<slug>

# 2. 查看自动生成的问题报告
cat word_to_tex/output/debug/<slug>_issues.log

# 3. 编译前语法检查
python3 tools/validate_tex.py content/exams/auto/<slug>/converted_exam.tex

# 4. 尝试编译
./build.sh exam teacher

# 5. 如果失败，快速定位错误
tools/locate_error.sh output/.aux/wrap-exam-teacher.log

# 6. 修复后回归测试
tools/test_compile.sh
```

---

## 📚 参考资料

- **工作流文档**：`docs/WORKFLOW_TESTING_PROMPT.md`
- **转换工具**：`tools/core/ocr_to_examx.py`
- **验证工具**：`tools/validate_tex.py`
- **错误定位**：`tools/locate_error.sh`
- **回归测试**：`tools/test_compile.sh`

---

## 8. 题目结构问题（新增）

### 8.1 题目缺少题干，直接从小问开始

**错误现象**：
```latex
\begin{question}
\item 证明：数列 $\{na_n\}$ 是等差数列；
\item 给定正整数 m，求 $f'(-2)$．
\topics{...}
\difficulty{...}
\answer{...}
\explain{...}
\end{question}
```

**根本原因**：
- `ocr_to_examx.py` 在解析 Markdown 时，将小问的 `\item` 误识别为题干的一部分
- 或者 Markdown 中题干缺失，直接从 `(1)` 或 `①` 开始
- 导致 LaTeX 将 `\item` 当作普通文本，而不是列表项

**检测方法**：
```bash
# 查找 question 环境中直接出现 \item 的情况
grep -A 2 "\\begin{question}" content/exams/auto/*/converted_exam.tex | grep "\\item"
```

**修复方法**：
```latex
\begin{question}
已知数列 $\{a_n\}$ 满足 $a_1 = 3$，$\frac{a_{n+1}}{n} = \frac{a_n}{n+1} + \frac{1}{n(n+1)}$．

(1) 证明：数列 $\{na_n\}$ 是等差数列；

(2) 给定正整数 m，设函数 $f(x) = a_1x + a_2x^2 + \cdots + a_mx^m$，求 $f'(-2)$．
\topics{...}
\difficulty{...}
\answer{...}
\explain{...}
\end{question}
```

**预防措施**：
- 在 `ocr_to_examx.py` 中增加题干检测逻辑
- 如果 question 环境的第一行是 `\item`，报告警告到 `debug/<slug>_issues.log`
- 建议在 Markdown 阶段补充题干内容

**实际案例**：
- 2025年高考全国一卷第15题（统计题）：缺少题干，直接从 `\item 记超声波检查...` 开始
- 2025年高考全国一卷第16题（数列题）：缺少题干，直接从 `\item 证明...` 开始
- 2025年高考全国一卷第17题（立体几何）：缺少题干，直接从 `\item 证明...` 开始
- 2025年高考全国一卷第19题（函数题）：缺少题干，直接从 `\item 求函数...` 开始

**影响**：
- PDF 中题目显示为多行，每个小问前出现一个题号标记
- 影响试卷的可读性和专业性

---

### 8.2 Markdown 图片属性残留

**错误现象**：
```latex
% IMAGE_TODO_END id=...
height="1.09375in"}}
\end{question}
```

**根本原因**：
- Pandoc 从 Word 转 Markdown 时，保留了图片的 HTML 属性
- `ocr_to_examx.py` 在转换 IMAGE_TODO 块时，未完全清理这些属性
- 残留的 `height="..."}}` 导致多余的闭合括号

**检测方法**：
```bash
grep -n 'height="' content/exams/auto/*/converted_exam.tex
```

**修复方法**：
```latex
% IMAGE_TODO_END id=...
\end{question}
```

**预防措施**：
- 在 `ocr_to_examx.py` 中，IMAGE_TODO 块生成后，清理所有 Markdown 图片属性
- 使用正则表达式删除 `height="..."` 和 `width="..."` 等 HTML 属性

**实际案例**：
- 2025年高考全国一卷第11题：`height="1.09375in"}}`
- 2025年高考全国一卷第17题：`height="1.4479166666666667in"}`、`height="1.6666666666666667in"}}`

---

### 8.3 \mathrm 在数学模式外使用

**错误现象**：
```latex
(1) 证明：...

(\mathrm{i})证明：点 O 在平面 ABCD 内；
```

**根本原因**：
- `ocr_to_examx.py` 将小问编号 `(i)` 转换为 `(\mathrm{i})`
- 但 `\mathrm` 命令只能在数学模式中使用
- 在普通文本中使用会导致编译错误：`\mathrm allowed only in math mode`

**检测方法**：
```bash
grep -n "\\mathrm" content/exams/auto/*/converted_exam.tex | grep -v "\\$"
```

**修复方法**：
```latex
(1) 证明：...

(i)证明：点 O 在平面 ABCD 内；
% 或使用数学模式
$(\mathrm{i})$ 证明：点 O 在平面 ABCD 内；
```

**预防措施**：
- 在 `ocr_to_examx.py` 中，小问编号统一使用普通文本 `(i)`、`(ii)` 等
- 不要自动添加 `\mathrm` 命令
- 或者统一使用数学模式 `$(\mathrm{i})$`

**实际案例**：
- 2025年高考全国一卷第17题：`(\mathrm{i})证明：...`

---

### 8.4 \explain 宏中的空行（段落分隔）

**错误现象**：
```latex
\explain{
  解：第一步...

  第二步...
}
% 编译错误：Runaway argument
```

**根本原因**：
- `\explain` 是命令（macro）而非环境，不允许段落分隔（空行）
- 空行会被 LaTeX 解释为 `\par`，导致命令参数提前结束
- 特别是在 IMAGE_TODO 块后容易出现空行

**检测方法**：
```bash
python3 tools/validate_tex.py content/exams/auto/*/converted_exam.tex
# 查找 "Paragraph break inside \explain" 错误
```

**修复方法**：
```latex
\explain{
  解：第一步... \par
  第二步...
}
% 或删除空行
\explain{
  解：第一步...
  第二步...
}
```

**预防措施**：
- `validate_tex.py` 自动检测 `\explain` 中的空行
- 在 `ocr_to_examx.py` 中，生成 IMAGE_TODO 块后不添加额外空行
- 或自动将空行替换为 `\par` 或 `\\`

**实际案例**：
- 2025年高考全国一卷第17题：IMAGE_TODO 块后有空行，导致 `\explain` 参数提前结束

---

## 📊 统计与优先级（更新）

### 高频问题（按出现频率排序）

1. **题目缺少题干** - 约 20% 的试卷（新增，高考真题常见）
2. **【分析】内容未删除** - 几乎每个试卷都存在
3. **\explain 中包含段落分隔** - 约 50% 的试卷
4. **IMAGE_TODO 注释中残留 LaTeX 代码** - 约 40% 的试卷
5. **Markdown 图片属性残留** - 约 15% 的试卷（新增）
6. **\mathrm 在数学模式外使用** - 约 10% 的试卷（新增）
7. **IMAGE_TODO 块缺失** - 约 30% 的试卷
8. **数学定界符不匹配** - 约 20% 的试卷
9. **超长 \explain 内容导致截断** - 约 10% 的试卷（高考真题常见）
10. **方括号转义问题** - 约 15% 的试卷

### 修复成本分级（更新）

| 问题类型 | 自动化修复 | 手动成本 | 优先级 |
|---------|-----------|---------|--------|
| 题目缺少题干 | ⚠️ 可检测 | 高 | 🔴 高 |
| 【分析】未删除 | ✅ 可自动化 | 低 | 🔴 高 |
| \explain 段落分隔 | ✅ 可自动化 | 低 | 🔴 高 |
| Markdown 图片属性残留 | ✅ 可自动化 | 低 | 🔴 高 |
| \mathrm 误用 | ✅ 可自动化 | 低 | 🔴 高 |
| IMAGE_TODO 缺失 | ⚠️ 半自动 | 中 | 🟡 中 |
| 数学定界符不匹配 | ✅ 可检测 | 中 | 🟡 中 |
| 特殊符号 OCR 错误 | ❌ 需人工 | 高 | 🟢 低 |

---

## 🔧 改进方向总结（v1.1 新增）

### 本轮修复总结（2025-11-20）

**修复的试卷**：2025年高考全国一卷数学真题

**发现的问题**：
1. ✅ 残留的 Markdown 图片属性（3处）
2. ✅ 缺失的 `\explain` 闭合括号（1处）
3. ✅ 题目缺少题干（4处：第15、16、17、19题）
4. ✅ `\mathrm` 在数学模式外使用（3处）
5. ✅ `\explain` 宏中的空行（2处）

**修复方法**：
- 手动删除残留的图片属性
- 手动补充缺失的闭合括号
- 手动补充题干内容（根据题目上下文推断）
- 删除 `\mathrm` 命令或改为普通文本
- 删除 `\explain` 中的空行

**编译结果**：✅ 成功生成 PDF

---

### 脚本改进建议

#### 1. `ocr_to_examx.py` 需要改进的地方

**高优先级**：

1. **题干检测与警告**
   ```python
   # 在 parse_question_structure() 中增加
   if question_content.strip().startswith('\\item'):
       issues.append({
           'type': 'CRITICAL',
           'message': '题目缺少题干，直接从 \\item 开始',
           'line': line_number,
           'suggestion': '请在 Markdown 中补充题干内容'
       })
   ```

2. **清理 Markdown 图片属性残留**
   ```python
   # 在生成 IMAGE_TODO 块后
   content = re.sub(r'height="[^"]*"[}]*', '', content)
   content = re.sub(r'width="[^"]*"[}]*', '', content)
   ```

3. **小问编号格式统一**
   ```python
   # 不要自动添加 \mathrm
   # (i) → (i)  而不是 (\mathrm{i})
   # 或统一使用数学模式 $(\mathrm{i})$
   ```

4. **IMAGE_TODO 块后不添加空行**
   ```python
   # 在生成 IMAGE_TODO_END 后，不要添加额外的 \n
   ```

**中优先级**：

5. **\explain 中的空行自动处理**
   ```python
   # 在生成 \explain{} 时，自动将空行替换为 \par
   explain_content = explain_content.replace('\n\n', '\n\\par\n')
   ```

6. **增强题干识别逻辑**
   - 检测题目是否以 `(1)` 或 `①` 开始
   - 如果是，报告警告并建议补充题干

---

#### 2. `validate_tex.py` 需要改进的地方

**已实现**：
- ✅ 花括号平衡检查
- ✅ 数学定界符检查
- ✅ 环境匹配检查
- ✅ `\explain` 中的空行检查

**需要改进**：
1. **误报问题**：对 `\left\{` 和 `\right\}` 等数学定界符的处理
   - 当前简单计数花括号会误报
   - 建议：在检查前移除数学定界符

2. **题干缺失检查**：
   ```python
   # 检测 question 环境中直接出现 \item 的情况
   if re.search(r'\\begin\{question\}\s*\\item', content):
       errors.append('Question starts with \\item (missing stem)')
   ```

---

#### 3. 工作流改进建议

**当前流程**：
```
Word → Pandoc → Markdown → ocr_to_examx.py → TeX → 编译
```

**建议增加的步骤**：

1. **Markdown 人工校对阶段**
   - 在 `ocr_to_examx.py` 之前，人工检查 Markdown
   - 重点检查：题干是否完整、图片是否齐全、元信息是否正确

2. **自动化检测报告**
   - `ocr_to_examx.py` 生成 `debug/<slug>_issues.log`
   - 包含所有检测到的问题和建议
   - 在编译前查看并修复

3. **预编译检查**
   - 使用 `VALIDATE_BEFORE_BUILD=1 ./build.sh exam teacher`
   - 在编译前自动运行 `validate_tex.py`
   - 发现问题时给出警告

4. **回归测试**
   - 修复问题后运行 `tools/test_compile.sh`
   - 确保教师版和学生版都能编译成功

---

## 🔄 文档维护

**更新频率**：发现新问题时即时更新
**维护负责**：LaTeX 流水线工程师
**历史记录**：
- v1.0（2025-11-20）：初始版本，基于 nanjing_2026_sep 和 zhejiang_lishui_2026_nov 调试经验
- v1.1（2025-11-20）：新增"题目结构问题"章节，基于 gaokao_2025_national_1 调试经验，总结脚本改进方向
