# 文档导航中心 (v4.2)

> **我该看哪个文档？** 根据你的需求快速找到对应文档。  
> **更新**: 2025-12-01

---

## 🎯 场景导航

### 场景1: 我是新手，想快速上手

**推荐阅读顺序**:

1. **[workflow.md](workflow.md)** - 完整流程概览与快速入门 ⭐
   - 了解整体流程（Word → TeX → PDF）
   - 掌握最小可行操作流程

2. **[REFERENCE.md](REFERENCE.md)** - 格式规范速查手册
   - 元信息映射（`【答案】` → `\answer{}`）
   - IMAGE_TODO 占位符格式
   - `\exstep` 详解语法

3. **运行第一个示例**:
   ```bash
   # 使用示例文档测试
   ./build.sh exam teacher
   ```

### 场景2: 我在转换文档，遇到了错误

**快速诊断流程**:

1. **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - 错误诊断与修复指南 ⭐⭐⭐
   - 预编译检查工具
   - 编译错误快速诊断
   - 常见问题详解（8 大类，19 种错误）

2. **快速命令**:
   ```bash
   # Step 1: 结构验证
   python3 tools/core/validate_tex.py content/exams/auto/<slug>/converted_exam.tex
   
   # Step 2: 数学完整性检查
   cd tools/testing && python3 math_sm_comparison.py ../../word_to_tex/output/<exam>_preprocessed.md
   
   # Step 3: 查看错误日志
   cat output/last_error.log
   tools/locate_error.sh output/.aux/wrap-exam-teacher.log
   ```

3. **如果是高频问题**:
   - `\explain{}` 中包含空行 → TROUBLESHOOTING.md § 4.4 问题 10
   - 【分析】内容未过滤 → TROUBLESHOOTING.md § 4.1 问题 2
   - 定界符不平衡 → TROUBLESHOOTING.md § 4.2 问题 3

### 场景3: 我需要处理图片（IMAGE_TODO → TikZ）

**图片流水线完整指南**:

1. **[workflow.md § 九](workflow.md)** - 图片流水线精简概览
   - 理解 IMAGE_TODO 占位符机制
   - 了解完整流程：导出 → AI 生成 → 回填

2. **[REFERENCE.md § 2](REFERENCE.md)** - IMAGE_TODO 格式规范
   - 必需字段：id, path, width, inline
   - 推荐字段：question_index, sub_index, CONTEXT_BEFORE/AFTER

3. **[IMAGE_JOBS_FULL.md](IMAGE_JOBS_FULL.md)** - image_jobs.jsonl 完整字段定义
   - 目录推断逻辑（唯一真理）
   - 所有字段详细说明（15+ 字段）

4. **[TIKZ_AGENT_PROMPT.md](TIKZ_AGENT_PROMPT.md)** - AI 生成 TikZ 的标准 Prompt
   - AI 输入/输出格式
   - TikZ 代码质量要求

5. **[dev/IMAGE_PIPELINE_TASKS.md](dev/IMAGE_PIPELINE_TASKS.md)** - 开发者任务清单
   - Tasks A/B/C/D 详细实现需求
   - 测试清单与完成标准

6. **实际操作流程**:
   ```bash
   # Step 1: 导出图片任务
   python tools/images/export_image_jobs.py \
       --files "content/exams/auto/<slug>/converted_exam.tex" \
       --output "content/exams/auto/<slug>/image_jobs.jsonl"
   
   # Step 2: AI 生成 TikZ（手动或调用 API）
   # 输出: generated_tikz.jsonl
   
   # Step 3: 写入 TikZ 片段
   python3 tools/images/write_snippets_from_jsonl.py \
       --jobs-file "content/exams/auto/<slug>/image_jobs.jsonl" \
       --tikz-file "generated_tikz.jsonl"
   
   # Step 4: 回填到 TeX 文件
   python tools/images/apply_tikz_snippets.py \
       --tex-file "content/exams/auto/<slug>/converted_exam.tex"
   
   # Step 5: 编译
   ./build.sh exam teacher
   ```

### 场景4: 我需要深入了解某个具体规范

**按主题查阅**:

