# OCR 脚本重构方案

## 目标
将 `tools/core/ocr_to_examx.py` (7000+ 行) 重构为模块化结构，以支持：
- **试卷 (Exam)**: 使用 `question`、`choices` 环境，分节（单选题/多选题/填空题/解答题）
- **讲义 (Handout)**: 使用 `definitionx`、`propertyx`、`examplex`、`notebox` 环境，章节结构

## 模块化设计

### 1. 核心库模块 (`tools/lib/`)

#### 1.1 `math_processing.py` - 数学公式处理
**功能**: 数学定界符解析、修复、转换

**包含**:
- `CHINESE_MATH_SEPARATORS` - 中文数学分隔词常量
- `TokenType` - 定界符token类型枚举
- `MathStateMachine` - 数学模式状态机类 (核心，~900行)
  - `preprocess_multiline_math()` - 预处理多行数学块
  - `tokenize()` - 分词器
  - `fix_malformed_patterns()` - 修复畸形模式
  - `normalize_punctuation_in_math()` - 标准化标点
  - `split_colon_from_math()` - 分离冒号
  - `fix_math_symbol_chinese_boundary()` - 修复数学符号边界
  - `split_chinese_from_math()` - 分离中文
  - `balance_delimiters()` - 平衡定界符
  - `final_cleanup()` - 最终清理
  - `fix_reversed_delimiters()` - 修复反向定界符
  - `process()` - 主处理入口
- `math_sm` - 单例实例
- 数学修复函数:
  - `fix_array_boundaries()` - 修复array边界
  - `fix_broken_set_definitions()` - 修复集合定义
  - `fix_ocr_specific_errors()` - 修复OCR错误
  - `fix_right_boundary_errors()` - 修复\\right.边界
  - `fix_unmatched_close_delimiters()` - 修复未匹配闭合符
  - `balance_array_and_cases_env()` - 平衡array/cases环境
  - `fix_trig_function_spacing()` - 修复三角函数空格
  - `fix_greek_letter_spacing()` - 修复希腊字母空格
  - `fix_bold_math_symbols()` - 修复粗体数学符号
  - `fix_overset_arrow_vectors()` - 修复向量箭头
  - `fix_specific_reversed_pairs()` - 修复特定反向配对
  - `fix_simple_reversed_inline_pairs()` - 修复简单反向行内配对
  - `collect_reversed_math_samples()` - 收集反向样本

**代码位置**: `ocr_to_examx.py` 第 194-1200 行, 1560-1700 行, 2700-3900 行

#### 1.2 `text_cleaning.py` - 文本清理与转义
**功能**: LaTeX特殊字符转义、文本规范化

**包含**:
- `LATEX_SPECIAL_CHARS` - 特殊字符映射常量
- `escape_latex_special()` - 转义LaTeX特殊字符 (行1304)
- `standardize_math_symbols()` - 标准化数学符号 (行1376)
- `clean_markdown()` - 清理Markdown残留 (行4141)
- `clean_image_attributes()` - 清理图片属性 (行1600)
- `remove_decorative_images()` - 移除装饰性图片 (行1650)
- `clean_residual_image_attrs()` - 清理残留属性 (行1700)
- `fix_markdown_bold_residue()` - 修复粗体残留 (行3500)
- `remove_blank_lines_in_macro_args()` - 移除宏参数空行
- `soft_wrap_paragraph()` - 软换行 (行2150)

**代码位置**: `ocr_to_examx.py` 第 1300-1750 行, 2150-2250 行, 3500-3550 行

#### 1.3 `meta_extraction.py` - 元数据提取
**功能**: 提取答案、解析、知识点等元数据

**包含**:
- `META_PATTERNS` - 元数据正则模式常量
- `extract_meta_and_images()` - 主提取函数 (行4350)
- `_extract_answer()` - 提取答案
- `_extract_analysis()` - 提取分析
- `_extract_difficulty()` - 提取难度
- `_extract_topics()` - 提取知识点

**代码位置**: `ocr_to_examx.py` 第 4350-4600 行

#### 1.4 `latex_utils.py` - LaTeX工具函数
**功能**: LaTeX环境处理、格式化

**包含**:
- `fix_tabular_environments()` - 修复tabular环境
- `add_table_borders()` - 添加表格边框
- `fix_fill_in_blanks()` - 修复填空题 (行1750)
- `remove_par_breaks_in_explain()` - 移除explain空段 (行2250)
- `clean_question_environments()` - 清理question环境

**代码位置**: `ocr_to_examx.py` 第 1750-2050 行, 2250-2350 行

#### 1.5 `question_processing.py` - 题目结构处理
**功能**: 题目合并、小问格式化、结构修复

**包含**:
- `fix_merged_questions_structure()` - 修复合并题目 (行2600)
- `fix_circled_subquestions_to_nested_enumerate()` - 嵌套enumerate (行2800)
- `fix_nested_subquestions()` - 嵌套子题 (行3100)
- `fix_spurious_items_in_enumerate()` - 修复多余item (行3150)
- `fix_missing_items_in_enumerate()` - 修复缺失item
- `_is_likely_stem()` - 判断题干 (行2500)
- `fix_keep_questions_together()` - 保持题目完整性

