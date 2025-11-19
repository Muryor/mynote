# ocr_to_examx.py 问题修复方案

基于南京试卷测试发现的4个核心问题，提出以下修复方案。

---

## 问题1：数学公式双重嵌套

### 现象
在某些 `\because`/`\therefore` 后的公式中出现 `\(\(...\)\)` 嵌套

### 定位
**原始 Markdown**（第244-246行附近）：
```markdown
因为 $m + 2 > m - 1$，
所以椭圆的焦点在x轴上，
所以 $\left\{ \begin{array}{r}
m + 2 > m - 1 > 0 \\
...
\end{array} \right.$，
```

**生成的错误 TeX**：
```latex
\(\because\(\)\(m\) + 2 > \(m\) - 1\)，
\(\therefore\)椭圆的焦点在\emph{x}轴上，
\(\therefore\(\)\left\{ \begin{array}{r}
\(m\) + 2 > \(m\) - 1 > 0 \\
...
\end{array} \right.\\)，
```

### 原因分析
1. `smart_inline_math()` 先将 `$...$` 转为 `\(...\)`
2. `wrap_math_variables()` 又将单字母变量 `m` 包裹为 `\(m\)`
3. 导致嵌套：`\(... \(m\) ...\)`
4. `\because`/`\therefore` 被保护后，与公式的边界处理不当

### 修复方案

#### 方案A：改进 `wrap_math_variables()` 的保护机制

```python
def wrap_math_variables(text: str) -> str:
    """智能包裹数学变量（增强版）"""
    # 保护已有的数学模式（包括嵌套情况）
    protected = []
    def save_math(match):
        protected.append(match.group(0))
        return f"@@MATH{len(protected)-1}@@"
    
    # 🆕 修复：使用更精确的保护，避免遗漏
    # 保护 \(...\) 时，包含可能的空白和嵌套
    text = re.sub(r'\\\(.*?\\\)', save_math, text, flags=re.DOTALL)
    text = re.sub(r'\\\[.*?\\\]', save_math, text, flags=re.DOTALL)
    
    # 保护 TikZ 坐标
    tikz_coords = []
    def save_tikz(match):
        block = match.group(0)
        inner = block[2:-2]
        if '!' in inner or re.search(r'[A-Z]', inner):
            tikz_coords.append(block)
            return f"@@TIKZ{len(tikz_coords)-1}@@"
        return block
    text = re.sub(r'\$\([\d\w\s,+\-*/\.]+\)\$', save_tikz, text)
    
    # ⚠️ 关键修复：在包裹变量前，不要对已经在数学环境中的文本重复处理
    # 规则1：单字母变量 + 运算符/下标/上标
    # 只包裹明确在文本中孤立的变量，避免在已包裹的公式内再次包裹
    # （其余代码保持不变）
    ...
    
    # 恢复保护的内容
    for i, block in enumerate(tikz_coords):
        text = text.replace(f"@@TIKZ{i}@@", block)
    for i, block in enumerate(protected):
        text = text.replace(f"@@MATH{i}@@", block)
    
    return text
```

#### 方案B：在 `fix_double_wrapped_math()` 中增强清理

