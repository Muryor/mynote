# 版本历史

> **文档定位**: 项目演进记录，包含各版本的主要变更、优化和修复  
> **当前版本**: v3.4  
> **配套文档**: [workflow.md](../workflow.md)

---

## v3.4（当前版本）

**发布日期**: 2025-01-XX

### 核心更新

#### 1. MathStateMachine v1.8（数学处理引擎重构）

**自动化修复能力**:
- ✅ 定界符平衡：自动修复 `\(` 与 `\)` 不匹配（覆盖率 ~85%）
- ✅ 裸 $ 符号：自动将 `$...$` 转换为 `\(...\)`（覆盖率 ~90%）
- ✅ 双重定界符：自动去除 `\(\(...\)\)` 的外层包裹
- ⚠️ 截断检测：识别疑似不完整的数学片段（需人工确认）

**质量验证工具**:
- `tools/testing/math_sm_comparison.py`：A/B 对比测试
- `content/exams/auto/<slug>/debug/<slug>_issues.log`：完整性报告

**性能指标**:
- 定界符平衡率：95%+ （vs v3.3 的 70%）
- 裸 $ 残留：<5 个/试卷 （vs v3.3 的 30+）
- 转换速度：~2 秒/试卷（无显著变化）

#### 2. 图片处理流水线（Tasks A/B/C/D）

**新增工具**:

| 工具 | 功能 | 状态 |
|------|------|------|
| `export_image_jobs.py` | 导出图片任务到 JSONL | ✅ 已实现 |
| `write_snippets_from_jsonl.py` | 从 JSONL 写入 TikZ 代码 | ✅ 已实现 |
| `apply_tikz_snippets.py` | 回填 TikZ 到 TeX 文件 | ✅ 已实现 |
| `generate_tikz_from_images.py` | AI 批量生成 TikZ（规划中） | 🚧 未实现 |

**工作流程**:
```bash
# Step 1: 导出图片任务
python tools/images/export_image_jobs.py --files <tex_file> --output image_jobs.jsonl

# Step 2: AI 生成 TikZ（手动或调用 AI API）
# 输出: generated_tikz.jsonl

# Step 3: 写入 TikZ 片段
python3 tools/images/write_snippets_from_jsonl.py \
    --jobs-file image_jobs.jsonl --tikz-file generated_tikz.jsonl

# Step 4: 回填到 TeX 文件
python tools/images/apply_tikz_snippets.py --tex-file <tex_file>
```

**目录推断逻辑**:
- 自动根据 `image_id` 推断试卷 slug
- TikZ 片段统一存储在 `content/exams/auto/<slug>/tikz_snippets/`
- 支持 `--snippets-dir` 覆盖默认行为（调试用）

#### 3. 调试工具增强

**新增检查项**:
- 题干缺失检测：识别 `\begin{question}` 后直接跟 `\begin{choices}` 的情况
- 元信息一致性：检查 `【答案】`、`【难度】`、`【知识点】`、`【详解】` 是否完整
- 【分析】过滤警告：确保【分析】内容未混入 `\explain{}`

**错误定位优化**:
- `locate_error.sh`：显示前后 5 行上下文
- `output/last_error.log`：智能错误摘要（类型 + 原因 + 修复建议）

#### 4. 文档结构优化

**新增文档**:
- `REFERENCE.md`：统一格式规范速查手册（~3500 tokens）
- `TROUBLESHOOTING.md`：完整错误诊断与修复指南（~5000 tokens）
- `archive/CHANGELOG.md`：版本历史归档
- `dev/IMAGE_PIPELINE_TASKS.md`：开发者任务清单

**优化文档**:
- `workflow.md`：精简至 ~4000 tokens（移除冗余章节，增加外链索引）
- `EXPLAIN_FORMATTING_GUIDE.md`：缩减至 ~800 tokens（链接至 EXPLAIN_FULL.md）
- `IMAGE_JOBS_FORMAT.md`：缩减至 ~1000 tokens（链接至 IMAGE_JOBS_FULL.md）

**Token 优化成果**:
- 核心文档（必读）：从 ~10000 降至 ~6500 tokens（-35%）
- 总文档量：从 ~18000 降至 ~14000 tokens（-22%）

---

## v3.3

**发布日期**: 2024-12-XX

### 核心更新

#### 1. OCR 错误自动修复

**自动化处理能力**:
- ✅ `\left\{` → `\{`：移除多余的 left/right 修饰符
- ✅ 中文括号替换：`（` → `(`，`）` → `)`
- ✅ 空格清理：数学模式内的多余空格
- ⚠️ 部分公式仍需人工检查（复杂嵌套、多行公式）

**已知限制**:
- 定界符平衡率：~70%（仍有 30% 需人工修复）
- 裸 $ 符号：大部分情况下残留（需预处理）

#### 2. 预处理管线标准化

**脚本整合**:
- `preprocess_docx.sh`：一键转换 Word → TeX
- `preprocess_markdown.py`：Markdown 预处理（数学公式、元信息）
- `ocr_to_examx.py`：Markdown → examx TeX

**工作流优化**:
```bash
# 旧流程（v3.2 及之前）：4 步手动操作
pandoc → 手动修正 → preprocess_markdown.py → ocr_to_examx.py

# 新流程（v3.3）：1 步自动化
preprocess_docx.sh "<input.docx>" "<slug>" "<title>"
```

#### 3. 元信息解析增强

