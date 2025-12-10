#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
math_processing.py - 数学公式处理模块 - 定界符解析、修复、转换

从 ocr_to_examx.py 提取的共享工具函数，供 exam 和 handout 转换器使用。

生成时间: 自动提取
源文件: tools/core/ocr_to_examx.py
"""

from enum import Enum, auto
import re

# ============================================================
# 数学公式处理模块 - 定界符解析、修复、转换
# ============================================================

CHINESE_MATH_SEPARATORS = {
    'connectors': ['即', '与', '或', '且', '故', '则', '所以', '因此', '因为', '由于', '根据', '显然', '可知', '可得', '于是', '从而'],
    'math_objects': ['直线', '曲线', '平面', '函数', '方程', '圆', '点', '椭圆', '双曲线', '抛物线', '向量', '矩阵', '集合', '区间'],
    'verbs': ['设', '令', '若', '当', '时', '有', '得', '知', '过', '取', '作'],
}


class TokenType(Enum):
    TEXT = auto()
    DOLLAR_SINGLE = auto()
    DOLLAR_DOUBLE = auto()
    LATEX_OPEN = auto()
    LATEX_CLOSE = auto()
    RIGHT_BOUNDARY = auto()
    NEWLINE = auto()
    EOF = auto()




class MathStateMachine:
    r"""数学模式状态机 - 统一解析/规范所有数学定界符

    设计目标：
    1. 支持混合出现的 $ ... $、$$ ... $$、\( ... \) 以及 OCR 生成的 \right. $$ 等畸形边界
    2. 将所有显示/行内数学统一规范为行内形式：\( ... \)（与 examx 包兼容）
    3. 保持已有正确的 \( ... \) / \) 不被二次包裹
    4. 防止跨行单美元未闭合造成吞并后续文本
    """

    def preprocess_multiline_math(self, text: str) -> str:
        """预处理多行数学环境（修复 P0-001, P0-002）

        处理跨多行的 $$...array/cases...$$ 块，避免被逐行拆散
        
        🆕 v1.9.3：修复 T008/T017 问题
        - 只合并冒号分隔的 $$标签$$：$$公式$$ 模式
        - 不合并逗号/顿号分隔的独立变量 $$P$$，$$B$$ 模式
        """
        # 🆕 修复 P0-001a: 只合并冒号分隔的模式（标签：公式）
        # 例如: $$C$$：$$x^{2}$$ → $$C：x^{2}$$
        # 🔧 v1.9.3: 移除逗号/顿号/句号/分号，这些分隔的应该保持独立
        text = re.sub(r'\$\$([^$]+)\$\$([：])\$\$([^$]+)\$\$', r'$$\1\2\3$$', text)

        # 🆕 v1.9.8: 处理嵌套的多行数学环境
        # 例如: $$\left\{...\Rightarrow \left\{...\right.\right.\ $$
        # 这种嵌套结构无法被单层正则匹配，需要特殊处理
        def process_nested_multiline(text):
            r"""处理嵌套的 \left...\right 多行数学环境"""
            # 匹配 $$\left 开头，到嵌套的 \right.\right.\ $$ 结尾的块
            # [\s\\]* 匹配空白和反斜杠（处理 \right.\ \right.\ $$ 格式）
            pattern = re.compile(
                r'\$\$\s*\\left.*?\\right\.[\s\\]*\\right\.[\s\\]*\$\$',
                re.DOTALL
            )

            def replace_nested(match):
                content = match.group(0)
                # 提取 \left 到最后一个 \right. 的内容（贪婪匹配）
                inner = re.search(r'\\left.*\\right\.[\s\\]*\\right\.', content, re.DOTALL)
                if inner:
                    return r'\(' + inner.group(0) + r'\)'
                # 降级处理
                inner = content.strip()
                if inner.startswith('$$'):
                    inner = inner[2:]
                if inner.endswith('$$'):
                    inner = inner[:-2]
                return r'\(' + inner.strip() + r'\)'

            return pattern.sub(replace_nested, text)

        text = process_nested_multiline(text)

        # 🆕 修复 P0-002: 处理 \right.\ $$ 跨行边界模式
        # 情况1: \right.\ $$ （反斜杠+空格+双美元）
        # 注意：\ 是两个字符：反斜杠和空格，\left\{ 是backslash-left-backslash-brace
        # (?:\\[\{\[\(])? 表示可选的 "\{" 或 "\[" 或 "\("
        pattern_backslash_space = re.compile(
            r'\$\$\s*\\left(?:\\[\{\[\(])?\s*\\begin\{(array|cases|matrix|pmatrix|bmatrix|vmatrix)\}.*?\\end\{\1\}\s*\\right(?:\\[\}\]\)])?\.?\s*\\ \$\$',
            re.DOTALL
        )
        
        def extract_content(match_obj):
            # Extract the \left...\right. part
            content = re.search(r'\\left.*?\\right(?:\\[\}\]\)])?\.?', match_obj.group(0), re.DOTALL)
            return r'\(' + content.group(0) + r'\)'
        
        text = pattern_backslash_space.sub(extract_content, text)

        # 情况2: \right.\\ $$ （双反斜杠+空格+双美元）
        pattern_double_backslash = re.compile(
            r'\$\$\s*\\left(?:\\[\{\[\(])?\s*\\begin\{(array|cases|matrix|pmatrix|bmatrix|vmatrix)\}.*?\\end\{\1\}\s*\\right(?:\\[\}\]\)])?\.?\s*\\\\ \$\$',
            re.DOTALL
        )
        text = pattern_double_backslash.sub(extract_content, text)

        # 匹配 $$...$$ 块，包括跨行的 array/cases/matrix 环境（原有逻辑）
        pattern = re.compile(
            r'\$\$\s*\\left(?:\\[\{\[\(])?\s*\\begin\{(array|cases|matrix|pmatrix|bmatrix|vmatrix)\}.*?\\end\{\1\}\s*\\right(?:\\[\}\]\)])?\.?\s*\$\$',
            re.DOTALL
        )

        def replace_multiline(match):
            # 🔧 v1.9.7: 修复内部 \left|...\right| 导致的截断问题
            # 原来的正则 \\left.*?\\right 使用非贪婪匹配，会在遇到第一个 \right 时停止
            # 当方程组内部包含 \left|...\right|（绝对值）时会错误截断
            #
            # 修复方案：使用贪婪匹配 .* 配合 \right\. 来匹配最外层的 \right.
            # 因为外层 pattern 已经确保了整个块的正确性，这里只需要提取 \left...\right. 部分
            content = re.search(r'\\left.*\\right\.', match.group(0), re.DOTALL)
            if content:
                return r'\(' + content.group(0) + r'\)'
            # 降级：如果没有 \right.，尝试匹配 \right 后跟其他括号
            content = re.search(r'\\left.*\\right(?:\\[\}\]\)])?', match.group(0), re.DOTALL)
            if content:
                return r'\(' + content.group(0) + r'\)'
            # 最后降级：返回去掉 $$ 的原内容
            inner = match.group(0).strip()
            if inner.startswith('$$'):
                inner = inner[2:]
            if inner.endswith('$$'):
                inner = inner[:-2]
            return r'\(' + inner.strip() + r'\)'

        return pattern.sub(replace_multiline, text)

    def tokenize(self, text: str) -> List:
        tokens = []
        i = 0
        n = len(text)
        while i < n:
            # 🔥 v1.8.6：增强 \right. 后的 OCR 边界检测（修复 P0-001）
            # 处理 \right. 后可能跟随的各种畸形格式：
            # - \right. $$
            # - \right. $
            # - \right.\ $$  （反斜杠空格，P0-CRITICAL）
            # - \right.\\ $$  （双反斜杠空格）
            # - \right.  $$  （多个空格）
            # - \right.，（直接跟中文标点）
            if text[i:].startswith(r'\right.'):
                j = i + 7  # 跳过 \right.
                found_boundary = False

                # 🆕 v1.9.3：修复 \right.\ $$ 处理
                # 生成 RIGHT_BOUNDARY token 后，还要生成 DOLLAR_DOUBLE token
                # 这样 process 函数才能正确识别数学模式的结束

                # 情况1：\right.\ $$（反斜杠+空格+双美元，P0-CRITICAL）
                if j < n - 3 and text[j:j+4] == r'\ $$':
                    tokens.append((TokenType.RIGHT_BOUNDARY, r'\right.', i))
                    tokens.append((TokenType.DOLLAR_DOUBLE, '$$', j + 2))  # 添加结束符
                    i = j + 4
                    found_boundary = True

                # 情况2：\right.\\ $$（双反斜杠+空格+双美元）
                elif j < n - 4 and text[j:j+5] == r'\\ $$':
                    tokens.append((TokenType.RIGHT_BOUNDARY, r'\right.', i))
                    tokens.append((TokenType.DOLLAR_DOUBLE, '$$', j + 3))  # 添加结束符
                    i = j + 5
                    found_boundary = True

                # 情况3：\right. $$（空格+双美元）
                elif j < n - 1 and text[j] == ' ':
                    # 跳过多个空格
                    k = j
                    while k < n and text[k] == ' ':
                        k += 1
                    if k < n - 1 and text[k:k+2] == '$$':
                        tokens.append((TokenType.RIGHT_BOUNDARY, r'\right.', i))
                        tokens.append((TokenType.DOLLAR_DOUBLE, '$$', k))  # 添加结束符
                        i = k + 2
                        found_boundary = True

                # 情况4：\right.$$（直接跟双美元，无空格）
                elif j < n - 1 and text[j:j+2] == '$$':
                    tokens.append((TokenType.RIGHT_BOUNDARY, r'\right.', i))
                    tokens.append((TokenType.DOLLAR_DOUBLE, '$$', j))  # 添加结束符
                    i = j + 2
                    found_boundary = True

                # 情况5：\right. $（单美元）- 这种情况比较特殊，保持原样
                elif j < n and text[j] == '$' and (j + 1 >= n or text[j+1] != '$'):
                    tokens.append((TokenType.RIGHT_BOUNDARY, r'\right.', i))
                    tokens.append((TokenType.DOLLAR_SINGLE, '$', j))  # 添加结束符
                    i = j + 1
                    found_boundary = True

                # 情况6：\right.\)（已经正确闭合）
                elif j < n - 1 and text[j:j+2] == r'\)':
                    # 这是正确的格式，保持原样
                    tokens.append((TokenType.TEXT, r'\right.', i))
                    i += 7
                    found_boundary = True

                # 情况7：\right. 后直接跟中文标点（，。；：等）
                elif j < n and text[j] in '，。；：、！？':
                    # OCR 错误：缺少闭合符号
                    # 插入 \right.\) 来闭合数学模式，标点保持在数学模式外
                    tokens.append((TokenType.RIGHT_BOUNDARY, r'\right.', i))
                    i = j  # 不跳过标点，让后续处理将其作为普通文本
                    found_boundary = True

                if not found_boundary:
                    # 不是边界错误，保持原样
                    tokens.append((TokenType.TEXT, r'\right.', i))
                    i += 7

                if found_boundary:
                    continue

            # $$ 显示数学
            if i < n - 1 and text[i:i+2] == '$$':
                tokens.append((TokenType.DOLLAR_DOUBLE, '$$', i))
                i += 2
                continue

            # 单 $ 行内数学
            if text[i] == '$':
                tokens.append((TokenType.DOLLAR_SINGLE, '$', i))
                i += 1
                continue

            # \( 与 \)
            if i < n - 1 and text[i:i+2] == r'\(':
                tokens.append((TokenType.LATEX_OPEN, r'\(', i))
                i += 2
                continue
            if i < n - 1 and text[i:i+2] == r'\)':
                tokens.append((TokenType.LATEX_CLOSE, r'\)', i))
                i += 2
                continue

            # 普通文本块收集
            j = i
            while j < n:
                if text[j] in '$\n':
                    break
                if j < n - 1 and text[j:j+2] in [r'\(', r'\)', '$$']:
                    break
                if text[j:].startswith(r'\right.'):
                    break
                j += 1
            if j > i:
                tokens.append((TokenType.TEXT, text[i:j], i))
                i = j
            else:
                tokens.append((TokenType.TEXT, text[i], i))
                i += 1
        return tokens

    def fix_malformed_patterns(self, text: str) -> str:
        r"""修复格式错误的数学模式（增强版 v1.9.2）

        🆕 v1.9.2: 处理更多的畸形模式
        - 嵌套定界符：\(P,B\(，\)C,D\) → \(P,B\)，\(C,D\)
        - 反向嵌套：\)...\( → 修正为正确顺序
        """
        import re

        # 1. 删除空数学模式 \(\)
        text = re.sub(r'\\\(\s*\\\)', '', text)

        # 2. 修复连续定界符（迭代处理，最多3次）
        for _ in range(3):
            before = text
            # \(\( → \(
            text = re.sub(r'\\\(\\\(', r'\\(', text)
            # \)\) → \)
            text = re.sub(r'\\\)\\\)', r'\\)', text)
            if text == before:
                break

        # 3. 修复错误嵌套 \((\) → (
        text = re.sub(r'\\\(\(\\\)', '(', text)

        # 4. 修复 \)(\( → )(  (错误的定界符包裹括号)
        # 🆕 v1.9.11：改为保守策略，只处理看起来像错误嵌套的情况
        # 不处理合法的 \(...\)(\(...\)) 结构（如条件表达式）
        # 只处理明显错误的情况：\)(\( 且前面的 \( 已闭合
        # 暂时禁用这个规则，因为它会破坏 \(x=16\)(\(y>0\)) 这种合法结构
        # text = re.sub(r'\\\)\(\\\(', ')(', text)
        
        # 🆕 v1.9.2: 修复嵌套定界符中的中文标点
        # 模式: \(标点\) → 标点 (当标点是独立的数学块时)
        # 例如: \(P,B\(，\)C,D\) 中的 \(，\) 应该变成 ，
        chinese_punct = ['，', '。', '；', '：', '、', '！', '？']
        for punct in chinese_punct:
            # 匹配 \(标点\) 模式（标点单独在数学块中）
            pattern = r'\\\(' + re.escape(punct) + r'\\\)'
            text = re.sub(pattern, punct, text)
        
        # 修复 \(，\therefore\) 这类模式 → ，\(\therefore\)
        text = re.sub(r'\\\(([，。；：、！？])\\\\therefore\\\)', r'\1\\(\\therefore\\)', text)
        
        # 修复 \(，\) 后面紧跟内容的情况（可能是嵌套错误）
        # \(内容\(，\)内容\) → \(内容\)，\(内容\)
        for punct in chinese_punct:
            pattern = rf'(\\\([^)]+)\\\({re.escape(punct)}\\\)([^)]+\\\))'
            replacement = r'\1\\)' + punct + r'\\(\2'
            for _ in range(3):
                new_text = re.sub(pattern, replacement, text)
                if new_text == text:
                    break
                text = new_text

        return text

    def normalize_punctuation_in_math(self, text: str) -> str:
        r"""规范化数学模式内的全角标点（增强版 v1.9.1）

        🆕 v1.9.1：添加更完整的中文标点映射
        - 顿号、冒号、句号等
        - 保护 \text{}, \mbox{}, \mathrm{} 内的中文标点
        🆕 P1-003：扩展标点映射列表，添加$$...$$处理
        """
        import re

        # 标点替换映射（在数学模式内使用半角）
        punct_map = {
            '，': ',',
            '；': ';',
            '：': ':',
            '（': '(',
            '）': ')',
            '、': ',',  # 顿号转为逗号
            '。': '.',
            '！': '!',
            '？': '?',
            '【': '[',
            '】': ']',
            '〔': '[',
            '〕': ']',
            '「': '"',
            '」': '"',
            # 🆕 v1.9.9: P2-9 补充更多中文标点
            '『': '"',
            '』': '"',
            '"': '"',
            '"': '"',
            ''': "'",
            ''': "'",
            '—': '-',
            '…': '...',
        }

        # 🆕 v1.9.9: P1-6 提取公共的文本保护逻辑
        def protect_text_commands(content: str, protected: list) -> str:
            """保护 \\text{}, \\mbox{} 等命令内的内容"""
            def save_text(m):
                protected.append(m.group(0))
                return f"@@TEXT_{len(protected)-1}@@"

            content = re.sub(r'\\text\{[^}]*\}', save_text, content)
            content = re.sub(r'\\mbox\{[^}]*\}', save_text, content)
            content = re.sub(r'\\mathrm\{[^}]*\}', save_text, content)
            content = re.sub(r'\\textbf\{[^}]*\}', save_text, content)
            content = re.sub(r'\\textit\{[^}]*\}', save_text, content)
            return content

        def restore_protected(content: str, protected: list) -> str:
            """恢复被保护的内容"""
            for i, p in enumerate(protected):
                content = content.replace(f"@@TEXT_{i}@@", p)
            return content

        # 🆕 v1.9.2: 使用基于位置的匹配来处理嵌套括号
        def process_all_math_blocks(text: str) -> str:
            """逐个处理所有数学块，支持嵌套括号"""
            result = []
            i = 0
            n = len(text)
            
            while i < n:
                # 查找 \(
                if i < n - 1 and text[i:i+2] == r'\(':
                    # 找到对应的 \)
                    start = i
                    depth = 1
                    j = i + 2
                    
                    # 🆕 v1.9.8: 修复 P0-2 边界检查，j < n 而非 j < n - 1
                    while j < n and depth > 0:
                        if j < n - 1 and text[j:j+2] == r'\(':
                            depth += 1
                            j += 2
                        elif j < n - 1 and text[j:j+2] == r'\)':
                            depth -= 1
                            if depth == 0:
                                break
                            j += 2
                        else:
                            j += 1
                    
                    if depth == 0:
                        # 成功匹配，处理内容
                        math_content = text[start+2:j]

                        # 🆕 v1.9.9: 使用提取的辅助函数
                        protected = []
                        processed = protect_text_commands(math_content, protected)

                        # 替换全角标点
                        for full, half in punct_map.items():
                            processed = processed.replace(full, half)

                        # 恢复保护的内容
                        processed = restore_protected(processed, protected)

                        result.append(r'\(' + processed + r'\)')
                        i = j + 2
                    else:
                        # 未能找到匹配的 \)，保持原样
                        result.append(text[i])
                        i += 1
                else:
                    result.append(text[i])
                    i += 1
            
            return ''.join(result)
        
        text = process_all_math_blocks(text)
        
        # 🆕 P1-003: 同样处理 $$...$$ 内的标点（转换前）
        def replace_in_dollar(match):
            content = match.group(1)
            for full, half in punct_map.items():
                content = content.replace(full, half)
            return '$$' + content + '$$'
        
        text = re.sub(r'\$\$([^$]+)\$\$', replace_in_dollar, text)

        return text

    def split_colon_from_math(self, text: str) -> str:
        r"""分离数学模式内的中文冒号
        
        模式：\(标签：公式\) → \(标签\)：\(公式\)
        """
        import re

        # 模式1: \(单字母：公式\)
        pattern1 = r'\\\(([A-Za-z])：([^)]+)\\\)'
        text = re.sub(pattern1, r'\\(\1\\)：\\(\2\\)', text)
        
        # 模式2: \(变量_下标：公式\)
        pattern2 = r'\\\(([a-z]_\{[^}]+\})：([^)]+)\\\)'
        text = re.sub(pattern2, r'\\(\1\\)：\\(\2\\)', text)
        
        # 模式3: \(变量下标：公式\) (无花括号)
        pattern3 = r'\\\(([a-z]_\d+)：([^)]+)\\\)'
        text = re.sub(pattern3, r'\\(\1\\)：\\(\2\\)', text)
        
        return text
    
    def fix_math_symbol_chinese_boundary(self, text: str) -> str:
        r"""修复数学符号后直接跟中文的边界问题
        
        处理模式：\(symbol中文...\) → \(symbol\)中文...\)
        """
        import re
        
        # 需要分离的数学符号列表
        symbols = [
            r'\\therefore',
            r'\\because', 
            r'\\subset',
            r'\\supset',
            r'\\in',
            r'\\notin',
            r'\\cap',
            r'\\cup',
            r'\\parallel',
            r'\\perp',
            r'\\forall',
            r'\\exists',
            r'\\Rightarrow',
            r'\\Leftrightarrow',
            r'\\sim',
            r'\\cong',
            r'\\equiv',
        ]
        
        # 多次迭代处理，直到没有更多匹配
        max_iterations = 5
        for _ in range(max_iterations):
            changed = False
            for sym in symbols:
                # 匹配 \(前缀symbol中文后缀\) 模式
                # 其中 symbol 后面直接跟中文
                pattern = rf'(\\\()([^)]*?)({sym})([\u4e00-\u9fa5]+)([^)]*?)(\\\))'
                
                def replace_fn(m):
                    nonlocal changed
                    changed = True
                    
                    open_paren = m.group(1)   # \(
                    before = m.group(2)        # symbol 前的内容
                    symbol = m.group(3)        # 数学符号
                    chinese = m.group(4)       # 中文
                    after = m.group(5)         # 中文后的内容
                    close_paren = m.group(6)   # \)
                    
                    # 重组：\(前缀+symbol\)中文\(后缀\)
                    result = ''
                    
                    # 前缀部分
                    if before.strip():
                        result += open_paren + before + symbol + close_paren
                    else:
                        result += open_paren + symbol + close_paren
                    
                    # 中文部分（在数学模式外）
                    result += chinese
                    
                    # 后缀部分 - 递归处理
                    if after.strip():
                        result += open_paren + after + close_paren
                    
                    return result
                
                text = re.sub(pattern, replace_fn, text, flags=re.DOTALL)
            
            if not changed:
                break
        
        # 清理空的数学模式
        text = re.sub(r'\\\(\s*\\\)', '', text)
        
        return text

    def split_chinese_from_math(self, text: str) -> str:
        """将中文词汇从数学模式中分离 - 重写版
        
        策略：将开头和结尾的中文移到数学模式外部，而不是在内部插入定界符
        """
        import re
        
        def process_math_block(match):
            content = match.group(1)
            original = match.group(0)
            
            # 如果内容为空或只有空白，保持原样
            if not content.strip():
                return original
            
            prefix = ''
            suffix = ''
            core = content
            
            # 检测并提取开头的中文
            chinese_start = re.match(r'^([\u4e00-\u9fa5，。；：、！？\s]+)', core)
            if chinese_start:
                prefix = chinese_start.group(1)
                core = core[len(prefix):]
            
            # 检测并提取结尾的中文
            chinese_end = re.search(r'([\u4e00-\u9fa5，。；：、！？\s]+)$', core)
            if chinese_end:
                suffix = chinese_end.group(1)
                core = core[:-len(suffix)]
            
            # 如果核心内容被完全移除，说明原本就不应该是数学模式
            if not core.strip():
                return prefix + suffix
            
            # 重组：中文前缀 + \(核心公式\) + 中文后缀
            result = prefix + r'\(' + core + r'\)' + suffix
            
            # 清理可能产生的空数学模式
            result = re.sub(r'\\\(\s*\\\)', '', result)
            
            return result
        
        # 处理所有 \(...\) 块
        return re.sub(r'\\\(([^)]*?)\\\)', process_math_block, text, flags=re.DOTALL)

    def balance_delimiters(self, text: str) -> str:
        r"""平衡数学定界符（增强版 v1.9.3）

        🆕 v1.9.3 修复:
        - 移除了错误的 connector 前添加 \) 的逻辑
        - 该逻辑假设 \therefore 等符号前一定有数学内容需要闭合
        - 但实际上这些符号可能出现在行首，前面是普通文本或中文标点

        🆕 v1.9.2 改进:
        1. 支持跨行数学环境（array/cases）的平衡检查
        3. 全局平衡检查和修复
        """
        import re

        # 步骤1：处理跨行数学环境
        # 检测 \(\left\{ \begin{array} 但没有对应的 \end{array} \right.\)
        lines = text.split('\n')
        processed_lines = []
        pending_close = 0  # 累积需要闭合的数量
        in_multiline_math = False
        
        for i, line in enumerate(lines):
            if line.strip().startswith('%'):
                processed_lines.append(line)
                continue

            # 检测跨行数学环境开始
            if re.search(r'\\\(.*\\begin\{(array|cases|matrix|pmatrix|bmatrix)\}', line) and \
               not re.search(r'\\end\{(array|cases|matrix|pmatrix|bmatrix)\}.*\\\)', line):
                in_multiline_math = True
                pending_close += 1
            
            # 检测跨行数学环境结束
            # 🆕 v1.9.8: 改进嵌套检测 - 只有当 \end 数量 >= \begin 数量时才认为环境结束
            if in_multiline_math and re.search(r'\\end\{(array|cases|matrix|pmatrix|bmatrix)\}', line):
                # 统计这行中 \begin 和 \end 的数量
                begin_count = len(re.findall(r'\\begin\{(array|cases|matrix|pmatrix|bmatrix)\}', line))
                end_count = len(re.findall(r'\\end\{(array|cases|matrix|pmatrix|bmatrix)\}', line))

                # 只有当 \end 数量 > \begin 数量时，才认为是真正的环境结束
                # 这样可以正确处理嵌套的情况
                if end_count > begin_count:
                    # 检查这行是否有 \)
                    if not re.search(r'\\\)', line):
                        # 只在最后一个 \right. 后添加 \)，避免破坏嵌套结构
                        last_right_pos = line.rfind(r'\right.')
                        if last_right_pos != -1:
                            insert_pos = last_right_pos + 7  # len(r'\right.') = 7
                            line = line[:insert_pos] + r'\)' + line[insert_pos:]
                        else:
                            line = line + r'\)'
                        pending_close = max(0, pending_close - 1)
                    in_multiline_math = False

            # 在每行内检查平衡（仅对非跨行环境）
            if not in_multiline_math:
                opens = list(re.finditer(r'\\\(', line))
                closes = list(re.finditer(r'\\\)', line))
                open_count = len(opens)
                close_count = len(closes)

                if open_count > close_count:
                    # 检查是否是跨行开始
                    if not re.search(r'\\begin\{(array|cases|matrix)', line):
                        line = line + r'\)' * (open_count - close_count)
                elif close_count > open_count:
                    diff = close_count - open_count
                    for _ in range(diff):
                        line = re.sub(r'^([^\\]*)\\\)', r'\1', line, count=1)

            processed_lines.append(line)

        return '\n'.join(processed_lines)
    
    def final_cleanup(self, text: str) -> str:
        """最终清理和验证（增强版 v1.9.2）
        
        🆕 v1.9.2 改进:
        1. 全局定界符平衡修复
        2. 识别并修复孤立的数学内容
        """
        import re
        
        if not text:
            return text
        
        # 1. 清理残留的 $$
        text = re.sub(r'\$\$', '', text)
        
        # 2. 清理空的数学模式
        text = re.sub(r'\\\(\s*\\\)', '', text)
        
        # 3. 清理连续的定界符
        for _ in range(3):
            text = re.sub(r'\\\(\\\(', r'\\(', text)
            text = re.sub(r'\\\)\\\)', r'\\)', text)
        
        # 4. 🆕 全局定界符平衡修复
        open_count = len(re.findall(r'\\\(', text))
        close_count = len(re.findall(r'\\\)', text))
        
        if open_count != close_count:
            diff = open_count - close_count
            # 🆕 v1.9.8: 移除冗余输出，仅在调试模式下显示
            
            # 尝试智能修复
            if diff > 0:
                # \( 多于 \)，需要添加 \)
                # 查找可能缺少 \) 的位置：行尾有 \( 但没有对应的 \)
                lines = text.split('\n')
                fixed_lines = []
                remaining_diff = diff
                
                for line in lines:
                    if remaining_diff > 0 and not line.strip().startswith('%'):
                        line_opens = len(re.findall(r'\\\(', line))
                        line_closes = len(re.findall(r'\\\)', line))
                        line_diff = line_opens - line_closes
                        
                        if line_diff > 0:
                            # 在行尾添加缺少的 \)
                            line = line + r'\)' * min(line_diff, remaining_diff)
                            remaining_diff -= line_diff
                    fixed_lines.append(line)
                
                text = '\n'.join(fixed_lines)
            elif diff < 0:
                # \) 多于 \(，需要移除多余的 \) 或添加 \(
                # 查找行首孤立的 \)
                lines = text.split('\n')
                fixed_lines = []
                remaining_diff = abs(diff)
                
                for line in lines:
                    if remaining_diff > 0 and not line.strip().startswith('%'):
                        # 检查行首是否有孤立的 \)
                        while remaining_diff > 0 and re.match(r'^\s*\\\)', line):
                            line = re.sub(r'^(\s*)\\\)', r'\1', line, count=1)
                            remaining_diff -= 1
                    fixed_lines.append(line)
                
                text = '\n'.join(fixed_lines)
            
            # 重新验证（静默处理）
            new_open = len(re.findall(r'\\\(', text))
            new_close = len(re.findall(r'\\\)', text))
        
        return text

    def fix_reversed_delimiters(self, text: str) -> str:
        r"""修复反向定界符模式（增强版 v1.9.1）

        修复模式：
        1. \)：公式\( → \)：\(公式\)（冒号后的公式缺少开启符）
        2. \)动词\( → 保持不变（可能是正确的）
        3. 孤立的 \) 删除
        """
        import re
        lines = text.split('\n')
        fixed_lines = []

        for line in lines:
            # 跳过注释行
            if line.strip().startswith('%'):
                fixed_lines.append(line)
                continue

            # 🆕 模式1：修复冒号后的公式缺少 \( 的情况
            # 匹配: \)：公式内容\( 或 \)：公式内容（行尾/标点）
            # 例如: 直线\(l_{1}\)：\sqrt{3}x - y = 0\) → 直线\(l_{1}\)：\(\sqrt{3}x - y = 0\)
            def fix_colon_pattern(match):
                close_paren = match.group(1)  # \)
                colon = match.group(2)  # ：或:
                formula = match.group(3)  # 公式内容
                terminator = match.group(4)  # \( 或标点或行尾

                # 检查公式内容是否包含数学符号（确认是数学公式）
                if re.search(r'[a-zA-Z_\^{}\\\d=+\-*/]', formula):
                    # 是数学内容，需要添加 \(
                    if terminator == r'\(':
                        # 后面已有 \(，替换为 \)
                        return f'{close_paren}{colon}\\({formula}\\)'
                    elif terminator in ['，', '。', '；', '、', '）', '\n', '']:
                        # 后面是标点或行尾，添加 \(\)
                        return f'{close_paren}{colon}\\({formula}\\){terminator}'
                    else:
                        return match.group(0)
                else:
                    # 不是数学内容，保持原样
                    return match.group(0)

            # 匹配冒号模式：\)：[公式内容][\(或标点或行尾]
            pattern_colon = re.compile(
                r'(\\\))' +                           # 捕获组1: \)
                r'([：:])' +                          # 捕获组2: 中文或英文冒号
                r'([^\\(）\n]{1,100}?)' +             # 捕获组3: 公式内容（非贪婪，不包含\(和））
                r'(\\\(|[，。；、）]|\n|$)'            # 捕获组4: \( 或标点或行尾
            )
            line = pattern_colon.sub(fix_colon_pattern, line)

            # 🆕 模式2：逐行检查定界符平衡（保留原有逻辑）
            opens = [(m.start(), r'\(') for m in re.finditer(r'\\\(', line)]
            closes = [(m.start(), r'\)') for m in re.finditer(r'\\\)', line)]

            all_delims = sorted(opens + closes, key=lambda x: x[0])

            depth = 0
            needs_fix = False
            for pos, delim in all_delims:
                if delim == r'\(':
                    depth += 1
                else:
                    depth -= 1
                    if depth < 0:
                        needs_fix = True
                        break

            if needs_fix:
                # 修复策略: 移除行首的孤立 \)
                line = re.sub(r'^([^\\\(]*?)\\\)', r'\1', line)

            fixed_lines.append(line)

        return '\n'.join(fixed_lines)

    def process(self, text: str) -> str:
        # 预处理：保护中文括号，避免与数学括号混淆
        chinese_paren_map = {
            '（': '@@ZH_PAREN_OPEN@@',
            '）': '@@ZH_PAREN_CLOSE@@',
            '【': '@@ZH_BRACKET_OPEN@@',
            '】': '@@ZH_BRACKET_CLOSE@@',
        }
        for char, placeholder in chinese_paren_map.items():
            text = text.replace(char, placeholder)

        # 🆕 P0-001 & P1-005: 在预处理多行数学之前修复集合定义和OCR错误
        text = fix_broken_set_definitions(text)
        text = fix_ocr_specific_errors(text)
        
        # 先预处理多行数学块
        text = self.preprocess_multiline_math(text)
        # 然后处理剩余的单行公式
        tokens = self.tokenize(text)
        out = []
        i = 0
        math_depth = 0  # 跟踪数学模式深度

        while i < len(tokens):
            t_type, val, pos = tokens[i]

            # 🔥 v1.8.3：智能处理 \right. 边界
            if t_type == TokenType.RIGHT_BOUNDARY:
                # 检查是否在数学模式内（有未闭合的 \(）
                if math_depth > 0:
                    out.append(r'\right.\)')
                    math_depth -= 1
                else:
                    # 不在数学模式内，保持原样（这是正常的 \right.）
                    out.append(r'\right.')
                i += 1
                continue
            if t_type == TokenType.DOLLAR_DOUBLE:
                # 收集直到下一个 $$ 或 RIGHT_BOUNDARY
                i += 1
                buf = []
                while i < len(tokens):
                    tt, tv, _ = tokens[i]
                    if tt == TokenType.DOLLAR_DOUBLE:
                        i += 1
                        break
                    # 🆕 v1.9.4：遇到 DOLLAR_SINGLE，视为 $$ 的错误结束符（$$...$模式）
                    # 将 $ 作为结束符，不收集到 buf 中
                    if tt == TokenType.DOLLAR_SINGLE:
                        i += 1
                        break
                    # 🆕 v1.9.3：遇到 RIGHT_BOUNDARY，输出它然后检查下一个是否是 $$
                    if tt == TokenType.RIGHT_BOUNDARY:
                        buf.append(r'\right.')
                        i += 1
                        # 检查下一个 token 是否是 $$ 结束符
                        if i < len(tokens) and tokens[i][0] == TokenType.DOLLAR_DOUBLE:
                            i += 1  # 跳过结束的 $$
                            break
                        # 也检查 DOLLAR_SINGLE（$$...\right.$模式）
                        if i < len(tokens) and tokens[i][0] == TokenType.DOLLAR_SINGLE:
                            i += 1
                            break
                        continue
                    buf.append(tv)
                    i += 1
                out.append(r'\(' + ''.join(buf).strip() + r'\)')
                continue

            if t_type == TokenType.DOLLAR_SINGLE:
                i += 1
                buf = []
                while i < len(tokens):
                    tt, tv, _ = tokens[i]
                    if tt == TokenType.DOLLAR_SINGLE:
                        i += 1
                        break
                    # 禁止跨行的单美元延伸
                    if '\n' in tv:
                        out.append('$')
                        out.extend(buf)
                        break
                    buf.append(tv)
                    i += 1
                if buf:
                    out.append(r'\(' + ''.join(buf) + r'\)')
                continue

            if t_type == TokenType.LATEX_OPEN:
                out.append(val)
                math_depth += 1
                i += 1
                continue

            if t_type == TokenType.LATEX_CLOSE:
                out.append(val)
                math_depth = max(0, math_depth - 1)
                i += 1
                continue
            out.append(val)
            i += 1

        result = ''.join(out)

        # 后处理步骤（按顺序执行）
        result = self.fix_malformed_patterns(result)
        result = self.normalize_punctuation_in_math(result)
        result = self.split_colon_from_math(result)
        result = self.fix_math_symbol_chinese_boundary(result)
        result = self.split_chinese_from_math(result)
        result = self.balance_delimiters(result)
        result = self.final_cleanup(result)

        # 修复反向定界符
        result = self.fix_reversed_delimiters(result)

        # 后处理：恢复中文括号
        for char, placeholder in chinese_paren_map.items():
            result = result.replace(placeholder, char)

        return result


# 单例实例供全局调用


math_sm = MathStateMachine()


def fix_array_boundaries(text: str) -> str:
    r"""修复 array 环境的边界符错误
    
    🆕 v1.6 P0 修复：修正 \right.\\) → \right.\)
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




