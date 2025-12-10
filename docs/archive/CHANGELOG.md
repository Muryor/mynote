# 版本历史

> **文档定位**: 项目演进记录，包含各版本的主要变更、优化和修复  
> **当前版本**: v4.7  
> **配套文档**: [workflow.md](../workflow.md)

---

## v4.7（当前版本）

**发布日期**: 2025-12-05

### 核心更新

#### 1. build.sh 重命名功能整合
- 重命名功能直接整合到 `build.sh`，删除 `scripts/build_named_exam.sh`
- 从源文件 `\examxtitle{}` 读取标题，不再依赖 `metadata.tex` 中的 `examDisplayName`
- 删除 `metadata.tex` 中的 `\examDisplayName` 和 `\handoutDisplayName` 变量

#### 2. synctex 正反向搜索修复
- `latexmk` 命令添加 `-synctex=1` 参数
- 重命名时同时复制 `.synctex.gz` 文件

#### 3. 文档精简
- `workflow.md` 精简至 ~80 行，版本历史移至本文件
- 移除讲义相关内容（专注试卷工作流）

#### 4. LaTeX Workshop 配置优化
- 添加 `build-exam-*` 工具和配方
- 支持从侧边栏直接调用 `build.sh`

---

## v4.6

**发布日期**: 2025-12-03

### 核心更新
- `\examimage` 宏 + 相对路径，支持移动文件夹后仍能编译
- `\setexamdir` 设置图片基准目录
- `convert_to_examimage.py` 自动转换脚本

---

## v3.6

**发布日期**: 2025-11-25

### 核心更新

#### 1. ocr_to_examx.py v1.9 解析与稳健性修复

**状态机关键修复**:
- 修复 NORMAL / IN_META / IN_ATTACHMENT 三态解析缺少 `elif` 导致的元信息丢失问题
- 纠正 `IN_META` 分支落入附件处理逻辑的结构性缺陷，确保 `\answer` / `\difficulty` / `\topics` / `\explain` 全量生成
- 增加 meta flush 前的安全 continue，避免后续块错写或花括号漂移

**功能增强**:
- 枚举与选择题环境稳健性：初步检测并在日志中提示 `choices` / `enumerate` 不匹配情况
- 图片目录推断改进：处理复杂 slug 与路径转义，减少手工指定 figures 目录的需要
- 输出问题日志扩展：加入反向定界符、截断贴图上下文采样

**可靠性指标（单卷实测）**:
- 元信息抽取完整率：100%（19 题全部包含 4 类 meta）
- 反向定界符检测覆盖：10 处全部标记
- 残留【分析】过滤：0 误报 / 0 漏报

#### 2. 数学与字体兼容增强（CJK in math）

**改动**:
- `settings/preamble.sty` 中添加 CJK 字体与数学字体协同配置（Fandol / Songti SC + NewCMMath / Asana-Math fallback）
- 解决行间/行内公式中中文字符渲染不一致、字号漂移与粗细不匹配问题
- 优化 `\setmathfont` 范围声明，避免对字母/希腊字母重新绑定导致的 spacing 回归

**结果**:
- 行内 CJK 出血与 baseline 漂移问题显著减少
- 复杂公式内中英文混排可读性提升（主观评分 +）

#### 3. 预编译验证器（validate_tex.py）迭代

**新增/增强**:
- 顺序合理性：行内与行间定界符早期失衡检测（Runaway 前置预警）
- 空段落检测：`\explain{}` 中双换行触发致命风险标记
- 环境平衡统计：`extra \begin` / `extra \end` 分类型输出
- 左右定界符平衡：减少 `\left` / `\right` 漂移误报（过滤特定组合）
- 统一错误/警告结构，便于后续接入自动修复管线

#### 4. OCR 批量修复辅助脚本

**脚本**: `tools/fix_ocr_math.py`
- 常见模式批量纠正：`\(，\)` → `\)，\(`、嵌套 `\(X\(：\)`、中文与 math 指令粘连、孤立花括号行尾
- 设计为保守转换：避免对含变量/复杂命令片段做激进替换
- 生成 `.before_fix` 备份，支持回滚

#### 5. 试卷样例清理（js-suxichang-2025-q2）

