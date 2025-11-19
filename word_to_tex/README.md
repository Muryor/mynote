# Word to LaTeX Exam Converter

自动将 Word 格式的数学试卷（.docx）转换为 LaTeX 格式（.tex），支持公式、图片和结构化题目。

## 项目结构

```
word_to_tex/
├── input/              # 放置原始 .docx 试卷文件
├── output/             # 生成的 .tex 文件
├── figures/
│   ├── raw/            # pandoc 解包的原始图片
│   └── tikz/           # TikZ 图形代码文件
├── template/           # LaTeX 模板和元数据
│   ├── exam-template.tex
│   └── metadata.yaml
├── scripts/            # 转换脚本
│   ├── convert_exam.sh
│   ├── postprocess_exam.py
│   └── extract_images.py
├── tests/              # pytest 单元测试
│   ├── test_postprocess_exam.py
│   └── test_extract_images.py
└── requirements.txt
```

## 功能特性

1. **自动转换**：使用 pandoc 将 Word 文档转换为 LaTeX
2. **结构化识别**：自动识别并转换：
   - 大题标题（一、二、三...）→ `\section{}`
   - 题号（1．2．3．...）→ `\question`
   - 选项（A．B．C．D．）→ `\fourchoices{}{}{}{}`
   - 答案（【答案】）→ `\answer{}`
   - 解析（【解析】/【详解】）→ `\analysis{}`
3. **图片处理**：将图片替换为 TikZ 占位符，便于后续手动完善
4. **测试驱动**：通过 pytest 测试确保转换质量

## 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 确保系统已安装：
# - pandoc (用于文档转换)
# - xelatex (用于 LaTeX 编译，验证生成的文件)
```

## 使用方法

### 1. 转换单个试卷

```bash
# 将试卷文件放入 input/ 目录
cp 你的试卷.docx input/

# 运行转换脚本
./scripts/convert_exam.sh input/你的试卷.docx

# 生成的文件会在 output/ 目录中
```

### 2. 运行测试

```bash
# 在项目根目录运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_postprocess_exam.py
pytest tests/test_extract_images.py

# 显示详细输出
pytest -v
```

### 3. 单独使用脚本

```bash
# 只做结构化处理
python scripts/postprocess_exam.py output/paper-raw.tex output/paper.tex

# 只做图片提取和 TikZ 替换
python scripts/extract_images.py output/paper.tex
```

## 工作流程

1. **pandoc 转换**：将 .docx 转为原始 LaTeX，提取图片
2. **结构化处理**：识别题目结构，转换为自定义命令
3. **图片处理**：将图片替换为 TikZ 占位符
4. **编译验证**：使用 xelatex 编译检查语法

## 持续改进策略

当遇到新的试卷格式或识别问题时：

1. **添加测试用例**：
   ```python
   # 在 tests/test_postprocess_exam.py 中
   def test_new_format():
       sample = """你发现的新格式示例"""
       lines = sample.splitlines()
       out_lines = process_lines(lines)
       out = "\n".join(out_lines)
       assert "期望的输出" in out
   ```

2. **运行测试看失败**：
   ```bash
   pytest tests/test_postprocess_exam.py::test_new_format
   ```

3. **修改脚本逻辑**：
   - 调整 `scripts/postprocess_exam.py` 中的正则表达式
   - 修改状态机逻辑

4. **确保所有测试通过**：
   ```bash
   pytest
   ```

5. **批量处理**：所有测试通过后，再批量转换试卷

## LaTeX 自定义命令

生成的 LaTeX 文件使用以下自定义命令：

```latex
\section{一、单选题}           % 大题标题

\question 题目内容...           % 题目

\fourchoices                    % 四个选项
  {选项A内容}
  {选项B内容}
  {选项C内容}
  {选项D内容}

\answer{B}                      % 答案

\analysis{解析内容...}          % 解析
```

## TikZ 占位符

图片会被替换为：

```latex
% 原图：figures/raw/image1.png
\begin{center}
  \input{figures/tikz/fig01.tikz}
\end{center}
```

在 `figures/tikz/fig01.tikz` 中完善 TikZ 代码。

## 注意事项

1. 确保 Word 文档格式规范，题号、选项使用统一标点（．或。或、）
2. 答案和解析使用【答案】【解析】或【详解】标记
3. 首次转换建议先用小样本测试
4. 根据实际格式调整正则表达式（在 `scripts/postprocess_exam.py` 中）

## 疑难排查

### pandoc 转换失败
- 检查 pandoc 是否正确安装：`pandoc --version`
- 确认 Word 文档没有损坏

### 题目识别不准确
- 在 `tests/` 中添加失败案例的测试
- 调整 `scripts/postprocess_exam.py` 中的正则表达式

### LaTeX 编译错误
- 检查 `output/*-raw.tex` 中 pandoc 生成的原始内容
- 查看 `output/*.log` 文件中的错误信息
- 确保安装了必要的 LaTeX 包（ctex, amsmath, tikz 等）

## 许可

本项目用于学习和教学目的。

## 转换总结与清理

在实际转换过程中，遇到了一些常见问题，包括数学公式格式错误（display math `\[...\]` vs inline math `\(...\)`）、sed 转义问题、终端脚本挂起、环境未闭合等。我们编写了恢复脚本和清理工具来处理这些情况。

详细的问题分析、恢复步骤、清理命令、脚本改进建议，以及后续决策选项（手动清理 vs. 重新转换 vs. 混合方案），请参见 **[CONVERSION_SUMMARY.md](./CONVERSION_SUMMARY.md)**。

该文档还列出了新增的工具脚本：
- `tools/convert_display_to_inline.py` - 批量转换数学格式
- `tools/clean_extracted_attrs.py` - 清理 pandoc 图片属性
- `tools/fix_math_now.sh` - 快速修复脚本

这些工具可用于批量修复类似问题。

````