def fix_broken_set_definitions(text: str) -> str:
    r"""修复被 $$ 截断的集合定义 (P0-001)
    
    检测模式：\right.\ $$中文$$\left. \
    替换为：\right.\text{中文}\left.
    
    示例：
        输入：\right.\ $$是质数$$\left. \
        输出：\right.\text{ 是质数 }\left.
    """
    import re
    
    if not text:
        return text
    
    # 模式1: \right.\ $$中文$$\left. \（集合条件被截断）
    pattern1 = re.compile(
        r'(\\right\.)\s*\\\s*\$\$([^$]+)\$\$\s*\\left\.\s*\\',
        re.DOTALL
    )
    text = pattern1.sub(r'\1\\text{\2}\\left.', text)
    
    # 模式2: \right.\ $$中文（行尾截断）
    # 🔧 v1.9.5：增加限制条件，避免匹配 \right.\ $$，\n 这种标点后换行的模式
    # 要求中文内容至少包含一个中文字符，而不仅仅是标点
    pattern2 = re.compile(
        r'(\\right\.)\s*\\\s*\$\$([\u4e00-\u9fff][^$]*)$',
        re.MULTILINE
    )
    text = pattern2.sub(r'\1\\text{\2}', text)
    
    # 模式3: $$或$$\left. \（"或"字被分离）
    pattern3 = re.compile(
        r'\$\$(或|且|和|即)\$\$\\left\.\s*\\',
        re.DOTALL
    )
    text = pattern3.sub(r'\\text{ \1 }\\left.', text)
    
    return text