**代码位置**: `ocr_to_examx.py` 第 2500-3350 行

#### 1.6 `validation.py` - 验证与检测
**功能**: LaTeX语法验证、错误检测

**包含**:
- `validate_math_integrity()` - 验证数学定界符 (行5415)
- `validate_brace_balance()` - 验证括号平衡 (行5384)
- `validate_latex_output()` - 验证LaTeX输出 (行6374)
- `validate_and_fix_image_todo_blocks()` - 验证图片TODO块 (行3400)

**代码位置**: `ocr_to_examx.py` 第 3400-3500 行, 5384-5650 行, 6374-6450 行

#### 1.7 `image_handling.py` - 图片处理
**功能**: 图片路径处理、占位符生成

**包含**:
- `IMAGE_PATTERN_*` - 图片模式常量
- `find_markdown_and_images()` - 查找图片 (行1263)
- `copy_images_to_output()` - 复制图片 (行1289)
- `generate_image_todo_block()` - 生成TODO块 (行5621)
- `infer_figures_dir()` - 推断图片目录

**代码位置**: `ocr_to_examx.py` 第 1200-1300 行, 5621-5700 行

### 2. 转换器架构 (`tools/converters/`)

#### 2.1 `base_converter.py` - 基础转换器
**功能**: 抽象基类，定义通用转换流程

**设计**:
```python
class BaseConverter(ABC):
    def __init__(self, input_md: Path, output_dir: Path):
        self.input_md = input_md
        self.output_dir = output_dir
        self.math_sm = math_sm  # 使用共享数学状态机
        
    @abstractmethod
    def parse_sections(self, markdown: str) -> List[Section]:
        """解析章节/分节结构（子类实现）"""
        pass
    
    @abstractmethod
    def format_content_block(self, block: ContentBlock) -> str:
        """格式化内容块（子类实现）"""
        pass
    
    def convert(self) -> Path:
        """主转换流程（模板方法）"""
        # 1. 读取Markdown
        # 2. 预处理（数学状态机）
        # 3. 解析sections
        # 4. 格式化blocks
        # 5. 验证输出
        # 6. 写入文件
        pass
```

#### 2.2 `exam_converter.py` - 试卷转换器
**功能**: 继承BaseConverter，实现试卷专用逻辑

**特性**:
- 解析分节: 单选题、多选题、填空题、解答题
- 使用环境: `question`, `choices`, `choicex`
- 题号处理: 自动编号、题目合并
- 特殊处理: 填空题横线、选择题选项

#### 2.3 `handout_converter.py` - 讲义转换器 (新增)
**功能**: 继承BaseConverter，实现讲义专用逻辑

**特性**:
- 解析章节: chapter级别结构
- 使用环境: `definitionx`, `propertyx`, `examplex`, `notebox`
- 内容块识别: 定义、性质、例题、注解
- 特殊处理: 例题小问编号、证明步骤

### 3. 重构步骤

#### Phase 1: 提取工具库 (Week 1)
1. ✅ 创建 `tools/lib/__init__.py` (已完成)
2. [ ] 创建 `math_processing.py` - 复制MathStateMachine及相关函数
3. [ ] 创建 `text_cleaning.py` - 复制文本处理函数
4. [ ] 创建 `meta_extraction.py` - 复制元数据提取函数  
5. [ ] 创建 `latex_utils.py` - 复制LaTeX工具函数
6. [ ] 创建 `question_processing.py` - 复制题目处理函数
7. [ ] 创建 `validation.py` - 复制验证函数
8. [ ] 创建 `image_handling.py` - 复制图片处理函数
9. [ ] 更新 `__init__.py` 导出列表

#### Phase 2: 创建转换器架构 (Week 2)
1. [ ] 创建 `tools/converters/__init__.py`
2. [ ] 实现 `base_converter.py` - 定义抽象基类
3. [ ] 重构 `exam_converter.py` - 将现有代码迁移
4. [ ] 更新 `ocr_to_examx.py` 使用新的ExamConverter
5. [ ] 运行回归测试，确保功能不变

#### Phase 3: 实现讲义转换器 (Week 3)
1. [ ] 实现 `handout_converter.py` - 继承BaseConverter
2. [ ] 创建 `ocr_to_handoutx.py` - 讲义转换脚本入口
3. [ ] 添加单元测试
4. [ ] 文档化API

#### Phase 4: 清理与优化 (Week 4)
1. [ ] 删除 `ocr_to_examx.py` 中的冗余代码
2. [ ] 优化共享函数
3. [ ] 添加类型注解
4. [ ] 更新 README 和文档
5. [ ] 性能测试与优化

## 代码复用策略

### 共享组件
- **数学处理**: 试卷和讲义都需要数学公式解析
- **文本清理**: 通用的Markdown残留清理
- **图片处理**: 图片占位符生成逻辑相同
- **LaTeX转义**: 特殊字符转义逻辑通用

