"""Utility helpers for images/TikZ pipeline.

Provides a canonical method to determine the target tikz_snippets directory
for an image job dict. Other scripts and external agents should call
`get_tikz_snippets_dir(job)` before writing snippet files.
"""
from pathlib import Path
from typing import Dict


def get_tikz_snippets_dir(job: Dict) -> Path:
    """根据规范推断 TikZ 片段目录。

    推断顺序（唯一真理）：
      1. 如果存在 job['tikz_snippets_dir']：直接使用
      2. 否则如果存在 job['exam_dir']：exam_dir / 'tikz_snippets'
      3. 否则如果存在 job['exam_prefix']：content/exams/auto/<exam_prefix>/tikz_snippets
      4. 否则抛出错误（不再回退到历史目录）

    不负责创建目录；调用方可使用 ensure_tikz_dir。
    """
    if not isinstance(job, dict):
        raise TypeError('job must be a dict')

    val = job.get('tikz_snippets_dir')
    if val:
        return Path(val).expanduser()

    exam_dir = job.get('exam_dir')
    if exam_dir:
        return Path(exam_dir).expanduser() / 'tikz_snippets'

    exam_prefix = job.get('exam_prefix') or job.get('exam_slug')
    if exam_prefix:
        return Path('content') / 'exams' / 'auto' / exam_prefix / 'tikz_snippets'

    raise ValueError('Cannot determine tikz_snippets_dir: job missing tikz_snippets_dir/exam_dir/exam_prefix')


def ensure_tikz_dir(job: Dict):
    """Ensure the directory exists and return the Path."""
    p = get_tikz_snippets_dir(job)
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_tikz_snippet(job: Dict, image_id: str, tikz_code: str) -> str:
    """根据 job 推断目录并写入 snippet。

    Args:
        job: 图片任务字典（至少包含 exam_prefix 或 exam_dir 或 tikz_snippets_dir）
        image_id: 图片唯一标识符（如 'nanjing_2026_sep-Q1-img1'）
        tikz_code: TikZ 源代码（可不含结尾换行，函数会补齐）

    Returns:
        写入的文件路径字符串。
    """
    dirpath = ensure_tikz_dir(job)
    return write_tikz_snippet_to_dir(image_id, tikz_code, dirpath)


def write_tikz_snippet_to_dir(image_id: str, tikz_code: str, tikz_dir: Path) -> str:
    """直接指定目标目录写入 snippet（外部 Agent 可用）。"""
    tikz_dir.mkdir(parents=True, exist_ok=True)
    out_path = tikz_dir / f"{image_id}.tex"
    if not tikz_code.endswith('\n'):
        tikz_code += '\n'
    out_path.write_text(tikz_code, encoding='utf-8')
    print(f"[TikZ] write snippet: id={image_id}  ->  {out_path}")
    return str(out_path)