def fix_ocr_specific_errors(text: str) -> str:
    r"""修复 OCR 特有的识别错误 (P1-005)
    
    处理：
    1. 移除 \boxed{}，保留内容
    2. 清理连续空格转义 \  \  \ 
    3. 修复 \left| 为 \mid（在集合定义中）
    
    示例：
        输入：B = \left\{ \boxed{x} - 3 < x < 1 \right\}
        输出：B = \left\{ x \mid -3 < x < 1 \right\}
    """
    import re
    
    if not text:
        return text
    
    # 1. 移除 \boxed{}，保留内容
    text = re.sub(r'\\boxed\{([^}]*)\}', r'\1', text)
    
    # 2. 清理连续空格转义 \  \  \ 
    text = re.sub(r'(\\ ){2,}', r' ', text)
    
    # 3. 修复 \left| 为 \mid（在集合定义中）
    # 匹配 \left\{ ... \left| ... \right. ... \right\}
    def fix_set_bar(match):
        content = match.group(0)
        # 将集合条件中的 \left| 替换为 \mid
        content = re.sub(r'\\left\|', r'\\mid ', content)
        # 移除对应的 \right.（如果有）
        content = re.sub(r'\\mid\s*([^}]*?)\\right\.', r'\\mid \1', content)
        return content
    
    text = re.sub(
        r'\\left\\{[^}]*?\\left\|[^}]*?\\right\\}',
        fix_set_bar,
        text,
        flags=re.DOTALL
    )
    
    return text