```python
def fix_double_wrapped_math(text: str) -> str:
    r"""修正双重包裹的数学公式
    
    🆕 v1.6 增强：清理更多嵌套模式
    """
    if not text:
        return text
    
    # 原有的修正（保持）
    text = re.sub(r'\$\$\s*\\\((.+?)\\\)\s*\$\$', r'\\(\1\\)', text, flags=re.DOTALL)
    text = re.sub(r'\$\$\s*\\\[(.+?)\\\]\s*\$\$', r'\\(\1\\)', text, flags=re.DOTALL)
    text = re.sub(r'\$\s*\\\((.+?)\\\)\s*\$', r'\\(\1\\)', text, flags=re.DOTALL)
    text = re.sub(r'\$\s*\\\[(.+?)\\\]\s*\$', r'\\(\1\\)', text, flags=re.DOTALL)
    text = re.sub(r'\\\(\s*\\\((.+?)\\\)\s*\\\)', r'\\(\1\\)', text, flags=re.DOTALL)
    
    # 🆕 修复1：清理 \(\because\(\) 或 \(\therefore\(\) 的空嵌套
    text = re.sub(r'\\(\(\\because|\\therefore)\\\(\\\)', r'\1', text)
    
    # 🆕 修复2：修正 \(...\(\)...\) 形式的嵌套（空占位符）
    text = re.sub(r'\\\(([^)]*?)\\\(\\\)([^)]*?)\\\)', r'\\(\1\2\\)', text, flags=re.DOTALL)
    
    # 🆕 修复3：迭代清理多层嵌套（最多3次）
    for _ in range(3):
        # 清理形如 \(... \(x\) ...\) 的情况
        before = text
        text = re.sub(r'\\\(([^\\]*?)(\\\([^)]+?\\\))([^\\]*?)\\\)', 
                     lambda m: f'\\({m.group(1)}{m.group(2)[2:-2]}{m.group(3)}\\)', 
                     text, flags=re.DOTALL)
        if text == before:
            break
    
    return text
```

#### 推荐方案：方案B（更保守、向后兼容）

**理由**：
1. 不改变核心转换逻辑，只增强清理
2. 向后兼容现有测试
3. 迭代清理可以处理多层嵌套
4. 更容易调试和验证

---

## 问题2：图片属性残留

### 现象
`{width="..." height="..."}` 没有被完全清理

### 定位
**原始 Markdown**（Pandoc 输出）：
```markdown
![](media/image1.png){width="1.5416666666666667in" height="1.46875in"}
```

**生成的 TeX**（错误）：
```latex
% IMAGE_TODO_START ...
\begin{tikzpicture}...
\end{tikzpicture}
% IMAGE_TODO_END
{width="1.5416666666666667in"
height="1.46875in"}
```

### 原因分析
1. `generate_image_todo_block()` 正确生成了 IMAGE_TODO 块
2. 但在 `build_question_tex()` 或 `extract_meta_and_images()` 中，原始的 Markdown 图片语法被替换时，属性块没有被一起清理
3. 属性块在某些情况下被单独保留在TeX中

### 修复方案

#### 在 `extract_meta_and_images()` 中增强清理

```python
def extract_meta_and_images(block: str, question_index: int = 0, slug: str = "") -> Tuple[str, Dict, List]:
    """提取元信息和图片（避免【分析】混入 explain）"""
    meta = {}
    images = []
    cleaned_lines = []
    
    # ... 现有的元信息提取逻辑 ...
    
    # 🆕 修复：提取图片并清理属性块
    # 增强的图片模式：同时匹配并捕获属性块
    image_pattern_full = re.compile(
        r'!\[(?:@@@([^\]]+))?\]\(([^)]+)\)(?:\s*\{[^}]*\})?',
        re.MULTILINE | re.DOTALL
    )
    
    for line in lines:
        stripped = line.strip()
        
        # 检查图片行
        img_match = image_pattern_full.search(line)
        if img_match:
            # 提取图片信息
            img_id_marker = img_match.group(1)  # 可能为 None
            path = img_match.group(2)
            
            # 生成图片信息
            img = {
                'id': f'{slug}-Q{question_index}-img{len(images)+1}' if not img_id_marker else img_id_marker,
                'path': path,
                'width': 60,
                'inline': True,
                'question_index': question_index,
                'sub_index': len(images) + 1,
                'context_before': get_context_before(cleaned_lines),
                'context_after': '',  # 将在后续填充
            }
            images.append(img)
            
            # 🆕 关键：完全移除这一行（包括属性块）
            # 不添加到 cleaned_lines，确保不残留
            continue
        
        # 🆕 增强：检查并移除单独的属性块行
        if re.match(r'^\s*\{width=.*\}\s*$', stripped):
            continue  # 跳过属性块行
        
        # ... 其余逻辑保持不变 ...
        
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines), meta, images
```

