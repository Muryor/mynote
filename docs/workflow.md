# LaTeX 试卷流水线指南 (v4.6)

> v4.6 (2025-12-03) | PNG 优先 | `\examimage` 宏 | TikZ 流程见 [TIKZ_WORKFLOW.md](TIKZ_WORKFLOW.md)

## 快速导航

| 文档 | 用途 |
|------|------|
| [REFERENCE.md](REFERENCE.md) | 格式规范（IMAGE_TODO、表格） |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | 错误诊断（19种问题） |
| [TIKZ_WORKFLOW.md](TIKZ_WORKFLOW.md) | TikZ 转换流程 |

---

## 一、路径约定

```
输入 Word:     word_to_tex/input/<name>.docx
中间 Markdown: word_to_tex/output/<prefix>_preprocessed.md
输出 TeX:      content/exams/auto/<prefix>/converted_exam.tex
输出图片:      content/exams/auto/<prefix>/images/media/
输出 PDF:      output/wrap-exam-*.pdf
```

## 二、元信息映射

| Markdown | LaTeX | 备注 |
|----------|-------|------|
| `【答案】` | `\answer{}` | 直接映射 |
| `【难度】` | `\difficulty{}` | 直接映射 |
| `【知识点】`/`【考点】` | `\topics{}` | 合并 |
| `【详解】`/`【点睛】` | `\explain{}` | ✅ 唯一来源 |
| `【分析】` | **丢弃** | ⚠️ 严禁 |

---

## 三、标准工作流

### 3.1 一键转换

```bash
# 1. Word → TeX（自动复制图片）
word_to_tex/scripts/preprocess_docx.sh \
    "word_to_tex/input/exam.docx" "exam_2025" "2025年试卷"

# 2. IMAGE_TODO → includegraphics（PNG优先）
python3 tools/images/process_images_to_tikz.py --mode include \
    --files content/exams/auto/exam_2025/converted_exam.tex

# 3. 修改 metadata.tex 并编译
# \newcommand{\examSourceFile}{content/exams/auto/exam_2025/converted_exam.tex}
./build.sh exam both
```

### 3.2 编译命令

```bash
./build.sh exam teacher/student/both      # 标准编译
VALIDATE_BEFORE_BUILD=1 ./build.sh exam teacher  # 带预检查
#自动重命名（可选）
# 在单次构建时设置源 TeX（脚本会尝试重命名输出）
EXAM_TEX='content/exams/auto/exam_2025/converted_exam.tex' ./build.sh exam both

# 仅运行重命名脚本（跳过实际编译）
EXAM_TEX='content/exams/auto/exam_2025/converted_exam.tex' SKIP_BUILD=1 ./scripts/build_named_exam.sh exam both
```

---

## 四、质量保证

### 4.1 验证命令

```bash
python3 tools/validate_tex.py <tex_file>                    # 结构验证
python3 tools/validate_tex.py <tex_file> --strict --warn-text-i  # 严格模式
python3 tools/core/ocr_to_examx.py --selftest               # 自测
tools/test_compile.sh                                        # 回归测试
```

### 4.2 调试命令

```bash
tools/locate_error.sh output/.aux/wrap-exam-teacher.log     # 错误定位
cat output/last_error.log                                    # 查看错误
cat word_to_tex/output/debug/*_issues.log | grep "CRITICAL\|ERROR"
```

---

## 五、图片处理

### 5.1 `\examimage` 宏（推荐）

试卷中的图片统一使用 `\examimage` 宏 + 相对路径，支持移动文件夹后仍能编译。

**试卷文件结构**：
```tex
\setexamdir{content/exams/auto/exam_2025}  % 设置图片基准目录

\examxtitle{2025年试卷}
...
\examimage{images/media/image1.png}{0.4}   % 相对路径
```

**宏定义**（`settings/preamble.sty`）：
```tex
\setexamdir{path}           % 设置试卷目录（路径会自动拼接）
\examimage{relpath}{width}  % 居中图片
\examimageinline{relpath}{width}  % 行内图片
```

**优势**：
- ✅ 移动整个试卷目录后仍能编译（只需更新 `\setexamdir`）
- ✅ 组卷时只需更改 `\setexamdir` 即可
- ✅ 图片路径简洁明了

### 5.2 转换脚本

```bash
# 预览
python3 tools/images/convert_to_examimage.py --dry-run <tex_file>

# 执行转换（自动插入 \setexamdir + 转换路径）
python3 tools/images/convert_to_examimage.py <tex_file>

# 批量转换所有试卷
python3 tools/images/convert_to_examimage.py content/exams/auto/*/converted_exam.tex
```

### 5.3 IMAGE_TODO 处理（旧流程）

```bash
# 替换为 includegraphics
python3 tools/images/process_images_to_tikz.py --mode include --files <tex_file>

# 生成 TikZ 模板
python3 tools/images/process_images_to_tikz.py --mode template --files <tex_file>
```

> TikZ 转换流程见 [TIKZ_WORKFLOW.md](TIKZ_WORKFLOW.md)

---

## 六、版本历史

| 版本 | 日期 | 更新 |
|------|------|------|
| v4.6 | 2025-12-03 | `\examimage` 宏 + 相对路径，支持移动文件夹 |
| v4.5 | 2025-01-15 | 精简文档，TikZ 流程外链 |
| v4.4 | 2025-01-15 | convert_images_to_tikz_templates.py v2.0 |
| v4.2 | 2025-12-01 | 图片自动复制、路径修复 |
