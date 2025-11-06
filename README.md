# MyNote – Exam/Lecture LaTeX Notes

基于 [`exam-zh`](https://ctan.org/pkg/exam-zh) 与自定义样式 `styles/examx.sty` 的中英混排**试卷/讲义**模板。提供教师版/学生版双输出，并在题目尾部按统一接口自动渲染“考点/难度/详解/来源”。

> 本项目仅文档与模板层改动，不引入破坏构建的依赖。提交前请本地通过 `./build.sh exam both` 和 `./build.sh handout both`。

---

## Features

- Teacher / Student **双版本输出**
- 统一题目元数据渲染：考点 / 难度 / 详解（来源可选）
- 难度小数 → 百分比（默认整数，可按需重定义为 1/2 位小数）
- `tcolorbox` 教师信息块或极简水平线风格
- **零侵入题面**：题面只写内容，元信息由 `examx` 自动排版

详见 [`features.md`](./features.md)。

---

## Requirements

## Features

 Teacher / Student **dual outputs**
 Unified metadata block (**teacher only**): Topics / Difficulty / Explanation / Source / **Answer**
 Difficulty `0..1` → percentage (overridable via `\ExamDifficultyFormat`)
 `tcolorbox` or minimal style for teacher block
 **Zero‑intrusion**: authors focus on content; metadata renders automatically
# 试卷
./build.sh exam teacher   # 教师版（含详解/考点/来源）
## Requirements

 TeX Live **2024+**（recommended 2025）
 Packages: `exam-zh`, `tcolorbox`, `ctex` (and others from `settings/preamble.sty`)
./build.sh handout student
## Build
在入口文件中，可通过包选项显式指定版本：
```tex
% 教师版
```bash
\usepackage[teacher]{styles/examx}
% 或者学生版
./build.sh exam teacher   # teacher version (shows metadata & answers)
\usepackage[student]{styles/examx}
./build.sh exam student   # student version (hides all teacher blocks)
```
./build.sh exam both

```bash
> 构建脚本会在需要时自动开启 `-shell-escape`（例如检测到 `minted`）；所有产物位于 `./output/`。

./build.sh handout teacher
---
./build.sh handout student

./build.sh handout both
## Runtime setup（可在导言区或章节前设置）

```tex
\examxsetup{
  autoprint=true,   % 每题结束自动打印教师块
  show-source=false,% 默认不展示“来源”
  boxed=true        % 教师块使用 tcolorbox 风格
}
```tex
% Teacher build
\usepackage[teacher]{styles/examx}
% Student build
% \usepackage[student]{styles/examx}
```

---
> Teacher build prints a metadata box **only when any field is non-empty** (including captured `答案`). Student build prints **nothing** (no shadow boxes).


## Runtime setup
- `\topics{...}`   题目考点（多个用分号分隔）
- `\difficulty{<0..1>}` 难度（小数；模板转换为百分比）
- `\explain{...}`  详解（可含数学环境与分页）
- `\source{...}`   来源（可选；由 `show-source` 控制展示）

自定义难度显示（例如显示一位小数）：

```tex
  \fp_eval:n { round((#1)*100, 1) } \%
## Metadata interfaces
}
`topics{...}` — topics (use semicolons to separate)
`difficulty{<0..1>}` — difficulty (decimal)
`explain{...}` — explanation (math friendly)
`source{...}` — source (optional; gated by `show-source`)
---

## Troubleshooting

- **Runaway argument / File ended while scanning use of ...**
  常为 `}` 被 `%` 注释吞掉；请检查最近改动。
- **一串 `expl3` 命令未定义**

## Project layout
---
`styles/examx.sty` — teacher/student controller, metadata & answer capture
`settings/preamble.sty` — fonts and common setup
`content/exams/*.tex` — exam sources (`exam02.tex` demonstrates both patterns)
`main-exam.tex` / `main-handout.tex` — entry points
- `content/exams/exam01.tex`：示例试卷
- `main-exam.tex` / `main-handout.tex`：试卷/讲义入口
## Contributing

Conventional commits suggested: `feat(examx): ...`, `fix(examx): ...`, `docs(readme): ...`
When styles change, update both `README.md` and `features.md`.
Keep filenames in **English** and lower_snake_case.

- 文档与样式变更须同步更新 `README.md` 与 `features.md`。
## License
- 目录/命名请保持英文小写与下划线风格。

---

## License

MIT