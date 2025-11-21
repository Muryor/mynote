# 图片流水线开发任务清单

> **文档定位**: 开发者任务说明，包含 Tasks A/B/C/D 的详细实现需求  
> **配套文档**: [workflow.md](../workflow.md), [REFERENCE.md](../REFERENCE.md), [IMAGE_JOBS_FULL.md](../IMAGE_JOBS_FULL.md)

---

## 任务概览

| 任务 | 目标 | 状态 | 优先级 |
|------|------|------|--------|
| Task A | 改造 `ocr_to_examx.py` 统一输出 IMAGE_TODO | ✅ 已完成 | P0 |
| Task B | 新增 `export_image_jobs.py` 生成 JSONL | ✅ 已完成 | P0 |
| Task C | 新增 `apply_tikz_snippets.py` 回填 TikZ | ✅ 已完成 | P0 |
| Task D | 新增 `write_snippets_from_jsonl.py` 落地 TikZ | ✅ 已完成 | P0 |
| Task E | 新增 `generate_tikz_from_images.py` AI 批量生成 | 🚧 未实现 | P1 |

---

## Task A：改造 `ocr_to_examx.py`，输出统一的 IMAGE_TODO_START/END

**目标**: 确保所有 Markdown 图片（独立行 + 内联）都转换为标准 IMAGE_TODO 占位块

### 实现要求

1. **所有 Markdown 图片转换**:
   - 独立行图片：`![description](path)` → `IMAGE_TODO_START/END` 块
   - 内联图片：文本中的 `![](path)` → 用占位符替换 + 在适当位置插入 IMAGE_TODO 块

2. **统一命名规范**:
   - `id`: `<slug>-Q<题号>-img<序号>`
   - 示例: `nanjing_2026_sep-Q3-img1`

3. **自测要求**:
   - 在 `run_self_tests()` 中新增测试用例
   - 覆盖场景: 同时存在行内/独立图片的题目
   - 确保 TeX 中不再出现 `![](...)` 这样的 Markdown 图片语法

### 关键字段

```latex
% IMAGE_TODO_START id=<id> path=<path> width=<pct>% inline=<bool> question_index=<num> sub_index=<idx>
% CONTEXT_BEFORE: <题干上下文>
% CONTEXT_AFTER: <题干下文>
\begin{tikzpicture}
  % TODO: AI_AGENT_REPLACE_ME (id=<id>)
\end{tikzpicture}
% IMAGE_TODO_END id=<id>
```

### 完成标准

- [ ] 所有图片类型（独立/内联/WMF/PNG）都正确转换
- [ ] TeX 文件中无残留 Markdown 图片语法
- [ ] 单元测试通过
- [ ] 实际试卷测试无编译错误

**参考规范**: [REFERENCE.md § 2](../REFERENCE.md)

---

## Task B：新增 `export_image_jobs.py` 生成 `image_jobs.jsonl`

**目标**: 从 TeX 文件中解析所有 IMAGE_TODO 占位符，导出为结构化 JSONL

### 实现要求

1. **解析 IMAGE_TODO 块**:
   - 从一个或多个 `converted_exam.tex` 中提取所有 IMAGE_TODO_START/END
   - 每个 IMAGE_TODO 对应一行 JSON 输出

2. **命令行参数**:
   ```bash
   python tools/images/export_image_jobs.py \
       --files <tex_file1> [<tex_file2> ...]  # 支持多文件
       --output <output_jsonl>
   ```

3. **字段完整性**:
   - 必需字段: `id`, `path`, `width_pct`, `inline`, `exam_slug`, `tex_file`
   - 推断字段: `exam_prefix`, `exam_dir`, `tikz_snippets_dir`（参见 IMAGE_JOBS_FORMAT.md）
   - 可选字段: `question_index`, `sub_index`, `context_before`, `context_after`, `todo_block_start_line`, `todo_block_end_line`

4. **错误处理**:
   - 对字段缺失/格式错误的 IMAGE_TODO，打印警告并跳过（不崩溃）
   - 输出统计信息: 成功解析数量、跳过数量

### 输出示例

```json
{"id": "nanjing_2026_sep-Q3-img1", "exam_slug": "nanjing_2026_sep", "exam_prefix": "nanjing_2026_sep", "exam_dir": "content/exams/auto/nanjing_2026_sep", "tikz_snippets_dir": "content/exams/auto/nanjing_2026_sep/tikz_snippets", "tex_file": "content/exams/auto/nanjing_2026_sep/converted_exam.tex", "question_index": 3, "sub_index": 1, "path": "word_to_tex/output/figures/media/image1.png", "width_pct": 60, "inline": false, "context_before": "已知函数 f(x)...", "context_after": "则下列结论中正确的是..."}
```

### 完成标准

