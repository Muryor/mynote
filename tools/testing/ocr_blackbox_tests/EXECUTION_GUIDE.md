# OCR 黑箱测试执行指南

本文档详细说明如何执行黑箱测试并分析结果。

## 测试环境确认

### 前置条件

1. **Python 3.x** 已安装
2. **测试数据** 已准备（`word_to_tex/output/*_preprocessed.md`）
3. **被测脚本** 存在（`tools/core/ocr_to_examx.py`）

### 验证环境

```bash
# 检查 Python 版本
python3 --version

# 检查测试数据
ls -1 word_to_tex/output/*_preprocessed.md | wc -l

# 检查被测脚本
ls -lh tools/core/ocr_to_examx.py
```

## 执行步骤

### 步骤 1: 单文件测试（验证框架）

```bash
# 测试单个试卷，验证测试框架工作正常
python3 tools/testing/ocr_blackbox_tests/run_tests.py \
    word_to_tex/output/gaokao_2025_national_1_preprocessed.md
```

**预期输出**：
```
============================================================
📋 OCR 黑箱测试报告
   文件: word_to_tex/output/gaokao_2025_national_1_preprocessed.md
   时间: 2025-11-28T00:01:13.675204
============================================================

✅ [T001] 【答案】提取
   找到 19 个 \answer，Markdown 中有 19 个【答案】
   └─ 提取率: 100.0%

✅ [T002] 【难度】提取
   找到 19 个 \difficulty，Markdown 中有 19 个【难度】

✅ [T003] 【知识点】/【考点】合并
   找到 19 个 \topics，Markdown 中有 19 个知识点/考点

✅ [T004] 【分析】过滤
   【分析】已正确过滤

✅ [T005] 【详解】保留
   找到 19 个 \explain，Markdown 中有 19 个【详解】

❌ [T008] 定界符平衡
   \( = 690, \) = 687, diff = 3
   └─ 不平衡，差值 3

✅ [T009] 反向定界符
   发现 0 处反向定界符

✅ [T010] 双重包裹
   发现 0 处双重包裹

✅ [T011] question 环境闭合
   \begin{question} = 19, \end{question} = 19

✅ [T012] choices 环境
   检查 11 个 choices 块

✅ [T013] 题干存在性
   发现 0 道题目缺少题干

✅ [T014] IMAGE_TODO 格式
   找到 16 个图片占位符

✅ [T015] 图片属性清理
   发现 0 处残留属性

❌ [T016] LaTeX 转义
   发现 11 处未转义字符
   └─ Line 102: 未转义的 '&'
   └─ Line 104: 未转义的 '&'
   └─ Line 105: 未转义的 '&'

❌ [T017] 数学模式内中文标点
   发现 18 处中文标点
   └─ 数学模式内发现 '，': ，...
   └─ 数学模式内发现 '，': ，...
   └─ 数学模式内发现 '，': 中，...

✅ [T018] array/cases 左括号
   找到 8 个 array/cases，20 个 \left\{
   └─ 需要手工检查具体上下文

✅ [T019] tabular 列格式
   发现 0 个缺少列格式的 tabular

✅ [T020] explain 空行
   发现 0 处空行问题

------------------------------------------------------------
📊 汇总: 通过 15/18, 失败 3
============================================================

📁 报告已保存: tools/testing/ocr_blackbox_tests/reports/gaokao_2025_national_1_preprocessed_test_report.json
```

### 步骤 2: 批量测试所有文件

```bash
# 批量测试所有预处理文件
for f in word_to_tex/output/*_preprocessed.md; do
    echo "========== 测试: $(basename "$f") =========="
    python3 tools/testing/ocr_blackbox_tests/run_tests.py "$f"
    echo ""
done
```

**输出说明**：
- 每个文件单独测试
- 生成独立的 JSON 报告
- 终端显示测试摘要

### 步骤 3: 生成汇总报告

```bash
# 分析所有测试报告，生成汇总
python3 tools/testing/ocr_blackbox_tests/analyze_results.py
```