def fix_right_boundary_errors(text: str) -> str:
    """修复 \\right. 边界错误 - 增强版
    
    处理以下畸形模式：
    1. \\right.\\ $$ → \\right.\\)  (反斜杠+空格+双美元)
    2. \\right.\\\\ $$ → \\right.\\)  (双反斜杠+双美元)
    3. \\right. $$ → \\right.\\)  (空格+双美元)
    4. \\right.中文 → \\right.\\)中文  (直接跟中文)
    """
    import re
    
    if not text:
        return text
    
    # 模式1: \right.\ $$ (反斜杠+空格+双美元) - 最常见的OCR错误
    text = re.sub(r'\\right\.\\\s\$\$', r'\\right.\\)', text)
    
    # 模式2: \right.\\ $$ (双反斜杠+可选空格+双美元)
    text = re.sub(r'\\right\.\\\\\s*\$\$', r'\\right.\\)', text)
    
    # 模式3: \right. $$ (一个或多个空格+双美元)
    text = re.sub(r'\\right\.\s+\$\$', r'\\right.\\)', text)
    
    # 模式4: \right.$$ (直接跟双美元，无空格)
    text = re.sub(r'\\right\.\$\$', r'\\right.\\)', text)
    
    # 模式5: \right. 后直接跟中文标点（缺少 \)）
    text = re.sub(r'(\\right\.)\s*([，。；：、！？])', r'\1\\)\2', text)
    
    # 模式6: \right. 后直接跟中文文字（缺少 \)）
    text = re.sub(r'(\\right\.)\s*([\u4e00-\u9fa5])', r'\1\\)\2', text)
    
    return text




