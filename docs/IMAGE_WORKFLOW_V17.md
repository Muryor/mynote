# 图片工作流 v1.7 - 使用 examimage 格式

## 核心改进

v1.7 版本引入了 `\examimage` 和 `\setexamdir` 机制，使得试卷可以自由移动文件夹而无需修改图片路径。

## 新格式说明

### 1. \setexamdir 指令

在试卷开头添加：

```latex
\examxtitle{试卷标题}
\setexamdir{content/exams/auto/exam_slug}
```

这个指令设置了试卷的根目录，所有图片路径都相对于这个目录。

### 2. \examimage 命令

**普通图片（独立成行，居中显示）：**

```latex
\examimage{images/media/image2.png}{0.60}
```

- 第一个参数：相对于试卷目录的图片路径
- 第二个参数：宽度比例（0.60 = 60% 页面宽度）

**内联图片（嵌入文本中）：**

```latex
如图 \examimageinline{images/media/image5.png}{0.30} 所示...
```

## 完整工作流

### 步骤 1: DOCX 转换

```bash
cd /Users/muryor/code/mynote
./word_to_tex/scripts/preprocess_docx.sh \
  "word_to_tex/input/试卷文件.docx" \
  exam_slug \
  "试卷标题"
```

**自动完成：**
1. ✅ Pandoc 转换 DOCX → Markdown
2. ✅ 提取图片到 `word_to_tex/output/figures/exam_slug/media/`
3. ✅ Markdown → examx LaTeX
4. ✅ Agent 精修（创建 TikZ 占位符）
5. ✅ **复制图片到试卷目录** `content/exams/auto/exam_slug/images/media/`
6. ✅ **自动转换 IMAGE_TODO → \examimage**
7. ✅ **自动添加 \setexamdir**
8. ✅ LaTeX 语法验证

### 步骤 2: 配置编译入口

编辑 `settings/metadata.tex`：

```latex
\newcommand{\examSourceFile}{content/exams/auto/exam_slug/converted_exam.tex}
```

### 步骤 3: 编译 PDF

```bash
./build.sh exam both
```

生成：
- `output/wrap-exam-teacher.pdf` - 教师版（带答案解析）
- `output/wrap-exam-student.pdf` - 学生版（无答案）

## 优势

### 1. 路径灵活性

**移动试卷文件夹后无需修改：**

```bash
# 移动前
content/exams/auto/jinan_2025_mock/converted_exam.tex

# 移动后
content/exams/archive/2025/jinan_mock/converted_exam.tex
```

只需更新 `\setexamdir` 一行即可：

```latex
- \setexamdir{content/exams/auto/jinan_2025_mock}
+ \setexamdir{content/exams/archive/2025/jinan_mock}
```

### 2. 图片路径统一

所有图片使用相对路径：

```latex
\examimage{images/media/image2.png}{0.60}
```

而非绝对路径：

```latex
\includegraphics[width=0.6\textwidth]{content/exams/auto/jinan_2025_mock/images/media/image2.png}
```

### 3. 自动化程度高

从 DOCX 到 PDF 只需两个命令：

```bash
# 1. 转换
./word_to_tex/scripts/preprocess_docx.sh "input/exam.docx" exam_slug "标题"

# 2. 编译
./build.sh exam both
```

## 示例对比

### v1.6 旧格式（不推荐）

```latex
\examxtitle{山东省济南市摸底考试}

\begin{center}
\includegraphics[width=0.6\textwidth]{content/exams/auto/jinan_2025_mock/images/media/image2.png}
\end{center}
```

**问题：**
- 移动文件夹需要全文搜索替换路径
- 图片路径硬编码，不灵活
- 需要手动添加 `\begin{center}...\end{center}`

### v1.7 新格式（推荐）

```latex
\examxtitle{山东省济南市摸底考试}
\setexamdir{content/exams/auto/jinan_2025_mock}

\examimage{images/media/image2.png}{0.60}
```

**优势：**
- 移动文件夹只需修改一行 `\setexamdir`
- 图片路径相对化，清晰简洁
- 自动居中，语法更简洁

## 手动转换现有试卷

如果有旧试卷使用 `\includegraphics` 格式，可以手动转换：

### 方法 1: 使用脚本（如果有 IMAGE_TODO）

```bash
python3 tools/images/replace_image_todos_with_includes.py \
  content/exams/auto/exam_slug/converted_exam.tex
```

### 方法 2: 手动编辑

1. 在文件开头添加：

```latex
\setexamdir{content/exams/auto/exam_slug}
```

2. 替换图片命令：

```latex
# 旧格式
\begin{center}
\includegraphics[width=0.6\textwidth]{content/exams/auto/exam_slug/images/media/image2.png}
\end{center}

# 新格式
\examimage{images/media/image2.png}{0.60}
```

3. 内联图片：

```latex
# 旧格式
\includegraphics[width=0.3\textwidth]{content/exams/auto/exam_slug/images/media/image5.png}

# 新格式
\examimageinline{images/media/image5.png}{0.30}
```

## 技术细节

### \examimage 宏定义位置

定义在 `styles/examx.sty` 中：

```latex
\newcommand{\examimage}[2]{%
  \begin{center}
  \includegraphics[width=#2\textwidth]{\theexamdir/#1}%
  \end{center}
}

\newcommand{\examimageinline}[2]{%
  \includegraphics[width=#2\textwidth]{\theexamdir/#1}%
}
```

### \setexamdir 工作原理

```latex
\newcommand{\setexamdir}[1]{%
  \def\theexamdir{#1}%
}
```

设置全局变量 `\theexamdir`，所有 `\examimage` 命令引用此变量。

## 版本历史

- **v1.7** (2024-12-10): 引入 `\examimage` 和 `\setexamdir`，自动转换工作流
- **v1.6**: 自动复制图片到试卷目录
- **v1.5**: 数学公式和选项格式自动修复

## 下一步计划

- [ ] 支持图片尺寸自动检测和优化
- [ ] 支持图片格式转换（JPG → PNG）
- [ ] 支持图片压缩（减小 PDF 体积）
- [ ] 集成 TikZ 自动生成（替代 PNG）
