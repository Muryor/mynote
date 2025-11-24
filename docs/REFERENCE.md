# LaTeX 试卷流水线参考手册 (v3.6)

> **用途**: 所有格式规范的统一速查手册  
> **更新**: 2025-11-24 （新增：附件模板与图片路径推断章节，版本与 workflow 同步）

---

## 1. 元信息映射规范

### 1.1 映射表

| Markdown 标记 | examx 命令 | 处理规则 |
|--------------|-----------|---------|
| `【答案】A` | `\answer{A}` | 直接映射 |
| `【难度】0.85` | `\difficulty{0.85}` | 直接映射 |
| `【知识点】...` 或 `【考点】...` | `\topics{...}` | 合并为一个 |
| `【详解】...` | `\explain{...}` | **唯一来源** |
| `【分析】...` | **舍弃** | ⚠️ **严禁使用** |

### 1.2 强制规则（不可违反）

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

---

## 2. IMAGE_TODO 占位符格式

### 2.1 基本格式示例

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

### 2.2 字段说明

| 字段 | 必需 | 说明 |
|------|------|------|
| `id` | ✅ | 全局唯一图片 ID，建议命名：`<slug>-Q<题号>-img<序号>` |
| `path` | ✅ | 原始图片文件的相对路径 |
| `width` | ✅ | 推荐宽度百分比，例如 `60%` |
| `inline` | ✅ | 是否行内图片：`true` / `false` |
| `question_index` | 建议 | 题号（整数） |
| `sub_index` | 建议 | 小问序号或该题下图片序号（从 1 开始） |
| `CONTEXT_BEFORE` | 可选 | 上文上下文，帮助 AI 理解图像用途 |
| `CONTEXT_AFTER` | 可选 | 下文上下文 |

> **注意**: 即使后续填入了真实 TikZ 代码，`IMAGE_TODO_START/END` 注释也建议保留不删，以便后续重新导出或替换图片。

---

## 3. image_jobs.jsonl 字段速查

### 3.1 生成命令

```bash
python tools/images/export_image_jobs.py \
  --files content/exams/auto/<slug>/converted_exam.tex
```

输出：`content/exams/auto/<slug>/image_jobs.jsonl`

### 3.2 最小 JSON 示例

```json
{
  "id": "hangzhou_2025-Q3-img1",
  "exam_prefix": "hangzhou_2025",
  "exam_dir": "content/exams/auto/hangzhou_2025",
  "tikz_snippets_dir": "content/exams/auto/hangzhou_2025/tikz_snippets",
  "tex_file": "content/exams/auto/hangzhou_2025/converted_exam.tex",
  "question_index": 3,
  "sub_index": 1,
  "path": "word_to_tex/output/figures/media/image1.png",
  "width_pct": 60,
  "inline": false
}
```

### 3.3 核心字段表

| 字段 | 用途 |
|------|------|
| id | 生成/匹配 TikZ 片段文件名 `{id}.tex` |
| exam_prefix | 试卷标识（路径推断后备） |
| exam_dir | 试卷根目录 |
| tikz_snippets_dir | 目标写入目录（若存在直接用） |
| tex_file | 来源 TeX 文件路径 |
| question_index/sub_index | 题号/序号（排序/提示） |
| path | 原始图片路径供识别/参考 |
| width_pct | 推荐宽度（整数百分比） |
| inline | 是否行内图（排版策略） |

可选字段：`context_before` / `context_after`、`todo_block_start_line` / `todo_block_end_line`。

### 3.4 TikZ 目录推断（唯一真理）

**推断顺序**：

1. 若有 `tikz_snippets_dir`：使用它。
2. 若有 `exam_dir`：`exam_dir / tikz_snippets`。
3. 若有 `exam_prefix`：`content/exams/auto/<exam_prefix>/tikz_snippets`。
4. 否则报错（缺少必要字段）。

**实现参考**: `tools/images/utils.py::get_tikz_snippets_dir`

**伪代码**:

```python
def get_tikz_dir(job):
    if job.get('tikz_snippets_dir'): 
        return Path(job['tikz_snippets_dir'])
    if job.get('exam_dir'): 
        return Path(job['exam_dir']) / 'tikz_snippets'
    if job.get('exam_prefix'): 
        return Path('content/exams/auto') / job['exam_prefix'] / 'tikz_snippets'
    raise ValueError('missing directory fields')
```

### 3.5 写入规范

**文件名**: `{id}.tex`

**内容**: 完整 `\begin{tikzpicture} ... \end{tikzpicture}`

**推荐工具**: `write_snippets_from_jsonl.py` 或 `utils.write_tikz_snippet_to_dir`

**日志格式**:

```text
[TikZ] write snippet: id=<ID>  ->  <path>
```

### 3.6 回填工具

```bash
# apply_tikz_snippets.py 默认行为
python tools/images/apply_tikz_snippets.py \
  --tex-file content/exams/auto/<slug>/converted_exam.tex
```

**默认**: `--snippets-dir` 为空时使用 `Path(<tex_file>).parent/'tikz_snippets'`

**缺失片段**: 跳过并在统计中列出

> **完整字段定义**: [IMAGE_JOBS_FULL.md](IMAGE_JOBS_FULL.md)

