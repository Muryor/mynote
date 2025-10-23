# MyMathLectureNotes – Exam System (exam-zh + examx)

本项目已对接 **exam-zh** 题目环境，并统一题目元数据接口：

```tex
\topics{<考察的知识点>}
\difficulty{<0..1>}
\explain{<详解文本>}
\source{<来源文本>}
```

- **教师版**：每题下方自动渲染（知识点 / 难度 / 详解；来源默认关闭）。
- **学生版**：仅保留原试卷题目，不显示上述信息块。
- `\topics{}` 为空自动隐藏整行；`\difficulty{}` 未设显示“—”；详解支持数学环境且可分页。

## 目录结构（关键）
- `styles/exam-zh.cls`：exam-zh 类（不改动）。
- `styles/examx.sty`：桥接包，自动挂钩 `question` / `problem` 并渲染教师块。
- `settings/preamble.sty`：字体与基础预设（保留原 PingFangSC 设置）。
- `content/exams/exam01.tex`：示例试卷内容（已迁移到 `question` 环境）。
- `content/handouts/ch01.tex`：示例讲义（`problem` 环境 + 复用同一接口）。
- `main-exam.tex`：试卷入口（`exam-zh` 类 + `examx`）。
- `main-handout.tex`：讲义入口（ElegantBook + `examx`）。

## 编译

```bash
# 试卷
./build.sh exam teacher   # 教师版
./build.sh exam student   # 学生版
./build.sh exam both      # 两者都编译

# 讲义
./build.sh handout teacher
./build.sh handout student
./build.sh handout both
```

> 构建脚本通过 `\PassOptionsToPackage{teacher|student}{styles/examx}` 切换渲染；
> 字体与版面沿用 `settings/preamble.sty`（例如 PingFangSC），本补丁不改动。

## 在内容中写题（对齐 exam-zh）

**选择题**：
```tex
\begin{question}
设复数 $(1+5i)i$ 的虚部为（ ）。
\begin{choices}
  \choice $-1$
  \choice $0$
  \choice $1$
  \choice $5$
\end{choices}
\topics{复数；虚部计算}
\difficulty{0.30}
\explain{$(1+5i)i = i + 5i^2 = i - 5$，虚部为 $1$。}
\end{question}
```

**解答题/讲义中的习题**：
```tex
\begin{problem}[例题]
已知椭圆 $C:\ \frac{x^2}{a^2}+\frac{y^2}{b^2}=1\ (a>b>0)$。
\topics{椭圆；标准方程}
\difficulty{0.40}
\explain{略。}
\end{problem}
```

## 自定义

- 显示“来源”：`\\examxsetup{show-source=true}`
- 修改“难度”格式：
  ```tex
  \renewcommand\ExamDifficultyFormat[1]{\number\numexpr#1*100\relax\%%}
  ```
- 局部关闭教师块自动渲染：`\\examxsetup{autoprint=false}`（再用 `true` 重新开启）。