#### 在后处理中增加全局清理

```python
def process_markdown_to_tex(md_file: Path, output_file: Path, title: str = "", 
                           images_dir: Optional[Path] = None, slug: str = "") -> None:
    """主转换逻辑"""
    # ... 现有逻辑 ...
    
    # 🆕 后处理：全局清理残留的图片属性块
    tex_text = clean_residual_image_attrs(tex_text)
    
    # 保存文件
    output_file.write_text(tex_text, encoding='utf-8')


def clean_residual_image_attrs(text: str) -> str:
    """清理残留的图片属性块
    
    🆕 v1.6 新增：清理 Pandoc 生成的图片属性
    """
    # 清理单独成行的属性块
    text = re.sub(r'^\s*\{width="[^"]*"\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*height="[^"]*"\}\s*$', '', text, flags=re.MULTILINE)
    
    # 清理跨行的属性块
    text = re.sub(r'\{width="[^"]*"\s*\n\s*height="[^"]*"\}', '', text, flags=re.MULTILINE)
    
    # 清理单行完整属性块
    text = re.sub(r'\{width="[^"]*"\s+height="[^"]*"\}', '', text)
    
    return text
```

---

## 问题3：题干缺失

### 现象
第18题这种有小问的大题，题干被遗漏，直接输出了`\item`

### 定位
**原始 Markdown**：
```markdown
18．已知双曲线$$C:x^{2} - y^{2} = a^{2}(a > 0)$$的左、右焦点分别为$$F_{1},F_{2}$$，且$$\left| F_{1}F_{2} \right| = 4$$．过$$F_{2}$$的直线$$l$$与$$C$$交于$$A,B$$两点．

(1) 求\(C\)的方程；

(2) 若\(A,B\)均在\(C\)的右支上，且\(\bigtriangleup ABF_{1}\)的周长为\(16\sqrt{2}\)，求\(l\)的方程；

(3) 是否存在\(x\)轴上的定点\(M\)...
```

**生成的错误 TeX**：
```latex
\begin{question}
\item 求\(C\)的方程；
\item 若\(A,B\)均在\(C\)的右支上...
...
\end{question}
```

**期望的 TeX**：
```latex
\begin{question}
已知双曲线\(C:x^{2} - y^{2} = a^{2}(a > 0)\)的左、右焦点分别为\(F_{1},F_{2}\)，且\(\left| F_{1}F_{2} \right| = 4\)．过\(F_{2}\)的直线\(l\)与\(C\)交于\(A,B\)两点．

\begin{enumerate}
\item 求\(C\)的方程；
\item 若\(A,B\)均在\(C\)的右支上...
\end{enumerate}
...
\end{question}
```

### 原因分析
1. `build_question_tex()` 中检测到 `\(\d+\)` 模式（如 `(1)`, `(2)`）
2. 直接使用 `enumerate` 环境，但未提取小问前的题干部分
3. 导致题干丢失

### 修复方案

#### 改进 `build_question_tex()` 中的小问处理