def fix_unmatched_close_delimiters(text: str) -> str:
    r"""修复未匹配的闭合定界符 - 使用栈算法（跨行处理）

    🆕 v1.9.8: 重命名自 fix_reversed_delimiters，避免与类方法同名混淆

    检测没有匹配的 \) 并删除它们。

    🆕 v1.9.4: 改为全文跨行处理，而非逐行处理，以正确处理多行数学块如：
        联立\(\left\{ \begin{array}{r}
        x = my + \frac{3}{2} \\
        y^{2} = 6x
        \end{array} \right.\)

    逐行处理会错误地在第一行末尾添加 \)，因为该行的 \( 在后续行才闭合。
    """
    import re
    
    if not text:
        return text
    
    # 全文处理：使用栈检测不匹配的定界符
    stack = []  # 存储 \( 的位置
    unmatched_close = []  # 存储没有匹配的 \) 的位置
    
    # 找到所有定界符（排除注释行中的）
    lines = text.split('\n')
    comment_ranges = []  # 记录注释行的字符范围
    pos = 0
    for line in lines:
        if line.strip().startswith('%'):
            comment_ranges.append((pos, pos + len(line)))
        pos += len(line) + 1  # +1 for \n
    
    def is_in_comment(position):
        for start, end in comment_ranges:
            if start <= position < end:
                return True
        return False
    
    for m in re.finditer(r'\\\(|\\\)', text):
        if is_in_comment(m.start()):
            continue
        delim = m.group(0)
        pos = m.start()
        
        if delim == r'\(':
            stack.append(pos)
        else:  # \)
            if stack:
                stack.pop()  # 找到匹配
            else:
                unmatched_close.append(pos)  # 没有匹配的 \)
    
    # 如果存在不匹配的定界符，需要修复
    if not unmatched_close and not stack:
        return text  # 已经平衡，无需修改
    
    # 删除没有匹配的 \)（从后往前删除以保持位置正确）
    result = text
    if unmatched_close:
        text_chars = list(result)
        for pos in reversed(unmatched_close):
            # 删除 \) (两个字符)
            if pos + 1 < len(text_chars):
                del text_chars[pos:pos+2]
        result = ''.join(text_chars)

    # 如果仍有未匹配的 \(（开多闭少），追加对应数量的收尾 \)
    # 只在全文级别处理，避免逐行补齐带来的误修复
    if stack:
        extra_closes = []
        # 第一个直接补一个 \)
        extra_closes.append('\\)')
        # 其余的用注释分隔，避免出现 \)\) 被判定为“双重包裹”
        for _ in range(len(stack) - 1):
            extra_closes.append('% auto-close added by fix_unmatched_close_delimiters\n\\)')
        result = result + ''.join(extra_closes)

    return result