**生成的文件**：
1. `tools/testing/ocr_blackbox_tests/SUMMARY.md` - 测试总结
2. `tools/testing/ocr_blackbox_tests/ISSUES.md` - 问题清单

## 报告解读

### 1. JSON 测试报告

位置: `tools/testing/ocr_blackbox_tests/reports/*.json`

**结构**：
```json
{
  "exam_file": "文件路径",
  "timestamp": "执行时间",
  "summary": {
    "total": 18,      // 总测试数
    "passed": 15,     // 通过数
    "failed": 3       // 失败数
  },
  "results": [
    {
      "test_id": "T001",
      "name": "【答案】提取",
      "passed": true,
      "message": "找到 19 个 \\answer...",
      "details": "提取率: 100.0%"
    }
  ]
}
```

### 2. SUMMARY.md 总结报告

**关键指标**：
- 整体通过率: 85.2% (138/162)
- P0 问题: 定界符不平衡（9/9 试卷）
- P2 问题: 数学模式内中文标点（9/9 试卷）

**测试用例通过率**：
| 测试ID | 通过 | 失败 | 通过率 |
|--------|------|------|--------|
| T008   | 0    | 9    | 0.0%   |
| T017   | 0    | 9    | 0.0%   |
| T016   | 3    | 6    | 33.3%  |

### 3. ISSUES.md 问题清单

按严重程度分级：

#### P0 级别（导致编译失败）

**问题 1: 数学定界符不平衡**
- 影响: 9/9 试卷
- 现象: `\(` 和 `\)` 数量不匹配
- 原因: 数学公式转换逻辑缺陷
- 修复建议: 增强定界符平衡检查

#### P2 级别（格式问题）

**问题 2: 数学模式内中文标点**
- 影响: 9/9 试卷
- 现象: 全角标点未转换为半角
- 修复建议: 自动转换 `，` → `,`、`。` → `.`

**问题 3: LaTeX 特殊字符未转义**
- 影响: 6/9 试卷
- 现象: `&`, `%`, `#` 未转义
- 修复建议: 在表格环境中自动转义

## 问题定位

### 定位 P0 问题：定界符不平衡

1. **查看报告详情**：
```bash
cat tools/testing/ocr_blackbox_tests/reports/gaokao_2025_national_1_preprocessed_test_report.json | \
    jq '.results[] | select(.test_id == "T008")'
```

输出：
```json
{
  "test_id": "T008",
  "name": "定界符平衡",
  "passed": false,
  "message": "\\( = 690, \\) = 687, diff = 3",
  "details": "不平衡，差值 3"
}
```

2. **检查生成的 TeX 文件**：
```bash
# 统计定界符
grep -o '\\(' tools/testing/ocr_blackbox_tests/output/gaokao_2025_national_1_converted.tex | wc -l
grep -o '\\)' tools/testing/ocr_blackbox_tests/output/gaokao_2025_national_1_converted.tex | wc -l
```

3. **查找不匹配位置**：
```bash
# 使用 validate_tex.py 定位问题
python3 tools/validate_tex.py \
    tools/testing/ocr_blackbox_tests/output/gaokao_2025_national_1_converted.tex
```

### 定位 P2 问题：中文标点

1. **提取数学模式内容**：
```bash
# 查找数学模式内的中文标点
grep -oP '\\\\\(.*?，.*?\\\\\)' \
    tools/testing/ocr_blackbox_tests/output/gaokao_2025_national_1_converted.tex | head -5
```

2. **对比原始 Markdown**：
```bash
# 查看原始文件中的对应位置
grep -n '，' word_to_tex/output/gaokao_2025_national_1_preprocessed.md | head -10
```

## 验证修复

假设修复了 `ocr_to_examx.py` 中的问题：

```bash
# 1. 重新运行测试
python3 tools/testing/ocr_blackbox_tests/run_tests.py \
    word_to_tex/output/gaokao_2025_national_1_preprocessed.md

# 2. 对比修复前后的报告
diff -u \
    tools/testing/ocr_blackbox_tests/reports/gaokao_2025_national_1_preprocessed_test_report.json \
    tools/testing/ocr_blackbox_tests/reports/gaokao_2025_national_1_preprocessed_test_report.json.backup

# 3. 验证特定测试用例
# 如果 T008 通过，说明定界符问题已解决
```

