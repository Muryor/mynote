# LaTeX 试卷流水线指南 (v4.2)

> **版本**: v4.2（2025-12-01）  
> **更新**: preprocess_docx.sh 自动复制图片；修复小问分割与条件表达式；process_images_to_tikz.py 路径/宽度修复

---

## 快速导航

| 文档 | 用途 |
|------|------|
| [REFERENCE.md](REFERENCE.md) | 格式规范速查（IMAGE_TODO、表格、脚本参数） |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | 错误诊断指南（19种常见问题） |
| [TIKZ_AGENT_PROMPT.md](TIKZ_AGENT_PROMPT.md) | TikZ 生成 Prompt |
| [IMAGE_JOBS_FULL.md](IMAGE_JOBS_FULL.md) | 图片任务 JSONL 字段定义 |

---

## 一、核心规范

### 1.1 路径约定

```text
输入 Word:     word_to_tex/input/<name>.docx
输出 Markdown: word_to_tex/output/<prefix>_preprocessed.md
输出 TeX:      content/exams/auto/<prefix>/converted_exam.tex
输出图片:      content/exams/auto/<prefix>/images/media/
输出 PDF:      output/wrap-exam-*.pdf
```

### 1.2 元信息映射

| Markdown | LaTeX | 备注 |
|----------|-------|------|
| `【答案】A` | `\answer{A}` | 直接映射 |
| `【难度】0.85` | `\difficulty{0.85}` | 直接映射 |
| `【知识点】`/`【考点】` | `\topics{...}` | 合并 |
| `【详解】`/`【点睛】` | `\explain{...}` | ✅ 主要来源 |
| `【分析】` | **丢弃** | ⚠️ 严禁使用 |

### 1.3 编译命令

```bash
# 标准编译
./build.sh exam teacher/student/both

# 带预检查（推荐）
VALIDATE_BEFORE_BUILD=1 ./build.sh exam teacher
```

---

## 二、标准工作流

### 一键转换（推荐）

```bash
# 1. 运行转换脚本（自动复制图片）
word_to_tex/scripts/preprocess_docx.sh \
    "word_to_tex/input/exam.docx" \
    "exam_2025" \
    "2025年试卷"

# 2. 替换 IMAGE_TODO 为 includegraphics
python3 tools/images/process_images_to_tikz.py --mode include \
    --files content/exams/auto/exam_2025/converted_exam.tex

# 3. 修改 metadata.tex 并编译
# \newcommand{\examSourceFile}{content/exams/auto/exam_2025/converted_exam.tex}
./build.sh exam teacher
```

---

## 三、质量保证

### 3.1 预编译检查

```bash
# 结构验证
python3 tools/validate_tex.py <tex_file>

# 带参数验证
python3 tools/validate_tex.py <tex_file> --strict --warn-text-i

# 自测
python3 tools/core/ocr_to_examx.py --selftest

# 回归测试
tools/test_compile.sh
```

### 3.2 调试命令

```bash
# 错误定位
tools/locate_error.sh output/.aux/wrap-exam-teacher.log

# 查看错误日志
cat output/last_error.log

# 检查问题日志
cat word_to_tex/output/debug/*_issues.log | grep "CRITICAL\|ERROR"

# 黑箱测试
python3 tools/testing/ocr_blackbox_tests/run_tests.py <preprocessed.md>
```

### 3.3 常见转换错误及自动修复

| 错误模式 | 正确格式 | 自动修复 |
|----------|----------|----------|
| `\left\| x \|` | `\left\| x \right\|` | ✅ v1.9.9 |
| `\left. <a,b>\right.>` | `\langle a,b \rangle` | ✅ v1.9.9 |
| `\overset{arrow}{a}` | `\vec{a}` 或 `\overrightarrow{a}` | ❌ 手动 |
| `\$\$...\$\$` 嵌套 `\(...\)` | `\(...\)` 统一格式 | ✅ 自动 |

---

## 四、图片处理

### 4.1 PNG 优先策略（推荐）

```bash
# 预览所有图片占位符
python3 tools/images/process_images_to_tikz.py --mode preview --files <tex_file>

# 批量替换为 includegraphics（宽度默认 0.30）
python3 tools/images/process_images_to_tikz.py --mode include --files <tex_file>

# 生成 TikZ 模板（用于后续手工绘制）
python3 tools/images/process_images_to_tikz.py --mode template --files <tex_file>
```

### 4.2 IMAGE_TODO 占位符格式

```tex
\begin{center}
% IMAGE_TODO_START id=exam-Q3-img1 path=figures/media/image1.png width=60% inline=false question_index=3 sub_index=1
% CONTEXT_BEFORE: 已知函数 f(x) 在区间 [0,1] 上单调递增，其图像如下所示：
% CONTEXT_AFTER: 则下列结论中正确的是（    ）。
\begin{tikzpicture}
  % TODO: AI_AGENT_REPLACE_ME (id=exam-Q3-img1)
\end{tikzpicture}
% IMAGE_TODO_END id=exam-Q3-img1
\end{center}
```

**字段说明**：`id`（必选）、`path`（必选）、`width`（必选）、`inline`（必选）、`question_index`（建议）、`sub_index`（建议）

### 4.3 TikZ 流水线（时间充裕时）

```bash
# 导出图片任务
python3 tools/images/export_image_jobs.py --files <tex_file>

# AI Agent 生成 TikZ → generated_tikz.jsonl

# 写入 TikZ 片段
python3 tools/images/write_snippets_from_jsonl.py --jobs-file image_jobs.jsonl --tikz-file generated_tikz.jsonl

# 应用 TikZ 代码
python3 tools/images/apply_tikz_snippets.py --tex-file <tex_file>
```

### 4.4 路径要求

```tex
% ✅ 正确（从项目根目录）
\includegraphics[width=0.30\textwidth]{content/exams/auto/exam/images/media/image1.png}

% ❌ 错误（相对路径）
\includegraphics[width=0.30\textwidth]{images/media/image1.png}
```

### 4.5 常见转换错误（自动修复）

| 错误模式 | 正确格式 | 说明 |
|----------|----------|------|
| `\left\| ... \|` | `\left\| ... \right\|` | 🆕 v1.9.9 自动修复绝对值配对 |
| `\left. <...\right.>` | `\langle...\rangle` | 🆕 v1.9.9 自动修复向量夹角 |
| `\overset{arrow}{a}` | `\vec{a}` | 手动修复向量符号 |

---

## 五、版本历史

### v4.3 (2025-12-01)
- 🆕 ocr_to_examx.py v1.9.9：自动修复 `\left|...|` → `\left|...\right|`
- 🆕 自动修复向量夹角 `\left.<...>` → `\langle...\rangle`
- 新增常见转换错误文档

### v4.2 (2025-12-01)
- preprocess_docx.sh 自动复制图片
- 修复方程组推导符号 `\right.\) \Rightarrow \left\{` → `\right. \Rightarrow \left\{`
- 修复小问分割（保护 `\left...\right`）
- 修复条件表达式 `(y>0)` 格式
- process_images_to_tikz.py：路径/宽度修复
- 【分析】检查跳过注释行

### v4.0 (2025-11-28)
- ocr_to_examx.py v1.9.5：智能 ∴/∵ 处理
- 18 项黑箱测试

---

**祝使用顺利！🚀**
