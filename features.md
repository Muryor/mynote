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
	opics{…} \difficulty{0.40} \explain{…} \source{…}
```
- 教师版：自动打印教师信息块（Topics / Difficulty / Explanation / Source / **Answer**）  
- 学生版：**完全不输出**教师块（无阴影框）  
- `答案` 来自两种途径：
  - `\mcq[<A-D>]` 的可选参数（内部等价于捕获 `\paren[<A-D>]`）；
  - `\paren[<A-D>]` 或 `\fillin[<text>]` 的方括号参数。

难度显示为百分比；可重定义格式：
```tex
\RenewDocumentCommand\ExamDifficultyFormat{m}{
  \fp_eval:n { round((#1)*100, 0) } \%
}
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

### Pattern 1 — `\mcq`（推荐）
```tex
\mcq[C]{题干}{$A$}{$B$}{$C$}{$D$}
	opics{…}\difficulty{0.4}\explain{…}
```

### Pattern 2 — 传统 exam-zh
```tex
\begin{question}
题干 \paren[C]
\begin{choices}
  \item A \item B \item C \item D
\end{choices}
	opics{…}\difficulty{0.4}\explain{…}
\end{question}
```

### Fill-in
```tex
函数 $f(x)=x^2-4x+3$ 的最小值为 \fillin[-1]{}。
	opics{二次函数；顶点式}\difficulty{0.40}\explain{$(x-2)^2-1$}
```

> 默认 `\examsetup{ fillin={type=line}, question={show-paren=true, show-points=false} }`。

---

## 5) Build matrix

```bash
./build.sh exam teacher|student|both
./build.sh handout teacher|student|both
```
产物输出到 `./output/`。

---

## 6) Changelog (highlights)

- **examx.sty**: teacher/student gating; empty‑box suppression; answer capture from `\mcq` / `\paren` / `\fillin`  
- **main-exam.tex**: simplified global setup (delegated to examx)  
- **exam02.tex**: demonstrates both authoring patterns
```