## 持续测试

### 回归测试

每次修改 `ocr_to_examx.py` 后：

```bash
# 运行完整测试套件
bash tools/testing/ocr_blackbox_tests/run_all_tests.sh

# 或使用 Makefile
make test-ocr
```

### 添加新测试数据

当有新的试卷文件：

```bash
# 1. 将新文件放入测试目录
cp new_exam_preprocessed.md word_to_tex/output/

# 2. 运行测试
python3 tools/testing/ocr_blackbox_tests/run_tests.py \
    word_to_tex/output/new_exam_preprocessed.md

# 3. 更新汇总报告
python3 tools/testing/ocr_blackbox_tests/analyze_results.py
```

## 常见测试场景

### 场景 1: 快速检查是否有 P0 问题

```bash
# 只测试关键的 P0 测试用例
python3 tools/testing/ocr_blackbox_tests/run_tests.py \
    word_to_tex/output/gaokao_2025_national_1_preprocessed.md | \
    grep -A 2 "T008\|T011"
```

### 场景 2: 对比两个版本的脚本

```bash
# 备份当前脚本
cp tools/core/ocr_to_examx.py tools/core/ocr_to_examx.py.v1

# 修改脚本后测试
python3 tools/testing/ocr_blackbox_tests/run_tests.py \
    word_to_tex/output/gaokao_2025_national_1_preprocessed.md

# 恢复旧版本
cp tools/core/ocr_to_examx.py.v1 tools/core/ocr_to_examx.py

# 再次测试并对比
```

### 场景 3: 生成测试覆盖率报告

```bash
# 统计每种问题的覆盖情况
python3 tools/testing/ocr_blackbox_tests/analyze_results.py
cat tools/testing/ocr_blackbox_tests/SUMMARY.md | grep "主要问题类型"
```

## 故障排除

### 测试脚本无法运行

```bash
# 检查 Python 依赖
python3 -c "import subprocess, re, json, pathlib"

# 检查文件权限
chmod +x tools/testing/ocr_blackbox_tests/run_tests.py
```

### 转换超时

```bash
# 增加超时时间（修改 run_tests.py）
# timeout=60 → timeout=120
```

### 报告无法生成

```bash
# 检查报告目录
ls -la tools/testing/ocr_blackbox_tests/reports/

# 手动创建目录
mkdir -p tools/testing/ocr_blackbox_tests/reports
```

## 测试数据说明

当前测试覆盖的 9 份试卷：

1. `gaokao_2025_national_1_preprocessed.md` - 2025 全国卷 I
2. `hangzhou_2025_2026_quality_preprocessed.md` - 杭州质检
3. `hunan-changsha-yali-2026-mock3_preprocessed.md` - 长沙雅礼模拟
4. `jiangsu-changzhou-2025-2026-midterm_preprocessed.md` - 常州期中
5. `js-suxichang-2025-q2_preprocessed.md` - 苏锡常二模
6. `nanjing_2026_sep_preprocessed.md` - 南京九月考试
7. `nanjing_yancheng_2025_mock1_preprocessed.md` - 南京盐城一模
8. `suzhou-2025-2026-yangguang_preprocessed.md` - 苏州阳光模拟
9. `zhejiang_lishui_2026_nov_preprocessed.md` - 丽水十一月考试

**覆盖特点**：
- 地域：江苏、浙江、湖南等多地
- 题型：全国卷、模拟考、期中考
- 难度：0.3-0.8 不等
- 题量：19-22 题

## 后续改进

1. **增加边界测试**：极端格式、空题目、超长公式
2. **性能测试**：转换耗时、内存占用
3. **集成测试**：端到端流程（Docx → Markdown → TeX → PDF）
4. **自动化 CI**：GitHub Actions 自动运行测试

## 参考文档

- `test_cases.md` - 完整测试用例定义
- `README.md` - 测试框架使用指南
- `SUMMARY.md` - 最新测试总结
- `ISSUES.md` - 详细问题清单
