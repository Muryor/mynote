# Features

本仓库是“**数学讲义 + 试卷**”双引擎，零侵入题面，统一渲染教师信息块。

---

## 1) Modules

### Exam

- **Class**: `exam-zh`
- **Bridge**: `styles/examx.sty` — hooks `question`/`problem` end to render teacher block
- **Content**: `content/exams/` — organized by grade and semester/test type
  - Grade 1-2: `g1/sem{1,2}/`, `g2/sem{1,2}/`
  - Grade 3: `g3/` (stage tests, mock exams, etc.)
- **Entry**: `main-exam.tex` — loads content via `settings/metadata.tex` (`\examSourceFile`)
- **Compilation Target**: Configured in `settings/metadata.tex`
  - Set `\examSourceFile` to the path of the exam you want to compile
  - Supports English paths (recommended) and Chinese paths (macOS + XeLaTeX tested)
  - Example: `\newcommand{\examSourceFile}{content/exams/exam01.tex}`

### Handout

- **Class**: `ElegantBook`
- **Extension**: `styles/handoutx.sty` — hooks `examplex` environment to render teacher metadata block
- **Content**: `content/handouts/` — organized by grade and semester/topic
  - Grade 1-2: `g1/sem{1,2}/`, `g2/sem{1,2}/`
  - Grade 3: `g3/<topic>/` (11 major topics)
    - functions（函数）, derivatives（导数）, conics（圆锥曲线）, sequences（数列）
    - trigonometry（三角函数）, vectors（向量）, combinatorics（排列组合）
    - probability_statistics（概率与统计）, solid_geometry（立体几何）
    - sets_complex_inequalities（集合、复数、不等式）, comprehensive（综合）
- **Entry**: `main-handout.tex` — loads content via `settings/metadata.tex` (`\handoutSourceFile`)
- **Compilation Target**: Configured in `settings/metadata.tex`
  - Set `\handoutSourceFile` to the path of the handout you want to compile
  - Example: `\newcommand{\handoutSourceFile}{content/handouts/g3/functions/g3_functions_topic01_basic_concepts.tex}`
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
  show-source=false,  % 是否显示"来源"
  boxed=true          % 使用 tcolorbox；false 为极简样式
}
```

- 当关闭 `autoprint` 时，如需手动输出，可使用 `teachernotes` 环境。

---

## 4) Authoring patterns

### TikZ Graphics Best Practices

**行内数学 vs TikZ 坐标计算**：
- **行内数学使用 `\(...\)`**：避免全局 `$...$` → `\(...\)` 替换时与 TikZ 冲突
- **TikZ 坐标计算使用 `$(...)$` 语法**：这是 TikZ calc 库的标准语法

**示例**：

```tex
% ✅ 正确：TikZ 坐标计算
\coordinate (M) at ($(A)!0.5!(B)$);  % 计算 A 和 B 的中点
\draw ($(A)+(0.7,0)$) node[right] {$D$};  % 从 A 偏移

% ✅ 推荐：使用 pos 参数（更稳健）
\path (A) -- (B) coordinate[pos=0.5] (M);  % M 是 AB 中点
\path (B) -- (C) coordinate[pos=0.5] (D);  % D 是 BC 中点

% ❌ 错误：双层括号会被全局替换破坏
\coordinate (M) at $((A)!0.5!(B))$;  % 替换后变成 \((A)!0.5!(B)\) 导致错误
```

**参考实现**：见 `content/exams/exam01.tex` Q4（向量图形）、Q12、Q13

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

## 5) Unified Table Environments

项目提供两套表格环境，分别用于试卷和讲义：

### examtableboxed（试卷专用）

带竖线的框线表格，符合试卷传统格式要求：

```tex
\begin{examtableboxed}{c|c|c|c}
级数 & 名称 & 风速大小（单位：m/s）\\
\hline
2 & 轻风 & 1.6--3.3 \\
\hline
3 & 微风 & 3.4--5.4 \\
\hline
4 & 和风 & 5.5--7.9 \\
\end{examtableboxed}
```

**特点**：
- 外框和列间都有竖线（`|c|c|c|`）
- 使用 `\hline` 作为水平线
- 自动居中、小字体、统一列间距和行高
- 适合数据表、统计表、对照表等

### examtable（讲义专用）

无竖线的 booktabs 专业三线表：

```tex
\begin{examtable}{cccc}
$P(\chi^{2} \ge k)$ & 0.050 & 0.010 & 0.001 \\
\midrule
$k$ & 3.841 & 6.635 & 10.828 \\
\end{examtable}
```

**特点**：
- 无竖线，使用 `\toprule`/`\midrule`/`\bottomrule`
- 现代化专业排版风格
- 适合讲义、论文等正式文档

**使用建议**：
- 试卷（exam-zh 文档类）统一使用 `examtableboxed`
- 讲义（article/ElegantBook 文档类）统一使用 `examtable`
- 两种环境参数相同，切换时只需修改环境名称和线条命令

---

## 6) Build matrix

```bash
./build.sh exam teacher|student|both
./build.sh handout teacher|student|both
```
产物输出到 `./output/`。

---

## 6) Changelog (highlights)

- **2025-11-13: exam01.tex 大规模重构**
  - 补充缺失的 Q11（数列λ-数列多选题）
  - 扩展 Q15-Q19 解答详解，提供完整推导步骤
  - 统一行内数学格式：所有 `$...$` → `\(...\)`，避免与 TikZ 坐标计算冲突
  - 清理所有 `\explain{}` 字段：移除"分析：/详解：/答案："前缀
  - 修复 Q4 缺失的向量图形（三角形 ABC 及中点 D、E）
  - 修正 Q16 最小值 -1/2，Q19(1)(ii) a=0
  - TikZ 图形使用 `coordinate[pos=0.5]` 语法计算中点，避免 `$(...)$` 坐标计算错误

- **字体系统更新**
  - 移除 Inter 字体依赖，使用 TeX 内置字体回退链
  - Sans: TeX Gyre Heros → Helvetica → Arial → Latin Modern Sans → Latin Modern Roman
  - Mono: JetBrains Mono → Fira Code → Latin Modern Mono → TeX Gyre Cursor → Courier New → Monaco
  - 修复 `mktexmf: font Inter not found` 构建失败问题

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
  - **exam01.tex**: 江苏省无锡市 2025-2026 学年高三上学期期中考试数学试题（Q1-Q19 完整）
