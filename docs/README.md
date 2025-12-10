# 文档导航中心 (v4.8)

> **快速定位**: 根据需求找到对应文档 | [工具架构](../tools/README.md) | [重构报告](../tools/docs/refactoring/REFACTORING_REPORT.md)  
> **更新**: 2025-12-09 - 工具重构完成，文档优化（减少 token 消耗）

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

### 场景3: 图片处理 (IMAGE_TODO → TikZ)

**完整指南**: [TIKZ_WORKFLOW.md](TIKZ_WORKFLOW.md) | [提示词模板](TIKZ_AGENT_PROMPT.md) | [任务清单](IMAGE_JOBS_FULL.md)

**快速流程**:
```bash
# 1. 导出任务
python tools/images/export_image_jobs.py --files <tex> --output image_jobs.jsonl

# 2. AI 生成（使用 TIKZ_AGENT_PROMPT.md）
# → generated_tikz.jsonl

# 3. 写入片段
python3 tools/images/write_snippets_from_jsonl.py \
    --jobs-file image_jobs.jsonl --tikz-file generated_tikz.jsonl

# 4. 回填
python tools/images/apply_tikz_snippets.py --tex-file <tex>
```

### 场景4: 深入了解工具架构

**工具文档**: [tools/README.md](../tools/README.md) ⭐  
**重构报告**: [tools/docs/refactoring/REFACTORING_REPORT.md](../tools/docs/refactoring/REFACTORING_REPORT.md)

**核心模块**:
- `tools/core/` - 转换引擎（ocr_to_examx.py, agent_refine.py）
- `tools/lib/` - 7个共享库（数学处理、文本清理等）
- `tools/scripts/` - 实用脚本（run_pipeline.py, validate_tex.py）

### 场景5: 规范速查

| 主题 | 文档 |
|------|------|
| 元信息映射 | [REFERENCE.md § 1](REFERENCE.md) |
| IMAGE_TODO 格式 | [REFERENCE.md § 2](REFERENCE.md) |
| `\exstep` 详解 | [REFERENCE.md § 4](REFERENCE.md) / [EXPLAIN_FULL.md](EXPLAIN_FULL.md) |
| TikZ 生成规范 | [TIKZ_AGENT_PROMPT.md](TIKZ_AGENT_PROMPT.md) |

### 场景6: 开发与扩展

**开发文档**: [dev/IMAGE_PIPELINE_TASKS.md](dev/IMAGE_PIPELINE_TASKS.md)  
**版本历史**: [archive/CHANGELOG.md](archive/CHANGELOG.md)

---

## 📁 文档分类

## 📋 核心必读

1. **[workflow.md](workflow.md)** - 标准格式工作流 ⭐⭐⭐
2. **[WORKFLOW_ZHIXUE.md](WORKFLOW_ZHIXUE.md)** - 智学网格式工作流
3. **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - 错误诊断与修复
4. **[tools/README.md](../tools/README.md)** - 工具架构与脚本使用

## 📖 参考文档

- [REFERENCE.md](REFERENCE.md) - 格式规范速查
- [TIKZ_WORKFLOW.md](TIKZ_WORKFLOW.md) - TikZ 图形转换
- [IMAGE_JOBS_FULL.md](IMAGE_JOBS_FULL.md) - 图片任务字段
- [EXPLAIN_FULL.md](EXPLAIN_FULL.md) - `\exstep` 详解

## 🔧 开发文档

- [tools/docs/refactoring/](../tools/docs/refactoring/) - 重构方案与报告
- [dev/IMAGE_PIPELINE_TASKS.md](dev/IMAGE_PIPELINE_TASKS.md) - 图片流水线任务
- [archive/CHANGELOG.md](archive/CHANGELOG.md) - 版本历史

---

## 💡 快速命令

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

## ❓ 常见问题速查

| 问题 | 快速链接 |
|------|----------|
| 编译失败 "Runaway argument" | [TROUBLESHOOTING.md § 4.4 问题 10](TROUBLESHOOTING.md) |
| 【分析】未过滤 | [TROUBLESHOOTING.md § 4.1 问题 2](TROUBLESHOOTING.md) |
| 数学公式异常 | [TROUBLESHOOTING.md § 4.2](TROUBLESHOOTING.md) |
| 图片路径错误 | [TROUBLESHOOTING.md § 4.5 问题 12](TROUBLESHOOTING.md) |
| TikZ 片段未回填 | [IMAGE_JOBS_FULL.md § 目录推断逻辑](IMAGE_JOBS_FULL.md) |

---

**版本**: v4.8 (2025-12-09) | 工具重构完成，文档优化
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