---

## 4. \exstep 详解格式化

### 4.1 核心语法

```latex
% 自动编号步骤
\exstep

% 自定义标签
\exstep[法一]
\exstep[向量法]
\exstep[小结]
```

### 4.2 选择策略

| 解析长度 | 推荐形式 | 说明 |
|----------|----------|------|
| ≤3 行 | 原样 | 不引入结构噪音 |
| 3–5 行 | 空行分段 | 逻辑块分隔 |
| 5–10 行 | 自动编号 `\exstep` | 演算 / 证明序列 |
| >10 行 或多解法 | `\exstep[标签]` | 策略切换 / 汇总 |

### 4.3 最小示例

```latex
\explain{
第一段推导...

\exstep 求导得 f'(x) = ...
\exstep 判断符号得单调性
\exstep[结论] 最大值为 3\sqrt{3}
}
```

### 4.4 标签建议

**简洁命名**:
- ✅ 法一 / 法二 / 代入 / 判定 / 小结
- ❌ 避免长句：不写"利用导数求函数单调性" → 改"导数判定"

### 4.5 常见误用

| 误用 | 问题 | 正确做法 |
|------|------|-----------|
| 每行都用 `\exstep` | 失去层次 | 仅关键跳点标记 |
| 标签冗长 | 占空间 | 用 1~3 词概念 |
| 步骤放公式内部 | 语法错 | 在公式外插入 `\exstep` |

> **完整示例库**: [EXPLAIN_FULL.md](EXPLAIN_FULL.md)

---

## 5. TikZ 生成约定

### 5.1 输入输出格式

**输入**:
- `image_jobs.jsonl` 单条记录
- 对应图片文件

**输出**:

```tex
\begin{tikzpicture}
  % 完整 TikZ 代码
\end{tikzpicture}
```

### 5.2 核心要求

- ✅ 语义化简化（复杂图允许合理简化）
- ❌ 禁止空环境（不能输出空 tikzpicture）
- ✅ 避免中文标签（使用数学符号或英文）
- ✅ 使用标准 tikz/pgfplots 库
- ✅ 确保数学语义正确

> **完整 AI Prompt**: [TIKZ_AGENT_PROMPT.md](TIKZ_AGENT_PROMPT.md)

---

## 6. 常用路径速查

```text
输入文件: word_to_tex/input/<file>.docx
输出MD: word_to_tex/output/<slug>_raw.md
输出TeX: content/exams/auto/<slug>/converted_exam.tex
图片目录: word_to_tex/output/figures/
TikZ片段: content/exams/auto/<slug>/tikz_snippets/
编译PDF: output/wrap-exam-teacher.pdf
错误日志: output/last_error.log
构建日志: output/build.log
配置: settings/metadata.tex
```

---

## 7. 常见问题速查

| 问题 | 原因 | 处理 |
|------|------|------|
| 【分析】混入 \explain{} | 元信息解析错误 | 检查 META_PATTERNS，重新生成 |
| IMAGE_TODO 未识别 | 格式不完整 | 补全必需字段 (id/path/width/inline) |
| TikZ 片段未写入 | 目录推断失败 | 使用 get_tikz_snippets_dir() 打印路径 |
| 回填缺失 | AI 未生成对应 id | 检查 generated_tikz.jsonl 完整性 |
| 数学公式不平衡 | OCR 边界错误 | 使用 MathStateMachine 自动修复 |

> **详细排查流程**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## 附件 Markdown 模板

### 基本格式

```markdown
20. 某题题干……

附：某地区历年数据表

| 年份 | A省 | B省 |
| ---- | --- | --- |
| 2020 |  10 |  12 |
| 2021 |  11 |  13 |
```

### 转换结果

附件会在 question 环境内部末尾渲染为：

```latex
\vspace{1em}
\textbf{附：}

\begin{center}
\begin{tabular}{ccc}
\hline
年份 & A省 & B省 \\
\hline
2020 & 10 & 12 \\
2021 & 11 & 13 \\
\hline
\end{tabular}
\end{center}
```

### 支持的附件类型

1. **表格附件**：Markdown 表格或 Box-drawing 字符表格
2. **文本附件**：以"附："、"附表"、"参考数据表"开头的文本
3. **图表附件**：包含特殊字符的图表（预留）

---

## 图片路径推断规则

### 自动推断逻辑

当未通过 `--figures-dir` 显式指定图片目录时，系统会自动推断：

**输入示例**：`word_to_tex/input/js-suxichang-2025-q2.md`

**推断顺序**：
1. `word_to_tex/output/figures/js-suxichang-2025-q2`
2. `word_to_tex/output/figures/js-suxichang-2025-q2/media`

**使用方法**：
```bash
# 自动推断（推荐）
python3 tools/core/ocr_to_examx.py input.md output/

# 手动指定（可选）
python3 tools/core/ocr_to_examx.py input.md output/ --figures-dir path/to/figures
```

**注意事项**：
- 系统会自动去除文件名后缀（`_local`、`_preprocessed`、`_raw`）
- 推断失败时不影响程序运行，仅提示警告

---

**最后更新**: v3.6（2025-11-24）
