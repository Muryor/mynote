# MyNote – Exam/Lecture LaTeX Notes

基于 [`exam-zh`](https://ctan.org/pkg/exam-zh) 与自定义样式 `styles/examx.sty` 的中英混排**试卷/讲义**模板。提供教师版/学生版双输出，并在题目尾部按统一接口自动渲染"考点/难度/答案/详解/来源"。

> 本项目仅文档与模板层改动，不引入破坏构建的依赖。提交前请本地通过 `./build.sh exam both` 和 `./build.sh handout both`。

---

## Features

- Teacher / Student **双版本输出**（试卷）+ Teacher-only **讲义输出**
- 统一题目元数据渲染：答案 / 考点 / 难度 / 详解（来源可选）
- 难度小数显示（默认 decimal，可配置为 percent）
- `tcolorbox` 教师信息块（学生版完全不渲染）
- **零侵入题面**：题面只写内容，元信息由 `examx` 自动排版
- **行内数学统一使用 `\(...\)`**：避免与 TikZ 坐标计算冲突
- **字体回退链**：Inter → TeX Gyre Heros → Helvetica → Arial → Latin Modern Sans
- **TikZ 图形支持**：使用 `\path coordinate[pos=t]` 语法计算中点，避免 `$(...)$` 冲突

详见 [`features.md`](./features.md)。

---

## Requirements

- TeX Live **2024+**（recommended 2025）with `xelatex` and `latexmk`
- Packages: `exam-zh`, `tcolorbox`, `ctex` (and others from `settings/preamble.sty`)
- **系统字体**:
  - **CJK**: PingFang SC / Noto Serif CJK SC / Source Han Serif SC / STSong (任一可用)
  - **Sans**: TeX Gyre Heros → Helvetica → Arial → Latin Modern Sans (回退链)
  - **Mono**: JetBrains Mono / Fira Code / Latin Modern Mono / Monaco (可选)
  - **数学**: STIX Two Math / Libertinus Math / Latin Modern Math (任一可用)
- **注意**: 本项目已移除 Inter 字体依赖，使用 TeX 内置字体回退链，无需安装额外字体

> 如遇 `mktexmf: font ... not found` 错误，检查 `settings/preamble.sty` 字体配置。

---

## Configuration

### Switching Compilation Target

The project uses a **metadata-driven entry point** system. To switch which exam or handout to compile:

1. Open `settings/metadata.tex`
2. Modify the source file path:
   - For exams: `\newcommand{\examSourceFile}{path/to/your/exam.tex}`
   - For handouts: `\newcommand{\handoutSourceFile}{path/to/your/handout.tex}`
3. Run the build command (see below)

**Path Support**:
- ✅ English paths (recommended): `content/exams/g3/sem1/midterm/g3_sem1_midterm_2025_wuxi.tex`
- ✅ Chinese paths (macOS + XeLaTeX tested): `content/exams/高三/上学期/期中/高三上学期期中考试数学试卷.tex`
- Use relative paths (from repository root) or absolute paths
- Avoid spaces in paths; use underscores instead (e.g., `高三上_期中.tex`)

**Example `settings/metadata.tex`**:
```tex
% Exam entry (currently selected)
\newcommand{\examSourceFile}{content/exams/exam01.tex}

% Handout entry (currently selected)
\newcommand{\handoutSourceFile}{content/handouts/g3/functions/g3_functions_topic01_basic_concepts.tex}
```

> The teacher/student role is controlled by `build.sh`, **not** in metadata. Metadata only specifies **which** file to compile.

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
已知集合 \(A=\{x\mid \log_2 x < 1\},\, B=\{x\mid x<1\}\)，则 \(A\cap B\) 等于
\begin{choices}
  \item \((-\infty,1)\)
  \item \((0,1)\)
  \item \((-\infty,2)\)
  \item \((0,2)\)
\end{choices}
\topics{交集；不等式与函数单调性}
\difficulty{0.40}
\answer{B}
\explain{由 \(\log_2 x<1\Rightarrow 0<x<2\)，与 \(x<1\) 取交得 \((0,1)\)。}
\end{question}
```

**Key Points**:

- **行内数学使用 `\(...\)`**: 避免 `$...$` 与 TikZ 坐标计算冲突
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

### Handout Examples (讲义)

Handouts use the **same metadata system** as exams. For `examplex` (例题) environments, add metadata at the end:

```tex
\begin{examplex}{例题：椭圆方程}{ex:ellipse-01}
已知椭圆 $C:\,\dfrac{x^2}{a^2}+\dfrac{y^2}{b^2}=1\ (a>b>0)$ 的左、右焦点分别为 $F_1,F_2$。
求椭圆 $C$ 的方程。
\topics{椭圆的标准方程；焦点坐标；离心率}
\difficulty{0.6}
\answer{$\dfrac{x^2}{a^2}+\dfrac{y^2}{b^2}=1$，其中 $c^2=a^2-b^2$}
\explain{可由定义 $|PF_1|+|PF_2|=2a$ 推导，或由几何关系 $c^2=a^2-b^2$ 确定参数。}
\end{examplex}
```

**Behavior**:

- Handouts are **teacher-facing only** (no student variant)
- After each `examplex` environment, a shaded metadata box appears with the same layout as exam questions
- First line: 【难度】...  【答案】... (if provided)
- Subsequent lines: 【知识点】..., 【详解】..., 【来源】... (if enabled)

---

## Project Layout

```
main-exam.tex                    — exam entry point (loads content via metadata)
main-handout.tex                 — handout entry point (loads content via metadata)
settings/
  metadata.tex                   — compilation target configuration
  preamble.sty                   — fonts and common setup
styles/
  examx.sty                      — teacher/student controller, exam-zh configuration
  qmeta.sty                      — metadata capture and rendering
  handoutx.sty                   — handout environment extensions
content/
  exams/
    exam01.tex                   — example exam (current default)
    g1/sem1/                     — grade 1 semester 1 exams
    g1/sem2/                     — grade 1 semester 2 exams
    g2/sem1/                     — grade 2 semester 1 exams
    g2/sem2/                     — grade 2 semester 2 exams
    g3/...                       — grade 3 stage tests, mock exams
  handouts/
    ch01.tex                     — legacy example handout
    g1/sem1/                     — grade 1 semester 1 handouts
    g1/sem2/                     — grade 1 semester 2 handouts
    g2/sem1/                     — grade 2 semester 1 handouts
    g2/sem2/                     — grade 2 semester 2 handouts
    g3/
      functions/                 — 函数专题
      derivatives/               — 导数专题
      conics/                    — 圆锥曲线专题
      sequences/                 — 数列专题
      trigonometry/              — 三角函数专题
      vectors/                   — 向量专题
      combinatorics/             — 排列组合专题
      probability_statistics/    — 概率与统计专题
      solid_geometry/            — 立体几何专题
      sets_complex_inequalities/ — 集合、复数、不等式专题
      comprehensive/             — 综合专题
output/                          — build artifacts (PDFs)
```

### Directory Organization

**Exams** (`content/exams/`):
- Grade 1-2: organized by semester (sem1/sem2)
- Grade 3: organized by test type (stage tests, mock exams, etc.)
- Use English lower_snake_case filenames (recommended)
- Metadata allows Chinese paths for personal use

**Handouts** (`content/handouts/`):
- Grade 1-2: organized by semester (sem1/sem2)
- Grade 3: organized by topic (11 major topics listed above)
- Each topic directory can contain multiple handout files
- See `content/handouts/README.md` for detailed structure

**Configuration**:
- `settings/metadata.tex`: Set `\examSourceFile` and `\handoutSourceFile` to switch compilation targets
- Supports both English and Chinese paths (macOS + XeLaTeX tested)

---

## Troubleshooting

### 编译错误

- **Runaway argument / File ended while scanning use of ...**
  常为 `}` 被 `%` 注释吞掉；请检查最近改动。
- **一串 `expl3` 命令未定义**
  确保 `\ExplSyntaxOn` / `\ExplSyntaxOff` 配对正确。
- **`mktexmf: font Inter not found` 或类似字体错误**
  - **原因**: 系统缺少字体，或 preamble.sty 引用了不存在的字体
  - **解决**: 检查 `settings/preamble.sty` 字体配置，使用内置 TeX 字体回退链（已移除 Inter）
  - 如需自定义字体，确保系统已安装或删除对应 `\IfFontExistsTF` 检查

### TikZ 图形错误

- **`No shape named '(A' is known` 或坐标计算错误**
  - **原因**: 使用 `$...$` 包裹 TikZ 计算表达式 `$(...)$` 导致全局替换产生 `\((A)\)` 错误语法
  - **解决**:
    - TikZ 坐标计算使用 `($(A)+(0.7,0)$)` 语法，不要用 `$((A)+(0.7,0))$`
    - 计算中点推荐 `\path (A) -- (B) coordinate[pos=0.5] (M);` 语法
    - 行内数学使用 `\(...\)`，TikZ 图形中使用 `$(...)$` 坐标计算
  - **示例**: 见 `content/exams/exam01.tex` Q4, Q12, Q13

### 元信息显示问题

- **学生版出现阴影方框**
  已修复：确保使用最新版 `qmeta.sty`。
- **教师版缺失元信息**
  元信息命令（`\topics`, `\difficulty`, `\explain`）**必须放在 `\end{question}` 之前**，否则在环境结束钩子触发时无法捕获。
- **单选题不显示【答案】**
  确认在题目的元信息中显式调用了 `\answer{X}`（或使用了 `\mcq[X]`），并且元数据命令放在 `\end{question}` 之前。
- **选择题选项不显示**
  `choices` 环境内应使用 `\item`（推荐）或 `\choice`（已提供别名）。两者等价。

### 构建流程

- **大规模重构后构建失败**
  - 建议流程: 1) 备份原文件 2) 执行修改 3) 测试编译 4) 逐个修复错误 5) 验证两版本输出
  - 使用 `./build.sh exam both` 同时编译教师/学生版，确保两版本都通过
  - 检查 `output/` 目录生成的 PDF 文件大小和内容是否符合预期

### 文件命名约定

**Repository files (tracked in Git)**:
- 推荐使用英文 lower_snake_case 文件名和目录名
- 示例: `g3_sem1_midterm_2025_wuxi.tex`, `g3_functions_topic01_basic_concepts.tex`
- 这确保了跨平台兼容性和版本控制的稳定性

**Local files (personal use)**:
- 允许使用中文文件名和目录名（macOS + XeLaTeX 环境下测试通过）
- 示例: `高三上学期期中考试数学试卷.tex`, `高三函数专题（一）.tex`
- 通过 `settings/metadata.tex` 配置路径即可编译
- 注意事项:
  - 避免路径中使用空格，建议用下划线连接
  - 如遇编译问题，可先用英文文件名测试排查
  - 这些文件可以不纳入版本控制（添加到 `.gitignore`）

---

## Contributing

Conventional commits suggested: `feat(examx): ...`, `fix(examx): ...`, `docs(readme): ...`

When styles change, update both `README.md` and `features.md`.

Keep filenames in **English** and lower_snake_case.

---

## License

MIT
