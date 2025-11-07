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

### Pattern 1: Using `\mcq` Macro (Recommended)

```tex
\mcq[B]{已知集合 $A=\{x\mid \log_2 x < 1\},\, B=\{x\mid x<1\}$，则 $A\cap B$ 等于}
{$(-\infty,1)$}{$(0,1)$}{$(-\infty,2)$}{$(0,2)$}[
\topics{交集；不等式与函数单调性}
\difficulty{0.40}
\explain{由 $\log_2 x<1\Rightarrow 0<x<2$，与 $x<1$ 取交得 $(0,1)$。}
\source{自编}
]
```

**Syntax**: `\mcq[answer]{stem}{optionA}{optionB}{optionC}{optionD}[metadata]`

- First optional argument `[answer]`: Correct answer (A/B/C/D)
- Four mandatory arguments: Question stem and four choices
- Last optional argument `[metadata]`: Metadata commands block

### Pattern 2: Using Traditional exam-zh Syntax

```tex
\begin{question}
已知函数 $f(x)=2^x$，则 $f(0)+f(1)$ 等于 \paren[C]
\begin{choices}[columns=2]
  \choice $1$
  \choice $2$
  \choice $3$
  \choice $4$
\end{choices}
\topics{指数函数；基本运算}
\difficulty{0.20}
\explain{$f(0)=2^0=1$，$f(1)=2^1=2$，故 $f(0)+f(1)=3$。}
\end{question}
```

### Metadata Commands

- `\answer{...}` — 答案（`\mcq` 自动捕获，手动题目需显式标注）
- `\topics{...}` — 题目考点（多个用分号分隔）
- `\difficulty{<0..1>}` — 难度（小数）
- `\explain{...}` — 详解（可含数学环境与分页）
- `\source{...}` — 来源（可选；由 `show-source` 控制展示）

> Teacher build prints a metadata box **only when any field is non-empty**. Student build prints **nothing** (no shadow boxes).

---

## Project Layout

```
styles/examx.sty          — teacher/student controller, \mcq macro
styles/qmeta.sty          — metadata capture and rendering
settings/preamble.sty     — fonts and common setup
content/exams/*.tex       — exam sources (exam02.tex demonstrates both patterns)
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
  使用 `\mcq` 时，元信息必须放在最后的可选参数 `[...]` 中。

---

## Contributing

Conventional commits suggested: `feat(examx): ...`, `fix(examx): ...`, `docs(readme): ...`

When styles change, update both `README.md` and `features.md`.

Keep filenames in **English** and lower_snake_case.

---

## License

MIT
