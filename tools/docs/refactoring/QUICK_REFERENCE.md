# OCR 脚本重构 - 快速参考卡片

## 📋 项目状态

**当前进度**: Phase 0 完成 (方案设计 + 工具开发)
**下一步**: 运行代码提取脚本

## 🎯 目标

将 `ocr_to_examx.py` (7000+行) 重构为模块化结构，支持:
- ✅ **试卷转换** (已有功能)
- 🆕 **讲义转换** (新功能)

## 📁 已创建文件

| 文件 | 用途 | 大小 |
|------|------|------|
| `REFACTORING_PLAN.md` | 详细方案设计 | 详尽 |
| `README_REFACTORING.md` | 快速上手指南 | 实用 |
| `REFACTORING_SUMMARY.md` | 工作总结 | 概览 |
| `extract_modules.py` | 自动提取工具 | 可执行 |
| `verify_refactoring.sh` | 环境验证脚本 | 可执行 |

## ⚡ 立即执行 (5分钟)

```bash
cd /Users/muryor/code/mynote

# 1. 验证环境
./tools/verify_refactoring.sh

# 2. 运行提取（生成7个模块文件）
python3 tools/extract_modules.py

# 3. 检查结果
ls -lh tools/lib/
```

## 📊 模块划分 (7个)

| 模块 | 功能 | 行数 |
|------|------|------|
| `math_processing.py` | 数学公式处理 | ~2000 |
| `text_cleaning.py` | 文本清理转义 | ~800 |
| `meta_extraction.py` | 元数据提取 | ~400 |
| `latex_utils.py` | LaTeX工具 | ~500 |
| `question_processing.py` | 题目结构处理 | ~900 |
| `validation.py` | 验证检测 | ~400 |
| `image_handling.py` | 图片处理 | ~300 |

## 🔄 工作流程

```
┌─────────────────┐
│ Phase 0 (完成)  │ 方案设计 + 工具开发
└────────┬────────┘
         ↓
┌─────────────────┐
│ Phase 1 (下一步)│ 运行 extract_modules.py
└────────┬────────┘
         ↓
┌─────────────────┐
│ Phase 2         │ 重构 ocr_to_examx.py
└────────┬────────┘
         ↓
┌─────────────────┐
│ Phase 3         │ 创建转换器架构
└────────┬────────┘
         ↓
┌─────────────────┐
│ Phase 4         │ 实现讲义转换器
└────────┬────────┘
         ↓
┌─────────────────┐
│ Phase 5         │ 清理优化文档
└─────────────────┘
```

## 🛠️ 常用命令

```bash
# 提取模块
python3 tools/extract_modules.py

# 验证环境
./tools/verify_refactoring.sh

# 查看模块
head -50 tools/lib/math_processing.py

# 运行测试
python3 tools/testing/quick_test_changes.py

# 查看计划
cat tools/REFACTORING_PLAN.md | less

# 查看指南
cat tools/README_REFACTORING.md | less
```

## 📖 文档导航

| 需求 | 文档 |
|------|------|
| 我想了解整体方案 | `REFACTORING_PLAN.md` |
| 我想快速开始 | `README_REFACTORING.md` |
| 我想知道进度 | `REFACTORING_SUMMARY.md` |
| 我想验证环境 | 运行 `verify_refactoring.sh` |
| 我想提取代码 | 运行 `extract_modules.py` |

## ✅ 检查清单

### 提取前
- [x] 阅读重构计划
- [x] 验证环境就绪
- [x] 理解模块划分

### 提取后
- [ ] 检查7个文件已生成
- [ ] 验证代码完整性
- [ ] 更新 __init__.py
- [ ] 运行回归测试

### 重构后
- [ ] 删除重复代码
- [ ] 更新导入语句
- [ ] 测试通过
- [ ] 文档更新

## 🎓 关键概念

**BaseConverter**: 抽象基类，定义通用转换流程
**ExamConverter**: 试卷转换器，继承BaseConverter
**HandoutConverter**: 讲义转换器，继承BaseConverter (新功能)

**共享模块**: math_processing, text_cleaning, validation
**差异化**: 章节结构、环境使用、元数据提取

## 🚨 注意事项

1. **备份原文件**: 提取前建议备份 `ocr_to_examx.py`
2. **逐步验证**: 每个阶段完成后运行测试
3. **保持兼容**: 重构过程中不改变外部API
4. **文档同步**: 代码修改后及时更新文档

## 📞 获取帮助

**问题**: 提取脚本报错
**解决**: 检查源文件路径，查看日志输出

**问题**: 某些函数没有提取
**解决**: 检查 MODULE_FUNCTIONS 配置，手动添加

**问题**: 测试失败
**解决**: 对比新旧输出diff，定位问题

## 🎉 成功标准

- [ ] 7个模块文件生成成功
- [ ] 回归测试100%通过
- [ ] 新旧输出文件一致
- [ ] LaTeX编译成功
- [ ] 讲义转换器实现

---

**当前状态**: ✅ 准备就绪
**下一步**: 运行 `python3 tools/extract_modules.py`
**预计时间**: 5分钟（提取） + 2小时（验证重构）

🚀 **开始重构吧！**
