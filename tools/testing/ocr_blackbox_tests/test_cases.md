# OCR to ExamX 黑箱测试用例定义

## 测试目标
对 `tools/core/ocr_to_examx.py` 进行系统性黑箱测试，发现脚本在处理真实高考试卷时的问题。

## 测试用例分类

| 用例ID | 类别 | 测试点 | 预期行为 |
|--------|------|--------|----------|
| T001 | 元信息解析 | 【答案】提取 | 正确映射到 `\answer{}` |
| T002 | 元信息解析 | 【难度】提取 | 正确映射到 `\difficulty{}` |
| T003 | 元信息解析 | 【知识点】/【考点】合并 | 合并到 `\topics{}` |
| T004 | 元信息解析 | 【分析】过滤 | **完全丢弃**，不出现在 TeX 中 |
| T005 | 元信息解析 | 【详解】保留 | 正确映射到 `\explain{}` |
| T006 | 数学公式 | `$...$` 转换 | 转为 `\(...\)` |
| T007 | 数学公式 | `$$...$$` 转换 | 转为 `\(...\)` 或 `$$\n...\n$$` |
| T008 | 数学公式 | 定界符平衡 | `\(` 和 `\)` 数量相等 |
| T009 | 数学公式 | 反向定界符 | `\)...\(` 模式被修复 |
| T010 | 数学公式 | 双重包裹 | 无 `$$$...$$$` 嵌套 |
| T011 | 结构完整性 | question 环境闭合 | `\begin` 与 `\end` 配对 |
| T012 | 结构完整性 | choices 环境 | 选项正确包裹 |
| T013 | 结构完整性 | 题干存在性 | 题目不以 `\item` 开头 |
| T014 | 图片处理 | IMAGE_TODO 格式 | 包含 id/path/width/inline |
| T015 | 图片处理 | 图片属性清理 | 无残留 `{width=... height=...}` |
| T016 | 特殊字符 | LaTeX 转义 | `%`, `&`, `#` 正确转义 |
| T017 | 中文处理 | 数学模式内标点 | 全角转半角 |
| T018 | array/cases | `\left\{` 补全 | 自动补全缺失的左括号 |
| T019 | tabular | 列格式参数 | 自动添加 `{|c|c|...}` |
| T020 | explain 空行 | 空行处理 | 空行替换为 `\par` 或删除 |

## 测试详情

### 元信息解析测试

#### T001: 【答案】提取
- **输入**: Markdown 中包含 `【答案】A` 或 `【答案】B`
- **预期**: 生成 `\answer{A}` 或 `\answer{B}`
- **验证方法**: 统计 `\answer{}` 数量 ≥ Markdown 中【答案】数量的 80%

#### T002: 【难度】提取
- **输入**: `【难度】0.65`
- **预期**: `\difficulty{0.65}`
- **验证方法**: 正则匹配 `\difficulty{[0-9.]+}`

#### T003: 【知识点】/【考点】合并
- **输入**: `【知识点】集合` 或 `【考点】集合`
- **预期**: `\topics{集合}`
- **验证方法**: 检查 `\topics{}` 存在且内容非空

#### T004: 【分析】过滤
- **输入**: `【分析】根据题意分析...`
- **预期**: TeX 中**完全不存在**任何【分析】标记或内容
- **验证方法**: 
  - 检查 TeX 中无 `【分析】` 字符串
  - 检查 `\explain{}` 中无典型分析词汇（如"根据题意分析"）

#### T005: 【详解】保留
- **输入**: `【详解】详细解答过程...`
- **预期**: `\explain{详细解答过程...}`
- **验证方法**: 统计 `\explain{}` 数量 ≥ Markdown 中【详解】数量的 80%

### 数学公式测试

#### T008: 定界符平衡
- **验证方法**: 排除注释行后，统计 `\(` 和 `\)` 数量，差值必须为 0

#### T009: 反向定界符检测
- **问题模式**: `...\) , \(...` (先闭后开)
- **验证方法**: 在同一行内检测 `\)` 在 `\(` 之前的情况

#### T010: 双重包裹
- **问题模式**: `$$\(`, `\)$$`, `\(\(`, `\)\)`
- **验证方法**: 正则匹配上述模式，数量应为 0

### 结构完整性测试

#### T011: question 环境闭合
- **验证方法**: `\begin{question}` 数量 = `\end{question}` 数量

#### T012: choices 环境
- **验证方法**: 每个 `\begin{choices}...\end{choices}` 块内包含 2-10 个 `\item`

#### T013: 题干存在性
- **问题模式**: `\begin{question}\n\item` (题目直接从选项开始)
- **验证方法**: 正则匹配该模式，数量应为 0

### 图片处理测试

#### T014: IMAGE_TODO 格式
- **预期格式**:
```
% IMAGE_TODO_START id=<uuid> path=<filename> width=0.6\textwidth inline=false
\includegraphics[width=0.6\textwidth]{figures/<filename>}
% IMAGE_TODO_END
```
- **验证方法**: 检查每个 IMAGE_TODO 块包含必需字段

#### T015: 图片属性清理
- **问题模式**: `{width="300px"}`, `height="200"`
- **验证方法**: 正则匹配残留的 HTML/Markdown 图片属性，数量应为 0

### 特殊处理测试

#### T017: 数学模式内中文标点
- **验证方法**: 提取 `\(...\)` 内容，排除 `\text{}`/`\mbox{}` 后检测全角标点

#### T020: explain 空行
- **问题**: `\explain{}` 内包含空行可能导致编译错误
- **验证方法**: 检测 `\explain{...}` 内是否有 `\n\n`

## 测试数据

### 可用的预处理文件
```
word_to_tex/output/gaokao_2025_national_1_preprocessed.md
word_to_tex/output/hangzhou_2025_2026_quality_preprocessed.md
word_to_tex/output/hunan-changsha-yali-2026-mock3_preprocessed.md
word_to_tex/output/jiangsu-changzhou-2025-2026-midterm_preprocessed.md
word_to_tex/output/js-suxichang-2025-q2_preprocessed.md
word_to_tex/output/nanjing_2026_sep_preprocessed.md
word_to_tex/output/nanjing_yancheng_2025_mock1_preprocessed.md
word_to_tex/output/suzhou-2025-2026-yangguang_preprocessed.md
word_to_tex/output/zhejiang_lishui_2026_nov_preprocessed.md
```

## 严重程度分级

- **P0**: 导致编译失败（定界符不平衡、环境不闭合）
- **P1**: 导致内容错误（【答案】丢失、【分析】未过滤）
- **P2**: 导致格式问题（空行、图片属性残留）

## 测试报告格式

每个测试生成 JSON 报告，包含：
```json
{
  "exam_file": "文件路径",
  "timestamp": "ISO时间戳",
  "summary": {
    "total": 20,
    "passed": 18,
    "failed": 2
  },
  "results": [
    {
      "test_id": "T001",
      "name": "【答案】提取",
      "passed": true,
      "message": "找到 22 个 \\answer，Markdown 中有 22 个【答案】",
      "details": "提取率: 100.0%"
    }
  ]
}
```