def balance_array_and_cases_env(text: str) -> str:
    """🆕 v1.8.6：后处理 - 删除明显多余的 \\end{array}/\\end{cases}

    只在没有匹配 \\begin 时丢弃 \\end，不自动生成新的 \\begin。
    使用栈匹配算法，确保 array/cases 环境平衡。

    示例：
        输入：\\end{array} \\right.\\)，则（无对应的 \\begin{array}）
        输出：\\right.\\)，则（丢弃多余的 \\end{array}）
    """
    if not text:
        return text

    pattern = re.compile(r'\\(begin|end)\{(array|cases)\}')
    out_parts = []
    stack = []
    last = 0

    for m in pattern.finditer(text):
        out_parts.append(text[last:m.start()])
        kind, env = m.group(1), m.group(2)
        token = m.group(0)

        if kind == 'begin':
            stack.append(env)
            out_parts.append(token)
        else:  # end
            if stack and env in stack:
                # 从栈尾找匹配的 begin
                idx = len(stack) - 1 - stack[::-1].index(env)
                stack.pop(idx)
                out_parts.append(token)
            else:
                # 没有匹配的 begin，说明是多余的 \end{env}，直接丢弃
                # 静默处理未匹配的 token
                pass

        last = m.end()

    out_parts.append(text[last:])
    return ''.join(out_parts)




