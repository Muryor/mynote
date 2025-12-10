# Testing 目录

本目录包含所有测试相关的脚本和测试套件。

## 📝 测试分类

### 单元测试

- **quick_test_changes.py** - 快速功能测试（中文标点、TikZ保护、故选删除）
  ```bash
  python3 tools/testing/quick_test_changes.py
  ```

- **test_ocr_fixes.py** / **test_ocr_fixes_new.py** - OCR 修复功能测试
  ```bash
  python3 tools/testing/test_ocr_fixes.py
  ```

### 集成测试

- **run_batch_tests.py** - 批量转换和编译测试
  ```bash
  python3 tools/testing/run_batch_tests.py
  ```

- **ocr_blackbox_tests/** - 黑盒测试套件
  ```bash
  cd tools/testing/ocr_blackbox_tests
  ./run_all_tests.sh
  ```

### 专项测试

- **test_array_left_braces.py** - 数组左括号测试
- **test_insert_allowbreaks.py** - 数学公式断行测试
- **test_reversed_delimiters.py** - 反转定界符测试
- **test_split_sections.py** - 分节测试
- **test_table_borders.py** - 表格边框测试
- **math_sm_comparison.py** - 数学状态机对比测试

## 🔧 运行测试

### 快速测试（推荐）

```bash
# 从项目根目录运行
python3 tools/testing/quick_test_changes.py
```

### VS Code 任务

使用 `Cmd+Shift+P` → "Run Task" → "Run Quick Test"

## 📊 测试覆盖

- ✅ 数学公式处理
- ✅ 文本清理
- ✅ 元数据提取
- ✅ 题目结构处理
- ✅ 图片处理
- ✅ 验证功能

## 📚 相关文档

- [tools/docs/refactoring/test_refactoring.py](../docs/refactoring/test_refactoring.py) - 重构测试套件
- [ocr_blackbox_tests/README.md](ocr_blackbox_tests/README.md) - 黑盒测试文档