- [ ] 支持多文件批量解析
- [ ] 所有必需字段正确填充
- [ ] 推断逻辑符合 IMAGE_JOBS_FORMAT.md 规范
- [ ] 错误处理健壮（缺失字段不崩溃）
- [ ] 输出 JSONL 格式正确（每行一个 JSON 对象）

**参考规范**: [IMAGE_JOBS_FULL.md](../IMAGE_JOBS_FULL.md)

---

## Task C：新增 `apply_tikz_snippets.py` 回填 TikZ

**目标**: 读取 TikZ 片段文件，替换 TeX 文件中的 IMAGE_TODO 占位符

### 实现要求

1. **输入参数**:
   ```bash
   python tools/images/apply_tikz_snippets.py \
       --tex-file <tex_file>                    # 待回填的 TeX 文件
       --snippets-dir <snippets_dir> (可选)     # TikZ 片段目录（默认: tex_file 所在目录的 tikz_snippets）
       --output <output_file> (可选)            # 输出文件路径（默认: 覆盖原文件，自动备份为 .tex.bak）
   ```

2. **回填逻辑**:
   - 遍历 TeX 文件中的所有 IMAGE_TODO 块
   - 根据 `id` 查找对应的 TikZ 片段文件: `<snippets_dir>/<id>.tex`
   - 如果片段存在，替换 `% TODO: AI_AGENT_REPLACE_ME` 行为片段内容
   - 如果片段不存在，跳过该 IMAGE_TODO（保留占位符）

3. **运行时输出**:
   - 打印实际使用的 snippets 目录（绝对路径）
   - 列出缺少 snippet 的图片 id（若存在）
   - 统计信息: 总 TODO 数量、成功替换、跳过（缺失 snippet）

### 使用示例

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

### 完成标准

- [ ] 默认 snippets 目录推断正确
- [ ] 支持覆盖原文件（自动备份）
- [ ] 支持指定输出文件
- [ ] 缺失 snippet 时优雅跳过（不报错）
- [ ] 输出清晰的统计信息

**参考规范**: [REFERENCE.md § 2](../REFERENCE.md)

---

## Task D：新增 `write_snippets_from_jsonl.py` 落地 TikZ

**目标**: 读取 AI 生成的 TikZ 代码（JSONL 格式），写入规范目录

### 实现要求

1. **输入参数**:
   ```bash
   python3 tools/images/write_snippets_from_jsonl.py \
       --jobs-file <image_jobs.jsonl>       # export_image_jobs.py 生成的文件
       --tikz-file <generated_tikz.jsonl>   # AI 输出的 TikZ 代码
       --dry-run (可选)                      # 仅预览写入计划，不实际创建文件
       --snippets-dir (可选)                # 强制所有 snippet 写入该目录（调试用，正常情况下不提供）
   ```

2. **AI 输出格式**:
   每行一个 JSON 对象:
   ```json
   {"id": "nanjing_2026_sep-Q3-img1", "tikz_code": "\\begin{tikzpicture}\n...\n\\end{tikzpicture}"}
   ```

3. **写入逻辑**:
   - 从 `jobs-file` 读取每个 job，获取 `tikz_snippets_dir` 字段
   - 从 `tikz-file` 读取对应 `id` 的 `tikz_code`
   - 写入路径: `<tikz_snippets_dir>/<id>.tex`
   - 如果 `tikz_code` 缺失，跳过该 id（仅统计与警告）

4. **目录推断**:
   - 每条 job 的目标目录由 `utils.get_tikz_snippets_dir(job)` 推断（唯一真理）
   - **禁止硬编码目录路径**

### 日志格式示例

```text
Snippets 目录: /full/path/to/content/exams/auto/nanjing_2026_sep/tikz_snippets
[TikZ] write snippet: id=nanjing_2026_sep-Q8-img1  ->  content/exams/auto/nanjing_2026_sep/tikz_snippets/nanjing_2026_sep-Q8-img1.tex
[TikZ] write snippet: id=nanjing_2026_sep-Q14-img1  ->  content/exams/auto/nanjing_2026_sep/tikz_snippets/nanjing_2026_sep-Q14-img1.tex

结果：
  ✓ 成功写入: 5
  ✗ 写入错误: 0
  ☐ 缺少 tikz_code: 0
```

### 完成标准

- [ ] 支持 `--dry-run` 预览模式
- [ ] 目录推断逻辑调用 `utils.get_tikz_snippets_dir()`（不硬编码）
- [ ] 缺失 `tikz_code` 时优雅跳过（不崩溃）
- [ ] 输出清晰的日志和统计信息
- [ ] 自动创建不存在的 snippets 目录

**参考规范**: [IMAGE_JOBS_FULL.md](../IMAGE_JOBS_FULL.md)

---

## Task E（规划中）：新增 `generate_tikz_from_images.py` AI 批量生成

**目标**: 调用 AI API 批量生成 TikZ 代码

### 实现要求（草案）