| 主题 | 文档 | 核心内容 |
|------|------|---------|
| 元信息映射 | [REFERENCE.md § 1](REFERENCE.md) | Markdown → LaTeX 映射表 |
| IMAGE_TODO 格式 | [REFERENCE.md § 2](REFERENCE.md) | 占位符字段定义与示例 |
| image_jobs.jsonl | [REFERENCE.md § 3](REFERENCE.md) 或 [IMAGE_JOBS_FULL.md](IMAGE_JOBS_FULL.md) | 核心 9 字段 vs 完整 15+ 字段 |
| `\exstep` 详解语法 | [REFERENCE.md § 4](REFERENCE.md) | 快速参考 |
| `\exstep` 详细示例 | [EXPLAIN_FULL.md](EXPLAIN_FULL.md) | 所有参数、技术细节 |
| TikZ 生成规范 | [TIKZ_AGENT_PROMPT.md](TIKZ_AGENT_PROMPT.md) | AI Prompt 模板 |
| 常见错误诊断 | [TROUBLESHOOTING.md § 四](TROUBLESHOOTING.md) | 8 大类、19 种错误详解 |

### 场景5: 我是开发者，想扩展功能

**开发者文档**:

1. **[dev/IMAGE_PIPELINE_TASKS.md](dev/IMAGE_PIPELINE_TASKS.md)** - 图片流水线任务清单
   - Tasks A/B/C/D/E 详细需求
   - 单元测试与集成测试清单

2. **[archive/CHANGELOG.md](archive/CHANGELOG.md)** - 版本历史
   - v3.0-v3.4 完整演进记录
   - 各版本核心特性与已知限制

3. **关键脚本源码**:
   - `tools/core/ocr_to_examx.py` - Markdown → TeX 核心转换
   - `tools/core/validate_tex.py` - 预编译结构验证
   - `tools/images/*.py` - 图片流水线工具集

### 场景6: 我想查看项目演进历史

**版本历史**:

- **[archive/CHANGELOG.md](archive/CHANGELOG.md)** - 完整版本历史
  - v3.4: MathStateMachine v1.8 + 图片流水线
  - v3.3: OCR 错误自动修复 + 预处理管线标准化
  - v3.2: examx 样式系统重构
  - v3.1: OCR 转换管线首次实现
  - v3.0: 基础 LaTeX 试卷编译

---

## 📁 文档分类

### 核心必读（按推荐顺序）

| 文档 | 作用 | 预计阅读时间 |
|------|------|------------|
| **README.md** (本文档) | 导航中心 | 5 分钟 |
| **[workflow.md](workflow.md)** | 完整流程概览 | 20 分钟 |
| **[REFERENCE.md](REFERENCE.md)** | 格式规范速查 | 10 分钟 |
| **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** | 错误诊断与修复 | 30 分钟（按需查阅）|

### 深度参考（按需查阅）

| 文档 | 作用 | 何时查阅 |
|------|------|---------|
| **[IMAGE_JOBS_FULL.md](IMAGE_JOBS_FULL.md)** | image_jobs.jsonl 完整字段 | 处理图片时查阅完整 schema |
| **[EXPLAIN_FULL.md](EXPLAIN_FULL.md)** | `\exstep` 详细示例 | 需要高级格式化详解时 |
| **[TIKZ_AGENT_PROMPT.md](TIKZ_AGENT_PROMPT.md)** | AI 生成 TikZ Prompt | 开发 AI 图片生成功能时 |

### 归档与开发

| 文档 | 作用 | 受众 |
|------|------|------|
| **[archive/CHANGELOG.md](archive/CHANGELOG.md)** | 版本历史 | 了解项目演进 |
| **[dev/IMAGE_PIPELINE_TASKS.md](dev/IMAGE_PIPELINE_TASKS.md)** | 开发任务清单 | 开发者 |

---

## 🚀 快速命令清单

### 文档转换

```bash
# 一键转换 Word → TeX
word_to_tex/scripts/preprocess_docx.sh \
    "word_to_tex/input/<文件名>.docx" \
    "<输出前缀>" \
    "<试卷标题>"

# 手动转换（分步）
pandoc input.docx -o output_raw.md --extract-media=figures
python3 tools/core/ocr_to_examx.py \
    output_raw.md \
    content/exams/auto/<slug>/converted_exam.tex \
    --title "<试卷标题>"
```

### 质量检查

