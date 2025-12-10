# Scripts 目录

本目录包含各种实用脚本工具。

## 📝 脚本列表

### 转换与验证

- **run_pipeline.py** - 快速转换与校验工具
  ```bash
  python3 tools/scripts/run_pipeline.py input.md --slug exam-2025
  ```

- **validate_tex.py** - TeX 预编译校验工具
  ```bash
  python3 tools/scripts/validate_tex.py output.tex
  ```

- **test_compile.sh** - 回归测试脚本
  ```bash
  ./tools/scripts/test_compile.sh
  ```

### 修复工具

- **apply_fixes.py** - 批量应用修复
- **fix_fill_blanks.py** - 修复填空题格式
- **fix_ocr_math.py** - 修复 OCR 数学公式错误
- **fix_q11.py** - 修复特定题目问题

## 🔧 使用说明

所有脚本都应该从项目根目录运行：

```bash
# 正确
cd /path/to/mynote
python3 tools/scripts/run_pipeline.py ...

# 错误（不要在 scripts/ 目录内运行）
cd tools/scripts
python3 run_pipeline.py ...  # ❌ 路径可能出错
```

## 📚 相关文档

- [tools/README.md](../README.md) - 工具总览
- [docs/workflow.md](../../docs/workflow.md) - 完整工作流