1. **输入参数**:
   ```bash
   python3 tools/images/generate_tikz_from_images.py \
       --jobs-file <image_jobs.jsonl>     # 图片任务列表
       --output <generated_tikz.jsonl>    # 输出 TikZ 代码
       --api-key <api_key> (可选)         # AI API 密钥（或从环境变量读取）
       --model <model_name> (可选)        # 模型名称（默认: gpt-4）
   ```

2. **AI Agent 使用场景**:

如果 Agent 可以直接 import 仓库代码，建议调用:

```python
from pathlib import Path
import json
from tools.images.utils import get_tikz_snippets_dir, write_tikz_snippet_to_dir

jobs = [json.loads(line) for line in Path("image_jobs.jsonl").read_text().splitlines() if line.strip()]

for job in jobs:
    # AI 生成 TikZ 代码
    tikz_code = your_ai_agent_function(job)
    
    # 写入规范目录
    snippets_dir = get_tikz_snippets_dir(job)
    write_tikz_snippet_to_dir(snippets_dir, job["id"], tikz_code)
```

3. **AI Prompt 要求**:
   - 使用标准 TikZ/pgfplots 语法
   - 避免中文标签
   - 优先数学语义正确性
   - 复杂图可适当简化
   - 禁止输出空 tikzpicture

4. **错误处理**:
   - API 调用失败时重试（最多 3 次）
   - 生成代码语法检查（简单验证）
   - 失败的 job 记录到 `failed_jobs.jsonl`

### 完成标准（待确认）

- [ ] 支持多种 AI API（OpenAI, Claude, etc.）
- [ ] 批量处理性能优化（并发请求）
- [ ] 生成质量评分机制（可选）
- [ ] 失败重试与错误日志
- [ ] 输出格式符合 Task D 输入要求

**参考规范**: [TIKZ_AGENT_PROMPT.md](../TIKZ_AGENT_PROMPT.md)

---

## 完整流程示例

### 场景: 从 Word 文档到 TikZ PDF

```bash
# Step 1: Word → TeX（Task A 已完成）
word_to_tex/scripts/preprocess_docx.sh \
    "word_to_tex/input/<文件名>.docx" \
    "<输出前缀>" \
    "<试卷标题>"

# Step 2: 导出图片任务（Task B）
python tools/images/export_image_jobs.py \
    --files "content/exams/auto/<输出前缀>/converted_exam.tex" \
    --output "content/exams/auto/<输出前缀>/image_jobs.jsonl"

# Step 3: AI 生成 TikZ（Task E - 手动或调用 API）
# 输出: generated_tikz.jsonl（每行包含 id + tikz_code）

# Step 4: 写入 TikZ 片段（Task D）
python3 tools/images/write_snippets_from_jsonl.py \
    --jobs-file "content/exams/auto/<输出前缀>/image_jobs.jsonl" \
    --tikz-file "generated_tikz.jsonl"

# Step 5: 回填到 TeX 文件（Task C）
python tools/images/apply_tikz_snippets.py \
    --tex-file "content/exams/auto/<输出前缀>/converted_exam.tex"

# Step 6: 编译 PDF
./build.sh exam teacher
```

---

## 测试清单

### 单元测试

- [ ] Task A: `ocr_to_examx.py` 的 IMAGE_TODO 生成逻辑
  - 测试用例: 同时存在独立/内联图片
  - 验证: TeX 中无 Markdown 图片语法残留

- [ ] Task B: `export_image_jobs.py` 的字段推断
  - 测试用例: 多文件、缺失字段、格式错误
  - 验证: JSONL 格式正确、推断字段准确

- [ ] Task C: `apply_tikz_snippets.py` 的回填逻辑
  - 测试用例: 部分 snippet 缺失、覆盖原文件
  - 验证: 备份文件创建、缺失 snippet 优雅跳过

- [ ] Task D: `write_snippets_from_jsonl.py` 的目录推断
  - 测试用例: 不同 exam_slug、dry-run 模式
  - 验证: 目录路径正确、不硬编码路径

### 集成测试

- [ ] 完整流程: Word → TeX → JSONL → TikZ → PDF
  - 测试试卷: 南京 2026 九月质检、杭州 2025-2026 质检
  - 验证: PDF 正常生成、图片显示正确

- [ ] 错误场景: 缺失图片文件、格式错误、API 失败
  - 验证: 优雅降级、清晰的错误提示

---

## 参考文档

- **格式规范**: [REFERENCE.md](../REFERENCE.md)
- **完整流程**: [workflow.md](../workflow.md)
- **图片任务字段**: [IMAGE_JOBS_FULL.md](../IMAGE_JOBS_FULL.md)
- **TikZ 生成指南**: [TIKZ_AGENT_PROMPT.md](../TIKZ_AGENT_PROMPT.md)
- **版本历史**: [archive/CHANGELOG.md](../archive/CHANGELOG.md)

---

**维护者**: [项目维护团队]  
**最后更新**: 2025-01-XX
