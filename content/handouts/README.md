# Handouts Directory Structure

本目录按年级和专题组织讲义内容。

## 目录结构说明

### 高一（G1）和高二（G2）

按学期划分：
- `g1/sem1/` - 高一上学期
- `g1/sem2/` - 高一下学期
- `g2/sem1/` - 高二上学期
- `g2/sem2/` - 高二下学期

每个学期目录可以进一步按章节或单元划分（可选）。

### 高三（G3）

按专题划分：
- `g3/functions/` - 函数专题
- `g3/derivatives/` - 导数专题
- `g3/conics/` - 圆锥曲线专题
- `g3/sequences/` - 数列专题
- `g3/trigonometry/` - 三角函数专题
- `g3/vectors/` - 向量专题
- `g3/combinatorics/` - 排列组合专题
- `g3/probability_statistics/` - 概率与统计专题
- `g3/solid_geometry/` - 立体几何专题
- `g3/sets_complex_inequalities/` - 集合、复数、不等式专题
- `g3/comprehensive/` - 综合专题

## 文件命名建议

推荐使用英文 lower_snake_case 文件名，例如：
- `g3_functions_topic01_basic_concepts.tex` - 高三函数专题（一）：基本概念
- `g1_sem1_chapter02_quadratic_functions.tex` - 高一上学期第二章：二次函数

## 元数据系统

讲义中的例题使用 `examplex` 环境，支持统一的元数据标记：
```latex
\begin{examplex}{例题标题}{ex:label}
题目内容...
\topics{考点1；考点2}
\difficulty{0.6}
\answer{答案内容}
\explain{详细解答}
\end{examplex}
```

## 切换讲义内容

修改 `settings/metadata.tex` 中的 `\handoutSourceFile` 路径即可切换要编译的讲义：
```latex
\newcommand{\handoutSourceFile}{content/handouts/g3/functions/g3_functions_topic01_basic_concepts.tex}
```

支持英文路径和中文路径（macOS + XeLaTeX 环境）。
