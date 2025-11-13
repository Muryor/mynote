# MyNote – Exam/Lecture LaTeX Notes

基于 [`exam-zh`](https://ctan.org/pkg/exam-zh) 与自定义样式 `styles/examx.sty` 的中英混排**试卷/讲义**模板。提供教师版/学生版双输出，并在题目尾部按统一接口自动渲染"考点/难度/详解/来源"。

> 本项目仅文档与模板层改动，不引入破坏构建的依赖。提交前请本地通过 `./build.sh exam both` 和 `./build.sh handout both`。

---

## Features

- Teacher / Student **双版本输出**
- 统一题目元数据渲染：答案 / 考点 / 难度 / 详解（来源可选）
- 难度小数显示（默认 decimal，可配置为 percent）
- `tcolorbox` 教师信息块（学生版完全不渲染）
- **零侵入题面**：题面只写内容，元信息由 `examx` 自动排版

详见 [`features.md`](./features.md)。

---

## Requirements

- TeX Live **2024+**（recommended 2025）
- Packages: `exam-zh`, `tcolorbox`, `ctex` (and others from `settings/preamble.sty`)

---

## Build

```bash
# 试卷
./build.sh exam teacher   # 教师版（含答案/详解/考点/难度）
./build.sh exam student   # 学生版（隐藏所有教师信息）
./build.sh exam both

# 讲义
./build.sh handout teacher
./build.sh handout student
./build.sh handout both
```

> 构建脚本会在需要时自动开启 `-shell-escape`（例如检测到 `minted`）；所有产物位于 `./output/`。

---

## Usage

### Authoring Multiple-Choice Questions

Use native `exam-zh` syntax with the `question` environment:

```tex
\begin{question}
已知集合 $A=\{x\mid \log_2 x < 1\},\, B=\{x\mid x<1\}$，则 $A\cap B$ 等于
\begin{choices}
  \item $(-\infty,1)$
  \item $(0,1)$
  \item $(-\infty,2)$
  \item $(0,2)$
\end{choices}
\topics{交集；不等式与函数单调性}
\difficulty{0.40}
\answer{B}
\explain{由 $\log_2 x<1\Rightarrow 0<x<2$，与 $x<1$ 取交得 $(0,1)$。}
\end{question}
```

**Key Points**:
- Answers are provided via **explicit metadata**: use `\answer{...}` (or `\answers{...}`) in the metadata section
- For quick MCQs, use `\mcq[correct]{stem}{A}{B}{C}{D}` which automatically captures the answer
- `\paren[...]` and `\fillin[...]` are **only for typesetting** and do NOT automatically capture answers
- Inline answer markers are **never shown** in either teacher or student builds
- Answers appear **only in the teacher metadata box** (【答案】), not inline in the question stem
- Use `\item` (or `\choice` alias) for each option in the `choices` environment
- **CRITICAL**: Metadata commands (`\topics`, `\difficulty`, `\answer`, `\explain`) must be placed **BEFORE** `\end{question}` to ensure they are captured in the teacher box

### Metadata Commands

- `\answer{...}` — 答案（must be explicitly provided; use `\mcq[...]` for quick MCQs）
- `\topics{...}` — 题目考点（多个用分号分隔）
- `\difficulty{<0..1>}` — 难度（小数）
- `\explain{...}` — 详解（可含数学环境与分页）
- `\source{...}` — 来源（可选；由 `show-source` 控制展示）

> Teacher build prints a metadata box **only when any field is non-empty**. Student build prints **nothing** (no shadow boxes).
>
> In the teacher metadata box, **Difficulty and Answer are printed on the same line** (e.g., 【难度】0.85  【答案】A), followed by Topics, Explanation, and Source on separate lines.

---

## Project Layout

```
styles/examx.sty          — teacher/student controller, exam-zh configuration
styles/qmeta.sty          — metadata capture and rendering
settings/preamble.sty     — fonts and common setup
content/exams/*.tex       — exam sources
main-exam.tex             — exam entry point
main-handout.tex          — handout entry point
```

---

## Troubleshooting

- **Runaway argument / File ended while scanning use of ...**
  常为 `}` 被 `%` 注释吞掉；请检查最近改动。
- **一串 `expl3` 命令未定义**
  确保 `\ExplSyntaxOn` / `\ExplSyntaxOff` 配对正确。
- **学生版出现阴影方框**
  已修复：确保使用最新版 `qmeta.sty`。
- **教师版缺失元信息**
  元信息命令（`\topics`, `\difficulty`, `\explain`）**必须放在 `\end{question}` 之前**，否则在环境结束钩子触发时无法捕获。
- **单选题不显示【答案】**
  确认在题目的元信息中显式调用了 `\answer{X}`（或使用了 `\mcq[X]`），并且元数据命令放在 `\end{question}` 之前。
- **选择题选项不显示**
  `choices` 环境内应使用 `\item`（推荐）或 `\choice`（已提供别名）。两者等价。

---

## Contributing

Conventional commits suggested: `feat(examx): ...`, `fix(examx): ...`, `docs(readme): ...`

When styles change, update both `README.md` and `features.md`.

Keep filenames in **English** and lower_snake_case.

---

## License

MIT
