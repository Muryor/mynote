
# MyNote – Exam/Lecture LaTeX Notes

> 基于 `exam-zh` + 自定义样式 `styles/examx.sty` 的中英混排试卷/讲义模板。

## Build
```bash
./build.sh exam teacher   # 教师版（含详解/考点/来源）
./build.sh exam student   # 学生版（隐藏详解）
```

## Metadata
- `\topics{...}`  题目考点
- `\difficulty{<0..1>}` 难度（小数）；模板会显示为百分比（四舍五入）
- `\explain{...}` 详解
- `\source{...}`  来源（可通过 `show-source=true` 控制是否展示）

> 自定义难度格式：
```tex
\RenewDocumentCommand\ExamDifficultyFormat{m}
  { \fp_eval:n { round((#1)*100,1) } \% } % 显示一位小数
```

## Runtime setup
```tex
\examxsetup{
  autoprint=true,     % 每题结束自动打印教师块
  show-source=false,  % 默认不展示来源
  boxed=true          % 教师块使用 tcolorbox 风格
}
```

## Troubleshooting
- **Runaway argument / File ended while scanning use of ...**：通常是 `}` 被 `%` 注释吃掉；检查最近改动。
- **一串 expl3 命令未定义**：不要在 `styles/examx.sty` 中途 `\ExplSyntaxOff`。

## Requirements
- TeX Live 2024+（推荐 2025）
- `exam-zh` 0.2.5+

License: MIT