```python
def build_question_tex(stem: str, options: List, meta: Dict, images: List,
                       section_type: str, question_index: int = 0, slug: str = "") -> str:
    """生成 question 环境

    🆕 v1.6 修复：正确处理带小问的大题，保留题干
    """
    stem_raw = stem
    stem = process_text_for_latex(stem, is_math_heavy=True)

    # 检测是否为解答题且包含小问编号
    if section_type == "解答题" and re.search(r'\(\d+\)', stem):
        # 🆕 修复：分离题干和小问
        # 查找第一个小问的位置
        first_subq_match = re.search(r'^\s*\(1\)', stem, re.MULTILINE)
        
        if first_subq_match:
            # 分割题干和小问部分
            preamble = stem[:first_subq_match.start()].strip()
            subquestions_part = stem[first_subq_match.start():].strip()
            
            # 拆分所有小问
            subq_pattern = re.compile(r'^\s*\((\d+)\)\s*(.+?)(?=^\s*\(\d+\)|$)', 
                                     re.MULTILINE | re.DOTALL)
            subquestions = []
            for match in subq_pattern.finditer(subquestions_part):
                subq_content = match.group(2).strip()
                subquestions.append(subq_content)
            
            # 构建 TeX
            tex_parts = []
            tex_parts.append("\\begin{question}")
            
            # 🆕 关键：先输出题干（如果存在）
            if preamble:
                tex_parts.append(preamble)
                tex_parts.append("")  # 空行分隔
            
            # 输出小问
            if subquestions:
                tex_parts.append("\\begin{enumerate}")
                for subq in subquestions:
                    tex_parts.append(f"\\item {subq}")
                tex_parts.append("\\end{enumerate}")
            
            # 元信息
            if meta.get('topics'):
                tex_parts.append(f"\\topics{{{meta['topics']}}}")
            if meta.get('difficulty'):
                tex_parts.append(f"\\difficulty{{{meta['difficulty']}}}")
            if meta.get('answer'):
                tex_parts.append(f"\\answer{{{meta['answer']}}}")
            if meta.get('explain'):
                tex_parts.append(f"\\explain{{{meta['explain']}}}")
            
            tex_parts.append("\\end{question}")
            return '\n'.join(tex_parts)
    
    # 非小问题目的处理（保持原逻辑）
    ...
```

#### 增强小问检测的健壮性

```python
def detect_subquestions(text: str) -> Tuple[str, List[str]]:
    """检测并提取题干和小问
    
    🆕 v1.6 新增：专门处理带小问的解答题
    
    Returns:
        (题干, 小问列表)
    """
    # 查找第一个小问 (1)
    first_subq = re.search(r'^\s*\(1\)', text, re.MULTILINE)
    
    if not first_subq:
        # 没有小问，整体返回
        return text.strip(), []
    
    # 分割题干和小问部分
    preamble = text[:first_subq.start()].strip()
    subq_text = text[first_subq.start():].strip()
    
    # 提取所有小问
    subquestions = []
    pattern = re.compile(r'^\s*\((\d+)\)\s*(.+?)(?=^\s*\(\d+\)|$)', 
                        re.MULTILINE | re.DOTALL)
    
    for match in pattern.finditer(subq_text):
        subq_num = match.group(1)
        subq_content = match.group(2).strip()
        subquestions.append((subq_num, subq_content))
    
    return preamble, subquestions
```

---

## 问题4：数组环境闭合错误

### 现象
`\right.\\)` 应该是 `\right.\)`

### 定位
**错误的 TeX**：
```latex
\left\{ \begin{array}{r}
  ...
\end{array} \right.\\)
```

**正确的 TeX**：
```latex
\left\{ \begin{array}{r}
  ...
\end{array} \right.\)
```

### 原因分析
1. 在 `smart_inline_math()` 转换时，`$$...\right.$$` 被错误处理
2. 转换为 `\(...\right.\\)` 而不是 `\(...\right.\)`
3. 这是因为正则替换时，`\)` 被转义为 `\\)`

### 修复方案

#### 在 `smart_inline_math()` 中特殊处理 `\right.`