```bash
# 结构验证
python3 tools/core/validate_tex.py content/exams/auto/<slug>/converted_exam.tex

# 数学完整性检查
cd tools/testing && python3 math_sm_comparison.py ../../word_to_tex/output/<exam>_preprocessed.md

# 查看问题日志
cat content/exams/auto/<slug>/debug/<slug>_issues.log
```

### 编译与测试

```bash
# 编译（带预检查）
VALIDATE_BEFORE_BUILD=1 ./build.sh exam teacher

# 查看错误
cat output/last_error.log
tools/locate_error.sh output/.aux/wrap-exam-teacher.log

# 回归测试
tools/test_compile.sh
```

### 图片处理

```bash
# 导出图片任务
python tools/images/export_image_jobs.py \
    --files "content/exams/auto/<slug>/converted_exam.tex" \
    --output "content/exams/auto/<slug>/image_jobs.jsonl"

# 写入 TikZ 片段
python3 tools/images/write_snippets_from_jsonl.py \
    --jobs-file image_jobs.jsonl \
    --tikz-file generated_tikz.jsonl

# 回填 TikZ 到 TeX
python tools/images/apply_tikz_snippets.py \
    --tex-file content/exams/auto/<slug>/converted_exam.tex
```

---

## 🔗 学习路径推荐

### 入门路径（新手）

1. 阅读 [workflow.md](workflow.md) § 一、二、四
2. 运行第一个示例：`./build.sh exam teacher`
3. 尝试转换一个简单的 Word 文档
4. 遇到问题时查阅 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

### 进阶路径（熟练用户）

1. 深入学习 [REFERENCE.md](REFERENCE.md) 所有规范
2. 理解 [TROUBLESHOOTING.md](TROUBLESHOOTING.md) 所有错误类型
3. 掌握图片流水线（IMAGE_TODO → TikZ）
4. 优化转换质量（减少人工修正）

### 专家路径（开发者）

1. 研读 [dev/IMAGE_PIPELINE_TASKS.md](dev/IMAGE_PIPELINE_TASKS.md)
2. 查阅 [archive/CHANGELOG.md](archive/CHANGELOG.md) 了解演进
3. 阅读核心脚本源码
4. 扩展功能或贡献代码

---

## 💡 常见问题速查

### Q1: 编译失败，显示 "Runaway argument"

**A**: `\explain{}` 中包含空行。  
**解决**: 删除空行或用 `%` 注释。  
**详见**: [TROUBLESHOOTING.md § 4.4 问题 10](TROUBLESHOOTING.md)

### Q2: 【分析】内容出现在 PDF 中

**A**: `ocr_to_examx.py` 未正确过滤【分析】。  
**解决**: 检查 `META_PATTERNS["analysis"]` 正则表达式。  
**详见**: [TROUBLESHOOTING.md § 4.1 问题 2](TROUBLESHOOTING.md)

### Q3: 数学公式显示异常

**A**: 定界符不平衡或裸 $ 符号残留。  
**解决**: 运行 `math_sm_comparison.py` 检查。  
**详见**: [TROUBLESHOOTING.md § 4.2](TROUBLESHOOTING.md)

### Q4: 图片路径错误

**A**: Pandoc 提取的图片路径与 TeX 中的 `\includegraphics` 不匹配。  
**解决**: 使用 `process_images_to_tikz.py` 自动处理路径。  
**详见**: [TROUBLESHOOTING.md § 4.5 问题 12](TROUBLESHOOTING.md)

### Q5: TikZ 片段未回填

**A**: AI 未生成对应 id 的 TikZ 代码，或目录推断失败。  
**解决**: 检查 `generated_tikz.jsonl` 和 `snippets_dir` 路径。  
**详见**: [IMAGE_JOBS_FULL.md § 目录推断逻辑](IMAGE_JOBS_FULL.md)

---

## 📞 获取帮助

### 文档内链

- 遇到术语不理解？查阅 [REFERENCE.md](REFERENCE.md)
- 遇到错误？查阅 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- 想了解历史？查阅 [archive/CHANGELOG.md](archive/CHANGELOG.md)

### 调试建议

1. **始终先运行预检查工具**: `validate_tex.py` + `math_sm_comparison.py`
2. **查看详细日志**: `cat content/exams/auto/<slug>/debug/<slug>_issues.log`
3. **使用智能错误定位**: `tools/locate_error.sh`

---

**文档维护**: 每次主要版本发布后同步更新  
**当前版本**: v3.4  
**最后更新**: 2025-01-XX