**处理内容**:
- 修复 50+ 行 OCR 错误：嵌套定界符、反向 `\)` / `\(`、`IMAGE_TODO_END` 后遗留文本、孤立 `}`
- choices 环境不平衡（10 begin / 11 end）定位与手工补齐 block 结构
- 对关键数学推导段落增加显式定界符闭合，避免 Runaway argument 触发

**遗留风险**:
- 少量复杂反向定界符（含变量）未自动修复，需后续 AI 精修
- 部分 explain 大段公式仍可能触发视觉排版拥挤（建议拆分为陈述 + 显式公式环境）

#### 6. 预处理脚本微调

- `preprocess_docx.sh` 稳定性提升：路径与 slug 包含空格/特殊 UTF-8 字符时的兼容性增强
- 增加对多语言 docx 文件的编码宽容模式（fallback ignore）

### 迁移与使用指南（v3.6）

| 场景 | 旧操作 | v3.6 推荐 |
|------|--------|-----------|
| 新增试卷转换 | 手工多步修复 OCR | 直接运行 `ocr_to_examx.py` + validate 预警 | 
| CJK 混排公式 | 手工插入 `\text{}` | 直接使用新版 preamble 自动字体配置 |
| Runaway 预防 | 编译失败后排查 | 先跑 `validate_tex.py` 定位 explain 空行 |
| OCR 批量清理 | 手工逐行替换 | 运行 `fix_ocr_math.py <file.tex>` 生成备份 |

### 升级注意事项

1. 若已有本地自定义字体，需合并新版 `preamble.sty` 中 CJK/Math 相关段落
2. 建议在批量修复前备份原始 OCR 转换输出，避免过度清理丢失上下文
3. 对 choices/enumerate 结构异常的卷，先用 validator 再行手工补齐，减少二次回归
4. 修改后的试卷建议重新跑一次 `validate_tex.py`，确认错误数下降（<5 建议进入人工精修阶段）

---

## v3.5

**发布日期**: 2025-01-24

### 核心更新

#### 1. ocr_to_examx.py v1.8.8/v1.8.9 智能修复增强

**v1.8.9: 方程组 \left\{ 补全**:
- ✅ 自动检测 `\begin{array}` 和 `\begin{cases}` 环境
- ✅ 智能补全缺失的 `\left\{`（当存在 `\right.` 且 left/right 不平衡时）
- ✅ 保守策略：检查 50 字符上下文，避免误补
- ✅ 集成到 `_sanitize_math_block` 管线，不影响现有降级逻辑

**v1.8.8: 反向定界符修复**:
- ✅ 检测功能：`collect_reversed_math_samples()` - 记录所有 `\)...\(` 模式
- ✅ 自动修复：`fix_simple_reversed_inline_pairs()` - 修复仅含标点/空白的简单情况
- ✅ 日志输出：`debug/{slug}_reversed_delimiters.log`
- ⚠️ 保守原则：复杂情况（包含字母/数字）不自动修复

**v1.8.8: Meta 命令重复检测**:
- ✅ 检测 `\answer`, `\explain`, `\topics`, `\difficulty` 重复
- ✅ 日志输出：`debug/{slug}_meta_duplicates.log`
- ℹ️ 仅检测不修改，保持输出稳定性

#### 2. validate_tex.py 增强

**新增验证方法**:
- `check_reversed_math_delimiters()`: 检测 `\)...\(` 反向模式
- `check_duplicate_meta_commands()`: 检测 Meta 命令重复
- `check_left_right_balance()`: 栈验证 `\left`/`\right` 配对
- `check_enumerate_structure()`: 检测 `enumerate` 外非 `\item` 内容
- `check_image_todo_trailing_text()`: 检测 `IMAGE_TODO_END` 后遗留文本

**增强现有方法**:
- `check_math_delimiters()`: 添加反向定界符检测
- `check_meta_commands()`: 添加重复命令检测

### 测试覆盖

- ✅ `test_array_left_braces.py`: 11 项测试全通过
- ✅ `test_reversed_delimiters.py`: 12 项测试全通过
- ✅ 实际文件验证：南京卷（9 个 array，0 需修复）、盐城卷（15 题全通过）

### 性能指标

- 方程组 `\left\{` 补全率：100%（高置信场景）
- 反向定界符自动修复率：~40%（简单情况）
- Meta 重复检测覆盖率：100%
- 编译成功率提升：~15%（减少人工修复）

---

## v3.4

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