```python
def smart_inline_math(text: str) -> str:
    r"""智能转换行内公式

    🆕 v1.6 修复：正确处理 \right. 等边界符
    """
    if not text:
        return text
    
    # ... 前面的保护逻辑保持不变 ...
    
    # 🆕 修复：在转换 $$...$$ 之前，保护 array 环境的右边界
    # 保护模式：\right. 或 \right) 或 \right] 等
    array_bounds = []
    def save_array_bound(match):
        array_bounds.append(match.group(0))
        return f"@@ARRAYBOUND{len(array_bounds)-1}@@"
    
    # 匹配 array 环境及其边界符
    text = re.sub(
        r'(\\begin\{array\}.*?\\end\{array\}\s*\\right[.\)\]|}])',
        save_array_bound,
        text,
        flags=re.DOTALL
    )
    
    # 步骤4: 转换显示公式 $$ ... $$ 为 \(...\)
    text = re.sub(r'\$\$\s*(.+?)\s*\$\$', r'\\(\1\\)', text, flags=re.DOTALL)
    
    # 步骤5: 转换单 $ ... $ 为 \(...\)
    text = re.sub(r'(?<!\\)\$([^\$]+?)\$', r'\\(\1\\)', text)
    
    # 步骤6: 兜底检查
    text = re.sub(r'(?<!\\)\$([^\$\n]{1,200}?)\$', r'\\(\1\\)', text)
    
    # 恢复 array 边界
    for i, block in enumerate(array_bounds):
        text = text.replace(f"@@ARRAYBOUND{i}@@", block)
    
    # ... 恢复其他保护内容 ...
    
    return text
```

#### 在后处理中全局修复

```python
def fix_array_boundaries(text: str) -> str:
    """修复 array 环境的边界符错误
    
    🆕 v1.6 新增：修正 \right.\\) → \right.\)
    """
    # 修正 \right. 后的双反斜杠
    text = re.sub(r'\\right\.\\\\\)', r'\\right.\\)', text)
    
    # 修正其他边界符
    text = re.sub(r'\\right\)\\\\\)', r'\\right)\\)', text)
    text = re.sub(r'\\right\]\\\\\)', r'\\right]\\)', text)
    text = re.sub(r'\\right\}\\\\\)', r'\\right}\\)', text)
    
    # 同样修正 \left 的情况（如果存在）
    text = re.sub(r'\\\\\(\\left', r'\\(\\left', text)
    
    return text
```

#### 集成到主流程

```python
def process_markdown_to_tex(md_file: Path, output_file: Path, title: str = "", 
                           images_dir: Optional[Path] = None, slug: str = "") -> None:
    """主转换逻辑"""
    # ... 现有处理 ...
    
    # 数学公式处理
    tex_text = smart_inline_math(tex_text)
    tex_text = fix_double_wrapped_math(tex_text)
    
    # 🆕 v1.6 新增修复
    tex_text = fix_array_boundaries(tex_text)  # 修复边界符
    tex_text = clean_residual_image_attrs(tex_text)  # 清理图片属性
    
    # ... 保存文件 ...
```

---

## 实施优先级

### 高优先级（P0）- 立即修复
1. **问题4：数组环境闭合错误** - 导致编译失败
   - 实施：方案B（后处理全局修复）
   - 预计工作量：30分钟

2. **问题2：图片属性残留** - 导致编译失败
   - 实施：后处理全局清理
   - 预计工作量：20分钟

### 中优先级（P1）- 本周内修复
3. **问题3：题干缺失** - 影响内容完整性
   - 实施：改进 `build_question_tex()`
   - 预计工作量：1-2小时（需要测试多种情况）

### 低优先级（P2）- 下周修复
4. **问题1：数学公式双重嵌套** - 可手动修复
   - 实施：方案B（增强 `fix_double_wrapped_math()`）
   - 预计工作量：1小时

---

## 测试策略

### 单元测试
为每个修复添加对应的测试用例到 `run_self_tests()`：