def fix_trig_function_spacing(text: str) -> str:
    r"""🆕 v1.9.6：修复三角函数和对数函数后缺少空格的问题
    
    问题模式：
    - \sinx → \sin x
    - \cosB → \cos B
    - \lnt → \ln t
    - \sinwt → \sin(\omega t) 或 \sin wt（特殊处理 wt/ωt 格式）
    
    保守处理：只修复后面紧跟字母/变量的情况
    """
    import re
    
    # 定义需要处理的函数名
    trig_funcs = ['sin', 'cos', 'tan', 'cot', 'sec', 'csc', 'arcsin', 'arccos', 'arctan',
                  'sinh', 'cosh', 'tanh', 'ln', 'log', 'lg', 'exp']
    
    for func in trig_funcs:
        # 特殊处理：\sinwt, \coswt 等 → \sin(\omega t), \cos(\omega t)
        # 这是物理/信号处理中常见的表达式
        text = re.sub(rf'\\{func}wt\b', rf'\\{func}(\\omega t)', text)
        text = re.sub(rf'\\{func}ωt\b', rf'\\{func}(\\omega t)', text)
        
        # 匹配 \func 后紧跟字母（非 { 或空格的情况）
        # 例如 \sinx → \sin x, \cosB → \cos B
        # 只处理单个字母的情况，避免误改复杂表达式
        pattern = rf'\\{func}([A-Za-z])(?![a-zA-Z])'
        text = re.sub(pattern, rf'\\{func} \1', text)
    
    return text




def fix_greek_letter_spacing(text: str) -> str:
    r"""🆕 v1.9.9：修复希腊字母与变量连写问题
    
    问题来源：
    - OCR 或 Pandoc 将希腊字母与变量连写，如 \pir 应该是 \pi r
    - LaTeX 会将 \pir 解释为未定义的命令
    
    保守策略：
    - 只处理常见的希腊字母后直接跟小写英文字母的情况
    - 不处理 \alpha_1 等下标情况（这是正确的）
    - 仅添加空格分隔，不改变其他内容
    
    常见问题模式：
    - \pir → \pi r
    - \thetar → \theta r
    
    注意：这是保守修复，只处理明确的连写模式
    """
    import re
    
    # 🆕 v1.9.9: P2-10 补充完整希腊字母列表
    greek_letters = [
        # 小写希腊字母
        'alpha', 'beta', 'gamma', 'delta', 'epsilon', 'varepsilon',
        'zeta', 'eta', 'theta', 'vartheta', 'iota', 'kappa', 'varkappa',
        'lambda', 'mu', 'nu', 'xi', 'pi', 'varpi',
        'rho', 'varrho', 'sigma', 'varsigma', 'tau', 'upsilon',
        'phi', 'varphi', 'chi', 'psi', 'omega',
        # 大写希腊字母（LaTeX 中只有部分大写有专门命令）
        'Gamma', 'Delta', 'Theta', 'Lambda', 'Xi', 'Pi',
        'Sigma', 'Upsilon', 'Phi', 'Psi', 'Omega',
    ]
    
    for letter in greek_letters:
        # 模式：\greek + 小写字母（不是下标开头）
        # 例如：\pir → \pi r，但不改变 \pi_r 或 \pi{...}
        pattern = rf'(\\{letter})([a-z])(?![_{{])'
        text = re.sub(pattern, r'\1 \2', text)
    
    return text




def fix_bold_math_symbols(text: str) -> str:
    r"""🆕 v1.9.9：修复 Pandoc 粗体包裹数学符号的问题
    
    问题来源：
    - Word 中的粗体字母（如 **R** 表示实数集）
    - Pandoc 转换为 *\(R\)* 格式
    - 这在 LaTeX 中会导致渲染问题
    
    保守策略：
    - 只处理 *\(X\)* 格式，其中 X 是单个大写字母
    - 转换为 \(\mathbf{X}\)
    - 常见于数学集合符号：R（实数）、Z（整数）、N（自然数）等
    
    例如：
    - *\(R\)* → \(\mathbf{R}\)
    - *\(Z\)* → \(\mathbf{Z}\)
    """
    import re
    
    # 模式：*\(单个大写字母\)* → \(\mathbf{字母}\)
    # 只匹配单个大写字母，避免误伤其他粗体数学表达式
    text = re.sub(r'\*\\\(([A-Z])\\\)\*', r'\\(\\mathbf{\1}\\)', text)
    
    return text




def fix_overset_arrow_vectors(text: str) -> str:
    r"""🆕 v1.9.10：修复 \overset{arrow}{...} 向量符号错误
    
    问题来源：
    - Pandoc 或 OCR 将向量符号转换为 \overset{arrow}{a} 或 \overset{\rightarrow}{a}
    - 这不是有效的 LaTeX 命令，会导致编译失败
    
    保守策略：
    - 只处理明确的 \overset{arrow}{...} 和 \overset{\rightarrow}{...} 模式
    - 转换为标准的 \vec{...} 符号
    - 不影响其他 \overset 用法（如 \overset{def}{=}）
    
    常见问题模式：
    - \overset{arrow}{a} → \vec{a}
    - \overset{\rightarrow}{a} → \vec{a}
    - \overset{arrow}{AB} → \overrightarrow{AB}（多字符用 overrightarrow）
    
    注意：这是保守修复，只处理向量相关的 overset 模式
    """
    import re
    
    # 模式1：\overset{arrow}{单个字母} → \vec{字母}
    # 匹配 \overset{arrow}{a} 或 \overset{arrow}{x} 等单字符
    text = re.sub(
        r'\\overset\{arrow\}\{([a-zA-Z])\}',
        r'\\vec{\1}',
        text
    )
    
    # 模式2：\overset{\rightarrow}{单个字母} → \vec{字母}
    text = re.sub(
        r'\\overset\{\\rightarrow\}\{([a-zA-Z])\}',
        r'\\vec{\1}',
        text
    )
    
    # 模式3：\overset{arrow}{多字符} → \overrightarrow{多字符}
    # 匹配 \overset{arrow}{AB} 或 \overset{arrow}{PQ} 等多字符（2个或更多）
    text = re.sub(
        r'\\overset\{arrow\}\{([a-zA-Z_][a-zA-Z0-9_]+)\}',
        r'\\overrightarrow{\1}',
        text
    )
    
    # 模式4：\overset{\rightarrow}{多字符} → \overrightarrow{多字符}
    text = re.sub(
        r'\\overset\{\\rightarrow\}\{([a-zA-Z_][a-zA-Z0-9_]+)\}',
        r'\\overrightarrow{\1}',
        text
    )
    
    return text




def fix_specific_reversed_pairs(text: str) -> str:
    r"""🆕 v1.8.7：极窄自动修复特定反向数学定界符模式

    仅针对精确匹配的已知错误模式：
    - 模式 A: 求点\)X_{2}\(所有可能的坐标 → 求点\(X_{2}\)所有可能的坐标
    - 模式 B: 其中\)x_{i} → 其中 x_{i}（删除不匹配的 \)）

    安全性：只针对精确匹配的模式，不影响其他内容
    """
    if not text:
        return text

    # 模式 A: 求点\)X_{2}\(所有可能的坐标 → 求点\(X_{2}\)所有可能的坐标
    # 精确匹配：\) + 字母/数字/下划线 + \( → \( + 字母/数字/下划线 + \)
    pattern_a = re.compile(r'\\\)([A-Za-z0-9_{}]+)\\\(')
    text = pattern_a.sub(r'\(\1\)', text)

    # 模式 B: 其中\)x_{i} → 其中 x_{i}（删除不匹配的 \)）
    # 精确匹配：\) + 空格 + 字母/数字（行尾或后续无 \(）
    pattern_b = re.compile(r'\\\)\s+([a-z][a-z_0-9{}]*(?![^\n]*\\\())')
    text = pattern_b.sub(r' \1', text)

    return text




