# Features

本仓库是“**数学讲义 + 试卷**”双引擎，零侵入题面，统一渲染教师信息块。

---

## 1) Modules

### Exam
- **Class**: `exam-zh`
- **Bridge**: `styles/examx.sty` — hooks `question`/`problem` end to render teacher block
- **Content**: `content/exams/*.tex` (e.g. `exam02.tex` demo)
- **Entry**: `main-exam.tex`

### Handout
- **Class**: `ElegantBook`
- **Extension**: `styles/handoutx.sty` — hooks `examplex` environment to render teacher metadata block
- **Content**: `content/handouts/*.tex`
- **Entry**: `main-handout.tex`
- **Metadata**: Same system as exams; `examplex` (例题) environments support `\topics`, `\difficulty`, `\answer`, `\explain`, `\source`

---

## 2) Unified metadata & answer capture

**Applies to**:
- **Exams**: `question` / `problem` environments (teacher vs student builds)
- **Handouts**: `examplex` (例题) environments (teacher-facing only, no student variant)

在题目/例题**尾部**使用：
```tex
\topics{…} \difficulty{0.40} \answer{…} \explain{…} \source{…}
```

**Behavior**:
- 教师版：自动打印教师信息块（Difficulty / Answer / Topics / Explanation / Source）
  - **Difficulty 和 Answer 显示在同一行**（例：【难度】0.85  【答案】A）
  - Topics、Explanation、Source 各占独立行
- 学生版（仅试卷）：**完全不输出**教师块（无阴影框）
- 讲义（handouts）：始终显示教师信息块（无学生版）
- `答案` 由以下方式提供：
  - 快速单选题（试卷）：`\mcq[<正确选项>]` 的可选参数
  - 其他题型：在元信息尾部显式写 `\answer{...}` 或 `\answers{...}`
- **不再从 `\paren[<A-D>]`、`\fillin[<text>]` 的方括号参数自动捕获答案**，以降低题面 TeX 复杂度、方便从外部题库导入
- **重要**：内联答案标记"（A）"已默认隐藏（`show-paren=false`），答案仅显示在教师信息块中

难度默认显示为小数（decimal）；可配置为百分比：
```tex
\PassOptionsToPackage{difficulty-format=percent}{qmeta}
```

---

## 3) Options (`\examxsetup{...}`)

```tex
\examxsetup{
  autoprint=true,     % 自动打印（仅教师版生效）
  show-source=false,  % 是否显示“来源”
  boxed=true          % 使用 tcolorbox；false 为极简样式
}
```

- 当关闭 `autoprint` 时，如需手动输出，可使用 `teachernotes` 环境。

---

## 4) Authoring patterns

### Multiple-choice questions (native exam-zh)
```tex
\begin{question}
题干
\begin{choices}
  \item A \item B \item C \item D
\end{choices}
\topics{…}
\difficulty{0.4}
\answer{B}
\explain{…}
\end{question}
```

### Quick MCQ (using \mcq macro)
```tex
\mcq[B]{题干}{选项A}{选项B}{选项C}{选项D}
\topics{…}
\difficulty{0.4}
\explain{…}
```
> `\mcq[<correct>]` 会自动调用 `\answer{<correct>}`，无需重复写 `\answer`。

### Fill-in questions
```tex
函数 $f(x)=x^2-4x+3$ 的最小值为 \fillin{}。
\topics{二次函数；顶点式}
\difficulty{0.40}
\answer{-1}
\explain{$(x-2)^2-1$}
```

> 默认 `\examsetup{ fillin={type=line}, paren={show-paren=false}, question={show-points=false} }`。
>
> **重要**：`\paren[...]` 和 `\fillin[...]` 仅用于排版，不再自动捕获答案。答案必须通过 `\answer{...}` 显式提供。

---

## 5) Build matrix

```bash
./build.sh exam teacher|student|both
./build.sh handout teacher|student|both
```
产物输出到 `./output/`。

---

## 6) Changelog (highlights)

- **examx.sty**:
  - Default `show-paren=false` — inline answer markers "（A）" suppressed
  - `\mcq[<correct>]` macro available for quick MCQs (automatically calls `\answer{<correct>}`)
  - Teacher/student gating; empty-box suppression
  - **Removed automatic answer capture from `\paren` / `\fillin`** — answers must be explicit via `\answer{...}` or `\mcq[...]`
  - Both teacher and student builds hide exam-zh inline answers (show only in metadata box)
- **qmeta.sty**:
  - Answer display in teacher box only
  - **Difficulty and Answer printed on same line** (e.g., 【难度】0.85  【答案】A)
  - Topics, Explanation, Source follow on separate lines
- **content/exams/*.tex**: Uses explicit `\answer{...}` metadata for all questions
