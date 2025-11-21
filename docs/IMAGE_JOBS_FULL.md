# image_jobs.jsonl 全量字段规范 (Full)

> 精简版请参考 `IMAGE_JOBS_FORMAT.md`；此文件保留全部字段说明、示例与扩展建议。

（以下为原始完整内容）

# image_jobs.jsonl 字段规范与使用指南

本文档定义由 `tools/images/export_image_jobs.py` 导出的 `image_jobs.jsonl` 每行 JSON 对象的字段、目录推断逻辑以及下游（看图→生成 TikZ）脚本/Agent 的统一写入规范。

## 1. 生成来源

命令示例：

```bash
python tools/images/export_image_jobs.py \
  --files content/exams/auto/nanjing_2026_sep/converted_exam.tex
```

默认输出：`content/exams/auto/nanjing_2026_sep/image_jobs.jsonl`

## 2. 单条任务 JSON 示例

```json
{
  "id": "nanjing_2026_sep-Q8-img1",
  "exam_slug": "nanjing_2026_sep",          // 兼容旧字段（以 id 解析）
  "exam_prefix": "nanjing_2026_sep",        // 统一使用的试卷前缀
  "exam_dir": "content/exams/auto/nanjing_2026_sep", // 当前试卷目录
  "tikz_snippets_dir": "content/exams/auto/nanjing_2026_sep/tikz_snippets", // 推荐写入目录
  "tex_file": "content/exams/auto/nanjing_2026_sep/converted_exam.tex", // 来源 TeX 文件
  "question_index": 8,
  "sub_index": 1,
  "path": "figures/source/Q8_img1.png",     // 原始图片路径（原 TeX 中出现的 path）
  "width_pct": 60,                            // 图片宽度（百分比整数）
  "inline": false,                            // 是否内联
  "context_before": "函数图像...",           // 提取的前文上下文
  "context_after": "回答下列问题...",        // 提取的后文上下文
  "todo_block_start_line": 312,               // IMAGE_TODO_START 行号（1-based）
  "todo_block_end_line": 320                  // IMAGE_TODO_END 行号（1-based）
}
```

> 注意：实际字段可能根据需求扩展；下游只需最小依赖即可。

## 3. 关键字段说明

| 字段 | 说明 | 必需 | 备注 |
|------|------|------|------|
| id | 图片唯一标识符：`<exam_prefix>-Q<题号>-img<序号>` | 是 | 用作 TikZ 文件名（`{id}.tex`） |
| exam_prefix | 试卷前缀（主键） | 是 | 与目录名保持一致 |
| exam_dir | 当前试卷目录 | 是 | 由 `tex_file.parent` 推断 |
| tikz_snippets_dir | 推荐 TikZ 输出目录 | 是 | `exam_dir/tikz_snippets` |
| tex_file | 原始 TeX 文件路径 | 是 | 解析 IMAGE_TODO 的来源 |
| path | 图片原始路径（在 TeX 中写的） | 否 | 可能用于查看或生成替代 includegraphics |
| width_pct | 宽度百分比（整数） | 否 | 从 `width=60%` 转为 `60` |
| inline | 是否内联图片 | 否 | 影响排版方式 |
| context_before / context_after | 上下文片段 | 否 | 提供语义辅助 |
| todo_block_start_line / todo_block_end_line | 占位符块行号 | 否 | 便于精确回填或校验 |

## 4. TikZ 目录推断（唯一真理）

所有下游生成 TikZ 代码的 Agent / 脚本必须严格遵循以下顺序推断输出目录：

1. 如果存在 `job['tikz_snippets_dir']`：直接使用。
2. 否则如果存在 `job['exam_dir']`：使用 `Path(exam_dir) / 'tikz_snippets'`。
3. 否则如果存在 `job['exam_prefix']`：使用 `Path('content/exams/auto') / exam_prefix / 'tikz_snippets'`。
4. 若以上均不存在：直接抛出错误（不要再回退到历史目录）。

