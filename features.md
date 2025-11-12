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
- **Extension**: `styles/handoutx.sty`
- **Content**: `content/handouts/*.tex`
- **Entry**: `main-handout.tex`

---

## 2) Unified metadata & answer capture

在题目/例题**尾部**使用：
```tex
\topics{…} \difficulty{0.40} \explain{…} \source{…}
```
- 教师版：自动打印教师信息块（Topics / Difficulty / Explanation / Source / **Answer**）
- 学生版：**完全不输出**教师块（无阴影框）
- `答案` 自动从 `\paren[<A-D>]` 或 `\fillin[<text>]` 的方括号参数捕获
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
题干 \paren[C]
\begin{choices}
  \item A \item B \item C \item D
\end{choices}
\end{question}
\topics{…}\difficulty{0.4}\explain{…}
```

### Fill-in questions
```tex
函数 $f(x)=x^2-4x+3$ 的最小值为 \fillin[-1]{}。
\topics{二次函数；顶点式}\difficulty{0.40}\explain{$(x-2)^2-1$}
```

> 默认 `\examsetup{ fillin={type=line}, paren={show-paren=false}, question={show-points=false} }`。
>
> **注意**：`\mcq` 宏已弃用。如遇到旧代码使用 `\mcq`，会触发警告并自动转换为 exam-zh 格式。

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
  - `\mcq` macro deprecated with warning (auto-converts to exam-zh format)
  - Teacher/student gating; empty-box suppression
  - Answer capture from `\paren` / `\fillin`
- **qmeta.sty**: Answer display in teacher box only
- **content/exams/*.tex**: Migrated to native exam-zh authoring (no `\mcq`)
```