### 差异化组件
- **章节解析**: 试卷按题型分节，讲义按chapter分章
- **环境使用**: 试卷用question/choices，讲义用definitionx/examplex
- **元数据提取**: 试卷需要答案/解析，讲义需要例题编号/注解
- **格式化逻辑**: 试卷强调题号，讲义强调逻辑结构

## 测试策略

### 单元测试
- `tools/testing/test_math_processing.py` - 测试数学状态机
- `tools/testing/test_text_cleaning.py` - 测试文本清理
- `tools/testing/test_converters.py` - 测试转换器

### 集成测试
- 使用现有测试用例 (`tools/testing/content/`)
- 对比重构前后输出一致性
- 黑盒测试 (`tools/testing/ocr_blackbox_tests/`)

### 回归测试
- 保留现有 `ocr_to_examx.py` 作为参考
- 对比新旧输出diff
- 确保编译成功且PDF一致

## 目录结构 (重构后)

```
tools/
├── lib/                          # 共享工具库
│   ├── __init__.py              # ✅ 已创建
│   ├── math_processing.py       # 数学处理
│   ├── text_cleaning.py         # 文本清理
│   ├── meta_extraction.py       # 元数据提取
│   ├── latex_utils.py           # LaTeX工具
│   ├── question_processing.py   # 题目处理
│   ├── validation.py            # 验证函数
│   └── image_handling.py        # 图片处理
├── converters/                   # 转换器模块
│   ├── __init__.py
│   ├── base_converter.py        # 抽象基类
│   ├── exam_converter.py        # 试卷转换器
│   └── handout_converter.py     # 讲义转换器 (新)
├── core/
│   ├── ocr_to_examx.py          # 试卷转换入口 (简化版)
│   └── ocr_to_handoutx.py       # 讲义转换入口 (新)
├── testing/                      # 测试
│   ├── test_math_processing.py
│   ├── test_converters.py
│   └── ...
└── ...
```

## 迁移检查清单

### math_processing.py
- [ ] CHINESE_MATH_SEPARATORS
- [ ] TokenType enum
- [ ] MathStateMachine class (所有方法)
- [ ] math_sm singleton
- [ ] 16个数学修复函数
- [ ] 导入: re, enum
- [ ] __all__ 列表

### text_cleaning.py
- [ ] LATEX_SPECIAL_CHARS
- [ ] escape_latex_special()
- [ ] standardize_math_symbols()
- [ ] clean_markdown()
- [ ] 5个图片清理函数
- [ ] 2个文本格式化函数
- [ ] 导入: re, pathlib
- [ ] __all__ 列表

### meta_extraction.py
- [ ] META_PATTERNS
- [ ] extract_meta_and_images()
- [ ] 4个内部提取函数
- [ ] 导入: re, typing
- [ ] __all__ 列表

### latex_utils.py
- [ ] 5个LaTeX环境处理函数
- [ ] 导入: re
- [ ] __all__ 列表

### question_processing.py
- [ ] 7个题目结构处理函数
- [ ] _is_likely_stem() 辅助函数
- [ ] 导入: re, typing
- [ ] __all__ 列表

### validation.py
- [ ] 4个验证函数
- [ ] 导入: re, typing, pathlib
- [ ] __all__ 列表

### image_handling.py
- [ ] IMAGE_PATTERN常量
- [ ] 4个图片处理函数
- [ ] 导入: re, pathlib, typing, shutil
- [ ] __all__ 列表

## 兼容性保证

1. **向后兼容**: 保留 `ocr_to_examx.py` 作为入口，内部调用新模块
2. **渐进迁移**: 先提取库函数，再重构转换器
3. **测试驱动**: 每个阶段都有测试验证
4. **文档更新**: 同步更新使用文档

## 预期收益

1. **代码复用**: 数学处理、文本清理等模块可被试卷和讲义共享
2. **易于扩展**: 新增转换类型（如练习册）只需实现新的Converter
3. **易于维护**: 模块化后，修复bug只需改动单个模块
4. **易于测试**: 每个模块可独立测试
5. **代码质量**: 减少重复代码，提高可读性

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 重构引入bug | 高 | 完整回归测试，保留旧代码对比 |
| 性能下降 | 中 | 性能测试，必要时优化导入 |
| 模块划分不当 | 中 | 渐进式重构，根据反馈调整 |
| 文档不同步 | 低 | 同步更新文档，代码审查 |

## 时间表

- **Week 1** (Dec 9-15): Phase 1 - 提取工具库模块
- **Week 2** (Dec 16-22): Phase 2 - 创建转换器架构
- **Week 3** (Dec 23-29): Phase 3 - 实现讲义转换器
- **Week 4** (Dec 30-Jan 5): Phase 4 - 清理与优化

## 参考资料

- 原始代码: `tools/core/ocr_to_examx.py` (v1.9.10, 7014行)
- 测试用例: `tools/testing/`
- 设计文档: `docs/workflow.md`
- 样式文件: `styles/examx.sty`, `styles/handoutx.sty`
