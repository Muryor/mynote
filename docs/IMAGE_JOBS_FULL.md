# image_jobs.jsonl 字段规范

## 生成命令

```bash
python tools/images/export_image_jobs.py --files <tex_file>
```

## JSON 示例

```json
{
  "id": "exam-Q3-img1",
  "exam_prefix": "exam_2025",
  "exam_dir": "content/exams/auto/exam_2025",
  "tikz_snippets_dir": "content/exams/auto/exam_2025/tikz_snippets",
  "tex_file": "content/exams/auto/exam_2025/converted_exam.tex",
  "question_index": 3,
  "sub_index": 1,
  "path": "figures/media/image1.png",
  "width_pct": 60,
  "inline": false
}
```

## 核心字段

| 字段 | 用途 |
|------|------|
| `id` | TikZ 文件名 `{id}.tex` |
| `exam_dir` | 试卷目录 |
| `tikz_snippets_dir` | TikZ 输出目录 |
| `path` | 原始图片路径 |
| `width_pct` | 宽度百分比 |

## TikZ 目录推断

```python
def get_tikz_dir(job):
    if job.get('tikz_snippets_dir'): return Path(job['tikz_snippets_dir'])
    if job.get('exam_dir'): return Path(job['exam_dir']) / 'tikz_snippets'
    if job.get('exam_prefix'): return Path('content/exams/auto') / job['exam_prefix'] / 'tikz_snippets'
    raise ValueError('missing fields')
```

## 写入规范

- 文件名: `{id}.tex`
- 内容: 完整 `\begin{tikzpicture}...\end{tikzpicture}`
- 工具: `write_snippets_from_jsonl.py`
