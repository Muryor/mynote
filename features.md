# Features

本仓库是“数学讲义 + 试卷”双引擎。

## 1. 模块与实现
- **Exam（试卷）**
  - 类：`exam-zh`
  - 桥接包：`styles/examx.sty`（自动在题目尾部渲染教师信息框）
  - 内容：`content/exams/*.tex`（示例：`exam01.tex`）
  - 入口：`main-exam.tex`
- **Handout（讲义）**
  - 类：`ElegantBook`
  - 扩展包：`styles/handoutx.sty`（定义/性质/例题/注意 等盒子）
  - 内容：`content/handouts/*.tex`（示例：`ch01.tex`）
  - 入口：`main-handout.tex`

## 2. 元数据与教师信息框（统一接口）
每道题或例题建议在尾部给出：

```tex
\topics{一次函数；待定系数}   % 知识点（分号分隔）
\difficulty{0.60}             % 难度（0..1）
\explain{略。}                % 详解（可含数学环境）
\source{自编/教材/某年某校}
