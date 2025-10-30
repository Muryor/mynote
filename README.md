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

- TeX Live **2024+**（推荐 2025）
- 宏包：`exam-zh`、`tcolorbox`、`ElegantBook`、`ctex` 等

---

## Build

```bash
# 试卷
./build.sh exam teacher   # 教师版（含详解/考点/来源）
./build.sh exam student   # 学生版（隐藏详解）
./build.sh exam both      # 教师版与学生版一起编译

# 讲义
./build.sh handout teacher
./build.sh handout student
./build.sh handout both
```

> 构建脚本会在需要时自动开启 `-shell-escape`（例如检测到 `minted`）；所有产物位于 `./output/`。

---

## Runtime setup（可在导言区或章节前设置）

```tex
\examxsetup{
  autoprint=true,   % 每题结束自动打印教师块
  show-source=false,% 默认不展示“来源”
  boxed=true        % 教师块使用 tcolorbox 风格
}
```

---

## Metadata（题目/例题尾部统一接口）

- `\topics{...}`   题目考点（多个用分号分隔）
- `\difficulty{<0..1>}` 难度（小数；模板转换为百分比）
- `\explain{...}`  详解（可含数学环境与分页）
- `\source{...}`   来源（可选；由 `show-source` 控制展示）

自定义难度显示（例如显示一位小数）：

```tex
\RenewDocumentCommand\ExamDifficultyFormat{m}{
  \fp_eval:n { round((#1)*100, 1) } \%
}
```

> 规范：**统一使用 `\fp_eval:n` 处理小数到百分比**；不要用 `\numexpr` 以避免精度与舍入问题。

---

## Troubleshooting

- **Runaway argument / File ended while scanning use of ...**
  常为 `}` 被 `%` 注释吞掉；请检查最近改动。
- **一串 `expl3` 命令未定义**
  请勿在 `styles/examx.sty` 中途 `\ExplSyntaxOff`；保持文件内一直开启。

---

## Project layout（关键路径）

- `styles/examx.sty`：桥接包，自动挂钩 `question` / `problem` 并渲染教师块
- `settings/preamble.sty`：字体与基础预设
- `content/exams/exam01.tex`：示例试卷
- `content/handouts/ch01.tex`：示例讲义
- `main-exam.tex` / `main-handout.tex`：试卷/讲义入口

---

## Contributing

- 提交信息建议：`fix(examx): ...` / `feat(examx): ...` / `docs(readme): ...`
- 文档与样式变更须同步更新 `README.md` 与 `features.md`。
- 目录/命名请保持英文小写与下划线风格。

---

## License

MIT