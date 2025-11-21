# image_jobs.jsonl 精简规范

> 完整字段与扩展说明：`IMAGE_JOBS_FULL.md`。此文件保留最小必需信息与目录推断“唯一真理”。

## 生成命令

```bash
python tools/images/export_image_jobs.py \
  --files content/exams/auto/<slug>/converted_exam.tex
```

输出：`content/exams/auto/<slug>/image_jobs.jsonl`

## 最小 JSON 示例

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

## 核心字段（使用时优先）

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

可选：`context_before` / `context_after`、`todo_block_start_line` / `todo_block_end_line`。

## TikZ 目录推断（唯一真理）

顺序：

1. 若有 `tikz_snippets_dir`：使用它。
2. 若有 `exam_dir`：`exam_dir / tikz_snippets`。
3. 若有 `exam_prefix`：`content/exams/auto/<exam_prefix>/tikz_snippets`。
4. 否则报错（缺少必要字段）。

实现参考：`tools/images/utils.py::get_tikz_snippets_dir`。

伪代码：

```python
def get_tikz_dir(job):
    if job.get('tikz_snippets_dir'): return Path(job['tikz_snippets_dir'])
    if job.get('exam_dir'): return Path(job['exam_dir']) / 'tikz_snippets'
    if job.get('exam_prefix'): return Path('content/exams/auto') / job['exam_prefix'] / 'tikz_snippets'
    raise ValueError('missing directory fields')
```

## 写入规范

文件名：`{id}.tex`。内容需包含完整 `\begin{tikzpicture} ... \end{tikzpicture}`。
调用：`write_snippets_from_jsonl.py` 或 `utils.write_tikz_snippet_to_dir`。

日志格式：

```text
[TikZ] write snippet: id=<ID>  ->  <path>
```

## 回填（apply_tikz_snippets.py）

默认 `--snippets-dir` 为空：使用 `Path(<tex_file>).parent/'tikz_snippets'`。缺失片段跳过并统计。

## 常见问题速查

| 问题 | 原因 | 处理 |
|------|------|------|
| 片段未写入 | 目录推断失败 | 打印路径核对字段是否缺失 |
| 回填缺失 | AI 未生成对应 id | 检查生成列表 / 重试生成 |
| 写入旧目录 | 硬编码历史路径 | 改用推断函数 |

## 参考 & 外链

- 完整规范：`IMAGE_JOBS_FULL.md`
- Agent Prompt：`TIKZ_AGENT_PROMPT.md`
- 工作流概览：`workflow.md`（阶段二）

版本：v1（精简）