仓库内的唯一实现：`tools/images/utils.py` 中的 `get_tikz_snippets_dir(job)`。

> 不允许“自创”其它目录或硬编码 `tools/images/tikz_snippets` 作为默认路径。

### 外部不可 import 情况
若外部环境无法直接 import 仓库代码，也必须复制上述逻辑；伪代码：

```python
from pathlib import Path

def get_tikz_dir(job):
    if job.get('tikz_snippets_dir'):
        return Path(job['tikz_snippets_dir'])
    if job.get('exam_dir'):
        return Path(job['exam_dir']) / 'tikz_snippets'
    if job.get('exam_prefix'):
        return Path('content/exams/auto') / job['exam_prefix'] / 'tikz_snippets'
    raise ValueError('missing directory fields')
```

## 5. 写入文件规范

文件命名：`{id}.tex`，保持与 `job['id']` 完全一致。

调用仓库内 helper：

```python
from pathlib import Path
import json
from tools.images.utils import get_tikz_snippets_dir, write_tikz_snippet_to_dir

for job in jobs:  # jobs 为解析后的 JSON 列表
    tikz_dir = get_tikz_snippets_dir(job)
    tikz_code = job['tikz_code']  # 由 AI 生成，需包含完整 tikzpicture 环境
    write_tikz_snippet_to_dir(job['id'], tikz_code, tikz_dir)
    # 会统一打印: [TikZ] write snippet: id=...  ->  <path>
```

若希望通过 job 自动推断目录，可使用：

```python
from pathlib import Path
import json
from tools.images.utils import write_tikz_snippet

write_tikz_snippet(job, job['id'], tikz_code)
```

## 6. 统一日志格式

成功写入后打印单行：

```text
[TikZ] write snippet: id=<ID>  ->  <绝对或相对路径>
```

用于人工快速核对路径是否符合试卷目录期望（例如：`content/exams/auto/nanjing_2026_sep/tikz_snippets/...`）。

## 7. 回填脚本（apply_tikz_snippets.py）默认行为

当执行：

```bash
python tools/images/apply_tikz_snippets.py \
  --tex-file content/exams/auto/nanjing_2026_sep/converted_exam.tex
```

未显式传入 `--snippets-dir` 时，脚本自动使用 `Path(tex_file).parent / 'tikz_snippets'`。
如果需要覆盖，可显式传入 `--snippets-dir`。

## 8. 常见错误与排查

| 问题 | 可能原因 | 解决 |
|------|----------|------|
| 未写入 snippet | 目录未创建或推断失败 | 使用 get_tikz_snippets_dir 显式打印路径；确保 JSON 字段完整 |
| 回填脚本缺少 snippet | AI 未生成对应 id 文件 | 检查写入日志或过滤的 job 列表 |
| 目录被写到历史路径 | 外部脚本仍硬编码旧路径 | 统一改为调用推断逻辑；更新代码 |

## 9. 附：快速落地器脚本（write_snippets_from_jsonl.py）

仓库提供：`tools/images/write_snippets_from_jsonl.py`，示例用法：

```bash
python tools/images/write_snippets_from_jsonl.py \
  --jobs-file content/exams/auto/nanjing_2026_sep/image_jobs.jsonl \
  --tikz-source generated_tikz.jsonl
```

`generated_tikz.jsonl` 每行需包含：`{"id": "...", "tikz_code": "..."}`。
脚本会匹配 `id` 并写入对应试卷目录的 `tikz_snippets`。

## 10. 后续扩展建议

- 支持多版本 TikZ：`tikz_snippets/v2/` + 字段 `tikz_version`
- 预检查：检测 `\begin{tikzpicture}` 与 `\end{tikzpicture}` 是否成对

---

以上规范确保所有 Agent/脚本在“图片 → TikZ”阶段产生一致的输出路径与日志，避免混乱与重复处理。
