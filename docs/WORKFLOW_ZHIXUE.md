# 智学网试卷格式工作流 (v1.3)

> v1.3 (2025-12-04) | 适用：智学网、菁优网（深圳中学试卷等）

## 快速导航

| 文档 | 用途 |
|------|------|
| [workflow.md](workflow.md) | 标准格式工作流 |
| [REFERENCE.md](REFERENCE.md) | 格式规范 |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | 错误诊断 |

---

## 一、格式特点

| 特征 | 智学网格式 | 标准格式 |
|------|------------|----------|
| 答案 | `【答案】*B*`（带斜体） | `【答案】B` |
| 解析 | `【解析】【分析】` + `【解答】` | `【详解】` |
| 难度/知识点 | ❌ 无 | ✅ 有 |

---

## 二、标准工作流

### 2.1 一键转换

```bash
# 1. Word → TeX（智学网格式专用）
word_to_tex/scripts/preprocess_zx_docx.sh \
    "word_to_tex/input/试卷.docx" "exam_2025" "2025年试卷"

# 2. 处理图片
python3 tools/images/process_images_to_tikz.py --mode include \
    --files content/exams/auto/exam_2025/converted_exam.tex
python3 tools/images/convert_to_examimage.py \
    content/exams/auto/exam_2025/converted_exam.tex

# 3. 修改 settings/metadata.tex 并编译
# \newcommand{\examSourceFile}{content/exams/auto/exam_2025/converted_exam.tex}
./build.sh exam both
```

### 2.2 编译命令

```bash
./build.sh exam teacher/student/both      # 标准编译
VALIDATE_BEFORE_BUILD=1 ./build.sh exam teacher  # 带预检查

# 自动重命名（可选）
EXAM_TEX='content/exams/auto/exam_2025/converted_exam.tex' ./build.sh exam both
```

---

## 三、质量保证

```bash
python3 tools/scripts/validate_tex.py <tex_file>   # 结构验证
tools/locate_error.sh output/.aux/wrap-exam-teacher.log  # 错误定位
cat output/last_error.log                  # 查看错误
```

### 常见问题

| 问题 | 表现 | 修复 |
|------|------|------|
| 重复答案 | `\)...\(...\).}` | 删除重复部分 |
| 根号格式 | `\sqrt[\ ]{...}` | 正常，不影响编译 |

---

## 四、脚本说明

| 脚本 | 位置 | 功能 |
|------|------|------|
| `preprocess_zx_docx.sh` | `word_to_tex/scripts/` | 一键转换：pandoc → 预处理 → ocr_to_examx → agent_refine |
| `preprocess_shenzhen_format.py` | `tools/utils/` | 移除答案斜体、转换解析结构 |

---

## 五、版本历史

| 版本 | 日期 | 更新 |
|------|------|------|
| v1.3 | 2025-12-04 | 精简文档，添加编译命令 |
| v1.2 | 2025-12-04 | 完整测试通过 |
