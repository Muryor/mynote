# Features

本仓库是“**讲义（Handout） + 试卷（Exam）**”双引擎，统一 **题目元数据接口**：
```tex
\topics{知识点（用分号分隔）}
\difficulty{0..1}     % 显示格式可通过 \renewcommand\ExamDifficultyFormat 定制
\explain{详解文本}     % 支持数学环境、分页
\source{来源文本}      % 默认教师版隐藏；可开启
```

## 1. 模块
- **Exam（试卷）**
  - 类：`styles/exam-zh.cls`（上游类）
  - 桥接：`styles/examx.sty`（自动在题尾渲染“教师信息框”；学生版隐藏）
  - 内容：`content/exams/*.tex`
  - 入口：`main-exam.tex`
- **Handout（讲义）**
  - 类：`ElegantBook`（仓库本地附带）
  - 扩展：`styles/handoutx.sty`（定义/性质/例题/注意 盒子；`kvtable`/`ellipsesummary` 表格）
  - 内容：`content/handouts/*.tex`
  - 入口：`main-handout.tex`

## 2. 教师信息框（仅教师版可见）
- 默认 **boxed** 样式，包含：**详解/答案、考点、难度、（可选）来源**。
- 开关与样式：
```tex
\examxsetup{ style=boxed }        % 或 simple
\examxsetup{ show-source=true }   % 默认 false
\examxsetup{ autoprint=false }    % 局部关闭自动渲染
```

## 3. 讲义盒子与表格
- `defbox/theorybox/examplebox/notebox` 四类盒子由 `tcolorbox` 实现，色板可在 `preamble.sty` 统一调整。
- `kvtable`：两列表格（粗体键，等宽自适应值），适合“范围/对称性/顶点”等摘要。
- `ellipsesummary`：三列“在 x 轴上/在 y 轴上”的对照表（见 `content/handouts/ch01.tex`）。

## 4. 编译
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

## 5. 转换脚本
- `tools/convert_tex_exam.py in.tex out.tex`
- 支持将“题号+ABCD选项+【答案/难度/知识点/详解】”的粗 TeX/Markdown 源转为本仓库标准格式。
```