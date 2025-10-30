# Features

本仓库是“**数学讲义 + 试卷**”双引擎，零侵入题面，统一渲染教师信息块。

---

## 1) 模块与实现

### Exam（试卷）
- **类**：`exam-zh`
- **桥接**：`styles/examx.sty`（在题目尾部自动渲染教师块）
- **内容**：`content/exams/*.tex`（示例：`exam01.tex`）
- **入口**：`main-exam.tex`

### Handout（讲义）
- **类**：`ElegantBook`
- **扩展**：`styles/handoutx.sty`（提供 *定义/性质/例题/注意* 等盒子）
- **内容**：`content/handouts/*.tex`（示例：`ch01.tex`）
- **入口**：`main-handout.tex`

---

## 2) 统一元数据接口与渲染

在题目或例题**尾部**补齐以下接口，即可在教师版自动打印信息块（学生版自动隐藏）：

```tex
\topics{一次函数；待定系数} % 知识点（分号分隔）
\difficulty{0.60}           % 难度（0..1）
\explain{略。}              % 详解（可含数学环境）
\source{自编/教材/某年某校} % 来源（可选）
```

- `\topics{}` 为空将自动隐藏整行；`\difficulty{}` 未设时显示“—”。
- 难度显示为百分比；如需显示 1 位或 2 位小数，可按下式重定义：

```tex
\RenewDocumentCommand\ExamDifficultyFormat{m}{
  \fp_eval:n { round((#1)*100, 1) } \% % 1 位小数
}
```

> 规范：请**使用 `\fp_eval:n`** 进行小数→百分比的计算，避免 `\numexpr`。

---

## 3) 可配置项（`\examxsetup{...}`）

```tex
\examxsetup{
  autoprint=true,    % 自动打印教师块（全局开关）
  show-source=false, % 是否显示“来源”
  boxed=true         % 教师块采用 tcolorbox 风格；false 为极简水平线
}
```

- 局部关闭/恢复自动渲染：`\examxsetup{autoprint=false}` / `\examxsetup{autoprint=true}`。
- 手动打印（当关闭自动渲染时）：`teachernotes` 环境可随处输出教师块。

---

## 4) 目录结构（关键）

- `styles/examx.sty`：Exam/Handout 统一渲染逻辑
- `settings/preamble.sty`：字体与通用预设（如 PingFangSC/Noto CJK 优雅回退）
- `content/exams/exam01.tex`、`content/handouts/ch01.tex`：内容示例
- `main-exam.tex`、`main-handout.tex`：编译入口

---

## 5) 构建矩阵

```bash
# 试卷
./build.sh exam teacher
./build.sh exam student
./build.sh exam both

# 讲义
./build.sh handout teacher
./build.sh handout student
./build.sh handout both
```

所有产物输出到 `./output/`。
```