def fix_simple_reversed_inline_pairs(text: str) -> str:
    r"""🆕 v1.8.8 / v1.9.3：极度保守的反向定界符自动修复

    只修复真正的反向定界符：即 \) 之前没有匹配的 \(，且 \( 之后没有匹配的 \)。

    v1.9.3 修复：不再错误地合并两个独立的正确数学块，例如：
    - 正确保留：\(AP\bot AB\)，\(AP\bot AD\) （两个独立块，不应修改）
    - 仅修复真正反向的：求点\) X_2 \(所有可能 → 求点\( X_2 \)所有可能

    安全性：使用定界符平衡检查，确保只修复真正悬空的定界符对
    """
    if not text:
        return text

    import re

    # 逐行处理，避免跨行匹配带来的复杂性
    lines = text.split('\n')
    fixed_lines = []

    for line in lines:
        # 跳过注释行
        if line.strip().startswith('%'):
            fixed_lines.append(line)
            continue

        # 🆕 v1.9.5：跳过多行数学块的中间行
        # 如果行包含 \begin{array/cases 或 \end{array/cases}，说明是多行块的一部分
        # 这些行的定界符可能是跨行配对的，不应该按单行处理
        if re.search(r'\\begin\{(array|cases|matrix|pmatrix|bmatrix|vmatrix)', line) or \
           re.search(r'\\end\{(array|cases|matrix|pmatrix|bmatrix|vmatrix)', line):
            fixed_lines.append(line)
            continue

        # 找到所有定界符的位置
        delimiters = []
        for m in re.finditer(r'\\\(|\\\)', line):
            delimiters.append((m.start(), m.group(0)))

        if len(delimiters) < 2:
            fixed_lines.append(line)
            continue

        # 使用栈算法找到真正悬空的 \) 和 \(
        stack = []  # 存储未匹配 \( 的索引
        unmatched_close_indices = []  # 存储悬空 \) 在 delimiters 中的索引
        unmatched_open_indices = []  # 存储悬空 \( 在 delimiters 中的索引

        for i, (pos, delim) in enumerate(delimiters):
            if delim == r'\(':
                stack.append(i)
            else:  # \)
                if stack:
                    stack.pop()  # 匹配成功
                else:
                    unmatched_close_indices.append(i)  # 悬空的 \)

        # 栈中剩余的是悬空的 \(
        unmatched_open_indices = stack

        # 只有当存在悬空的 \) 且紧随其后有悬空的 \( 时，才考虑修复
        # 找到 (悬空\), 悬空\() 配对
        pairs_to_fix = []
        for close_idx in unmatched_close_indices:
            # 找紧随其后的悬空 \(
            for open_idx in unmatched_open_indices:
                if open_idx > close_idx:
                    # 检查中间是否只有简单内容（标点、空白、简单字母数字）
                    close_pos = delimiters[close_idx][0]
                    open_pos = delimiters[open_idx][0]
                    middle = line[close_pos + 2:open_pos]  # 跳过 \) 的两个字符

                    # 允许空白、标点、简单字母数字和下划线（类似变量名）
                    # 但不允许复杂的 LaTeX 命令或嵌套定界符
                    if re.fullmatch(r'[\s.,，。；;:：、!?！？"""\'\'《》（）()…—\-A-Za-z0-9_{}]*', middle or ''):
                        pairs_to_fix.append((close_idx, open_idx, middle))
                        break  # 每个悬空 \) 只配对一个悬空 \(

        # 从后往前修复（保持位置正确）
        line_chars = list(line)
        for close_idx, open_idx, middle in reversed(pairs_to_fix):
            close_pos = delimiters[close_idx][0]
            open_pos = delimiters[open_idx][0]
            # 替换 \) 为 \(
            line_chars[close_pos:close_pos + 2] = list(r'\(')
            # 替换 \( 为 \)（注意：由于前面的替换，长度不变）
            line_chars[open_pos:open_pos + 2] = list(r'\)')

        fixed_lines.append(''.join(line_chars))

    return '\n'.join(fixed_lines)




def collect_reversed_math_samples(text: str, slug: str = "") -> None:
    r"""🆕 v1.8.8 / v1.9.9：检测并记录反向数学定界符案例（只记录，不修改）

    🆕 v1.9.9: P1-7 修复误报问题
    - 使用栈算法检测真正的反向定界符
    - 正常的 \(A\)，\(B\) 模式不再被误报
    - 只检测悬空的 \) 后紧跟悬空的 \( 的情况

    Args:
        text: 完整的 TeX 文本
        slug: 试卷 slug（用于日志文件名）
    """
    if not text or not slug:
        return

    import re

    lines = text.splitlines()
    reversed_cases = []

    for line_num, line in enumerate(lines, start=1):
        # 只考虑注释前的部分
        content = line.split('%', 1)[0]
        if not content.strip():
            continue

        # 🆕 v1.9.9: 使用栈算法检测真正的反向定界符
        # 找到所有定界符位置
        delimiters = []
        for m in re.finditer(r'\\\(|\\\)', content):
            delimiters.append((m.start(), m.group(0)))

        if len(delimiters) < 2:
            continue

        # 使用栈找到未匹配的定界符
        stack = []
        unmatched_close = []  # 悬空的 \) 索引

        for idx, (pos, delim) in enumerate(delimiters):
            if delim == r'\(':
                stack.append(idx)
            else:  # \)
                if stack:
                    stack.pop()
                else:
                    unmatched_close.append(idx)

        unmatched_open = stack  # 剩余未匹配的 \(

        # 检查是否有悬空的 \) 后面紧跟悬空的 \(（真正的反向定界符）
        for close_idx in unmatched_close:
            for open_idx in unmatched_open:
                if open_idx > close_idx:
                    close_pos = delimiters[close_idx][0]
                    open_pos = delimiters[open_idx][0]
                    between = content[close_pos+2:open_pos]
                    # 只有中间是标点/空白时才认为是反向定界符
                    if re.match(r'^[\s，。；：、！？\s]*$', between):
                        line_display = line[:100] + '...' if len(line) > 100 else line
                        reversed_cases.append(
                            f"Line {line_num}: Found reversed inline math \\)...\\("
                            f"\n  Between content: '{between}'"
                            f"\n  Line: {line_display}"
                        )
                    break

    # 如果找到反向定界符，记录到日志
    if reversed_cases:
        from pathlib import Path
        debug_dir = Path("word_to_tex/output/debug")
        debug_dir.mkdir(parents=True, exist_ok=True)
        log_file = debug_dir / f"{slug}_reversed_delimiters.log"

        with log_file.open("w", encoding="utf-8") as f:
            f.write(f"# Reversed Math Delimiters Detection Log for {slug}\n")
            f.write(f"# Total cases found: {len(reversed_cases)}\n")
            f.write(f"# Generated: {Path(__file__).name}\n")
            f.write("\n")

            for i, case in enumerate(reversed_cases, start=1):
                f.write(f"{'='*80}\n")
                f.write(f"Case #{i}:\n")
                f.write(case + "\n\n")

        # 静默记录到日志文件





# ============================================================
# 导出列表
# ============================================================

__all__ = [
    'CHINESE_MATH_SEPARATORS',
    'TokenType',
    'MathStateMachine',
    'math_sm',
    'fix_array_boundaries',
    'fix_broken_set_definitions',
    'fix_ocr_specific_errors',
    'fix_right_boundary_errors',
    'fix_unmatched_close_delimiters',
    'balance_array_and_cases_env',
    'fix_trig_function_spacing',
    'fix_greek_letter_spacing',
    'fix_bold_math_symbols',
    'fix_overset_arrow_vectors',
    'fix_specific_reversed_pairs',
    'fix_simple_reversed_inline_pairs',
    'collect_reversed_math_samples',
]