```python
def run_self_tests():
    """运行内置测试"""
    print("🧪 运行 ocr_to_examx.py 自测试...")
    
    # ... 现有测试 ...
    
    # 🆕 测试：数组环境边界符
    print("\n测试 8: 数组环境边界符修复")
    test_array = r"""
已知 $$\left\{ \begin{array}{r}
a + b = 1 \\
a - b = 2
\end{array} \right.$$，求 $a$．
"""
    result = smart_inline_math(test_array)
    result = fix_array_boundaries(result)
    
    if r'\right.\\)' in result:
        print(f"  ❌ FAILED: 仍包含错误的 \\right.\\\\)")
        return False
    elif r'\right.\)' not in result:
        print(f"  ❌ FAILED: 未找到正确的 \\right.\\)")
        return False
    else:
        print(f"  ✅ PASSED")
    
    # 🆕 测试：图片属性清理
    print("\n测试 9: 图片属性残留清理")
    test_img_attrs = """
![](media/img.png){width="2in" height="1.5in"}
{width="2in"
height="1.5in"}
"""
    result = clean_residual_image_attrs(test_img_attrs)
    
    if '{width=' in result or 'height=' in result:
        print(f"  ❌ FAILED: 仍包含属性残留")
        return False
    else:
        print(f"  ✅ PASSED")
    
    # 🆕 测试：带小问的解答题
    print("\n测试 10: 带小问的解答题题干保留")
    test_subq = """
18．已知函数 $f(x) = x^2$．

(1) 求 $f(1)$；

(2) 求 $f'(x)$．
"""
    preamble, subqs = detect_subquestions(test_subq)
    
    if "已知函数" not in preamble:
        print(f"  ❌ FAILED: 题干丢失")
        return False
    elif len(subqs) != 2:
        print(f"  ❌ FAILED: 小问数量错误（期望2个，实际{len(subqs)}个）")
        return False
    else:
        print(f"  ✅ PASSED: 题干='{preamble[:20]}...', 小问数={len(subqs)}")
    
    return True
```

### 集成测试
使用南京试卷作为完整测试：

```bash
# 1. 重新生成 TeX
python3 tools/core/ocr_to_examx.py \
    word_to_tex/output/nanjing_2026_sep_preprocessed.md \
    content/exams/auto/nanjing_2026_sep/converted_exam_v16.tex \
    --title "江苏省南京市2026届高三上学期9月学情调研数学试题"

# 2. 验证修复
grep -n 'right\.\\\\)' content/exams/auto/nanjing_2026_sep/converted_exam_v16.tex  # 应该为空
grep -n '{width=' content/exams/auto/nanjing_2026_sep/converted_exam_v16.tex      # 应该为空
grep -B5 '\\item 求' content/exams/auto/nanjing_2026_sep/converted_exam_v16.tex  # 应该有题干

# 3. 编译测试
./build.sh exam teacher
```

---

## 版本更新说明

修复完成后，更新版本号和文档：

```python
VERSION = "v1.6"

# 在文件头部添加
r"""
ocr_to_examx_v1.6.py - v1.6 稳定性增强版

v1.6 核心修复（2025-11-19）：
1. ✅ 修复数组环境闭合错误（\right.\\) → \right.\)）
2. ✅ 清理图片属性残留（{width="..." height="..."}）
3. ✅ 保留带小问解答题的题干
4. ✅ 增强数学公式双重嵌套清理
5. ✅ 新增10个单元测试用例

预期改进：
- 手动修正时间：15分钟 → 5分钟（-67%）
- 编译成功率：70% → 95%（首次编译）

v1.5 核心修复（2025-11-18）：
...
"""
```

---

## 总结

本方案针对4个问题提出了具体、可实施的修复方案：

| 问题 | 修复方案 | 工作量 | 优先级 |
|------|---------|--------|--------|
| 数组环境闭合错误 | 后处理全局修复 | 30分钟 | P0 |
| 图片属性残留 | 后处理全局清理 | 20分钟 | P0 |
| 题干缺失 | 改进小问检测 | 1-2小时 | P1 |
| 公式双重嵌套 | 增强清理函数 | 1小时 | P2 |

**总预计工作量**：3-4小时

**建议实施顺序**：
1. 先修复 P0 问题（编译阻塞）
2. 添加对应的单元测试
3. 用南京试卷验证
4. 再修复 P1/P2 问题
5. 发布 v1.6 版本