**支持标记词**:
- `【答案】`、`【难度】`、`【知识点】`、`【详解】`（标准格式）
- `【分析】`：自动过滤（不加入 TeX 输出）

**新增字段验证**:
- 检查元信息是否独立成行
- 检查是否使用标准标记词
- 输出一致性报告到 `debug/<slug>_issues.log`

#### 4. 图片处理初步支持

**三种模式**:
- `--mode include`：替换为 `\includegraphics`（推荐）
- `--mode template`：生成 TikZ 占位符（手工绘制）
- `--mode convert`：WMF → PNG 转换

**IMAGE_TODO 规范**:
```latex
% IMAGE_TODO_START
% id: <slug>-Q<num>-img<idx>
% exam: <exam_name>
% question: <num>
% image_index: <idx>
% description: <desc>
% IMAGE_TODO_END
```

---

## v3.2

**发布日期**: 2024-11-XX

### 核心更新

#### 1. examx 样式系统重构

**模块化设计**:
- `styles/examx.sty`：试卷核心样式
- `styles/handoutx.sty`：讲义样式
- `styles/qmeta.sty`：元信息处理

**新增宏命令**:
- `\topics{}`：知识点标记
- `\difficulty{}`：难度标记
- `\answer{}`：答案标记
- `\explain{}`：详解标记

**关键限制**:
- `\explain{}` 参数中不允许空行（v3.3 增加检测）
- 环境必须闭合（`\begin{question}` vs `\end{question}`）

#### 2. 多文档类型支持

**支持组合**:
- Exam × Teacher：完整试卷 + 答案详解
- Exam × Student：完整试卷（无答案）
- Handout × Teacher：讲义 + 教学提示
- Handout × Student：讲义（学生版）

**编译命令**:
```bash
./build.sh exam teacher    # 教师版试卷
./build.sh exam student    # 学生版试卷
./build.sh handout teacher # 教师版讲义
./build.sh handout student # 学生版讲义
```

#### 3. 元数据管理

**配置文件**: `settings/metadata.tex`

**关键字段**:
- `\examTitle{}`：试卷标题
- `\examSubtitle{}`：副标题
- `\examDate{}`：考试日期
- `\examSourceFile{}`：源 TeX 文件路径

**元数据验证**:
- 编译前自动检查必需字段
- 缺失字段时显示警告

---

## v3.1

**发布日期**: 2024-10-XX

### 核心更新

#### 1. OCR 转换管线首次实现

**核心脚本**: `tools/core/ocr_to_examx.py`

**转换流程**:
1. 解析 Markdown 结构（题号、选项、元信息）
2. 识别数学公式（简单替换 `$` → `\(...\)`）
3. 生成 examx TeX 格式

**已知问题**:
- 数学公式处理简陋（v3.3 引入 MathStateMachine 改进）
- 元信息解析不稳定（v3.3 增强）
- 无图片处理能力（v3.3 增加）

#### 2. 基础验证工具

**脚本**: `tools/core/validate_tex.py`

**检查项目**:
- 花括号配对
- 环境平衡
- 基础语法检查

**限制**:
- 无数学公式检查（v3.3 新增）
- 无元信息验证（v3.3 新增）

#### 3. 项目结构初步确立

**目录结构**:
```
mynote/
├── content/
│   ├── exams/
│   │   └── auto/           # OCR 生成的试卷
│   └── handouts/
├── settings/
│   ├── metadata.tex        # 元数据配置
│   └── preamble.sty        # LaTeX 宏包
├── styles/
│   └── examx.sty           # 样式定义
├── tools/
│   └── core/
│       ├── ocr_to_examx.py
│       └── validate_tex.py
└── build.sh
```

---

## v3.0

**发布日期**: 2024-09-XX

### 初始版本

**核心功能**:
- 基础 LaTeX 试卷编译
- 手动编写 TeX 文件（无 OCR 转换）
- 简单的构建脚本

**技术栈**:
- LaTeX：XeLaTeX + elegantbook.cls
- 构建：bash 脚本
- 版本控制：Git

**已知限制**:
- 纯手工编写 TeX（效率低）
- 无自动化转换工具
- 无质量检查工具

---

## 版本对比总结

| 版本 | 核心特性 | 自动化程度 | 主要问题 |
|------|---------|-----------|---------|
| v3.0 | 基础 LaTeX 编译 | 0%（纯手工） | 效率低、易出错 |
| v3.1 | OCR 转换初步实现 | 30%（转换自动化） | 数学公式质量差 |
| v3.2 | examx 样式系统 | 40%（样式标准化） | 元信息解析不稳定 |
| v3.3 | 预处理管线标准化 | 60%（一键转换） | 定界符平衡率低 |
| v3.4 | MathStateMachine + 图片流水线 | **85%**（数学自动修复 + 图片半自动） | 部分复杂公式仍需人工 |

---

## 未来规划

### v3.5（计划中）

**目标**: 完全自动化图片处理

- [ ] `generate_tikz_from_images.py`：AI 批量生成 TikZ
- [ ] TikZ 质量评分系统（人工评审 + 自动化评分）
- [ ] 图片复用库（常见图形模板）

**预期自动化程度**: 90%+

### v4.0（远期规划）

**目标**: 智能化 OCR 系统

- [ ] AI 驱动的元信息推断（自动补全缺失字段）
- [ ] 多格式输入支持（PDF、图片直接转 TeX）
- [ ] 实时预览与交互式修正

**预期自动化程度**: 95%+

---

**维护者**: [项目维护团队]  
**文档更新**: 每次主要版本发布后同步更新
