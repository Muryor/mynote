#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
ocr_to_examx_v1.9.py - v1.9.3 改进版

🆕 v1.9.3 黑箱测试修复（2025-01-XX）：
1. ✅ 修复 T008/T017 根本原因：preprocess_multiline_math 错误合并
   - 问题：$$P$$，$$B$$ 错误合并为 $$P，B$$，导致嵌套定界符
   - 修复：只对冒号（：）分隔的模式进行合并（标签：公式）
   - 移除：逗号（，）、顿号（、）、句号（。）、分号（；）分隔的合并
   - 结果：$$P$$，$$B$$ → \(P\)，\(B\)（正确保持独立）

🆕 v1.9.2 黑箱测试修复（2025-11-28）：
1. ✅ 修复 T008 定界符不平衡问题（P0 - 最高优先级）
   - 问题：跨行数学环境（array/cases）导致定界符不平衡
   - 修复：增强 balance_delimiters() 支持跨行环境检测
   - 修复：处理 \therefore \( 等符号后直接跟数学模式的情况
   - 改进：全局平衡检查和智能修复
2. ✅ 修复 T016 LaTeX 特殊字符转义问题（P2）
   - 问题：& 等字符在非数学模式下未正确转义
   - 修复：增强 escape_latex_special() 保护数学模式内的 &
   - 改进：正确处理 tabular/array/matrix 环境中的列分隔符
3. ✅ 修复 T017 数学模式内中文标点问题（P2）
   - 问题：数学模式内残留全角标点（逗号、分号等）
   - 修复：增强 normalize_punctuation_in_math() 迭代处理
   - 新增：额外的遗漏标点检测和转换逻辑

🆕 v1.9.1 关键修复（2025-11-26）：
1. ✅ 修复反向定界符 - 冒号模式（P0 - 最高优先级）
   - 问题：\)：公式\( 模式导致 160 个反向定界符案例
   - 修复：增强 fix_reversed_delimiters() 检测冒号后的公式缺少 \(
   - 模式：\)：\sqrt{3}x - y = 0\) → \)：\(\sqrt{3}x - y = 0\)
   - 改进：智能判断数学内容，避免误修复
2. ✅ 清理 \right. 后的异常字符（P0）
   - 问题：\right.\ 和 \right.\\ 模式导致定界符不平衡
   - 修复：增强 fix_right_boundary_errors() 预处理清理反斜杠异常
   - 模式：\right.\ ，\therefore → \right.\)，\therefore
   - 改进：减少定界符差值从 +25 到接近 0
3. ✅ 完善数学模式内中文标点转换（P1）
   - 问题：23 处中文标点残留在数学模式内
   - 修复：增强 normalize_punctuation_in_math() 添加完整标点映射
   - 新增：顿号、冒号、句号、感叹号、问号等
   - 保护：\text{}, \mbox{}, \mathrm{}, \textbf{}, \textit{} 内的中文
4. ✅ 修复 tabular 环境缺失列格式（P1）
   - 问题：\begin{tabularend{center} 缺少列格式参数
   - 新增：fix_tabular_environments() 函数
   - 修复：自动推断列数并添加默认格式 {|c|c|...}
   - 改进：避免 LaTeX 编译错误
5. ✅ 清理 CONTEXT 注释污染（P1）
   - 问题：CONTEXT 包含 LaTeX 环境命令，长度超过 80 字符
   - 修复：增强 clean_context() 函数
   - 改进：最大长度从 50 增加到 80 字符
   - 清理：将 \begin{...} 和 \end{...} 替换为 [ENV_START/END]

🆕 v1.8.7 精准修复（2025-11-21）：
1. ✅ 数学定界符统计忽略注释（P0 - 最高优先级）
   - 问题：注释中的 \( / \) 被计入全局统计，造成虚假 diff
   - 修复：validate_math_integrity() 按行扫描，先去掉 % 注释再统计
   - 改进：统计更加真实，不受注释行干扰
2. ✅ 检测反向数学定界符模式（P1）
   - 问题：\) 在 \( 前面的行难以定位
   - 新增：行级检测逻辑，找出 idx_close < idx_open 的行
   - 输出：行号 + 行内容片段，方便人工审查
3. ✅ 极窄自动修复特定反向模式（P1）
   - 新增：fix_specific_reversed_pairs() 函数
   - 模式 A：求点\)X_{2}\(所有可能的坐标 → 求点\(X_{2}\)所有可能的坐标
   - 模式 B：其中\)x_{i} → 其中 x_{i}（删除不匹配的 \)）
   - 安全性：只针对精确匹配的模式，不影响其他内容

🆕 v1.8.6 关键修复（2025-11-21）：
1. ✅ 收紧 fix_right_boundary_errors 行为（P0 - 最高优先级）
   - 问题：旧版无条件补 \)，导致全局 \( / \) diff 长期维持在 -18
   - 修复：按逐字符扫描，仅在行内存在未闭合 \( 时才补 \)
   - 新增：has_unmatched_open() 辅助函数判断行内平衡
   - 保留：模式3（\right.，则\) → \right.\)，则）只调整顺序，不改变数量
2. ✅ 新增 balance_array_and_cases_env 后处理（P0）
   - 问题：array/cases 环境不平衡，多出 1 个 \end{array} / \end{cases}
   - 修复：使用栈匹配算法，删除没有匹配 \begin 的 \end
   - 不自动生成新的 \begin，只删除多余的 \end
3. ✅ 新增 validate_brace_balance 全局花括号检查（P1）
   - 问题：Line 555 有多余的 }，不利于快速定位
   - 新增：按行扫描，忽略注释和转义的 \{ \}
   - 输出：行号 + 错误类型（balance went negative / EOF imbalance）
   - 不自动修复，仅输出日志方便人工定位
4. ✅ 增强 validate_math_integrity 日志（P1）
   - 新增：优先输出包含 \right.、array、cases、题号标记的样本
   - 新增：_has_priority_keywords() 检测关键词
   - 新增：_get_line_number() 输出行号
   - 改进：样本格式为 "Line X: ..." 方便定位
5. ✅ 增强题干缺失检测日志（P1）
   - 新增：输出题型、题号、原始 Markdown 片段（前 3 行）
   - 改进：多行格式化输出，方便人工回看 Markdown
   - 保留：现有 _is_likely_stem 启发式逻辑

🆕 v1.8.5 关键修复（2025-11-21）：
1. ✅ 增强 \right. 边界检测（P0 - 最高优先级）
   - 新增：检测 \right. 后的单美元符号 $
   - 新增：检测 \right. 后直接跟中文标点（，。；：等）
   - 新增：智能判断 \right.\) 已正确闭合的情况
   - 修复：8个题目中的 \right. 边界错误
2. ✅ 后处理修复 \right. 边界错误（P0 - 兜底方案）
   - 新增：fix_right_boundary_errors() 函数
   - 修复：\right. 后直接跟中文标点（缺少 \)）
   - 修复：array/cases 环境后的 \right. 边界错误
   - 修复：\right.，则\) 模式（\) 位置错误）
3. ✅ IMAGE_TODO 块格式验证和修复（P0）
   - 新增：validate_and_fix_image_todo_blocks() 函数
   - 修复：IMAGE_TODO_END 后的多余花括号
   - 修复：IMAGE_TODO_START 行末的多余字符
   - 自动检测并报告格式错误
4. ✅ 增强题干识别规则（P1）
   - 新增：题型判断（解答题/选择题/填空题）
   - 新增：动态调整长度阈值和关键词
   - 新增：关键词检查（已知、设、如图、证明等）
   - 改进：综合判断逻辑（题型 + 关键词 + 长度）
   - 新增：从 \section 命令推断题型

🆕 v1.8.4 重要修复（2025-11-21）：
1. ✅ 修复合并题目结构问题：题干 vs 小问识别（P0）
   - 问题：相同题号合并后，所有部分都显示为 \item
   - 修复：第一个 \item 转为题干，后续包裹在 enumerate 中
   - 新增：fix_merged_questions_structure 后处理函数
2. ✅ 增强题干识别逻辑（P1）
   - 新增：_is_likely_stem 启发式判断函数
   - 检测：字数、小问标记（①②③、(1)(2)等）、后续内容
   - 避免：误将真实小问识别为题干
3. ✅ 修复 IMAGE_TODO 路径转义问题（P0）
   - 问题：路径中的下划线导致 LaTeX 编译错误
   - 修复：自动转义 _ 为 \_

🆕 v1.8 P0/P1 修复（2025-11-20）：
1. ✅ 修复数学模式边界解析错误：\right.\ $$ → \right.\) （P0）
   - 修复分段函数/矩阵后紧跟文本时的数学模式闭合问题
   - 避免中文文本被错误地放入数学模式
2. ✅ 增强题干缺失检测：自动插入 TODO 注释（P1）
   - 检测直接从 \item 开始的题目
   - 在 \begin{question} 后自动添加警告注释

v1.7 改进（2025-11-20）：
1. ✅ 题干检测与警告：检测缺少题干的题目（直接从 \item 开始）
2. ✅ 清理 Markdown 图片属性残留：删除 height="..." 和 width="..." 残留
3. ✅ 小问编号格式统一：不自动添加 \mathrm，使用普通文本
4. ✅ IMAGE_TODO 块后不添加空行：优化格式
5. ✅ \explain 中的空行自动处理：空行替换为 \par

v1.6 P0 修复（2025-11-19）：
1. ✅ 修复数组环境闭合错误（\right.\\) → \right.\)）
2. ✅ 清理图片属性残留（{width="..." height="..."}）

版本：v1.9.1
日期：2025-11-26
"""

import re
import argparse
import shutil
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from enum import Enum, auto  # 引入枚举支持（状态机需要）

# ==================== 数学状态机（来自 ocr_to_examx_complete.py） ====================
# 注意：此状态机完全取代原先基于正则的 smart_inline_math / sanitize_math 等管线。
# 旧函数保留但标记为 DEPRECATED，主流程不再调用，避免相互干扰。

# 应该从数学模式移出的中文词汇
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
            # Extract just the \left...\right. part
            content = re.search(r'\\left.*?\\right(?:\\[\}\]\)])?\.?', match.group(0), re.DOTALL)
            return r'\(' + content.group(0) + r'\)'

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
        """修复格式错误的数学模式（增强版 v1.9.2）
        
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
        text = re.sub(r'\\\)\(\\\(', ')(', text)
        
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
        }

        def replace_in_math(match):
            content = match.group(1)
            # 不处理 \text{}, \mbox{}, \mathrm{} 内的内容
            protected = []
            def save_text(m):
                protected.append(m.group(0))
                return f"@@TEXT_{len(protected)-1}@@"

            # 保护各种文本命令
            content = re.sub(r'\\text\{[^}]*\}', save_text, content)
            content = re.sub(r'\\mbox\{[^}]*\}', save_text, content)
            content = re.sub(r'\\mathrm\{[^}]*\}', save_text, content)
            content = re.sub(r'\\textbf\{[^}]*\}', save_text, content)
            content = re.sub(r'\\textit\{[^}]*\}', save_text, content)

            # 替换全角标点
            for full, half in punct_map.items():
                content = content.replace(full, half)

            # 恢复保护的内容
            for i, p in enumerate(protected):
                content = content.replace(f"@@TEXT_{i}@@", p)

            return r'\(' + content + r'\)'
        
        # 处理 \(...\) 内的标点（使用更宽松的匹配，支持嵌套括号）
        def replace_in_math_v2(match):
            content = match.group(1)
            # 不处理 \text{}, \mbox{}, \mathrm{} 内的内容
            protected = []
            def save_text(m):
                protected.append(m.group(0))
                return f"@@TEXT_{len(protected)-1}@@"

            # 保护各种文本命令
            content = re.sub(r'\\text\{[^}]*\}', save_text, content)
            content = re.sub(r'\\mbox\{[^}]*\}', save_text, content)
            content = re.sub(r'\\mathrm\{[^}]*\}', save_text, content)
            content = re.sub(r'\\textbf\{[^}]*\}', save_text, content)
            content = re.sub(r'\\textit\{[^}]*\}', save_text, content)

            # 替换全角标点
            for full, half in punct_map.items():
                content = content.replace(full, half)

            # 恢复保护的内容
            for i, p in enumerate(protected):
                content = content.replace(f"@@TEXT_{i}@@", p)

            return r'\(' + content + r'\)'
        
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
                    
                    while j < n - 1 and depth > 0:
                        if text[j:j+2] == r'\(':
                            depth += 1
                            j += 2
                        elif text[j:j+2] == r'\)':
                            depth -= 1
                            if depth == 0:
                                break
                            j += 2
                        else:
                            j += 1
                    
                    if depth == 0:
                        # 成功匹配，处理内容
                        math_content = text[start+2:j]
                        
                        # 保护 \text{} 等
                        protected = []
                        def save_text(m):
                            protected.append(m.group(0))
                            return f"@@TEXT_{len(protected)-1}@@"
                        
                        processed = re.sub(r'\\text\{[^}]*\}', save_text, math_content)
                        processed = re.sub(r'\\mbox\{[^}]*\}', save_text, processed)
                        processed = re.sub(r'\\mathrm\{[^}]*\}', save_text, processed)
                        
                        # 替换全角标点
                        for full, half in punct_map.items():
                            processed = processed.replace(full, half)
                        
                        # 恢复保护的内容
                        for idx, p in enumerate(protected):
                            processed = processed.replace(f"@@TEXT_{idx}@@", p)
                        
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
        """平衡数学定界符（增强版 v1.9.3）
        
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
            if in_multiline_math and re.search(r'\\end\{(array|cases|matrix|pmatrix|bmatrix)\}', line):
                # 检查这行是否有 \)
                if not re.search(r'\\\)', line):
                    # 在 \right. 或行尾添加 \)
                    if r'\right.' in line:
                        line = line.replace(r'\right.', r'\right.\)')
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
            print(f"⚠️ 警告：定界符不平衡！\\( = {open_count}, \\) = {close_count}, diff = {diff}")
            
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
            
            # 重新验证
            new_open = len(re.findall(r'\\\(', text))
            new_close = len(re.findall(r'\\\)', text))
            if new_open != new_close:
                print(f"⚠️ 自动修复后仍不平衡：\\( = {new_open}, \\) = {new_close}")
            else:
                print(f"✅ 定界符已自动平衡：\\( = {new_open}, \\) = {new_close}")
        
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


# ==================== 配置 ====================

VERSION = "v1.9.6"

SECTION_MAP = {
    "一、单选题": "单选题",
    "二、单选题": "单选题",
    "二、多选题": "多选题",
    "三、填空题": "填空题",
    "四、解答题": "解答题",
}

META_PATTERNS = {
    "answer": r"^【答案】(.*)$",
    "difficulty": r"^【难度】([\d.]+)",
    "topics": r"^【知识点】(.*)$",
    "analysis": r"^【分析】(.*)$",
    "explain": r"^【详解】(.*)$",
    "diangjing": r"^【点睛】(.*)$",
    "dianjing_alt": r"^【点评】(.*)$",
}

# 🆕 扩展图片检测：支持绝对路径、相对路径、多行属性块
# 匹配两种形式：
#   1) 带ID: ![@@@id](path){...}
#   2) 无ID: ![](path){...}
# 属性块可跨多行，可选
IMAGE_PATTERN_WITH_ID = re.compile(
    r"!\[@@@([^\]]+)\]\(([^)]+)\)(?:\s*\{[^}]*\})?",
    re.MULTILINE | re.DOTALL,
)
IMAGE_PATTERN_NO_ID = re.compile(
    r"!\[\]\(([^)]+)\)(?:\s*\{[^}]*\})?",
    re.MULTILINE | re.DOTALL,
)
# 兼容旧版（保留用于简单场景）
IMAGE_PATTERN = re.compile(r"!\[\]\((images/[^)]+)\)(?:\{width=(\d+)%\})?")

LATEX_SPECIAL_CHARS = {
    "%": r"\%",
    "&": r"\&",
    "#": r"\#",
    "~": r"\textasciitilde{}",
}

# 解析标记词（扩展列表）
ANALYSIS_MARKERS = [
    '根据', '由题意', '因为', '所以', '故选', '答案',
    '分析', '详解', '解答', '证明', '计算可得',
    '显然', '易知', '可知', '不难看出', '由此可得',
    '综上', '故', '即', '则', '可得'
]


# 更严格的解析起始词，只用于判断是否进入解析段落（避免像“则”这样在题干中出现时被误判）
ANALYSIS_START_MARKERS = [
    '根据', '由题意', '因为', '所以', '故选', '答案',
    '分析', '详解', '解答', '证明', '计算可得',
    '显然', '易知', '可知', '不难看出', '由此可得', '综上'
]

# ==================== 文件夹处理函数 ====================

def infer_figures_dir(input_md: str) -> str:
    """根据 Markdown 文件名推断图片目录

    推断规则：
    1. 提取 md_path.stem 作为 prefix
    2. 去除常见后缀（_local, _preprocessed, _raw）
    3. 按顺序尝试以下候选目录：
       - word_to_tex/output/figures/{prefix}
       - word_to_tex/output/figures/{prefix}/media
    4. 返回第一个存在的目录，都不存在则返回空字符串

    Args:
        input_md: Markdown 文件路径

    Returns:
        推断出的图片目录路径，或空字符串
    """
    md_path = Path(input_md)

    # 提取文件名前缀（去除后缀）
    prefix = md_path.stem

    # 去除常见的 Markdown 文件后缀
    for suffix in ['_local', '_preprocessed', '_raw']:
        if prefix.endswith(suffix):
            prefix = prefix[:-len(suffix)]
            break

    # 候选目录列表（按优先级排序）
    candidates = [
        Path("word_to_tex/output/figures") / prefix,
        Path("word_to_tex/output/figures") / prefix / "media",
    ]

    # 返回第一个存在的目录
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return str(candidate)

    # 都不存在则返回空字符串
    return ""


def detect_images_for_markdown(md_file: Path) -> Optional[Path]:
    """根据 markdown 文件推断图片目录"""
    parent = md_file.parent
    candidates: List[Path] = []

    # 常规：同级 images 目录
    candidates.append(parent / 'images')

    slug = None
    slug_match = re.match(r'(.+?)_(?:preprocessed|raw|local)\.md$', md_file.name)
    if slug_match:
        slug = slug_match.group(1)
    elif md_file.suffix == '.md':
        slug = md_file.stem

    figures_root = parent / 'figures'
    if slug:
        candidates.append(figures_root / slug / 'media')
        candidates.append(figures_root / slug)
    candidates.append(figures_root / 'media')
    candidates.append(figures_root)

    for cand in candidates:
        if cand.exists():
            return cand

    if slug and figures_root.exists():
        for cand in figures_root.glob(f"**/{slug}*"):
            media_dir = cand / 'media'
            if media_dir.exists():
                return media_dir
            if cand.is_dir():
                return cand

    return None


def find_markdown_and_images(input_path: Path) -> Tuple[Path, Optional[Path]]:
    """智能识别输入路径"""
    input_path = Path(input_path).resolve()
    
    if input_path.is_file() and input_path.suffix == '.md':
        md_file = input_path
        return md_file, detect_images_for_markdown(md_file)
    
    if input_path.is_dir():
        md_files = list(input_path.glob('*_local.md'))
        if not md_files:
            md_files = list(input_path.glob('*.md'))
        
        if not md_files:
            raise FileNotFoundError(f"在 {input_path} 中未找到 .md 文件")
        
        if len(md_files) > 1:
            print(f"⚠️  找到多个 .md 文件，使用：{md_files[0].name}")
        
        md_file = md_files[0]
        images_dir = detect_images_for_markdown(md_file)
        return md_file, images_dir
    
    raise ValueError(f"无效的输入：{input_path}")


def copy_images_to_output(images_dir: Path, output_dir: Path) -> int:
    """复制图片"""
    if images_dir is None or not images_dir.exists():
        return 0
    
    output_images_dir = output_dir / 'images'
    if output_images_dir.exists():
        shutil.rmtree(output_images_dir)
    
    shutil.copytree(images_dir, output_images_dir)
    return len(list(output_images_dir.glob('*')))


# ==================== LaTeX 处理函数 ====================

def escape_latex_special(text: str, in_math_mode: bool = False) -> str:
    """转义 LaTeX 特殊字符（增强版 v1.9.2）
    
    🆕 v1.9.2 改进:
    1. 正确保护数学模式内的 & （用于 matrix/array 列分隔）
    2. 保护已转义的字符（\&, \%, \#）
    3. 保护 LaTeX 命令（\text{}, \left, \right 等）
    """
    if not text:
        return text
        
    # 保护已经转义的字符
    protected_escaped = []
    def save_escaped(match):
        protected_escaped.append(match.group(0))
        return f"@@ESCAPED_{len(protected_escaped)-1}@@"
    
    # 保护已转义的特殊字符
    text = re.sub(r'\\[%&#~]', save_escaped, text)
    
    if in_math_mode:
        # 在数学模式内，不转义 &（用于 array/matrix 列分隔）
        for char in ["%", "#", "~"]:
            if char in LATEX_SPECIAL_CHARS:
                text = text.replace(char, LATEX_SPECIAL_CHARS[char])
    else:
        # 保护注释
        protected_comments = []
        def save_comment(match):
            protected_comments.append(match.group(0))
            return f"@@COMMENT_{len(protected_comments)-1}@@"
        text = re.sub(r'%.*$', save_comment, text, flags=re.MULTILINE)
        
        # 保护数学模式内的 &（用于 array/matrix/tabular）
        protected_math = []
        def save_math(match):
            protected_math.append(match.group(0))
            return f"@@MATH_{len(protected_math)-1}@@"
        
        # 保护 \(...\) 和 \[...\] 内的内容
        text = re.sub(r'\\\([^)]*\\\)', save_math, text, flags=re.DOTALL)
        text = re.sub(r'\\\[[^\]]*\\\]', save_math, text, flags=re.DOTALL)
        
        # 保护 tabular/array/matrix 环境
        text = re.sub(r'\\begin\{(tabular|array|matrix|pmatrix|bmatrix|vmatrix|cases)\}.*?\\end\{\1\}', 
                       save_math, text, flags=re.DOTALL)
        
        # 转义特殊字符
        for char, escaped in LATEX_SPECIAL_CHARS.items():
            text = text.replace(char, escaped)
        
        # 恢复保护的数学模式
        for i, math_block in enumerate(protected_math):
            text = text.replace(f"@@MATH_{i}@@", math_block)
        
        # 恢复保护的注释
        for i, comment in enumerate(protected_comments):
            text = text.replace(f"@@COMMENT_{i}@@", comment)
    
    # 恢复保护的已转义字符
    for i, escaped in enumerate(protected_escaped):
        text = text.replace(f"@@ESCAPED_{i}@@", escaped)
    
    # 清理可能的异常模式
    text = re.sub(r'\\\)([\u4e00-\u9fa5]{1,3})\\\(', r'\1', text)

    # 统一常见数学符号的排版
    text = standardize_math_symbols(text)
    
    return text


def standardize_math_symbols(text: str) -> str:
    r"""标准化数学符号（虚数单位/圆周率/自然底数等）

    修复 P2-001: 处理 \text{数字}、\text{数字π} 等模式
    🆕 P1-001: 添加数学函数和数集符号的标准化
    """
    if not text:
        return text

    # 🆕 P1-001: 数学函数替换 (\text{sin} → \sin)
    math_func_replacements = [
        (r'\\text\{\s*sin\s*\}', r'\\sin'),
        (r'\\text\{\s*cos\s*\}', r'\\cos'),
        (r'\\text\{\s*tan\s*\}', r'\\tan'),
        (r'\\text\{\s*cot\s*\}', r'\\cot'),
        (r'\\text\{\s*sec\s*\}', r'\\sec'),
        (r'\\text\{\s*csc\s*\}', r'\\csc'),
        (r'\\text\{\s*ln\s*\}', r'\\ln'),
        (r'\\text\{\s*log\s*\}', r'\\log'),
        (r'\\text\{\s*lg\s*\}', r'\\lg'),
        (r'\\text\{\s*lim\s*\}', r'\\lim'),
        (r'\\text\{\s*max\s*\}', r'\\max'),
        (r'\\text\{\s*min\s*\}', r'\\min'),
        (r'\\text\{\s*exp\s*\}', r'\\exp'),
        (r'\\text\{\s*arcsin\s*\}', r'\\arcsin'),
        (r'\\text\{\s*arccos\s*\}', r'\\arccos'),
        (r'\\text\{\s*arctan\s*\}', r'\\arctan'),
    ]
    
    for pattern, replacement in math_func_replacements:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # 🆕 P1-001: 数集符号替换 (\text{N} → \mathbb{N})
    number_set_replacements = [
        (r'\\text\{\s*N\s*\}', r'\\mathbb{N}'),
        (r'\\text\{\s*Z\s*\}', r'\\mathbb{Z}'),
        (r'\\text\{\s*Q\s*\}', r'\\mathbb{Q}'),
        (r'\\text\{\s*R\s*\}', r'\\mathbb{R}'),
        (r'\\text\{\s*C\s*\}', r'\\mathbb{C}'),
    ]
    
    for pattern, replacement in number_set_replacements:
        text = re.sub(pattern, replacement, text)

    # 虚数单位 - 保持 \text{i} 格式与范本一致
    # 注释掉以下转换，保留原始 \text{i} 格式
    # text = re.sub(r'\\text\{\s*i\s*\}', r'\\mathrm{i}', text)
    # text = re.sub(r'\\text\{\s*-\s*i\s*\}', r'-\\mathrm{i}', text)

    # 🆕 P2-001: 处理 \text{数字π} 或 \text{数字\pi}（必须在 \text{数字} 之前）
    text = re.sub(r'\\text\{(\d+)π\}', r'\1\\pi', text)
    text = re.sub(r'\\text\{(\d+)\\pi\}', r'\1\\pi', text)

    # 🆕 P2-001: 处理 \text{π数字} 或 \text{\pi数字}
    text = re.sub(r'\\text\{π(\d+)\}', r'\\pi\1', text)
    text = re.sub(r'\\text\{\\pi(\d+)\}', r'\\pi\1', text)

    # 🆕 P2-001: 处理 \text{数字}
    text = re.sub(r'\\text\{(\d+)\}', r'\1', text)

    # 圆周率
    text = re.sub(r'\\text\{\s*π\s*\}', r'\\pi', text)
    text = re.sub(r'(?<!\\)π', r'\\pi', text)

    # 自然对数底 e：仅在作为指数底数时替换
    text = re.sub(r'\\text\{\s*e\s*\}(?=\s*[\^_])', r'\\mathrm{e}', text)

    return text


# DEPRECATED: 已被 MathStateMachine 替换，保留以兼容旧测试；主流程不再调用
def smart_inline_math(text: str) -> str:
    r"""智能转换行内公式：$...$ -> \(...\)，$$...$$ -> \(...\)

    🆕 v1.5 改进：彻底避免双重包裹，examx 统一使用 \(...\)

    注意：所有 $$...$$ 显示公式都会被转换为行内 \(...\) 格式，
    这是为了与 examx 包的兼容性。如果需要真正的显示公式，
    应在后续手动调整为 \[...\] 格式。
    """
    if not text:
        return text
    
    # 步骤1: 保护已有的行内公式 \(...\)（避免重复转换）
    inline_math_blocks = []
    def save_inline(match):
        inline_math_blocks.append(match.group(0))
        return f"@@INLINEMATH{len(inline_math_blocks)-1}@@"
    text = re.sub(r'\\\((.+?)\\\)', save_inline, text, flags=re.DOTALL)
    
    # 步骤2: 保护已有的显示公式 \[...\]（保持不变）
    display_math_blocks = []
    def save_display(match):
        display_math_blocks.append(match.group(0))
        return f"@@DISPLAYMATH{len(display_math_blocks)-1}@@"
    text = re.sub(r'\\\[(.+?)\\\]', save_display, text, flags=re.DOTALL)
    
    # 步骤3: 保护TikZ坐标 $(A)$ 或 $(A)!0.5!(B)$ 或 $(A)+(1,2)$
    tikz_coords = []
    def save_tikz_coord(match):
        block = match.group(0)      # 形如 '$(A)!0.5!(B)$' 或 '$(0,1)$'
        inner = block[2:-2]         # 去掉外层 '$(' 和 ')$'
        # 仅当内部包含 '!' 或 大写字母 时，认为是 TikZ 坐标表达式
        if '!' in inner or re.search(r'[A-Z]', inner):
            tikz_coords.append(block)
            return f"@@TIKZCOORD{len(tikz_coords)-1}@@"
        else:
            # 否则认为是普通数学坐标/区间，原样返回
            return block
    # 匹配 TikZ 坐标：$(...)$ 内部是简单的坐标计算表达式
    # 包含字母、数字、括号、加减乘除、点、感叹号、冒号等但不包含复杂数学
    text = re.sub(r'\$\([A-Za-z0-9!+\-*/\.\(\):,\s]+\)\$', save_tikz_coord, text)

    # 步骤3.5: 🆕 v1.8 修复 \right.\ $$ 边界问题
    # 将 \right.\ $$ 转换为 \right.\) （闭合当前数学模式）
    text = re.sub(r'\\right\.\\\s+\$\$', r'\\right.\\) ', text)

    # 步骤4: 转换显示公式 $$ ... $$ 为 \(...\)（examx 统一风格）
    # 注意：所有 $$...$$ 都转为行内格式，不生成 \[...\]
    text = re.sub(r'\$\$\s*(.+?)\s*\$\$', r'\\(\1\\)', text, flags=re.DOTALL)
    
    # 步骤5: 转换单 $ ... $ 为 \(...\)
    text = re.sub(r'(?<!\\)\$([^\$]+?)\$', r'\\(\1\\)', text)
    
    # 步骤6: 兜底检查，清理残留的单 $（单行内，限制200字符）
    text = re.sub(r'(?<!\\)\$([^\$\n]{1,200}?)\$', r'\\(\1\\)', text)
    
    # 步骤7: 恢复保护的内容
    for i, block in enumerate(tikz_coords):
        text = text.replace(f"@@TIKZCOORD{i}@@", block)
    for i, block in enumerate(display_math_blocks):
        text = text.replace(f"@@DISPLAYMATH{i}@@", block)
    for i, block in enumerate(inline_math_blocks):
        text = text.replace(f"@@INLINEMATH{i}@@", block)
    
    return text


# DEPRECATED: 已被 MathStateMachine 统一处理双重包裹
def fix_double_wrapped_math(text: str) -> str:
    r"""修正双重包裹的数学公式
    
    🆕 v1.6 增强：清理更多嵌套模式
    🆕 v1.5 新增：清理可能残留的嵌套格式
    例如：$$\(...\)$$ → \(...\)
    """
    if not text:
        return text
    
    # 修正 $$\(...\)$$ 或 $$\[...\]$$
    # 注意：\\\( 匹配字面的 \(
    text = re.sub(r'\$\$\s*\\\((.+?)\\\)\s*\$\$', r'\\(\1\\)', text, flags=re.DOTALL)
    text = re.sub(r'\$\$\s*\\\[(.+?)\\\]\s*\$\$', r'\\(\1\\)', text, flags=re.DOTALL)
    
    # 修正 $\(...\)$ 或 $\[...\]$
    text = re.sub(r'\$\s*\\\((.+?)\\\)\s*\$', r'\\(\1\\)', text, flags=re.DOTALL)
    text = re.sub(r'\$\s*\\\[(.+?)\\\]\s*\$', r'\\(\1\\)', text, flags=re.DOTALL)
    
    # 修正三重嵌套（极端情况）
    text = re.sub(r'\\\(\s*\\\((.+?)\\\)\s*\\\)', r'\\(\1\\)', text, flags=re.DOTALL)
    
    # 🆕 v1.6 P0 修复：清理 \because\(\) 或 \therefore\(\) 的空嵌套
    # 注意：替换后保留空格，避免与后续字母连接
    text = re.sub(r'\\because\s*\\\(\\\)\s*', r'\\because ', text)
    text = re.sub(r'\\therefore\s*\\\(\\\)\s*', r'\\therefore ', text)
    
    # 🆕 v1.6 P0 修复：清理 \(\because\(\) 或 \(\therefore\(\) 形式
    text = re.sub(r'\\\(\\because\s*\\\(\\\)\s*', r'\\(\\because ', text)
    text = re.sub(r'\\\(\\therefore\s*\\\(\\\)\s*', r'\\(\\therefore ', text)
    
    # 🆕 v1.6 P0 修复：清理独立的空括号 \(\)（可能出现在任何位置）
    text = re.sub(r'\\\(\s*\\\)', r'', text)
    
    # 🆕 v1.6 P0 修复：修正 \(...\(\)...\) 形式的嵌套（空占位符）
    # 迭代清理，最多3次
    for _ in range(3):
        before = text
        text = re.sub(r'\\\(([^)]*?)\\\(\\\)([^)]*?)\\\)', r'\\(\1\2\\)', text, flags=re.DOTALL)
        if text == before:
            break
    
    return text


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


def clean_image_attributes(text: str) -> str:
    r"""统一清理 Markdown 图片标记中的属性块（增强版 P2-001）
    
    支持：
    - 单行属性块：{width="3in" height="2in"}
    - 跨行属性块：{width="3in"\nheight="2in"}
    - 科学计数法尺寸：{width="1.38e-2in"}
    - 孤立的 width/height 行
    - 极小图片移除（OCR 噪声）
    """
    if not text:
        return text

    # 🆕 P1-004 修复：支持跨行属性块（使用 DOTALL 标志）
    # 匹配包含科学计数法的尺寸值，如 1.3888888888888888e-2in
    attr_pattern = re.compile(
        r'\{[^{}]*(?:width|height)\s*=\s*"[^"]*"[^{}]*\}',
        re.IGNORECASE | re.DOTALL
    )
    text = attr_pattern.sub('', text)

    # 🆕 P2-001: 清理孤立的 width="..." / height="..." 行
    text = re.sub(r'^\s*(width|height)="[^"]*"\s*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    
    # 🆕 P2-001: 清理跨行的属性块
    text = re.sub(r'\{width="[^"]*"\s*\n\s*height="[^"]*"\}', '', text, flags=re.MULTILINE)
    
    # 🆕 P2-001: 清理单行完整属性块
    text = re.sub(r'\{width="[^"]*"\s+height="[^"]*"\}', '', text)
    
    # 🆕 P2-001: 清理残留的 height="..." 和 width="..."（带可能的尾随 }）
    text = re.sub(r'height="[^"]*"[}]*', '', text)
    text = re.sub(r'width="[^"]*"[}]*', '', text)
    
    # 🆕 P2-001: 移除极小图片（尺寸使用科学计数法 e-2 或更小，可能是 OCR 噪声）
    tiny_pattern = re.compile(
        r'!\[[^\]]*\]\([^)]+\)\s*\{[^}]*?(?:\d+\.?\d*e-[2-9]|\d+\.?\d*e-\d{2,})in[^}]*\}',
        re.IGNORECASE | re.DOTALL
    )
    text = tiny_pattern.sub('', text)
    
    return text


def remove_decorative_images(text: str) -> str:
    """移除极小的装饰性图片（通常是 OCR 噪声）

    检测尺寸小于 0.1in 的图片，包括科学计数法格式如:
    - 1.3888888888888888e-2in (约 0.014in)
    - 1e-3in (0.001in)
    - 0.01in, 0.001in (常规小数格式)
    """
    if not text:
        return text

    # 🆕 P1-003 修复：匹配科学计数法格式的极小尺寸（e-2, e-3 或更小）
    # 支持文件首行、行中、行尾的图片标记
    tiny_sci_pattern = re.compile(
        r'!\[[^\]]*\]\([^)]+\)\{[^}]*?(?:\d+\.?\d*e-[2-9]|\d+\.?\d*e-\d{2,})in[^}]*\}',
        re.IGNORECASE | re.DOTALL,
    )
    text = tiny_sci_pattern.sub('', text)

    # 🆕 P1-003 修复：匹配常规小数格式的极小尺寸（0.0开头）
    tiny_decimal_pattern = re.compile(
        r'!\[[^\]]*\]\([^)]+\)\{[^}]*?0\.0\d+in[^}]*\}',
        re.IGNORECASE | re.DOTALL,
    )
    text = tiny_decimal_pattern.sub('', text)

    return text


def clean_residual_image_attrs(text: str) -> str:
    r"""清理残留的图片属性块

    🆕 v1.7 增强：清理更多 Markdown 图片属性残留
    🆕 v1.6 P0 修复：清理 Pandoc 生成的图片属性
    """
    if not text:
        return text

    text = clean_image_attributes(text)

    # 清理单独成行的属性块开始
    text = re.sub(r'^\s*\{width="[^"]*"\s*$', '', text, flags=re.MULTILINE)
    # 清理单独成行的属性块结束
    text = re.sub(r'^\s*height="[^"]*"\}\s*$', '', text, flags=re.MULTILINE)

    # 清理跨行的属性块
    text = re.sub(r'\{width="[^"]*"\s*\n\s*height="[^"]*"\}', '', text, flags=re.MULTILINE)

    # 清理单行完整属性块
    text = re.sub(r'\{width="[^"]*"\s+height="[^"]*"\}', '', text)

    # 🆕 v1.7：清理残留的 height="..." 和 width="..." （带可能的尾随 }）
    text = re.sub(r'height="[^"]*"[}]*', '', text)
    text = re.sub(r'width="[^"]*"[}]*', '', text)

    return text


# DEPRECATED: 状态机后不再需要变量自动包裹，可能导致过度包裹
def wrap_math_variables(text: str) -> str:
    """智能包裹数学变量（增强版）"""
    # 保护已有的数学模式
    protected = []
    def save_math(match):
        protected.append(match.group(0))
        return f"@@MATH{len(protected)-1}@@"
    
    text = re.sub(r'\\\(.*?\\\)', save_math, text, flags=re.DOTALL)
    text = re.sub(r'\\\[.*?\\\]', save_math, text, flags=re.DOTALL)
    
    # 保护 TikZ 坐标
    tikz_coords = []
    def save_tikz(match):
        block = match.group(0)      # 形如 '$(A)$' 或 '$(0,1)$'
        inner = block[2:-2]
        if '!' in inner or re.search(r'[A-Z]', inner):
            tikz_coords.append(block)
            return f"@@TIKZ{len(tikz_coords)-1}@@"
        else:
            return block
    text = re.sub(r'\$\([\d\w\s,+\-*/\.]+\)\$', save_tikz, text)
    
    # 规则1：单字母变量 + 运算符/下标/上标
    text = re.sub(
        r'\b([a-zA-Z])(?=\s*[=+\-*/^<>]|_{|\^{)',
        r'\\(\1\\)',
        text
    )
    
    # 规则2：数学函数必须有反斜杠
    math_functions = [
        'sin', 'cos', 'tan', 'cot', 'sec', 'csc',
        'arcsin', 'arccos', 'arctan',
        'sinh', 'cosh', 'tanh',
        'log', 'ln', 'lg', 'exp',
        'lim', 'sup', 'inf',
        'max', 'min', 'det', 'dim', 'ker'
    ]
    for func in math_functions:
        text = re.sub(rf'(?<!\\)\b{func}\b(?!\w)', rf'\\{func}', text)
    
    # 规则3：虚数单位 i（避免误转换罗马数字）
    # 只在明确的数学上下文中转换，避免 (i), (ii) 等罗马数字被转换
    # 匹配：独立的 i 后面跟着数学运算符或结束，但不在括号内
    text = re.sub(r'(?<!\\)(?<!\()\bi\b(?=[^a-zA-Z\)])', r'\\mathrm{i}', text)
    
    # 恢复保护的内容
    for i, coord in enumerate(tikz_coords):
        text = text.replace(f"@@TIKZ{i}@@", coord)
    for i, math in enumerate(protected):
        text = text.replace(f"@@MATH{i}@@", math)
    
    return text


def _fix_array_left_braces(block: str) -> str:
    r"""🆕 v1.8.9：在数学块内部，为典型的 array/cases 方程组尝试补全缺失的 \left\{（非常保守）
    
    启动条件（必须全部满足）：
    1. block 中包含 \begin{array} 或 \begin{cases}
    2. block 中包含 \right.（右侧已有右边界）
    3. block 中 \left 的个数少于 \right
    
    补全规则（保守启发式）：
    - 对每个 \begin{array} / \begin{cases}：
      - 检查其前方 50 个字符的上下文窗口
      - 如果窗口内没有 \left 或 \{，则插入 \left\{
      - 如果窗口内已有左边界，则不插入
    
    风险控制：
    - 宁可不修，不要误伤
    - 只在高置信度场景下补全
    - 保留原有降级逻辑作为兜底
    """
    if not block:
        return block
    
    # 启动条件检查（注意：block 中的反斜杠是单个 \，不是双反斜杠）
    has_array_or_cases = '\\begin{array}' in block or '\\begin{cases}' in block
    has_right_dot = '\\right.' in block
    
    if not has_array_or_cases or not has_right_dot:
        return block
    
    # 统计 left/right 数量，只有 right 偏多时才考虑补
    left_count = len(re.findall(r'\\left\b', block))
    right_count = len(re.findall(r'\\right\b', block))
    
    if left_count >= right_count:
        return block  # 不缺 left，不需要补
    
    # 对 \begin{array} 和 \begin{cases} 尝试补全
    # 使用回调函数检查上下文并决定是否插入
    def _insert_left_if_needed(m: re.Match) -> str:
        start = m.start()
        # 向前看 50 个字符作为上下文窗口
        prefix = block[:start]
        context = prefix[-50:] if len(prefix) > 50 else prefix
        
        # 如果上下文中已经有 \left 或显式的大括号 \{，则不插入
        if '\\left' in context or '\\{' in context:
            return m.group(0)  # 保持原样
        
        # 满足条件：在 begin 前插入 \left\{
        return r'\left\{' + m.group(0)
    
    # 先处理 \begin{array}
    block = re.sub(r'\\begin\{array\}', _insert_left_if_needed, block)
    
    # 再处理 \begin{cases}
    block = re.sub(r'\\begin\{cases\}', _insert_left_if_needed, block)
    
    return block


def _sanitize_math_block(block: str) -> str:
    """修正数学块内部的 OCR 错误
    
    修复：
    - \\left / \\right 不匹配时降级为普通括号
    - \\right.\\ ) 等畸形组合
    """
    if not block:
        return block
    
    # 统一数学环境内的中文标点为英文标点
    block = (block
             .replace('，', ',')
             .replace('：', ':')
             .replace('；', ';')
             .replace('。', '.')
             .replace('、', ','))

    # 替换常见的 Unicode 符号为 LaTeX 命令（避免缺字形）
    block = block.replace('∵', r'\\because').replace('∴', r'\\therefore')

    # 将上下标中的中文包装为 \text{...}
    # 形式一：_[{...中文...}] 或 ^[{...中文...}]
    def _wrap_cjk_in_braced_subsup(m: re.Match) -> str:
        lead = m.group(1)
        inner = m.group(2)
        if '\\text{' in inner:
            return f"{lead}{{{inner}}}"
        return f"{lead}{{\\text{{{inner}}}}}"
    block = re.sub(r'([_^])\{([^{}]*?[\u4e00-\u9fff]+[^{}]*?)\}', _wrap_cjk_in_braced_subsup, block)

    # 形式二：单字符上下标：_水 或 ^高
    block = re.sub(r'([_^])([\u4e00-\u9fff])', r'\1{\\text{\2}}', block)

    # 数学内常见中文连接词，替换为 \text{...}（保守集）
    for w in ['且', '或', '则', '即', '故', '所以', '因为']:
        block = re.sub(fr'(?<!\\text\{{){re.escape(w)}(?![^\{{]*\}})', rf'\\text{{{w}}}', block)
    
    # 🆕 v1.8.9：在统计 left/right 之前，先尝试修复典型 array/cases 方程组
    # 为缺失 \\left\\{ 的方程组补全左大括号，避免后续降级处理
    block = _fix_array_left_braces(block)
    
    # 统计 left/right 数量
    left_count = len(re.findall(r'\\left\b', block))
    right_count = len(re.findall(r'\\right\b', block))
    
    # 修复畸形 \right.\ ) 和 \right.\\)
    block = re.sub(r'\\right\.\s*\\\s*\)', r'\\right.', block)
    # 修复 \right.\\\) 模式（array结尾的常见OCR错误）
    block = re.sub(r'\\right\.\\\\+\)', r'\\right.', block)
    
    # 如果 left/right 不匹配，降级为普通括号
    if left_count != right_count:
        block = re.sub(r'\\left\s*([\(\[\{])', r'\1', block)
        block = re.sub(r'\\right\s*([\)\]\}])', r'\1', block)
        block = re.sub(r'\\left\.', '', block)
        block = re.sub(r'\\right\.', '', block)
    
    return block


# DEPRECATED: 状态机已处理数学定界符与 OCR 边界，此函数仅保留兼容性
def sanitize_math(text: str) -> str:
    """扫描全文，仅修正数学环境内的 OCR 错误
    
    只处理 \\(...\\) 和 \\[...\\] 内部的内容。
    """
    if not text:
        return text
    
    result = []
    i = 0
    n = len(text)
    
    while i < n:
        # 匹配 \(..\)
        if text.startswith(r"\(", i):
            j = text.find(r"\)", i + 2)
            if j == -1:
                result.append(text[i:])
                break
            inner = text[i+2:j]
            inner = _sanitize_math_block(inner)
            result.append(r"\(" + inner + r"\)")
            i = j + 2
            continue
        
        # 匹配 \[..\]
        if text.startswith(r"\[", i):
            j = text.find(r"\]", i + 2)
            if j == -1:
                result.append(text[i:])
                break
            inner = text[i+2:j]
            inner = _sanitize_math_block(inner)
            result.append(r"\[" + inner + r"\]")
            i = j + 2
            continue
        
        result.append(text[i])
        i += 1
    
    return "".join(result)


def remove_blank_lines_in_macro_args(text: str) -> str:
    """删除宏参数中的空行（增强版）"""
    macros = ['explain', 'topics', 'answer', 'difficulty', 'source']
    
    for macro in macros:
        pattern = rf'(\\{macro}\{{)([^{{}}]*(?:\{{[^{{}}]*\}}[^{{}}]*)*?)(\}})'
        
        def clean_arg(match):
            prefix = match.group(1)
            arg = match.group(2)
            suffix = match.group(3)
            
            # 改进1：删除连续空行
            arg = re.sub(r'\n\s*\n+', '\n', arg)
            
            # 改进2：删除段首段尾空行
            arg = arg.strip()
            
            # 改进3：清理行首行尾空格（保留缩进）
            lines = arg.split('\n')
            lines = [line.rstrip() for line in lines]
            arg = '\n'.join(lines)
            
            return prefix + arg + suffix
        
        text = re.sub(pattern, clean_arg, text, flags=re.DOTALL)
    
    return text


def clean_question_environments(text: str) -> str:
    """清理 question 环境内部的多余空行，并检测缺少题干的题目"""
    pattern = r'(\\begin\{question\})(.*?)(\\end\{question\})'

    def clean_env(match):
        begin = match.group(1)
        content = match.group(2)
        end = match.group(3)

        # 删除连续的3个以上换行
        content = re.sub(r'\n{3,}', '\n\n', content)

        # 🆕 v1.8: 检测缺少题干的题目（直接从 \item 开始）
        # 去除前导空白后检查是否以 \item 开头
        content_stripped = content.lstrip()
        if content_stripped.startswith('\\item'):
            # 在 \begin{question} 后插入 TODO 注释
            warning = '\n% ⚠️ TODO: 补充题干 - 此题直接从 \\item 开始，请在上方添加题目主干描述\n'
            content = warning + content

        return begin + content + end

    return re.sub(pattern, clean_env, text, flags=re.DOTALL)


def split_long_lines_in_explain(text: str, max_length: int = 800) -> str:
    """在 explain{} 中自动分割超长行"""
    pattern = r'(\\explain\{)([^{}]*(?:\{[^{}]*\}[^{}]*)*?)(\})'

    def split_content(match):
        prefix = match.group(1)
        content = match.group(2)
        suffix = match.group(3)

        lines = content.split('\n')
        new_lines = []

        for line in lines:
            if len(line) <= max_length:
                new_lines.append(line)
            else:
                # 在标点后分割
                segments = re.split(r'([，。；！？])', line)
                current = ""
                for seg in segments:
                    if len(current + seg) > max_length and current:
                        new_lines.append(current.rstrip())
                        current = seg
                    else:
                        current += seg
                if current:
                    new_lines.append(current.rstrip())

        return prefix + '\n'.join(new_lines) + suffix

    return re.sub(pattern, split_content, text, flags=re.DOTALL)


def fix_missing_items_in_enumerate(tex: str) -> str:
    """🆕 任务1：在 enumerate 环境中自动补充缺失的 \\item

    功能：扫描 TeX 文本，检测 \\begin{enumerate} 到 \\end{enumerate} 之间的内容，
    在枚举环境内自动为非空行（非注释行、非 \\item 行）添加 \\item 前缀。

    逻辑：
    - 空行：保留
    - 注释行（以 % 开头）：保留
    - 以 \\item 开头的行：保留
    - 其他非空行：在行首自动添加 \\item（保持原有缩进）

    Args:
        tex: 完整的 TeX 文本

    Returns:
        修复后的 TeX 文本
    """
    if not tex:
        return tex

    result = []
    i = 0
    lines = tex.split('\n')
    n = len(lines)

    while i < n:
        line = lines[i]

        # 检测 enumerate 环境开始
        if r'\begin{enumerate}' in line:
            result.append(line)
            i += 1

            # 处理 enumerate 环境内的内容
            depth = 1
            while i < n and depth > 0:
                current_line = lines[i]

                # 检测嵌套的 enumerate 环境
                if r'\begin{enumerate}' in current_line:
                    depth += 1
                    result.append(current_line)
                    i += 1
                    continue
                elif r'\end{enumerate}' in current_line:
                    depth -= 1
                    result.append(current_line)
                    i += 1
                    if depth == 0:
                        break
                    continue

                stripped = current_line.strip()

                # 规则1：空行 - 保留
                if not stripped:
                    result.append(current_line)
                    i += 1
                    continue

                # 规则2：注释行（以 % 开头）- 保留
                if stripped.startswith('%'):
                    result.append(current_line)
                    i += 1
                    continue

                # 规则3：已有 \item 的行 - 保留
                if stripped.startswith(r'\item'):
                    result.append(current_line)
                    i += 1
                    continue

                # 规则4：其他非空行 - 添加 \item
                # 保持原有缩进
                leading_spaces = len(current_line) - len(current_line.lstrip())
                indent = current_line[:leading_spaces]
                content = current_line[leading_spaces:]
                result.append(f"{indent}\\item {content}")
                i += 1
        else:
            result.append(line)
            i += 1

    return '\n'.join(result)


def soft_wrap_paragraph(s: str, limit: int = 80) -> str:
    """🆕 任务2：为长段落在标点处添加软换行，便于 LaTeX 报错定位

    功能：对于超过指定长度的字符串，在合适的标点位置插入换行符，
    使得每行长度不超过 limit，便于 LaTeX 编译时快速定位错误行。

    逻辑：
    - 如果字符串长度 < limit，直接返回
    - 如果较长：
      - 从头扫描，记录最近的"可拆分标点"位置（。；？！，）
      - 当当前行长度超过 limit/2 时，在最近标点后插入换行
      - 避免在 LaTeX 命令内部拆行（遇到 \\ 开头的 token 时不拆）

    Args:
        s: 输入字符串
        limit: 每行最大长度限制（默认 80）

    Returns:
        添加软换行后的字符串
    """
    if not s or len(s) < limit:
        return s

    # 可拆分的中文标点
    breakable_puncts = set('。；？！，')

    result = []
    current_line = []
    current_length = 0
    last_punct_pos = -1  # 记录当前行中最近的标点位置

    i = 0
    while i < len(s):
        char = s[i]

        # 检测 LaTeX 命令（以 \ 开头）
        if char == '\\' and i + 1 < len(s):
            # 收集完整的 LaTeX 命令
            cmd_start = i
            i += 1
            # 跳过命令名（字母）
            while i < len(s) and s[i].isalpha():
                i += 1
            # 跳过可能的参数（花括号）
            if i < len(s) and s[i] == '{':
                brace_depth = 1
                i += 1
                while i < len(s) and brace_depth > 0:
                    if s[i] == '{':
                        brace_depth += 1
                    elif s[i] == '}':
                        brace_depth -= 1
                    i += 1

            # 将整个命令作为一个单元添加
            cmd = s[cmd_start:i]
            current_line.append(cmd)
            current_length += len(cmd)
            continue

        # 检测换行符 - 保留原有换行
        if char == '\n':
            result.append(''.join(current_line))
            result.append('\n')
            current_line = []
            current_length = 0
            last_punct_pos = -1
            i += 1
            continue

        # 普通字符
        current_line.append(char)
        current_length += 1

        # 记录可拆分标点的位置
        if char in breakable_puncts:
            last_punct_pos = len(current_line) - 1

        # 检查是否需要换行
        if current_length > limit // 2 and last_punct_pos >= 0:
            # 在最近的标点后换行
            before_break = ''.join(current_line[:last_punct_pos + 1])
            after_break = current_line[last_punct_pos + 1:]

            result.append(before_break)
            result.append('\n')

            current_line = after_break
            current_length = len(after_break)
            last_punct_pos = -1

        i += 1

    # 添加剩余内容
    if current_line:
        result.append(''.join(current_line))

    return ''.join(result)


def remove_par_breaks_in_explain(text: str) -> str:
    r"""移除 \explain{...} 中的空段落（改进版：正确处理嵌套括号）

    🆕 v1.8.2：完全重写，修复括号计数错误
    - 正确处理 \{ \} 转义括号（不计入 depth）
    - 正确处理反斜杠转义（\\ 后的字符不处理）
    - 将空段落替换为 % 注释而非 \par（更安全）
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    out = []
    i = 0
    n = len(text)

    while i < n:
        if text.startswith("\\explain{", i):
            out.append("\\explain{")
            i += len("\\explain{")
            depth = 1
            buf = []

            while i < n and depth > 0:
                # 处理反斜杠转义序列
                if text[i] == '\\' and i + 1 < n:
                    next_char = text[i + 1]
                    # \{ 和 \} 不计入括号深度
                    if next_char in '{}':
                        buf.append(text[i:i+2])
                        i += 2
                        continue
                    # 其他反斜杠序列（如 \\, \left, \right 等）直接复制
                    buf.append(text[i])
                    i += 1
                    continue

                # 检测空段落（连续两个换行，中间只有空白）
                if text[i] == '\n':
                    j = i + 1
                    while j < n and text[j] in ' \t':
                        j += 1
                    if j < n and text[j] == '\n':
                        # 空段落：替换为注释行
                        buf.append('\n%\n')
                        i = j + 1
                        continue

                # 普通大括号计数
                if text[i] == '{':
                    depth += 1
                    buf.append(text[i])
                    i += 1
                elif text[i] == '}':
                    depth -= 1
                    if depth == 0:
                        # 找到匹配的闭括号
                        out.append(''.join(buf))
                        out.append('}')
                        i += 1
                        break
                    buf.append(text[i])
                    i += 1
                else:
                    buf.append(text[i])
                    i += 1

            # 如果循环结束但 depth > 0，说明括号不匹配（保留原内容）
            if depth > 0:
                out.append(''.join(buf))
        else:
            out.append(text[i])
            i += 1

    return ''.join(out)


def _is_likely_stem(first_item: str, all_lines: list, item_indices: list, section_type: str = "") -> bool:
    """🆕 v1.8.5：判断第一个 \\item 是否可能是题干（增强版）

    启发式规则：
        1. 题型判断：解答题更可能有题干，选择题可能直接是小问
        2. 长度检查：根据题型动态调整阈值
        3. 关键词检查：检查是否包含"已知"、"设"、"如图"等题干关键词
        4. 小问标记检查：第一行不包含常见小问标记（①②③、(1)(2)等）
        5. 后续检查：后续 \\item 包含小问标记

    Args:
        first_item: 第一个 \\item 行的内容
        all_lines: question 环境内的所有行
        item_indices: 所有 \\item 的行索引
        section_type: 题型（如 "解答题"、"单选题"、"多选题"、"填空题"）

    Returns:
        True 如果可能是题干，False 如果可能是小问
    """
    # 提取第一个 \\item 的纯文本内容
    stem_text = re.sub(r'^(\s*)\\item\s*', '', first_item).strip()

    # 规则1：题型判断 - 动态调整阈值和关键词
    if section_type == "解答题":
        # 解答题通常有题干
        min_length = 15
        stem_keywords = ['已知', '设', '如图', '证明', '求', '计算', '若', '假设', '在']
    elif section_type in ["单选题", "多选题"]:
        # 选择题可能直接是小问
        min_length = 30
        stem_keywords = ['已知', '设', '如图', '若', '假设', '下列', '关于', '在']
    else:
        # 填空题或未知类型
        min_length = 20
        stem_keywords = ['已知', '设', '如图', '若', '假设', '在']

    # 规则2：长度检查（去掉LaTeX命令后）
    # 去掉数学模式和常见LaTeX命令来估算文本长度
    clean_text = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', stem_text)
    clean_text = re.sub(r'\\[()\[\]]', '', clean_text)

    if len(clean_text) < min_length:
        # 太短，可能不是题干
        return False

    # 规则3：关键词检查
    has_stem_keyword = any(kw in stem_text for kw in stem_keywords)

    # 规则4：检查第一行是否包含小问标记（排除法）
    subq_markers = [
        r'[①②③④⑤⑥⑦⑧⑨⑩]',  # 圆圈数字
        r'\(\d+\)',            # (1) (2)
        r'^\d+[\.、]',         # 1. 1、
        r'^[Ⅰ-Ⅹ][\.、]',      # Ⅰ. Ⅱ.
    ]

    has_subq_marker = False
    for pattern in subq_markers:
        if re.search(pattern, stem_text[:50]):  # 只检查前50个字符
            # 第一行有小问标记，可能不是题干
            has_subq_marker = True
            break

    if has_subq_marker:
        return False

    # 规则5：检查后续 \\item 是否包含小问标记
    # 如果后续有标记，说明当前这个可能是题干
    next_items_have_markers = False
    if len(item_indices) >= 2:
        # 检查第二个和第三个 \\item
        for idx in item_indices[1:min(3, len(item_indices))]:
            if idx < len(all_lines):
                next_item = all_lines[idx]
                for pattern in subq_markers:
                    if re.search(pattern, next_item):
                        # 后续有小问标记，当前可能是题干
                        next_items_have_markers = True
                        break
                if next_items_have_markers:
                    break

    if next_items_have_markers:
        return True

    # 规则6：综合判断
    if section_type == "解答题":
        # 解答题：有关键词或长度足够 → 题干
        return has_stem_keyword or len(clean_text) > 30
    else:
        # 其他题型：必须有关键词且长度足够 → 题干
        return has_stem_keyword and len(clean_text) > min_length


def fix_merged_questions_structure(content: str) -> str:
    """🆕 v1.8.4：修复合并题目的结构问题（增强版）
    
    问题场景：
        当同一题号的多个部分被合并后，所有部分都显示为 \\item，
        但正确结构应该是：第一部分=题干，后续部分=小问
    
    示例：
        输入（错误）：
            \\begin{question}
            \\item 甲、乙两人组队参加挑战...  （应该是题干）
            \\item 已知甲先上场...              （这才是小问1）
            \\item 如果n关都挑战成功...         （这是小问2）
            \\end{question}
        
        输出（正确）：
            \\begin{question}
            甲、乙两人组队参加挑战...  （题干）
            
            \\begin{enumerate}[label=(\\arabic*)]
            \\item 已知甲先上场...      （小问1）
            \\item 如果n关都挑战成功... （小问2）
            \\end{enumerate}
            \\end{question}
    
    🆕 v1.8.4 增强检测逻辑：
        1. 找到 \\begin{question} 后第一个 \\item
        2. 检查第一个 \\item 是否为题干（启发式规则）：
           - 字数较多（>20字符）且不包含小问标记（①②③、(1)(2)等）
           - 后续有其他 \\item 且包含小问标记
        3. 如果满足条件，将第一个 \\item 提取为题干，其余包裹在 enumerate 中
    
    Args:
        content: 完整的 LaTeX 内容
    
    Returns:
        修复后的 LaTeX 内容
    """
    lines = content.split('\n')
    result = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # 检测 question 环境开始
        if r'\begin{question}' in line:
            result.append(line)
            i += 1
            
            # 收集 question 环境内的所有行
            question_lines = []
            question_start = i
            depth = 1
            
            while i < len(lines) and depth > 0:
                current_line = lines[i]
                if r'\begin{question}' in current_line:
                    depth += 1
                elif r'\end{question}' in current_line:
                    depth -= 1
                    if depth == 0:
                        break
                question_lines.append(current_line)
                i += 1
            
            # 分析 question 内容
            item_indices = []
            for idx, qline in enumerate(question_lines):
                if r'\item' in qline and not qline.strip().startswith('%'):
                    item_indices.append(idx)
            
            # 如果有多个 \item，需要修复结构
            if len(item_indices) >= 2:
                # 检查是否已经包含 enumerate（避免重复处理）
                has_enumerate = any(r'\begin{enumerate}' in qline for qline in question_lines)
                
                if not has_enumerate:
                    # 提取第一个 \item 作为题干
                    first_item_idx = item_indices[0]
                    stem_line = question_lines[first_item_idx]

                    # 🆕 v1.8.5：推断题型（从前面的 \section 命令）
                    section_type = ""
                    # 向前查找最近的 \section 命令
                    for prev_line in reversed(result[-50:]):  # 检查前50行
                        if r'\section{' in prev_line:
                            # 提取 section 名称
                            match = re.search(r'\\section\{([^}]+)\}', prev_line)
                            if match:
                                section_type = match.group(1)
                                break

                    # 🆕 v1.8.5：增强题干识别 - 检查第一个 \item 是否真的是题干
                    is_likely_stem = _is_likely_stem(stem_line, question_lines, item_indices, section_type)
                    
                    # 如果第一个 \item 不像题干（例如直接是小问），跳过修复
                    if not is_likely_stem:
                        result.extend(question_lines)
                        if i < len(lines):
                            result.append(lines[i])
                            i += 1
                        continue
                    
                    # 去掉 \item 前缀得到题干
                    stem_content = re.sub(r'^(\s*)\\item\s*', r'\1', stem_line)
                    
                    # 构建新的 question 内容
                    new_question_lines = []
                    
                    # 添加题干之前的内容（如果有）
                    new_question_lines.extend(question_lines[:first_item_idx])
                    
                    # 添加题干
                    new_question_lines.append(stem_content)
                    new_question_lines.append('')  # 空行分隔
                    
                    # 添加 enumerate 环境包裹剩余的 \item
                    new_question_lines.append(r'\begin{enumerate}[label=(\arabic*)]')
                    
                    # 添加剩余的 \item（从第二个 \item 开始）
                    new_question_lines.extend(question_lines[first_item_idx + 1:])
                    
                    # 添加 enumerate 结束标记
                    new_question_lines.append(r'\end{enumerate}')
                    
                    result.extend(new_question_lines)
                else:
                    # 已有 enumerate，保持原样
                    result.extend(question_lines)
            else:
                # 只有 0 或 1 个 \item，保持原样
                result.extend(question_lines)
            
            # 添加 \end{question}
            if i < len(lines):
                result.append(lines[i])
                i += 1
        else:
            result.append(line)
            i += 1
    
    return '\n'.join(result)


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


def fix_reversed_delimiters(text: str) -> str:
    r"""修复反向定界符 - 使用栈算法（跨行处理）
    
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
    
    # 注意：不再为未匹配的 \( 在行尾添加 \)
    # 这是因为多行数学块的 \( 可能在后续行才闭合，逐行添加会造成错误
    # 如果真的有未闭合的 \(，应该由其他后处理函数或手动修复
    # （只记录警告，不自动添加）
    if stack:
        # 可以选择打印警告，但不自动修复
        pass
    
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
                # 可以增加日志，如果项目中有 logger
                print(f"⚠️  [balance_array_and_cases_env] Drop unmatched {token} at pos {m.start()}")
                pass

        last = m.end()

    out_parts.append(text[last:])
    return ''.join(out_parts)


def fix_nested_subquestions(text: str) -> str:
    r"""🆕 v1.9.6：修复嵌套子题号格式
    
    问题模式：
    - \item (i)xxx → 需要特殊处理，因为 (i)(ii) 是第二级子题
    - 目前保守处理：只清理 \item 后紧跟 (i)/(ii) 的情况
    
    例如：
    - \item (i)求角的大小 → \item[(i)] 求角的大小
    """
    import re
    
    # 匹配 \item 后紧跟 (i)/(ii)/(iii) 等
    # 替换为 \item[(i)] 格式
    pattern = r'\\item\s+\(([ivxIVX]+)\)'
    text = re.sub(pattern, r'\\item[(\1)]', text)
    
    # 同样处理全角括号
    pattern_cn = r'\\item\s+（([ivxIVX]+)）'
    text = re.sub(pattern_cn, r'\\item[(\1)]', text)
    
    return text


def fix_spurious_items_in_enumerate(text: str) -> str:
    r"""🆕 v1.9.6：合并 enumerate 中错误的多余 \item
    
    问题模式：
    在 enumerate 环境中，如果一个子问题跨多行，每行可能都被错误地加上 \item。
    例如：
      \item 若角平分线交AC于点D，
      \item 且AD = 2DC，
      \item 求BD．
    
    应该合并为：
      \item 若角平分线交AC于点D，且AD = 2DC，求BD．
    
    保守策略：
    - 只合并那些不以小问编号（如 "①②" 或 "(1)(2)"）开头的 \item
    - 如果 \item 内容以 "求"、"证明"、"设" 等动词开头，保留为独立 \item
    """
    import re
    
    lines = text.split('\n')
    result = []
    i = 0
    n = len(lines)
    
    # 用于判断是否是子问题开头的模式
    subq_start_patterns = [
        r'^\\item\s*[\(（][1-9ivxIVX]+[\)）]',  # (1), (i), （1）, （i）
        r'^\\item\s*[①②③④⑤⑥⑦⑧⑨⑩]',  # ①②③...
        r'^\\item\s*\[[^\]]+\]',  # \item[(i)]
        r'^\\item\s*(求证|证明|求|设|解)',  # 以动词开头
    ]
    
    def is_subq_start(line: str) -> bool:
        """判断是否是子问题开头"""
        for pattern in subq_start_patterns:
            if re.match(pattern, line.strip()):
                return True
        return False
    
    in_enumerate = False
    enumerate_depth = 0
    pending_item = None  # 待合并的 \item 行
    
    while i < n:
        line = lines[i]
        stripped = line.strip()
        
        # 检测 enumerate 环境
        if r'\begin{enumerate}' in line:
            if pending_item:
                result.append(pending_item)
                pending_item = None
            result.append(line)
            in_enumerate = True
            enumerate_depth += 1
            i += 1
            continue
        
        if r'\end{enumerate}' in line:
            if pending_item:
                result.append(pending_item)
                pending_item = None
            result.append(line)
            enumerate_depth -= 1
            if enumerate_depth == 0:
                in_enumerate = False
            i += 1
            continue
        
        # 如果不在 enumerate 中，直接输出
        if not in_enumerate:
            result.append(line)
            i += 1
            continue
        
        # 在 enumerate 中
        if stripped.startswith(r'\item'):
            # 检查是否是子问题开头
            if is_subq_start(stripped):
                # 这是一个新的子问题，先输出之前的 pending
                if pending_item:
                    result.append(pending_item)
                pending_item = line
            else:
                # 不是子问题开头，可能需要合并
                if pending_item:
                    # 提取 \item 后的内容
                    item_content = re.sub(r'^\\item\s*', '', stripped)
                    # 合并到 pending_item
                    pending_item = pending_item.rstrip() + item_content
                else:
                    # 没有 pending，这是第一个 item
                    pending_item = line
        else:
            # 非 \item 行
            if pending_item:
                result.append(pending_item)
                pending_item = None
            result.append(line)
        
        i += 1
    
    # 输出最后的 pending
    if pending_item:
        result.append(pending_item)
    
    return '\n'.join(result)


def fix_keep_questions_together(text: str) -> str:
    r"""🆕 v1.9.7：尽量不分页（保守）

    ⚠️ 已禁用：samepage 环境不能在 question 环境内部使用，会导致嵌套错误。
    需要在 examx.sty 中通过其他方式实现（如 needspace 或 samepage 在 question 环境定义中）。
    
    原设计：在每个 `question` 环境的主体前后添加 `samepage` 环境包装
    问题：question 环境有特殊结构，内部插入 samepage 会导致 LaTeX 嵌套错误
    """
    # 暂时禁用，直接返回原文本
    return text


def fix_trig_function_spacing(text: str) -> str:
    r"""🆕 v1.9.6：修复三角函数和对数函数后缺少空格的问题
    
    问题模式：
    - \sinx → \sin x
    - \cosB → \cos B
    - \lnt → \ln t
    
    保守处理：只修复后面紧跟单个字母/变量的情况
    """
    import re
    
    # 定义需要处理的函数名
    trig_funcs = ['sin', 'cos', 'tan', 'cot', 'sec', 'csc', 'arcsin', 'arccos', 'arctan',
                  'sinh', 'cosh', 'tanh', 'ln', 'log', 'lg', 'exp']
    
    for func in trig_funcs:
        # 匹配 \func 后紧跟字母（非 { 或空格的情况）
        # 例如 \sinx → \sin x, \cosB → \cos B
        pattern = rf'\\{func}([A-Za-z])(?![a-zA-Z])'
        text = re.sub(pattern, rf'\\{func} \1', text)
    
    return text


def fix_undefined_symbols(text: str) -> str:
    r"""🆕 v1.9.6：替换可能未定义的数学符号
    
    已知问题：
    - \bigtriangleup → \triangle (amssymb 中有定义)
    """
    import re
    
    # \bigtriangleup 替换为 \triangle
    text = re.sub(r'\\bigtriangleup\b', r'\\triangle', text)
    
    return text


def fix_markdown_bold_residue(text: str) -> str:
    r"""🆕 v1.9.7：清理 Markdown 粗体残留
    
    问题来源：
    - Word 文档中某些标点被加粗，Pandoc 转换为 **，** 等
    - 预处理可能没有完全清理干净
    
    保守策略：
    - 只处理"纯标点或短文本+标点被粗体包裹"的情况
    - 不处理正常的粗体文本
    
    例如：
    - **，** → ，
    - **，得证.** → ，得证.
    - **。** → 。
    """
    import re
    
    # 模式1：纯标点被粗体包裹 **，** **。** **；** 等
    text = re.sub(r'\*\*([，。；、：！？,.;:!?])\*\*', r'\1', text)
    
    # 模式2：标点开头+短文本+标点结尾被粗体包裹
    # 例如：**，得证.** → ，得证.
    text = re.sub(r'\*\*([，。；、：,.;:][^\*]{0,10}[.．。])\*\*', r'\1', text)
    
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
    r"""🆕 v1.8.8：检测并记录反向数学定界符案例（只记录，不修改）

    搜索 \)...\( 和 \]...\[ 类型的反向定界符，记录到 issue 日志。

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

        # 检测反向的行内数学定界符 \)...\(
        inline_pattern = re.compile(r'\\\)([^%]*?)\\\(')
        inline_matches = list(inline_pattern.finditer(content))
        for match in inline_matches:
            middle = match.group(1)
            # 截断行内容用于日志显示
            line_display = line[:100] + '...' if len(line) > 100 else line
            reversed_cases.append(
                f"Line {line_num}: Found reversed inline math \\)...\\("
                f"\n  Middle content: '{middle}'"
                f"\n  Line: {line_display}"
            )

        # 检测反向的显示数学定界符 \]...\[
        display_pattern = re.compile(r'\\\]([^%]*?)\\\[')
        display_matches = list(display_pattern.finditer(content))
        for match in display_matches:
            middle = match.group(1)
            line_display = line[:100] + '...' if len(line) > 100 else line
            reversed_cases.append(
                f"Line {line_num}: Found reversed display math \\]...\\["
                f"\n  Middle content: '{middle}'"
                f"\n  Line: {line_display}"
            )

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

        print(f"⚠️  Found {len(reversed_cases)} reversed math delimiter cases, logged to {log_file}")


def validate_and_fix_image_todo_blocks(text: str) -> str:
    """🆕 v1.8.5：验证并修复 IMAGE_TODO 块格式错误

    检查并修复：
    1. IMAGE_TODO_END 后的多余花括号
    2. IMAGE_TODO_START 参数格式错误
    3. 缺失的必需参数

    示例：
        输入：% IMAGE_TODO_END id=xxx{
        输出：% IMAGE_TODO_END id=xxx
    """
    if not text:
        return text

    issues = []

    # 修复1：IMAGE_TODO_END 后的多余字符（花括号或其他）
    # 匹配：% IMAGE_TODO_END id=xxx{ 或 % IMAGE_TODO_END id=xxx {
    pattern = r'(% IMAGE_TODO_END id=[a-zA-Z0-9_-]+)\s*\{[^}]*\}'
    matches = list(re.finditer(pattern, text))
    for match in matches:
        line_num = text[:match.start()].count('\n') + 1
        issues.append(f"Line {line_num}: IMAGE_TODO_END has extra brace")

    # 执行修复
    text = re.sub(pattern, r'\1', text)

    # 修复2：IMAGE_TODO_END 后的单个花括号（无配对）
    text = re.sub(
        r'(% IMAGE_TODO_END id=[a-zA-Z0-9_-]+)\s*\{',
        r'\1',
        text
    )

    # 修复3：IMAGE_TODO_START 行末的多余字符
    text = re.sub(
        r'(% IMAGE_TODO_START[^\n]+)\s*\{[^}]*\}',
        r'\1',
        text
    )

    # 修复4：IMAGE_TODO_END 与正文同处一行，自动拆分
    def _split_image_end(match: re.Match) -> str:
        trailing = match.group(2)
        if not trailing.strip():
            return match.group(1)
        return f"{match.group(1)}\n{trailing.lstrip()}"

    text = re.sub(
        r'(% IMAGE_TODO_END id=[^\n]+)([^\n]+)',
        _split_image_end,
        text
    )

    if issues:
        print(f"⚠️  修复了 {len(issues)} 个 IMAGE_TODO 格式错误：")
        for issue in issues[:5]:  # 只显示前5个
            print(f"   - {issue}")

    return text


def balance_left_right_delimiters(text: str) -> str:
    r"""平衡 \left/\right 定界符，孤立项降级为普通括号"""
    if not text or ('\\left' not in text and '\\right' not in text):
        return text

    pattern = re.compile(r'\\left\s*(?:\\[a-zA-Z]+|\\.|.)|\\right\s*(?:\\[a-zA-Z]+|\\.|.)')
    parts: List[str] = []
    stack: List[int] = []
    last = 0

    def _downgrade_left(token: str) -> str:
        remainder = token[len('\\left'):].lstrip()
        return '' if remainder.startswith('.') else remainder

    def _downgrade_right(token: str) -> str:
        remainder = token[len('\\right'):].lstrip()
        return '' if remainder.startswith('.') else remainder

    for match in pattern.finditer(text):
        parts.append(text[last:match.start()])
        token = match.group(0)

        if token.startswith('\\left'):
            parts.append(token)
            stack.append(len(parts) - 1)
        else:
            if stack:
                stack.pop()
                parts.append(token)
            else:
                parts.append(_downgrade_right(token))
        last = match.end()

    parts.append(text[last:])

    for idx in stack:
        parts[idx] = _downgrade_left(parts[idx])

    return ''.join(parts)


def cleanup_remaining_image_markers(text: str) -> str:
    """🆕 后备占位符转换：清理任何残留的 Markdown 图片标记
    
    🆕 v1.6.2：增强内联公式处理
    - 独立成行的图片 → TikZ占位符块（大图）
    - 内联图片（公式）→ 简单文本占位符 [公式:filename]
    
    将残留的 Markdown 图片标记替换为占位符，避免在 PDF 中显示
    为原始路径文本。支持：
      - ![@@@id](path){...}
      - ![](path){...}
    """
    if not text:
        return text
    
    def _make_tikz_placeholder(label: str) -> str:
        """创建 TikZ 占位符块（用于独立图片）"""
        label = label.strip() or "image"
        return (
            "\n\\begin{center}\n"
            "\\begin{tikzpicture}[scale=1.05,>=Stealth,line cap=round,line join=round]\n"
            f"  \\node[draw, minimum width=6cm, minimum height=4cm] {{图略（图 ID: {label}）}};\n"
            "\\end{tikzpicture}\n"
            "\\end{center}\n"
        )
    
    def _make_inline_placeholder(label: str) -> str:
        """创建内联占位符（用于公式图片）"""
        label = label.strip() or "formula"
        # 使用简单的文本占位符，可以在后续被识别和替换
        return f"[公式:{label}]"
    
    def is_standalone_line(match_obj: re.Match, full_text: str) -> bool:
        """判断匹配是否为独立成行的图片"""
        # 获取匹配前后的文本
        start = match_obj.start()
        end = match_obj.end()
        
        # 向前查找到行首
        line_start = start
        while line_start > 0 and full_text[line_start - 1] not in '\n':
            line_start -= 1
        
        # 向后查找到行尾
        line_end = end
        while line_end < len(full_text) and full_text[line_end] not in '\n':
            line_end += 1
        
        # 检查行内容：去除空白后是否只有这个图片标记
        line_content = full_text[line_start:line_end].strip()
        match_content = match_obj.group(0).strip()
        
        return line_content == match_content
    
    # 处理带ID的图片标记
    def repl_with_id(m: re.Match) -> str:
        img_id = m.group(1)
        basename = os.path.basename(img_id) if img_id else "image"
        if is_standalone_line(m, text):
            return _make_tikz_placeholder(basename)
        else:
            return _make_inline_placeholder(basename)
    
    import os  # 确保导入
    text = IMAGE_PATTERN_WITH_ID.sub(repl_with_id, text)
    
    # 处理无ID的图片标记
    def repl_no_id(m: re.Match) -> str:
        path = m.group(1).strip()
        basename = os.path.basename(path)
        label = basename if basename else "image"
        if is_standalone_line(m, text):
            return _make_tikz_placeholder(label)
        else:
            return _make_inline_placeholder(label)
    
    text = IMAGE_PATTERN_NO_ID.sub(repl_no_id, text)
    
    return text


def cleanup_guxuan_in_macros(text: str) -> str:
    """🆕 v1.6：清理宏参数内的"故选"残留
    
    针对 \\topics{...} 和 \\explain{...} 等宏参数内的"故选：X"进行清理。
    
    Args:
        text: LaTeX 文本
        
    Returns:
        清理后的文本
    """
    if not text or '故选' not in text:
        return text
    
    # 定义要清理的宏列表
    macros = ['topics', 'explain', 'keywords', 'analysis']
    
    for macro_name in macros:
        # 匹配 \macro{content}，使用递归匹配嵌套大括号
        # 由于Python re不支持递归，我们使用更宽松的匹配+手工解析
        pattern = rf'\\{macro_name}\{{'
        
        pos = 0
        result_parts = []
        
        while True:
            start_idx = text.find(pattern, pos)
            if start_idx == -1:
                result_parts.append(text[pos:])
                break
            
            # 添加前面的文本
            result_parts.append(text[pos:start_idx])
            
            # 手工解析嵌套大括号
            brace_count = 0
            content_start = start_idx + len(pattern)
            i = content_start
            
            while i < len(text):
                if text[i] == '{':
                    brace_count += 1
                elif text[i] == '}':
                    if brace_count == 0:
                        # 找到匹配的右大括号
                        content = text[content_start:i]
                        
                        # 清理各种形式的"故选"
                        # 1. 清理行末的"故选：X"（含各种标点组合和可能的后续文本）
                        content = re.sub(r'[,，。\.;；、]?\s*故选[:：][ABCD]+\.?[^\n]*$', '', content, flags=re.MULTILINE)
                        # 2. 清理单独一行的"故选：X"
                        content = re.sub(r'^\s*故选[:：][ABCD]+\.?[^\n]*$', '', content, flags=re.MULTILINE)
                        # 3. 清理换行符后的"故选：X"
                        content = re.sub(r'\n+故选[:：][ABCD]+\.?[^\n]*(?=\n|$)', '', content)
                        # 4. 清理任意位置的"故选：X"（更激进）
                        content = re.sub(r'故选[:：][ABCD]+\.?[^\n]*', '', content)
                        # 5. 清理"故答案为"
                        content = re.sub(r'[,，。\.;；、]?\s*故答案为[:：]?[ABCD]*[.。]?\s*', '', content)
                        
                        result_parts.append(rf'\{macro_name}{{{content}}}')
                        pos = i + 1
                        break
                    else:
                        brace_count -= 1
                elif text[i] == '\\' and i + 1 < len(text):
                    # 跳过转义字符
                    i += 1
                i += 1
            else:
                # 没找到匹配的右大括号，保留原文
                result_parts.append(text[start_idx:])
                break
        
        text = ''.join(result_parts)
    
    return text


def fix_tabular_environments(text: str) -> str:
    r"""🆕 v1.9.1：修复 tabular 环境缺失列格式（P1）

    检测并修复 \begin{tabular} 缺少列格式参数的问题
    例如：\begin{tabularend{center} → \begin{tabular}{|c|c|}...\end{center}

    Args:
        text: LaTeX 文本

    Returns:
        修复后的文本
    """
    if not text or '\\begin{tabular}' not in text:
        return text

    import re

    # 检测不完整的 tabular（后面没有紧跟 {列格式}）
    pattern = re.compile(r'\\begin\{tabular\}(?!\s*\{)')

    def fix_tabular(match):
        # 获取匹配位置
        start_pos = match.end()

        # 查找后续内容，尝试推断列数
        # 向后查找最多500个字符
        remaining = text[start_pos:start_pos+500]

        # 尝试找到第一行内容（到 \\ 或换行）
        first_row_match = re.search(r'([^\n\\]+?)(?:\\\\|\n)', remaining)
        if first_row_match:
            first_row = first_row_match.group(1)
            # 统计 & 的数量来推断列数
            col_count = first_row.count('&') + 1
        else:
            # 默认2列
            col_count = 2

        # 生成默认的列格式（居中对齐，带竖线）
        col_format = '|' + 'c|' * col_count

        return match.group(0) + '{' + col_format + '}'

    return pattern.sub(fix_tabular, text)


def convert_markdown_table_to_latex(text: str) -> str:
    """将 Markdown 表格转换为 LaTeX tabular"""
    table_pattern = r'(\|[^\n]+\|\n)+\|[-:\s|]+\|\n(\|[^\n]+\|\n)+'

    def convert_one_table(match):
        table_text = match.group(0)
        lines = [line.strip() for line in table_text.split('\n') if line.strip()]

        data_lines = [line for line in lines if not re.match(r'^\|[-:\s|]+\|$', line)]

        if not data_lines:
            return table_text

        rows = []
        for line in data_lines:
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            rows.append(cells)

        if not rows:
            return table_text

        ncols = len(rows[0])
        latex = "\\begin{center}\n"
        latex += f"\\begin{{tabular}}{{{'c' * ncols}}}\n"
        latex += "\\hline\n"

        header = rows[0]
        latex += " & ".join(escape_latex_special(cell, False) for cell in header)
        latex += " \\\\\n\\hline\n"

        for row in rows[1:]:
            latex += " & ".join(escape_latex_special(cell, False) for cell in row)
            latex += " \\\\\n"

        latex += "\\hline\n\\end{tabular}\n\\end{center}"
        return latex

    return re.sub(table_pattern, convert_one_table, text)


def convert_ascii_table_blocks(text: str) -> str:
    """将由横线 + 空格对齐组成的 ASCII 表格转换为 tabular"""
    if not text:
        return text

    lines = text.splitlines()
    result: List[str] = []
    i = 0

    def _is_rule(line: str) -> bool:
        stripped = line.strip()
        if not stripped:
            return False
        return all(ch in {'-', ' '} for ch in stripped) and stripped.count('-') >= 6

    def _convert_block(block: List[str]) -> Optional[str]:
        inner = [ln.rstrip() for ln in block[1:-1]]
        rows = [ln.strip() for ln in inner if ln.strip() and not _is_rule(ln)]
        if len(rows) < 2:
            return None

        split_rows = [re.split(r'\s{2,}', row) for row in rows]
        col_count = max(len(r) for r in split_rows)
        if col_count < 2:
            return None

        def _pad(row: List[str]) -> List[str]:
            padded = [cell.strip() for cell in row]
            while len(padded) < col_count:
                padded.append('')
            return padded[:col_count]

        latex_lines = ["\\begin{center}", f"\\begin{{tabular}}{{{'c' * col_count}}}", "\\hline"]

        header = _pad(split_rows[0])
        latex_lines.append(" & ".join(escape_latex_special(cell, False) for cell in header) + r" \\")
        latex_lines.append("\\hline")

        for row in split_rows[1:]:
            cells = _pad(row)
            latex_lines.append(" & ".join(escape_latex_special(cell, False) for cell in cells) + r" \\")

        latex_lines.append("\\hline")
        latex_lines.append("\\end{tabular}")
        latex_lines.append("\\end{center}")
        return "\n".join(latex_lines)

    while i < len(lines):
        if _is_rule(lines[i]):
            j = i + 1
            while j < len(lines) and not _is_rule(lines[j]):
                j += 1
            if j < len(lines):
                block = lines[i:j + 1]
                converted = _convert_block(block)
                if converted:
                    result.append(converted)
                    i = j + 1
                    continue
        result.append(lines[i])
        i += 1

    return "\n".join(result)


def normalize_fullwidth_brackets(text: str) -> str:
    """🆕 v1.6.3：统一全角括号为半角

    注意：不要替换用于 meta 标记的【】
    """
    pairs = {
        "（": "(",
        "）": ")",
        "｛": "{",
        "｝": "}",
        # 不替换 ［］，避免影响某些 Markdown 语法
    }
    for fw, hw in pairs.items():
        text = text.replace(fw, hw)
    return text


def clean_markdown(text: str) -> str:
    """清理 markdown 垃圾

    🆕 v1.3 改进：统一中英文标点
    🆕 v1.6.3：增强全角括号统一
    """
    # 🆕 v1.6.3：首先统一全角括号
    text = normalize_fullwidth_brackets(text)

    text = re.sub(
        r"<br><span class='markdown-page-line'>.*?</span><br><br>",
        "\n", text, flags=re.S,
    )
    text = re.sub(
        r"<span id='page\d+' class='markdown-page-text'>\[.*?\]</span>",
        "", text,
    )

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 预清理装饰性图片及其属性
    text = remove_decorative_images(text)
    text = clean_image_attributes(text)

    # 🆕 v1.3 改进：统一中英文标点
    # 保护已有的LaTeX命令
    protected = []
    def save_latex_cmd(match):
        protected.append(match.group(0))
        return f"@@LATEXCMD{len(protected)-1}@@"
    text = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', save_latex_cmd, text)

    # 统一括号（全角→半角）- 已在 normalize_fullwidth_brackets 中处理
    text = text.replace('（', '(').replace('）', ')')
    # 统一引号（弯引号→直引号）
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")

    # 恢复LaTeX命令
    for i, cmd in enumerate(protected):
        text = text.replace(f"@@LATEXCMD{i}@@", cmd)

    # 清理代码块标记
    text = re.sub(r'```[a-z]*\n?', '', text)
    text = re.sub(r'```', '', text)

    # 转换表格
    text = convert_ascii_table_blocks(text)
    if '|' in text and '---' in text:
        text = convert_markdown_table_to_latex(text)

    # 处理下划线
    text = text.replace(r'\_', '@@ESCAPED_UNDERSCORE@@')
    text = re.sub(r'(?<!\\)_(?![{_])', r'\\_', text)
    text = text.replace('@@ESCAPED_UNDERSCORE@@', r'\_')

    return text.strip()


# ==================== 题目解析函数 ====================

def split_sections(text: str) -> List[Tuple[str, str]]:
    """拆分章节（支持 markdown 标题和加粗格式）
    
    支持两种格式：
    1. Markdown 标题：# 一、单选题
    2. 加粗格式：**一、单选题**
    """
    lines = text.splitlines()
    sections = []
    current_title = None
    current_lines = []

    for line in lines:
        stripped = line.strip()
        # 优先匹配 markdown 标题格式
        m = re.match(
            r"^#+\s*(一、单选题|二、单选题|二、多选题|三、填空题|四、解答题)",
            stripped,
        )
        # 如果不匹配，尝试匹配加粗格式 **章节标题**
        if not m:
            m = re.match(
                r"^\*\*(一、单选题|二、单选题|二、多选题|三、填空题|四、解答题)\*\*",
                stripped,
            )
        
        if m:
            if current_title is not None:
                sections.append((current_title, "\n".join(current_lines).strip()))
                current_lines = []
            current_title = m.group(1)
        else:
            if current_title is not None:
                current_lines.append(line)

    if current_title is not None and current_lines:
        sections.append((current_title, "\n".join(current_lines).strip()))

    return sections


def split_questions(section_body: str) -> List[str]:
    """拆分题目（智能合并相同题号）
    
    🆕 v1.8.5：改进题目拆分逻辑，避免将解答题的小问误识别为新题
    - 只在题号连续递增时才拆分新题
    - 相同题号或题号不连续的行不会被拆分（可能是小问）
    
    修复：连续相同题号的内容会合并到一个题目中
    例如：17. 题干  17. (1)...  17. (2)... → 合并为一题
    """
    lines = section_body.splitlines()
    blocks = []
    current = []
    last_question_num = 0  # 记录上一题的题号，初始为0

    def flush():
        if current:
            blocks.append("\n".join(current).strip())
            current.clear()

    for line in lines:
        stripped = line.strip()
        # 匹配题号：1. 或 1． 或 1、
        match = re.match(r"^(\d+)[\.．、]\s*", stripped)
        if match:
            num = int(match.group(1))
            # 只有在题号连续递增时才认为是新题
            # 或者是第一题（last_question_num == 0）
            if last_question_num == 0 or num == last_question_num + 1:
                flush()
                last_question_num = num
                current.append(line)
            else:
                # 题号不连续（包括相同题号），可能是小问标号，不拆分
                current.append(line)
        else:
            current.append(line)

    flush()
    return blocks


def extract_context_around_image(text: str, img_match_start: int, img_match_end: int,
                                  context_len: int = 50) -> Tuple[str, str]:
    """提取图片前后的上下文文本

    Args:
        text: 完整文本
        img_match_start: 图片匹配的起始位置
        img_match_end: 图片匹配的结束位置
        context_len: 上下文长度（字符数）

    Returns:
        (context_before, context_after) 元组
    """
    # 提取前文
    before_start = max(0, img_match_start - context_len)
    context_before = text[before_start:img_match_start].strip()
    # 清理换行符和多余空格
    context_before = ' '.join(context_before.split())

    # 提取后文
    after_end = min(len(text), img_match_end + context_len)
    context_after = text[img_match_end:after_end].strip()
    context_after = ' '.join(context_after.split())

    return context_before, context_after


def extract_meta_and_images(block: str, question_index: int = 0, slug: str = "") -> Tuple[str, Dict, List, List]:
    r"""提取元信息、图片与附件（状态机重构：防止跨题累积）

    🆕 v1.9: 新增附件识别与提取
    🆕 新增参数：question_index 和 slug 用于生成图片 ID

    目标：避免上一题的多行【详解】/【分析】错误吞并下一题题干。
    关键边界：
      - 新的 meta 开始（答案/难度/知识点/详解/分析）
      - 题号开始：^\s*>?\s*(?:\d+[\.．、]\s+|（\d+）\s+|\d+\)\s+)
      - 章节标题：^#{1,6}\s*(第?[一二三四五六七八九十]+[、．.].*)$
      - 空行 + lookahead 为题号时，作为安全边界（若上一行像环境续行则跳过该空行边界）
      - 引述空行 ^>\s*$ 忽略
      - 🆕 附件标记：^附[:：]、^附表、^参考数据表

    Returns:
        (content, meta, images, attachments) 四元组
        attachments: List[Dict] 包含 kind, lines 字段
    """
    # 规范化并切分行
    lines = block.splitlines()

    # 结果容器
    meta = {k: "" for k in META_PATTERNS}
    # 🆕 修复：analysis 单独存在，后续会被丢弃
    meta_alias_map = {
        "analysis": "analysis",  # analysis 单独存在，后面会被丢弃
        "explain": "explain",
        "answer": "answer",
        "difficulty": "difficulty",
        "topics": "topics",
    }

    content_lines: List[str] = []
    images: List[Dict] = []
    attachments: List[Dict] = []  # 🆕 附件列表

    # 编译边界正则（增强版：支持更多题号格式和章节标题）
    question_start_perm = re.compile(r"^\s*>?\s*(?:\d{1,3}[\.．、]\s+|（\d{1,3}）\s+|\d{1,3}\)\s+)")
    section_header = re.compile(r"^#{1,6}\s*(第?[一二三四五六七八九十]+[、．.].*)$")
    quote_blank = re.compile(r"^>\s*$")
    env_cont_hint = re.compile(r"(\\\\\s*$)|\\begin\{|\\left|\\right")

    # 🆕 v1.9: 附件标记正则
    attachment_start = re.compile(r"^(附[:：]|附表|参考数据表)")
    markdown_table_line = re.compile(r"^\s*\|.*\|.*$")  # Markdown 表格行
    box_drawing_chars = re.compile(r"[│─┌┐└┘┼├┤┬┴]")  # Box-drawing 字符

    # 🆕 修复：将 META_PATTERNS 编译，分离 analysis 和 explain
    meta_starts = [
        ("answer", re.compile(r"^【\s*答案\s*】[:：]?\s*(.*)$")),
        ("difficulty", re.compile(r"^【\s*难度\s*】[:：]?\s*([\d.]+).*")),
        ("topics", re.compile(r"^【\s*(知识点|考点)\s*】[:：]?\s*(.*)$")),
        ("analysis", re.compile(r"^【\s*分析\s*】[:：]?\s*(.*)$")),
        ("explain", re.compile(r"^【\s*详解\s*】[:：]?\s*(.*)$")),
        ("diangjing", re.compile(r"^【\s*点睛\s*】[:：]?\s*(.*)$")),
        ("dianjing_alt", re.compile(r"^【\s*点评\s*】[:：]?\s*(.*)$")),
    ]

    # 状态
    state = "NORMAL"  # or "IN_META" or "IN_ATTACHMENT"
    current_meta_key: Optional[str] = None
    current_meta_lines: List[str] = []

    # 🆕 v1.9: 附件状态
    current_attachment_lines: List[str] = []
    current_attachment_kind: Optional[str] = None  # "table", "text", "figure"

    def flush_meta():
        nonlocal current_meta_key, current_meta_lines
        if current_meta_key is None:
            return
        # 归一化到别名键
        key = meta_alias_map.get(current_meta_key, current_meta_key)
        # 🆕 修复：遇到 analysis/diangjing/dianjing_alt 时直接丢弃
        if key in ("analysis", "diangjing", "dianjing_alt"):
            # 说明这是【分析】/【点睛】/【点评】段，直接舍弃，不写入 meta 字典
            current_meta_key = None
            current_meta_lines = []
            return
        # 合并清理
        text = "\n".join(current_meta_lines)
        # 去掉可能残留的标签前缀
        text = re.sub(r"^【?(?:答案|难度|知识点|考点|详解|分析)】?[:：]?\s*", "", text)
        # 对于 explain 字段，保留原始格式（不折叠空行），让后续 remove_par_breaks_in_explain 处理
        # 其他字段压缩空行
        if key != "explain":
            text = re.sub(r"\n\s*\n+", "\n", text)
        # 合并：若已有 explain，则追加一行
        if key == "explain" and meta.get("explain"):
            meta["explain"] = (meta["explain"] + "\n" + text.strip()).strip()
        else:
            meta[key] = text.strip()
        # 重置
        current_meta_key = None
        current_meta_lines = []

    def flush_attachment():
        """🆕 v1.9: 刷新附件缓冲区"""
        nonlocal current_attachment_lines, current_attachment_kind
        if not current_attachment_lines or current_attachment_kind is None:
            current_attachment_lines = []
            current_attachment_kind = None
            return

        # 添加到附件列表
        attachments.append({
            "kind": current_attachment_kind,
            "lines": current_attachment_lines.copy()
        })

        # 重置
        current_attachment_lines = []
        current_attachment_kind = None

    def is_question_start(s: str) -> bool:
        return bool(question_start_perm.match(s))

    def is_section_header(s: str) -> bool:
        return bool(section_header.match(s))

    def image_match(s: str):
        # 优先匹配带ID的图片
        m = IMAGE_PATTERN_WITH_ID.search(s)
        if m:
            return ('with_id', m)
        # 然后匹配无ID的图片
        m = IMAGE_PATTERN_NO_ID.search(s)
        if m:
            return ('no_id', m)
        # 最后尝试旧版简单格式
        m = IMAGE_PATTERN.search(s)
        if m:
            return ('simple', m)
        return None

    # 查找上一条非空行（用于环境续行判断）
    def find_prev_nonempty(idx: int) -> Optional[str]:
        j = idx - 1
        while j >= 0:
            if lines[j].strip():
                return lines[j]
            j -= 1
        return None

    # 查找下一条非空行（用于 blank+lookahead 判断）
    def find_next_nonempty(idx: int) -> Optional[str]:
        j = idx + 1
        while j < len(lines):
            if lines[j].strip():
                return lines[j]
            j += 1
        return None

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # 🆕 v1.6.2：图片行识别增强 - 区分独立图片块 vs 内联公式图片
        # 只有当图片"独占一行"且是完整匹配时，才提取为图片块
        # 内联图片（如 "已知集合![](image2.wmf)，则..."）保留在文本中
        # 🆕 Prompt 3: 统一处理所有图片（独立和内联）
        # 检查整行是否包含图片标记
        img_result = image_match(line)  # 注意：使用完整行而非stripped
        if img_result:
            img_type, m_img = img_result
            # 检查是否为独立图片行：整行只有一个图片标记
            is_standalone = (m_img.group(0).strip() == stripped)

            # 🆕 生成图片 ID 和提取上下文
            img_counter = len(images) + 1
            generated_id = f"{slug}-Q{question_index}-img{img_counter}" if slug else f"Q{question_index}-img{img_counter}"

            # 提取上下文
            full_text = "\n".join(lines)
            img_start = full_text.find(m_img.group(0))
            img_end = img_start + len(m_img.group(0))
            context_before, context_after = extract_context_around_image(full_text, img_start, img_end)

            if is_standalone:
                # 独立图片块：提取到images列表
                if img_type == 'with_id':
                    # ![@@@id](path){...}
                    img_id = m_img.group(1)
                    path = m_img.group(2).strip()
                    images.append({
                        "path": path,
                        "width": 60,
                        "id": generated_id,
                        "inline": False,
                        "question_index": question_index,
                        "sub_index": 1,
                        "context_before": context_before,
                        "context_after": context_after
                    })
                elif img_type == 'no_id':
                    # ![](path){...}
                    path = m_img.group(1).strip()
                    images.append({
                        "path": path,
                        "width": 60,
                        "id": generated_id,
                        "inline": False,
                        "question_index": question_index,
                        "sub_index": 1,
                        "context_before": context_before,
                        "context_after": context_after
                    })
                else:
                    # 简单格式: ![](images/...)
                    path = m_img.group(1)
                    width = int(m_img.group(2)) if m_img.group(2) else 60
                    images.append({
                        "path": path,
                        "width": width,
                        "id": generated_id,
                        "inline": False,
                        "question_index": question_index,
                        "sub_index": 1,
                        "context_before": context_before,
                        "context_after": context_after
                    })
                i += 1
                continue
            else:
                # 内联图片：替换为占位符，记录到images列表
                if img_type == 'with_id':
                    img_id = m_img.group(1)
                    path = m_img.group(2).strip()
                    images.append({
                        "path": path,
                        "width": 60,
                        "id": generated_id,
                        "inline": True,
                        "question_index": question_index,
                        "sub_index": 1,
                        "context_before": context_before,
                        "context_after": context_after
                    })
                elif img_type == 'no_id':
                    path = m_img.group(1).strip()
                    images.append({
                        "path": path,
                        "width": 60,
                        "id": generated_id,
                        "inline": True,
                        "question_index": question_index,
                        "sub_index": 1,
                        "context_before": context_before,
                        "context_after": context_after
                    })
                else:
                    path = m_img.group(1)
                    width = int(m_img.group(2)) if m_img.group(2) else 60
                    images.append({
                        "path": path,
                        "width": width,
                        "id": generated_id,
                        "inline": True,
                        "question_index": question_index,
                        "sub_index": 1,
                        "context_before": context_before,
                        "context_after": context_after
                    })

                # 替换图片标记为占位符（使用新的 ID 格式）
                line = line.replace(m_img.group(0), f"<<IMAGE_INLINE:{generated_id}>>")
                # 继续处理该行（fallthrough）

        # 引述空行：丢弃
        if quote_blank.match(stripped):
            i += 1
            continue

        if state == "NORMAL":
            # 🆕 v1.9: 检测附件开始
            if attachment_start.match(stripped):
                # 进入附件状态
                state = "IN_ATTACHMENT"
                current_attachment_lines = [line]
                # 判断附件类型（初步）
                if "表" in stripped or markdown_table_line.match(stripped):
                    current_attachment_kind = "table"
                elif box_drawing_chars.search(stripped):
                    current_attachment_kind = "table"
                else:
                    current_attachment_kind = "text"
                i += 1
                continue

            # 新的 meta 开始？
            started = False
            for key, pat in meta_starts:
                m = pat.match(stripped)
                if m:
                    state = "IN_META"
                    current_meta_key = key
                    seed = m.group(m.lastindex or 1) if m.groups() else ""
                    current_meta_lines = [seed.strip()] if seed.strip() else []
                    started = True
                    break
            if started:
                i += 1
                continue

            # 普通内容
            content_lines.append(line)
            i += 1
            continue

        elif state == "IN_META":
            # state == IN_META
            # 1) 新 meta 开始 -> 刷新并切换
            started = False
            for key, pat in meta_starts:
                m = pat.match(stripped)
                if m:
                    flush_meta()
                    state = "IN_META"
                    current_meta_key = key
                    seed = m.group(m.lastindex or 1) if m.groups() else ""
                    current_meta_lines = [seed.strip()] if seed.strip() else []
                    started = True
                    break
            if started:
                i += 1
                continue

            # 2) 确认题号或章节边界 -> 结束 meta，保留该行给题干
            if is_question_start(stripped) or is_section_header(stripped):
                flush_meta()
                state = "NORMAL"
                content_lines.append(line)
                i += 1
                continue

            # 3) 空行 + lookahead 为题号 -> 安全地结束 meta
            if stripped == "":
                next_ne = find_next_nonempty(i)
                if next_ne and is_question_start(next_ne.strip()):
                    prev_ne = find_prev_nonempty(i)
                    # 若上一非空行看起来是环境续行，则不要在此空行切断
                    if prev_ne and env_cont_hint.search(prev_ne):
                        # 继续把空行也并入 meta（保持原样）
                        current_meta_lines.append(line)
                        i += 1
                        continue
                    # 否则切断 meta（不消费空行）
                    flush_meta()
                    state = "NORMAL"
                    i += 1  # 跳过该空行，下一轮看到题号行会进入 NORMAL 流程
                    continue

            # 4) 继续累积 meta 内容
            current_meta_lines.append(line)
            i += 1
            continue

        elif state == "IN_ATTACHMENT":
            # 附件状态处理
            # 1) 新 meta 开始 -> 刷新附件并切换到 meta
            started = False
            for key, pat in meta_starts:
                m = pat.match(stripped)
                if m:
                    flush_attachment()
                    state = "IN_META"
                    current_meta_key = key
                    seed = m.group(m.lastindex or 1) if m.groups() else ""
                    current_meta_lines = [seed.strip()] if seed.strip() else []
                    started = True
                    break
            if started:
                i += 1
                continue

            # 2) 确认题号或章节边界 -> 结束附件，保留该行给题干
            if is_question_start(stripped) or is_section_header(stripped):
                flush_attachment()
                state = "NORMAL"
                content_lines.append(line)
                i += 1
                continue

            # 3) 空行 - 可能结束附件
            if stripped == "":
                next_ne = find_next_nonempty(i)
                # 如果下一行是题号、meta标记或章节标题，则结束附件
                if next_ne and (is_question_start(next_ne.strip()) or
                               is_section_header(next_ne.strip()) or
                               any(pat.match(next_ne.strip()) for _, pat in meta_starts)):
                    flush_attachment()
                    state = "NORMAL"
                    i += 1
                    continue
                # 否则继续累积（可能是附件内的空行）
                current_attachment_lines.append(line)
                i += 1
                continue

            # 4) 继续累积附件内容
            # 动态更新附件类型
            if markdown_table_line.match(stripped):
                current_attachment_kind = "table"
            elif box_drawing_chars.search(stripped):
                current_attachment_kind = "table"

            current_attachment_lines.append(line)
            i += 1
            continue

    # 循环结束，若还在 meta 或 attachment 状态则刷新
    if state == "IN_META":
        flush_meta()
    elif state == "IN_ATTACHMENT":
        flush_attachment()

    content = "\n".join(content_lines).strip()
    return content, meta, images, attachments


def parse_question_structure(content: str) -> Dict:
    """智能识别题目结构（增强版）
    
    解析题干、选项、解析三部分，避免将解析文本混入选项
    """
    lines = content.splitlines()
    
    structure = {
        'stem_lines': [],
        'choices': [],
        'analysis_lines': [],
        'in_choice': False,
        'in_analysis': False,
        'current_choice': '',
        'skip_analysis_block': False,
    }
    
    choice_pattern = re.compile(r'^([A-D])[\.．、]\s*(.*)$')
    analysis_marker = re.compile(r'^【?\s*分析\s*】[:：]?')
    explain_marker = re.compile(r'^【?\s*详解\s*】[:：]?\s*(.*)$')
    
    for line in lines:
        stripped = line.strip()
        normalized = re.sub(r'^>+\s*', '', stripped)

        if structure['skip_analysis_block']:
            if normalized.startswith('【'):
                structure['skip_analysis_block'] = False
            else:
                continue

        # 🆕 修复：只在遇到【详解】时进入解析模式，遇到【分析】时跳过
        if analysis_marker.match(normalized):
            structure['in_choice'] = False
            structure['in_analysis'] = False
            structure['skip_analysis_block'] = True
            continue

        explain_match = explain_marker.match(normalized)
        if explain_match:
            if structure['current_choice']:
                structure['choices'].append(structure['current_choice'].strip())
                structure['current_choice'] = ''
            structure['in_choice'] = False
            structure['in_analysis'] = True
            remainder = explain_match.group(1).strip()
            if remainder:
                structure['analysis_lines'].append(remainder)
            continue

        # 匹配选项标记 (A. B. C. D.)
        m = choice_pattern.match(normalized)
        if m:
            if structure['current_choice']:
                structure['choices'].append(structure['current_choice'].strip())
            
            structure['current_choice'] = m.group(2)
            structure['in_choice'] = True
            structure['in_analysis'] = False
            continue
        
        # 根据当前状态分配行
        if structure['in_analysis']:
            structure['analysis_lines'].append(line)
        elif structure['in_choice']:
            structure['current_choice'] += ' ' + normalized
        else:
            structure['stem_lines'].append(line)
    
    if structure['current_choice']:
        structure['choices'].append(structure['current_choice'].strip())
    
    return structure


def split_inline_choice_line(line: str) -> List[str]:
    """将单行多选项（含 $$ 数学公式）拆成独立字符串

    修复 P0-002: 使用保护-分割-恢复策略，避免数学公式干扰选项分割
    """
    text = re.sub(r'^>+\s*', '', line.strip())
    if not text:
        return []

    # 步骤1: 保护数学公式
    math_blocks = []
    def save_math(match):
        math_blocks.append(match.group(0))
        return f'@@MATH{len(math_blocks)-1}@@'

    # 保护所有数学模式：$$...$$, $...$, \(...\), \[...\]
    protected = re.sub(r'\$\$[^$]+\$\$|\$[^$]+\$|\\[()\[].*?\\[)\]]', save_math, text, flags=re.DOTALL)

    # 步骤2: 使用 finditer 找到所有选项标记及其位置
    option_pattern = re.compile(r'([A-D][．.])\s*')
    matches = list(option_pattern.finditer(protected))

    if not matches:
        return []

    # 步骤3: 提取每个选项的内容
    segments: List[str] = []
    for i, match in enumerate(matches):
        option_marker = match.group(1)
        start = match.end()

        # 确定内容结束位置（下一个选项标记的开始，或字符串末尾）
        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(protected)

        # 提取选项内容
        content = protected[start:end].strip()

        # 恢复数学公式
        for j, block in enumerate(math_blocks):
            content = content.replace(f'@@MATH{j}@@', block)

        segments.append(f'{option_marker} {content}')

    return segments


def expand_inline_choices(content: str) -> str:
    """展开单行/多行引述选项并去除'>'前缀"""
    output_lines: List[str] = []
    pending_block: List[str] = []

    def flush_pending():
        nonlocal pending_block
        if not pending_block:
            return

        normalized = " ".join(re.sub(r'^>+\s*', '', ln).strip() for ln in pending_block if ln.strip())
        marker_count = len(re.findall(r'[A-D][．\.\、]', normalized))
        if marker_count >= 2:
            expanded = split_inline_choice_line(normalized)
            if expanded:
                output_lines.extend(expanded)
            else:
                output_lines.extend(pending_block)
        elif marker_count == 1:
            expanded = split_inline_choice_line(normalized)
            if expanded:
                output_lines.extend(expanded)
            else:
                output_lines.extend(pending_block)
        else:
            output_lines.extend(pending_block)
        pending_block = []

    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith('>'):
            pending_block.append(line)
            continue

        flush_pending()
        output_lines.append(line)

    flush_pending()
    return '\n'.join(output_lines)


def convert_choices(content: str) -> Tuple[str, List[str], str]:
    """拆分题干、选项、解析（增强版）
    
    🆕 v1.4 改进：先展开单行选项再解析
    """
    # 🆕 先展开可能的单行选项
    content = expand_inline_choices(content)
    
    structure = parse_question_structure(content)
    
    stem = '\n'.join(structure['stem_lines']).strip()
    stem = re.sub(r"^\s*\d+[\.．、]\s*", "", stem)
    
    # 提取的解析内容
    analysis = '\n'.join(structure['analysis_lines']).strip()
    
    return stem, structure['choices'], analysis


def handle_subquestions(content: str) -> str:
    r"""处理解答题的小题编号

    🆕 v1.7：统一小问编号格式，不添加 \mathrm
    🆕 v1.9：保留题干前导文本并自动包裹 enumerate
    """
    if not re.search(r'\(\d+\)', content):
        return content

    parts = re.split(r'\((\d+)\)', content)
    if len(parts) < 3:
        return content

    prefix = parts[0].strip()
    subquestions = []
    for i in range(1, len(parts), 2):
        if i + 1 >= len(parts):
            break
        num = parts[i]
        body = parts[i + 1].strip()
        if body:
            subquestions.append((num, body))

    if len(subquestions) < 2:
        return content

    result_lines: List[str] = []
    if prefix:
        result_lines.append(prefix)

    result_lines.append(r"\begin{enumerate}[label=(\arabic*)]")
    for _, content_text in subquestions:
        result_lines.append(f"  \\item {content_text}")
    result_lines.append(r"\end{enumerate}")

    return '\n'.join(result_lines)


def ensure_choices_environment(lines: List[str], has_options: bool) -> List[str]:
    r"""如果存在 \item 但缺少 choices 环境，则自动补充"""
    if not has_options:
        return lines

    has_begin = any(r"\begin{choices}" in line for line in lines)
    has_end = any(r"\end{choices}" in line for line in lines)
    item_indices = [
        idx for idx, line in enumerate(lines)
        if re.match(r'\s*\\item\b', line)
    ]

    if item_indices and not has_begin:
        insert_at = item_indices[0]
        lines.insert(insert_at, r"\begin{choices}")
        item_indices = [idx + 1 if idx >= insert_at else idx for idx in item_indices]
        has_begin = True

    if item_indices and has_begin and not has_end:
        insert_at = item_indices[-1] + 1
        lines.insert(insert_at, r"\end{choices}")

    return lines


def _smart_replace_because_therefore(text: str) -> str:
    """智能替换 ∵/∴ 符号为 LaTeX 命令
    
    🆕 v1.9.6：根据符号位置决定是否需要包裹在数学模式内
    
    规则：
    1. 如果 ∵/∴ 在 $$...$$ 内部，直接替换为 \\because/\\therefore
    2. 如果 ∵/∴ 在 $$...$$ 外部，替换为 \\(\\because\\)/\\(\\therefore\\)
    
    判断方法：计算符号前的 $$ 数量，奇数 = 在数学内，偶数 = 在数学外
    """
    if not text:
        return text
    
    def replace_symbol(symbol: str, latex_cmd: str, text: str) -> str:
        if symbol not in text:
            return text
        
        result = []
        last_pos = 0
        
        for i, char in enumerate(text):
            if char == symbol:
                # 计算此位置前 $$ 的数量
                before = text[:i]
                dollar_count = before.count('$$')
                
                # 奇数 = 在数学模式内，偶数 = 在数学模式外
                in_math = dollar_count % 2 == 1
                
                result.append(text[last_pos:i])
                
                if in_math:
                    # 在数学模式内，直接替换
                    result.append(f'\\{latex_cmd} ')
                else:
                    # 在数学模式外，需要包裹
                    result.append(f'\\(\\{latex_cmd}\\) ')
                
                last_pos = i + 1
        
        result.append(text[last_pos:])
        return ''.join(result)
    
    text = replace_symbol('∵', 'because', text)
    text = replace_symbol('∴', 'therefore', text)
    
    return text


# DEPRECATED: 状态机已避免这些行内异常，保留兜底测试使用
def fix_inline_math_glitches(text: str) -> str:
    """🆕 修复行内数学的各种异常模式

    修复：
    - 空的 $$
    - $$$x$ → $x$
    - \therefore$$ → \therefore
    - \because$$ → \because
    """
    if not text:
        return text

    # 1. 去掉完全空的 $$
    text = re.sub(r'\$\s*\$', '', text)

    # 2. 修复 $$$x$ → $x$
    text = re.sub(r'\$\s*\$\s*(\\\()', r'\1', text)

    # 3. 特例：\therefore$$ → \therefore
    text = re.sub(r'(\\therefore)\s*\$\s*\$', r'\1', text)

    # 4. 特例：\because$$ → \because
    text = re.sub(r'(\\because)\s*\$\s*\$', r'\1', text)

    return text


def process_text_for_latex(text: str, is_math_heavy: bool = False) -> str:
    r"""统一入口：题干/选项/解析文本的 LaTeX 处理（状态机版）

    重构目标：
    1. 保留原有“非数学”清理与转义逻辑（故选/【详解】/OCR 边界修复等）
    2. 用 MathStateMachine 完全替换旧的 smart_inline_math / sanitize_math 等正则管线
    3. 数学定界符统一：$...$ / $$...$$ → \(...\)，保持已有 \(...\) 不重复包裹
    4. 在状态机处理后做轻量兜底清理（空数学块、图片属性残留等）
    """
    if not text:
        return text

    # ---------- 1. 前置：纯文本/非数学层面清理（原逻辑保留） ----------
    text = re.sub(r'\*\s*(\$[^$]+\$)\s*\*', r'\1', text)  # *$x$* → $x$
    text = re.sub(r'\*([A-Za-z0-9])\*', r'\\emph{\1}', text)  # *x* → \emph{x}

    # "故选" / "故答案为" 系列清理
    text = re.sub(r'[,，。\.;；]\s*故选[:：][ABCD]+[.。]?\s*$', '', text)
    text = re.sub(r'\n+故选[:：][ABCD]+[.。]?\s*$', '', text)
    text = re.sub(r'^\s*故选[:：][ABCD]+[.。]?\s*', '', text)
    text = re.sub(r'\n+故答案为[:：]', '', text)
    text = re.sub(r'^\s*故选[:：][ABCD]+[.。]?\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'[，,]?\s*故选[:：]\s*[ABCD]+[。．.]*\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^【?详解】?[:：]?\s*', '', text)

    # OCR 边界畸形预处理（保持原逻辑）
    text = re.sub(r'\\\\right\.\s*\\\\\\\)', r'\\\\right.', text)
    text = re.sub(r'\\\\right\.\\\\\+\)', r'\\\\right.', text)

    # Unicode 符号替换（智能处理 ∵/∴）
    # 🆕 v1.9.6：根据符号位置决定是否需要包裹在数学模式内
    if '∵' in text or '∴' in text:
        text = _smart_replace_because_therefore(text)

    # 非数学模式下的 LaTeX 特殊字符转义
    if not is_math_heavy:
        text = escape_latex_special(text, in_math_mode=False)

    # ---------- 2. 数学模式统一：状态机处理 ----------
    global math_sm
    text = math_sm.process(text)

    # ---------- 2.5. 标准化数学符号（在状态机之后） ----------
    text = standardize_math_symbols(text)

    # ---------- 3. 轻量后处理：常见空块/残留修复 ----------
    text = fix_common_issues_v2(text)

    # ---------- 3.5. 修复未闭合的数学模式 ----------
    text = fix_unclosed_math_mode(text)

    return text


def fix_unclosed_math_mode(text: str) -> str:
    """修复未闭合的数学模式（如 \\(text\\)text}）

    修复模式：
    1. \\)text} → \\)text（删除多余的}）
    2. \\(text未闭合 → \\(text\\)
    """
    if not text:
        return text

    # 模式1: \\)后面跟着文本和}，删除多余的}
    # 例如: \\)相交但不过圆心} → \\)相交但不过圆心
    text = re.sub(r'(\\\))([^}]*?)\}(\s*\\end\{)', r'\1\2\3', text)

    return text


def fix_common_issues_v2(text: str) -> str:
    r"""状态机后的兜底纯文本修复（只处理不改变数学语义的残留）

    包含：
    - 空的行内/显示数学块 \(\) / \[\] 删除
    - \because\(\) / \therefore\(\) 清理为纯命令
    - OCR 产生的数组边界畸形（\right.\\) → \right.\)）
    - 图片残余属性清理（利用原 clean_residual_image_attrs）
    - 去除孤立的重复显示公式定界符（状态机已规范，兜底防御）
    """
    if not text:
        return text
    # 空数学块
    text = re.sub(r'\\\(\s*\\\)', '', text)
    text = re.sub(r'\\\[\s*\\\]', '', text)
    # 清理 \because\(\) / \therefore\(\)
    text = re.sub(r'\\because\s*\\\(\\\)', r'\\because ', text)
    text = re.sub(r'\\therefore\s*\\\(\\\)', r'\\therefore ', text)
    # 数组/分段等环境边界畸形（与 complete 版本保持一致）
    text = text.replace(r'\right.\\)', r'\right.\)')
    text = text.replace(r'\right)\\)', r'\right)\)')
    # 图片属性残留（复用已有函数）
    text = clean_residual_image_attrs(text)
    # 移除任何残留的裸 $$（状态机后理论上不会出现）
    text = text.replace('$$', '')

    # 清理外层多余美元: $\(x\)$ → \(x\)
    text = re.sub(r'\$(\\\([^$]+?\\\))\$', r'\1', text)
    # 清理 $\because$ → \because （以及 \therefore）
    text = re.sub(r'\$(\\because)\$', r'\1', text)
    text = re.sub(r'\$(\\therefore)\$', r'\1', text)
    # 清理简单变量形式 $x$ 若单字符且不在已有数学（保守：仅字母/数字）→ \(x\)
    def _wrap_simple_var(m: re.Match) -> str:
        var = m.group(1)
        return f'\\({var}\\)'
    text = re.sub(r'(?<!\\)\$([a-zA-Z0-9])\$', _wrap_simple_var, text)
    # 再次移除可能产生的空数学块 \(\)
    text = re.sub(r'\\\(\s*\\\)', '', text)
    # 去除遗留的孤立单美元（不在配对内）：删除
    # 匹配单独一行只包含 $ 或行首/行末的单美元
    text = re.sub(r'(^|\s)(\$)(?=\s|$)', lambda m: m.group(1), text)
    
    # 🔧 v1.9.3: 移除 v1.8.6 的错误合并逻辑
    # 原策略错误地将 \(D\)均在球\(O\) 合并成 \(D均在球O\)
    # 正确行为是保持各个独立变量的数学模式分隔
    # 
    # 已删除的错误代码：
    # - 策略1: text = re.sub(r'\\\)([\u4e00-\u9fa5]{1,3})\\\(', r'\1', text)
    # - 策略2: text = re.sub(r'(\\right\.)\\\)...', r'\1\2', text)
    # - 策略3: 重复的策略1
    
    return text


INLINE_MATH_PATTERN = re.compile(r'\\\((.+?)\\\)')
TRAILING_MATH_PUNCT = set('，。！？；：,.!?、;:')
CJK_CHAR_RE = re.compile(
    r'['
    r'\u3400-\u4dbf'
    r'\u4e00-\u9fff'
    r'\uf900-\ufaff'
    r']'
)
CJK_PUNCT_CHARS = set('，。！？；：、“”‘’（）《》【】—……·、')
MATH_BLACKLIST_TOKENS = [
    '=', '+', '-', '^', '_',
    '\\frac', '\\sum', '\\int', '\\times', '\\div',
    '\\sqrt', '\\log', '\\sin', '\\cos', '\\tan',
]


def _is_cjk_char(ch: str) -> bool:
    return bool(CJK_CHAR_RE.match(ch)) or ch in CJK_PUNCT_CHARS


def _split_trailing_punct(segment: str) -> Tuple[str, str]:
    idx = len(segment)
    while idx > 0 and segment[idx - 1].isspace():
        idx -= 1
    punct_end = idx
    while idx > 0 and segment[idx - 1] in TRAILING_MATH_PUNCT:
        idx -= 1
    core = segment[:idx].rstrip()
    trailing = segment[idx:punct_end]
    return core, trailing


def _should_unwrap_inline_math(content: str) -> bool:
    tokenized = content.strip()
    if not tokenized:
        return True

    filtered = ''.join(ch for ch in tokenized if not ch.isspace())
    if not filtered:
        return True

    cjk_chars = sum(1 for ch in filtered if _is_cjk_char(ch))
    ratio = cjk_chars / len(filtered)
    if ratio <= 0.7:
        return False

    lowered = filtered.lower()
    for token in MATH_BLACKLIST_TOKENS:
        if token in lowered:
            return False

    return True


def postprocess_inline_math(line: str) -> str:
    """清洗内联数学环境，移除标点并拆掉纯中文"""
    if r'\(' not in line:
        return line

    def _replace(match: re.Match) -> str:
        inner = match.group(1)
        core, trailing = _split_trailing_punct(inner)
        normalized = core.strip()

        if not normalized:
            return trailing

        if _should_unwrap_inline_math(normalized):
            return normalized + trailing

        return f"\\({normalized}\\){trailing}"

    return INLINE_MATH_PATTERN.sub(_replace, line)


def validate_brace_balance(tex: str) -> List[str]:
    """🆕 v1.8.6：全局花括号检查 - 忽略 \\{ \\} 和注释，只统计裸 { }

    返回形如：
    - "Line 555: extra '}' (brace balance went negative)"
    - "Global brace imbalance at EOF: balance=..."
    """
    issues: List[str] = []
    balance = 0

    for lineno, raw_line in enumerate(tex.splitlines(), start=1):
        # 去掉注释
        line = raw_line.split('%', 1)[0]
        # 去掉转义的 \{ \}
        line_wo_esc = re.sub(r'\\[{}]', '', line)

        for ch in line_wo_esc:
            if ch == '{':
                balance += 1
            elif ch == '}':
                balance -= 1
                if balance < 0:
                    issues.append(f"Line {lineno}: extra '}}' (brace balance went negative)")
                    balance = 0

    if balance != 0:
        issues.append(f"Global brace imbalance at EOF: balance={balance}")

    return issues


def validate_math_integrity(tex: str) -> List[str]:
    r"""分析最终 TeX 数学完整性问题并返回警告列表（扩展版）

    检查项：
    - 行内数学定界符数量差异（opens vs closes）- 🆕 v1.8.7：忽略注释中的定界符
    - 裸露美元符号
    - 双重包裹残留
    - 右边界畸形（\right. $$ 等）
    - 空数学块
    - 🆕 截断/未闭合的数学片段（收集前若干样本）
      典型来源：图片占位符或 explain 合并时跨行被截断，导致缺失 \)
    - 🆕 v1.8.7：检测 \) 在 \( 前面的反向模式
    """
    issues: List[str] = []
    tex_no_comments_lines: List[str] = []
    for raw_line in tex.splitlines():
        tex_no_comments_lines.append(raw_line.split('%', 1)[0])
    tex_no_comments = "\n".join(tex_no_comments_lines)

    # 🆕 v1.8.7：统计时忽略注释中的定界符
    opens = 0
    closes = 0
    left_total = 0
    right_total = 0
    left_right_samples: List[str] = []
    reversed_pairs: List[Tuple[int, str]] = []  # (line_num, line_content)

    for lineno, code_part in enumerate(tex_no_comments_lines, start=1):
        line_opens = code_part.count('\\(')
        line_closes = code_part.count('\\)')
        line_left = code_part.count('\\left')
        line_right = code_part.count('\\right')
        opens += line_opens
        closes += line_closes
        left_total += line_left
        right_total += line_right

        if line_left != line_right and (line_left or line_right):
            snippet = code_part.strip()
            if len(snippet) > 80:
                snippet = snippet[:77] + '...'
            left_right_samples.append(
                f"Line {lineno}: \\left={line_left}, \\right={line_right} → {snippet}"
            )

        if line_opens >= 1 and line_closes >= 1:
            idx_open = code_part.find(r'\(')
            idx_close = code_part.find(r'\)')
            if idx_close < idx_open:
                display_line = code_part.strip()
                if len(display_line) > 80:
                    display_line = display_line[:77] + '...'
                reversed_pairs.append((lineno, display_line))

    if opens != closes:
        issues.append(f"Math delimiter imbalance: opens={opens} closes={closes} diff={opens - closes}")
    if left_total != right_total:
        issues.append(f"\\left/\\right imbalance: left={left_total}, right={right_total}")
        if left_right_samples:
            issues.extend(left_right_samples[:5])

    stray = len(re.findall(r'(?<!\\)\$', tex_no_comments))
    if stray:
        issues.append(f"Stray dollar signs detected: {stray}")

    double_wrapped = (
        len(re.findall(r'\$\s*\\\(.*?\\\)\s*\$', tex_no_comments, flags=re.DOTALL)) +
        len(re.findall(r'\$\$\s*\\\(.*?\\\)\s*\$\$', tex_no_comments, flags=re.DOTALL))
    )
    if double_wrapped:
        issues.append(f"Double-wrapped math segments: {double_wrapped}")

    right_glitch = (
        len(re.findall(r'\\right\.\s*\$\$', tex_no_comments)) +
        len(re.findall(r'\\right\.\\\\\)', tex_no_comments))
    )
    if right_glitch:
        issues.append(f"Right boundary glitches: {right_glitch}")

    empty_math = (
        len(re.findall(r'\\\(\s*\\\)', tex_no_comments)) +
        len(re.findall(r'\\\[\s*\\\]', tex_no_comments))
    )
    if empty_math:
        issues.append(f"Empty math blocks: {empty_math}")

    unmatched_open_positions: List[int] = []
    unmatched_close_positions: List[int] = []

    token_iter = list(re.finditer(r'(\\\(|\\\))', tex_no_comments))
    stack: List[int] = []
    for m in token_iter:
        tok = m.group(0)
        pos = m.start()
        if tok == '\\(':
            stack.append(pos)
        else:
            if stack:
                stack.pop()
            else:
                unmatched_close_positions.append(pos)
    unmatched_open_positions.extend(stack)

    def _sample_at(pos: int, direction: str = 'forward', span: int = 140) -> str:
        if direction == 'forward':
            raw = tex_no_comments[pos:pos+span]
        else:
            start = max(0, pos-span)
            raw = tex_no_comments[start:pos+10]
        end_delim = raw.find('\\)')
        if end_delim != -1:
            raw = raw[:end_delim+2]
        raw = re.sub(r'\s+', ' ', raw).strip()
        return raw

    def _get_line_number(pos: int) -> int:
        return tex_no_comments[:pos].count('\n') + 1

    def _has_priority_keywords(sample: str) -> bool:
        """检查样本是否包含优先关键词（\\right.、array、cases、题号标记等）"""
        priority_patterns = [
            r'\\right\.',
            r'\\begin\{array\}',
            r'\\end\{array\}',
            r'\\begin\{cases\}',
            r'\\end\{cases\}',
            r'\(\d+\)',  # (1) (2) 等小问标记
            r'[①②③④⑤⑥⑦⑧⑨⑩]',  # 圆圈数字
        ]
        return any(re.search(pat, sample) for pat in priority_patterns)

    # 🆕 v1.8.6：进一步甄别"疑似截断"，优先输出包含关键词的样本
    truncated_open_samples: List[str] = []
    priority_open_samples: List[str] = []

    for p in unmatched_open_positions:
        segment = tex_no_comments[p:p+300]
        if '\\)' not in segment:  # 明显没有闭合
            sample = _sample_at(p, 'forward')
            line_num = _get_line_number(p)
            sample_with_line = f"Line {line_num}: {sample}"

            if _has_priority_keywords(sample):
                priority_open_samples.append(sample_with_line)
            else:
                truncated_open_samples.append(sample_with_line)
        else:
            # 可能闭括号远在超过 120 之后，也认为可疑
            close_rel = segment.find('\\)')
            if close_rel > 120:
                sample = _sample_at(p, 'forward')
                line_num = _get_line_number(p)
                sample_with_line = f"Line {line_num}: {sample}"

                if _has_priority_keywords(sample):
                    priority_open_samples.append(sample_with_line)
                else:
                    truncated_open_samples.append(sample_with_line)

        # 限制总数
        if len(priority_open_samples) + len(truncated_open_samples) >= 10:
            break

    # 优先展示包含关键词的样本，然后是普通样本
    final_open_samples = priority_open_samples[:5] + truncated_open_samples[:max(0, 5 - len(priority_open_samples))]

    truncated_close_samples: List[str] = []
    priority_close_samples: List[str] = []

    for p in unmatched_close_positions[:10]:
        sample = _sample_at(p, 'backward')
        line_num = _get_line_number(p)
        sample_with_line = f"Line {line_num}: {sample}"

        if _has_priority_keywords(sample):
            priority_close_samples.append(sample_with_line)
        else:
            truncated_close_samples.append(sample_with_line)

    final_close_samples = priority_close_samples[:5] + truncated_close_samples[:max(0, 5 - len(priority_close_samples))]

    if final_open_samples:
        issues.append(
            "Unmatched opens (samples): " +
            '; '.join(final_open_samples)
        )
    if final_close_samples:
        issues.append(
            "Unmatched closes (samples): " +
            '; '.join(final_close_samples)
        )

    # 针对图片占位符附近的截断：\( ... IMAGE_TODO_START 未闭合
    image_trunc = re.findall(r'\\\([^\\)]{0,200}?% IMAGE_TODO_START', tex_no_comments)
    if image_trunc:
        issues.append(f"Potential image-adjacent truncated math segments: {len(image_trunc)}")

    # 🆕 v1.8.7：报告反向模式（\) 在 \( 前面）
    if reversed_pairs:
        issues.append(f"Reversed inline math pairs detected: {len(reversed_pairs)} lines")
        for lineno, line_content in reversed_pairs[:5]:  # 只显示前5个
            issues.append(f"  Line {lineno}: {line_content}")

    return issues


def generate_image_todo_block(img: Dict, stem_text: str = "", is_inline: bool = False) -> str:
    """生成新格式的 IMAGE_TODO 占位块

    🆕 v1.7：IMAGE_TODO 块后不添加额外空行

    Args:
        img: 图片信息字典，包含 id, path, width, inline, question_index, sub_index
        stem_text: 题干文本，用于提取上下文
        is_inline: 是否为内联图片

    Returns:
        格式化的 IMAGE_TODO 占位块
    """
    img_id = img.get('id', 'unknown')
    path = img.get('path', '')
    width = img.get('width', 60)
    inline = 'true' if img.get('inline', False) else 'false'
    q_idx = img.get('question_index', 0)
    sub_idx = img.get('sub_index', 1)

    # 提取上下文（简化版：取图片前后各50个字符）
    # 清理 context 内容：去除 LaTeX 命令，限制长度，检查括号平衡
    def clean_context(text: str, max_len: int = 80) -> str:
        r"""清理 CONTEXT 注释内容（增强版 v1.9.1）

        🆕 v1.9.1：
        - 增加最大长度到 80 字符（根据报告建议）
        - 更好地处理 LaTeX 环境命令
        - 去除 LaTeX 环境命令（\begin{...}、\end{...}）
        - 去除 LaTeX 命令（\xxx{...}）
        - 去除数学定界符 \(...\) 和 \[...\]
        - 截断到最多 max_len 字符
        - 检查括号平衡，如果不平衡则返回空字符串
        """
        if not text:
            return ""

        # 🆕 v1.9.1：更激进地去除 LaTeX 环境命令
        # 匹配 \begin{...} 或 \end{...}，并删除整个命令
        text = re.sub(r'\\begin\{[^}]+\}', '[ENV_START]', text)
        text = re.sub(r'\\end\{[^}]+\}', '[ENV_END]', text)

        # 去除 LaTeX 命令（\xxx{...}）
        text = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', text)

        # 去除数学定界符
        text = re.sub(r'\\\(|\\\)|\\\[|\\\]', '', text)

        # 去除多余的空格
        text = re.sub(r'\s+', ' ', text).strip()

        # 截断到第一个换行符
        if '\n' in text:
            text = text.split('\n')[0]

        # 🆕 v1.9.1：截断到最多 max_len 字符（默认 80）
        if len(text) > max_len:
            text = text[:max_len] + '...'

        # 检查括号平衡
        open_count = text.count('{')
        close_count = text.count('}')
        if open_count != close_count:
            # 括号不平衡，返回空字符串避免编译错误
            return ""

        return text

    context_before = clean_context(img.get('context_before', '').strip())
    context_after = clean_context(img.get('context_after', '').strip())

    # 🆕 v1.7：构建占位块，IMAGE_TODO_END 后不添加额外的 \n
    # 🆕 v1.8.4：转义路径中的特殊字符（下划线等）
    path_escaped = path.replace('_', '\\_') if path else ''
    
    if is_inline:
        # 内联图片：不使用 center 环境
        block = (
            f"\n% IMAGE_TODO_START id={img_id} path={path_escaped} width={width}% inline={inline} "
            f"question_index={q_idx} sub_index={sub_idx}\n"
        )
        if context_before:
            block += f"% CONTEXT_BEFORE: {context_before}\n"
        if context_after:
            block += f"% CONTEXT_AFTER: {context_after}\n"
        block += (
            "\\begin{tikzpicture}[scale=0.8,baseline=-0.5ex]\n"
            f"  % TODO: AI_AGENT_REPLACE_ME (id={img_id})\n"
            "\\end{tikzpicture}\n"
            f"% IMAGE_TODO_END id={img_id}\n"
        )
    else:
        # 独立图片：使用 center 环境
        block = (
            "\\begin{center}\n"
            f"% IMAGE_TODO_START id={img_id} path={path_escaped} width={width}% inline={inline} "
            f"question_index={q_idx} sub_index={sub_idx}\n"
        )
        if context_before:
            block += f"% CONTEXT_BEFORE: {context_before}\n"
        if context_after:
            block += f"% CONTEXT_AFTER: {context_after}\n"
        block += (
            "\\begin{tikzpicture}[scale=1.05,>=Stealth,line cap=round,line join=round]\n"
            f"  % TODO: AI_AGENT_REPLACE_ME (id={img_id})\n"
            "\\end{tikzpicture}\n"
            f"% IMAGE_TODO_END id={img_id}\n"
            "\\end{center}\n"  # 🆕 v1.7：不添加尾随空白行
        )

    return block


def merge_explanations(analysis: str, explain: str) -> str:
    """智能合并解析和详解

    Args:
        analysis: 【分析】内容
        explain: 【详解】内容

    Returns:
        合并后的内容
    """
    if not analysis:
        return explain or ""
    if not explain:
        return analysis or ""

    # 检查是否内容相似
    if analysis in explain or explain in analysis:
        return max(analysis, explain, key=len)  # 选择较长的

    # 都有内容且不重复，合并
    return f"{analysis}\n\n{explain}"


def clean_explain_content(explain_text: str) -> str:
    """清理 explain 内容中的空行与残留的【分析】标记"""
    if not explain_text:
        return ""

    text = explain_text.replace("\r\n", "\n")
    text = re.sub(r'【\s*分析\s*】.*?(?=【|$)', '', text, flags=re.DOTALL)
    text = re.sub(r'\n\s*\n+', r'\\par\n', text)
    return text.strip()


def build_question_tex(stem: str, options: List, meta: Dict, images: List, attachments: List,
                       section_type: str, question_index: int = 0, slug: str = "") -> str:
    """生成 question 环境

    🆕 v1.9: 支持附件渲染（表格、文本、图表）
    🆕 v1.8.8: 增加 meta 命令使用计数检测
    🆕 Prompt 3: 支持内联图片占位符替换
    🆕 新格式: 使用 IMAGE_TODO_START/END 带 ID 的占位块
    """
    # 🆕 v1.8.8：meta 使用计数（检测重复的元信息命令）
    meta_usage = {
        "answer": 0,
        "explain": 0,
        "topics": 0,
        "difficulty": 0,
    }

    # 先处理文本，但保留占位符
    stem_raw = stem  # 保存原始文本用于上下文提取
    stem = process_text_for_latex(stem, is_math_heavy=True)
    # 🆕 任务2：对题干应用软换行
    stem = soft_wrap_paragraph(stem)

    if section_type == "解答题" and re.search(r'\(\d+\)', stem):
        stem = handle_subquestions(stem)

    explain_raw = meta.get("explain", "").strip()
    if explain_raw and re.search(r'【\s*分析\s*】', explain_raw):
        print(f"⚠️  Q{question_index}: explain 段落包含【分析】标记，已自动移除")
        explain_raw = re.sub(r'【\s*分析\s*】.*?(?=【|$)', '', explain_raw, flags=re.DOTALL)
    if explain_raw:
        explain_raw = re.sub(r'^【?详解】?[:：]?\s*', '', explain_raw)
        explain_raw = process_text_for_latex(explain_raw, is_math_heavy=True)
        explain_raw = soft_wrap_paragraph(explain_raw)
        explain_raw = clean_explain_content(explain_raw)

    topics_raw = meta.get("topics", "").strip()
    if topics_raw:
        topics_raw = topics_raw.replace("、", "；")
        topics_raw = escape_latex_special(topics_raw, in_math_mode=False)

    lines = []
    lines.append(r"\begin{question}")

    if stem:
        lines.append(stem)

    if options:
        lines.append(r"\begin{choices}")
        for opt in options:
            opt_processed = process_text_for_latex(opt, is_math_heavy=True)
            lines.append(f"  \\item {opt_processed}")
        lines.append(r"\end{choices}")

    # 🆕 新格式: 使用 IMAGE_TODO_START/END 占位块
    for idx, img in enumerate(images):
        # 生成新格式的占位块
        img_todo_block = generate_image_todo_block(img, stem_raw, img.get('inline', False))

        if img.get('inline', False):
            # 内联图片：替换占位符
            placeholder = f"<<IMAGE_INLINE:{img.get('id', f'img{idx}')}>>"
            stem = stem.replace(placeholder, img_todo_block)
            explain_raw = explain_raw.replace(placeholder, img_todo_block) if explain_raw else explain_raw
            # 更新已处理的选项
            for i, line in enumerate(lines):
                if placeholder in line:
                    lines[i] = line.replace(placeholder, img_todo_block)
        else:
            # 独立图片：追加到题目末尾
            lines.append("")
            lines.append(img_todo_block)

    if topics_raw:
        lines.append(f"\\topics{{{topics_raw}}}")
        meta_usage["topics"] += 1
    if meta.get("difficulty"):
        lines.append(f"\\difficulty{{{meta['difficulty']}}}")
        meta_usage["difficulty"] += 1
    if meta.get("answer"):
        # 使用与题干/解析一致的处理，以规范数学格式，避免 $$...$$ 残留
        ans = process_text_for_latex(meta["answer"], is_math_heavy=True)
        lines.append(f"\\answer{{{ans}}}")
        meta_usage["answer"] += 1
    if explain_raw:
        lines.append(f"\\explain{{{explain_raw}}}")
        meta_usage["explain"] += 1

    # 🆕 v1.9: 渲染附件
    if attachments:
        lines.append("")
        lines.append("\\vspace{1em}")
        lines.append("\\textbf{附：}")
        lines.append("")

        for att in attachments:
            kind = att.get("kind", "text")
            att_lines = att.get("lines", [])

            if not att_lines:
                continue

            if kind == "table":
                att_text = "\n".join(att_lines)
                converted_md = None
                if "|" in att_text and any(re.match(r'^\s*\|[-:\s|]+\|$', line) for line in att_lines):
                    converted_md = convert_markdown_table_to_latex(att_text)
                ascii_table = convert_ascii_table_blocks(att_text)

                if converted_md:
                    lines.append(converted_md)
                elif ascii_table != att_text:
                    lines.append(ascii_table)
                else:
                    lines.append("\\begin{verbatim}")
                    for line in att_lines:
                        lines.append(line)
                    lines.append("\\end{verbatim}")
            elif kind == "text":
                # 文本附件，使用 process_text_for_latex 处理
                att_text = "\n".join(att_lines)
                processed_att = process_text_for_latex(att_text, is_math_heavy=False)
                lines.append(processed_att)
            elif kind == "figure":
                # 图表附件（暂时使用 verbatim）
                lines.append("\\begin{verbatim}")
                for line in att_lines:
                    lines.append(line)
                lines.append("\\end{verbatim}")

            lines.append("")

    lines = ensure_choices_environment(lines, bool(options))
    lines.append(r"\end{question}")
    raw_question = "\n".join(lines)
    processed_lines = [
        postprocess_inline_math(line)
        for line in raw_question.splitlines()
    ]
    question_tex = "\n".join(processed_lines)

    # 🆕 v1.8.8：检查 meta 命令是否重复使用
    if slug:  # 只在有 slug 时才记录日志
        from pathlib import Path
        for key, cnt in meta_usage.items():
            if cnt > 1:
                # 记录到专门的 issue 日志
                debug_dir = Path("word_to_tex/output/debug")
                debug_dir.mkdir(parents=True, exist_ok=True)
                log_file = debug_dir / f"{slug}_meta_duplicates.log"

                with log_file.open("a", encoding="utf-8") as f:
                    if log_file.stat().st_size == 0:
                        # 首次写入，添加头部
                        f.write(f"# Duplicate Meta Commands Detection Log for {slug}\n")
                        f.write(f"# Generated: {Path(__file__).name}\n\n")

                    f.write(f"{'='*80}\n")
                    f.write(f"Question {question_index}: meta '\\{key}' appears {cnt} times\n")
                    f.write(f"  Section: {section_type}\n")
                    f.write(f"  → Please check duplicated 【详解】/【考点】/【答案】/【难度】 blocks in Markdown\n\n")

    return question_tex


def convert_md_to_examx(md_text: str, title: str, slug: str = "", enable_issue_detection: bool = True) -> str:
    """主转换函数（增强版）

    🆕 v1.6.3：增加问题检测和日志记录

    Args:
        md_text: Markdown 文本
        title: 试卷标题
        slug: 试卷 slug（用于日志文件名）
        enable_issue_detection: 是否启用问题检测
    """
    md_text = clean_markdown(md_text)
    sections = split_sections(md_text)

    # 🆕 v1.6.3：初始化问题日志
    if enable_issue_detection and slug:
        init_issue_log(slug)

    out_lines = []
    out_lines.append(f"\\examxtitle{{{title}}}")

    q_index = 0  # 全局题号计数器
    for raw_title, body in sections:
        sec_label = SECTION_MAP.get(raw_title, raw_title)
        out_lines.append("")
        out_lines.append(f"\\section{{{sec_label}}}")

        for block in split_questions(body):
            if not block.strip():
                continue

            q_index += 1  # 题号递增
            raw_block = block  # 保存原始 Markdown 片段

            try:
                # 🆕 传递 question_index 和 slug 用于生成图片 ID
                content, meta, images, attachments = extract_meta_and_images(block, question_index=q_index, slug=slug)

                # 使用增强的转换函数（返回3个值）
                stem, options, extracted_analysis = convert_choices(content)

                # 合并提取的解析和元信息中的解析
                if extracted_analysis and not meta.get('explain'):
                    meta['explain'] = extracted_analysis
                elif extracted_analysis:
                    meta['explain'] = meta['explain'] + '\n' + extracted_analysis

                # 🆕 传递 question_index 和 slug 到 build_question_tex
                q_tex = build_question_tex(stem, options, meta, images, attachments, sec_label,
                                          question_index=q_index, slug=slug)

                # 🆕 v1.6.4：检测问题并记录日志（传入 meta & section_label）
                if enable_issue_detection and slug:
                    issues = detect_question_issues(
                        slug=slug,
                        q_index=q_index,
                        raw_block=raw_block,
                        tex_block=q_tex,
                        meta=meta,
                        section_label=sec_label,
                    )
                    append_issue_log(
                        slug=slug,
                        q_index=q_index,
                        raw_block=raw_block,
                        tex_block=q_tex,
                        issues=issues,
                        meta=meta,
                        section_label=sec_label,
                    )

                # 验证生成的 TeX 是否完整
                if r'\begin{question}' in q_tex and r'\end{question}' not in q_tex:
                    print(f"⚠️  Q{q_index} 缺少 \\end{{question}}，自动补全")
                    q_tex += "\n\\end{question}"

                out_lines.append("")
                out_lines.append(q_tex)
            except Exception as e:
                import traceback
                print(f"⚠️  Q{q_index} ({sec_label}) 转换失败: {str(e)}")
                print(f"   {traceback.format_exc()}")
                out_lines.append("")
                out_lines.append(r"\begin{question}")
                out_lines.append(f"% ERROR: Q{q_index} 转换失败 - {str(e)}")
                out_lines.append(r"\end{question}")

    out_lines.append("")

    # 最终处理：清理空行和分割超长行
    result = "\n".join(out_lines)
    result = remove_blank_lines_in_macro_args(result)
    result = split_long_lines_in_explain(result, max_length=800)
    # 🔥 v1.8.3：重新启用（已修复括号计数逻辑）
    result = remove_par_breaks_in_explain(result)
    # 🔥 v1.8.1：clean_question_environments 仍然禁用（正则匹配问题）

    # 最终兜底：规范/移除残留的 $$ 显示数学标记
    # 1) 将成对 $$...$$ 统一为行内 \(...\)（与 smart_inline_math 行为一致）
    # 🆕 v1.9.3：跳过注释行，避免破坏 CONTEXT 注释
    def convert_display_math_skip_comments(text: str) -> str:
        lines = text.split('\n')
        result_lines = []
        for line in lines:
            if line.strip().startswith('%'):
                # 注释行：不处理，直接保留（包括 $$...$$）
                result_lines.append(line)
            else:
                # 非注释行：转换 $$...$$ 为 \(...\)
                line = re.sub(r'\$\$\s*(.+?)\s*\$\$', r'\\(\1\\)', line)
                result_lines.append(line)
        return '\n'.join(result_lines)
    
    result = convert_display_math_skip_comments(result)
    # 2) 清理任何残留的孤立 $$（避免编译错误）- 同样跳过注释行
    lines = result.split('\n')
    result = '\n'.join(
        line if line.strip().startswith('%') else line.replace('$$', '')
        for line in lines
    )

    # 🆕 后备占位符转换：清理任何残留的 Markdown 图片标记
    result = cleanup_remaining_image_markers(result)

    # 🆕 v1.6：清理宏参数内的"故选"残留（分两步）
    result = cleanup_guxuan_in_macros(result)

    # 🆕 v1.6.1：全局清理任何残留的"故选"（兜底方案）
    # 清理各种形式的"故选：X"，无论在什么位置
    result = re.sub(r'故选[:：][ABCD]+\.?[^\n}]*', '', result)
    # 清理"故答案为"
    result = re.sub(r'故答案为[:：]?[ABCD]*\.?', '', result)

    # 🆕 v1.8.4：修复合并题目的结构（题干 vs 小问）
    result = fix_merged_questions_structure(result)

    # 🆕 v1.8.6：后处理修复 \right. 边界错误（收紧版 - P0 最高优先级）
    result = fix_right_boundary_errors(result)
    result = fix_reversed_delimiters(result)

    # 🆕 v1.8.5：验证并修复 IMAGE_TODO 块格式错误（P0）
    result = validate_and_fix_image_todo_blocks(result)

    # 🆕 v1.8.6：平衡 array/cases 环境（P0 - 删除多余的 \end）
    result = balance_array_and_cases_env(result)

    # 🆕 v1.8.7：修复特定的反向数学定界符模式（极窄自动修复）
    result = fix_specific_reversed_pairs(result)

    # 🆕 v1.8.8：极度保守的反向定界符自动修复（仅在简单场景启用）
    result = fix_simple_reversed_inline_pairs(result)
    result = balance_left_right_delimiters(result)

    # 🆕 v1.8.8：检测反向定界符并记录日志（不改变输出）
    if slug:
        collect_reversed_math_samples(result, slug)

    # 🆕 v1.9.6：禁用 fix_missing_items_in_enumerate
    # 原因：这个函数会把 enumerate 中的每行都加 \item，导致多行子问题变成多个 \item
    # result = fix_missing_items_in_enumerate(result)

    # 🆕 v1.9.1：修复 tabular 环境缺失列格式（P1）
    result = fix_tabular_environments(result)

    # 🆕 v1.9.6：修复三角函数空格和未定义符号
    result = fix_trig_function_spacing(result)
    result = fix_undefined_symbols(result)
    result = fix_markdown_bold_residue(result)  # 🆕 v1.9.7：清理粗体残留
    result = fix_nested_subquestions(result)
    result = fix_spurious_items_in_enumerate(result)
    result = fix_keep_questions_together(result)

    return result


# ==================== 🆕 v1.6.3 新增：问题检测与日志系统 ====================

def detect_question_issues(
    slug: str,
    q_index: int,
    raw_block: str,
    tex_block: str,
    meta: Optional[Dict[str, str]] = None,
    section_label: Optional[str] = None,
) -> List[str]:
    """🆕 v1.7：检测题目中的可疑模式（增强版）
    🆕 v1.6.4：检测题目中的可疑模式（增强版）

    Args:
        slug: 试卷 slug（如 "nanjing_2026_sep"）
        q_index: 题号（从 1 开始）
        raw_block: 原始 Markdown 片段
        tex_block: 生成的 TeX 片段
        meta: 解析得到的元信息字典（答案、难度、知识点、解析等）
        section_label: 当前大题标题（如 "单选题"、"多选题" 等）

    Returns:
        问题列表
    """
    issues: List[str] = []
    tex_no_comments_lines: List[str] = []
    for _line in tex_block.splitlines():
        tex_no_comments_lines.append(_line.split('%', 1)[0])
    tex_no_comments = "\n".join(tex_no_comments_lines)

    # ---------- 🆕 v1.8.6：检测缺少题干的题目（增强版 - 带上下文） ----------
    # 检查题目是否直接从 \item 开始（缺少题干）
    # 在 \begin{question} 后，如果第一个非空行是 \item 或 \begin{choices}，则缺少题干
    question_content = tex_block
    if r'\begin{question}' in question_content:
        # 提取 \begin{question} 和 \begin{choices} 之间的内容
        match = re.search(r'\\begin\{question\}(.*?)(?:\\begin\{choices\}|\\item|\\end\{question\})',
                         question_content, re.DOTALL)
        if match:
            content_between = match.group(1).strip()
            # 如果内容为空或只有注释，则缺少题干
            # 移除注释行
            content_no_comments = re.sub(r'^\s*%.*$', '', content_between, flags=re.MULTILINE).strip()
            if not content_no_comments:
                # 🆕 v1.8.6：提取原始 Markdown 上下文（题号前后各 1-2 行）
                raw_lines = raw_block.splitlines()
                context_lines = []

                # 提取前 3 行（截断显示）
                for i, line in enumerate(raw_lines[:3]):
                    truncated = line[:80] + '...' if len(line) > 80 else line
                    context_lines.append(f"  MD L{i+1}: {truncated}")

                context_str = '\n'.join(context_lines)

                issues.append(
                    f"⚠️ CRITICAL: 题目缺少题干，直接从 \\item 开始\n"
                    f"  题型: {section_label or 'N/A'}\n"
                    f"  题号: Q{q_index}\n"
                    f"  原始 Markdown 片段:\n{context_str}\n"
                    f"  → 请在 Markdown 中补充题干内容"
                )

    # ---------- 1) 原有检查逻辑（保留 & 复刻） ----------

    # 1.1 检测 meta 形式的【分析】（不应该出现）
    if "【分析】" in raw_block and "【分析】" in tex_no_comments:
        issues.append("Contains meta 【分析】 in both raw and tex (should be discarded)")
    elif "【分析】" in tex_no_comments:
        issues.append("Contains meta 【分析】 in tex (should be discarded)")

    # 1.2 检测 *$x$* 或其他 star + math 模式
    if re.search(r'\*\s*\$', tex_no_comments) or re.search(r'\$\s*\*', tex_no_comments):
        issues.append("Star-emphasis around inline math, e.g. *$x$*")

    # 1.3 检测空 $$ 或形如 $$\(
    if re.search(r'\$\s*\$', tex_no_comments):
        issues.append("Empty inline/ display math $$")
    if re.search(r'\$\s*\$\s*\\\(', tex_no_comments):
        issues.append("Suspicious pattern $$\\(")

    # 1.4 检测行内 math 分隔符数量明显不匹配
    open_count = tex_no_comments.count(r'\(')
    close_count = tex_no_comments.count(r'\)')
    if open_count != close_count:
        issues.append(f"Unbalanced inline math delimiters: ${open_count} vs$ {close_count}")

    # 1.5 检测全角括号残留
    if '（' in tex_no_comments or '）' in tex_no_comments:
        issues.append("Fullwidth brackets （）found in tex")

    # 1.6 检测"故选"残留
    if re.search(r'故选[:：][ABCD]+', tex_no_comments):
        issues.append("'故选' pattern found in tex")

    # ---------- 2) 新增：基于 meta 的一致性检查 ----------

    if meta is not None:
        # 辅助函数：安全取值并 strip
        def _get(key: str) -> str:
            return (meta.get(key) or "").strip()

        answer = _get("answer")
        difficulty = _get("difficulty")
        topics = _get("topics")
        explain = _get("explain")
        analysis = _get("analysis")

        # 2.1 检查"分析"字段是否仍然存在（按规范应丢弃，仅允许作为中间态，而不应写入 TeX）
        if analysis:
            issues.append("Meta contains 'analysis' field (【分析】) – it should not be used in output")

        # 2.2 检查 section/大题 与答案必需性
        sec = section_label or ""
        is_choice_section = ("单选" in sec) or ("多选" in sec)

        # 对选择题，小题通常必须有答案
        if is_choice_section and not answer:
            issues.append("Choice question in section '{0}' has no 【答案】 meta".format(sec or "?"))

        # 对于非选择题，答案缺失不一定是致命错误，但可以提示
        if not is_choice_section and not answer:
            issues.append("Question has no 【答案】 meta (section='{0}')".format(sec or "?"))

        # 2.3 meta 与 TeX 的映射一致性
        has_answer_macro = "\\answer{" in tex_block
        has_explain_macro = "\\explain{" in tex_block

        if answer and not has_answer_macro:
            issues.append("Meta has answer but TeX is missing \\answer{}")
        if has_answer_macro and not answer:
            issues.append("TeX has \\answer{} but meta.answer is empty")

        if explain and not has_explain_macro:
            issues.append("Meta has explain but TeX is missing \\explain{}")
        if has_explain_macro and not explain:
            issues.append("TeX has \\explain{} but meta.explain is empty")

        # 2.4 确保 \\explain{} 不会偷偷吃进【分析】内容
        # 这里只做简单文本级检测：如果 raw_block 里有"【分析】"且 meta.explain 为空，则额外提示
        if "【分析】" in raw_block and not explain:
            issues.append("Raw block contains 【分析】 but meta.explain is empty – this question is treated as 'no explain'")

        # 2.5 检测超长 explain 内容（>500行）
        if explain:
            explain_lines = explain.count('\n') + 1
            if explain_lines > 500:
                issues.append(f"⚠️  LONG_EXPLAIN: {explain_lines} lines (>500) – may cause conversion issues")
            elif explain_lines > 200:
                issues.append(f"Long explain: {explain_lines} lines (>200) – consider simplification")

    return issues


def append_issue_log(
    slug: str,
    q_index: int,
    raw_block: str,
    tex_block: str,
    issues: List[str],
    meta: Optional[Dict[str, str]] = None,
    section_label: Optional[str] = None,
) -> None:
    """🆕 v1.6.4：将问题记录到 debug 日志（增强版）

    Args:
        slug: 试卷 slug
        q_index: 题号
        raw_block: 原始 Markdown 片段
        tex_block: 生成的 TeX 片段
        issues: 问题列表
        meta: 解析得到的元信息字典（可选）
        section_label: 当前大题标题（如 "单选题" / "多选题" 等）
    """
    if not issues:
        return

    debug_dir = Path("word_to_tex/output/debug")
    debug_dir.mkdir(parents=True, exist_ok=True)
    log_file = debug_dir / f"{slug}_issues.log"

    with log_file.open("a", encoding="utf-8") as f:
        f.write(f"{'='*80}\n")
        f.write(f"# Q{q_index} issues (section={section_label or 'N/A'})\n\n")

        # 简要 meta 概览（如果有）
        if meta is not None:
            # 只展示关键信息，避免日志太冗长
            summary_keys = ["answer", "difficulty", "topics", "explain", "analysis"]
            f.write("## Meta summary:\n")
            for key in summary_keys:
                if key in meta:
                    val = (meta.get(key) or "").strip()
                    if len(val) > 80:
                        val_display = val[:77] + "..."
                    else:
                        val_display = val
                    f.write(f"- {key}: {val_display}\n")
            f.write("\n")

        f.write("## Issues:\n")
        for issue in issues:
            f.write(f"- {issue}\n")

        f.write("\n## Raw Markdown:\n")
        f.write("```markdown\n")
        f.write(raw_block.strip() + "\n")
        f.write("```\n\n")

        f.write("## Generated TeX:\n")
        f.write("```tex\n")
        f.write(tex_block.strip() + "\n")
        f.write("```\n\n")


def init_issue_log(slug: str) -> None:
    """🆕 v1.6.3：初始化问题日志文件

    Args:
        slug: 试卷 slug
    """
    debug_dir = Path("word_to_tex/output/debug")
    debug_dir.mkdir(parents=True, exist_ok=True)
    log_file = debug_dir / f"{slug}_issues.log"

    # 清空旧日志
    with log_file.open("w", encoding="utf-8") as f:
        f.write(f"# Issue Detection Log for {slug}\n")
        f.write(f"# Generated: {Path(__file__).name} v{VERSION}\n")
        f.write(f"# Date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("\n")


# ==================== 🆕 v1.3 新增：自动验证函数 ====================

def assert_no_analysis_meta_in_auto_tex(slug: str) -> None:
    """🆕 v1.6.3：检查 auto 目录中是否残留【分析】meta 段

    Args:
        slug: 试卷 slug（如 "nanjing_2026_sep"）

    Raises:
        RuntimeError: 如果发现【分析】残留
    """
    root = Path("content/exams/auto") / slug
    if not root.exists():
        return

    for tex in root.rglob("*.tex"):
        txt = tex.read_text(encoding="utf-8")
        # 只拦类似【分析】这类 meta 段，而不是自然语言中的"分析"二字
        if re.search(r"【\s*分析\s*】", txt):
            raise RuntimeError(f"[ANALYSIS-META-LEFTOVER] {tex} still contains 【分析】.")


def validate_latex_output(tex_content: str) -> List[str]:
    """
    🆕 v1.3 新增：验证LaTeX输出，返回警告列表
    🆕 v1.6.3：增加【分析】残留检查

    Args:
        tex_content: 生成的LaTeX内容

    Returns:
        警告信息列表
    """
    warnings = []

    # 去除注释内容，避免 IMAGE_TODO 的 CONTEXT 注释触发误报
    tex_no_comments_lines: List[str] = []
    for line in tex_content.splitlines():
        tex_no_comments_lines.append(line.split('%', 1)[0])
    tex_no_comments = "\n".join(tex_no_comments_lines)

    # 🆕 检查0：【分析】meta 段残留
    analysis_meta = re.findall(r'【\s*分析\s*】', tex_no_comments)
    if analysis_meta:
        warnings.append(f"❌ 发现 {len(analysis_meta)} 处【分析】meta 段残留（应已被丢弃）")

    # 检查1：残留的 $ 符号
    dollar_matches = re.findall(r'(?<!\\)\$[^\$]+\$', tex_no_comments)
    if dollar_matches:
        warnings.append(f"⚠️  发现 {len(dollar_matches)} 处残留的 $ 格式")
        for i, match in enumerate(dollar_matches[:3], 1):  # 只显示前3个
            warnings.append(f"     示例{i}: {match}")

    # 检查2：残留的"故选"
    guxuan_matches = re.findall(r'故选[:：][ABCD]+', tex_no_comments)
    if guxuan_matches:
        warnings.append(f"⚠️  发现 {len(guxuan_matches)} 处残留的'故选'")

    # 检查3：中文括号
    chinese_paren = re.findall(r'[（）]', tex_no_comments)
    if chinese_paren:
        warnings.append(f"⚠️  发现 {len(chinese_paren)} 处中文括号")

    # 检查4：环境闭合
    begin_count = tex_content.count(r'\begin{question}')
    end_count = tex_content.count(r'\end{question}')
    if begin_count != end_count:
        warnings.append(f"❌ question 环境不匹配: {begin_count} 个 begin, {end_count} 个 end")

    begin_choices = tex_content.count(r'\begin{choices}')
    end_choices = tex_content.count(r'\end{choices}')
    if begin_choices != end_choices:
        warnings.append(f"❌ choices 环境不匹配: {begin_choices} 个 begin, {end_choices} 个 end")

    # 检查5：空行在宏参数中
    problematic_macros = []
    for macro in ['explain', 'topics', 'answer']:
        pattern = rf'\\{macro}\{{[^}}]*\n\s*\n[^}}]*\}}'
        if re.search(pattern, tex_content):
            problematic_macros.append(macro)
    if problematic_macros:
        warnings.append(f"⚠️  以下宏参数中可能有空行: {', '.join(problematic_macros)}")

    return warnings


# ==================== 主函数 ====================

def main():
    parser = argparse.ArgumentParser(
        description=f"OCR 试卷预处理脚本 - {VERSION}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🆕 v1.5 核心功能：
  - 修复数学公式双重包裹（$$\\(...\\)$$ → \\(...\\)）
  - 统一数学公式格式：所有 $$...$$ 转换为行内 \\(...\\)
  - 自动展开单行选项（> A... B... → 多行）
  - 强制检查【分析】残留（确保已被丢弃）

✅ v1.4 改进回顾：
  - 数学公式双重包裹修复（初版）
  - 单行选项自动展开（初版）

✅ v1.3 改进回顾：
  - 修复 docstring 警告，添加 $ 格式兜底转换
  - 改进"故选"清理规则
  - 统一中英文标点（括号、引号）
  - 添加自动验证功能

✅ v1.2 改进回顾：
  - 加强空行清理（解决80%的Runaway argument错误）
  - 超长行自动分割（解决编译慢问题）
  - 增强数学变量检测（减少Missing $错误）
  - 增强选项解析（处理嵌入的解析内容）

使用示例:
  python3 ocr_to_examx.py "浙江省金华十校/" output/
        """
    )
    
    parser.add_argument("input", help="输入路径（.md 文件或 OCR 文件夹）")
    parser.add_argument("output", help="输出路径（目录或 .tex 文件）")
    parser.add_argument("--title", help="试卷标题", default=None)
    parser.add_argument("--figures-dir", help="指定图片资源所在目录（优先于自动检测）", default=None)
    parser.add_argument("--legacy-math", action="store_true", help="使用旧数学正则管线 (smart_inline_math 等) 进行数学处理，仅测试比较用")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    
    args = parser.parse_args()
    
    try:
        print(f"🔍 OCR 试卷预处理脚本 - {VERSION}")
        print("━" * 60)
        # 可选：切换到旧数学管线（A/B 测试用）
        _orig_process = None
        if args.legacy_math:
            print("⚠️ 使用 legacy 数学管线 (smart_inline_math 等) — 仅供比较测试")
            _orig_process = process_text_for_latex
            def _legacy_wrapper(t: str, is_math_heavy: bool = False):
                if not t:
                    return t
                # 前置清理（复用现行版本的初段逻辑）
                t = re.sub(r'\*\s*(\$[^$]+\$)\s*\*', r'\1', t)
                t = re.sub(r'\*([A-Za-z0-9])\*', r'\\emph{\1}', t)
                t = re.sub(r'[,，。\.;；]\s*故选[:：][ABCD]+[.。]?\s*$', '', t)
                t = re.sub(r'\n+故选[:：][ABCD]+[.。]?\s*$', '', t)
                t = re.sub(r'^\s*故选[:：][ABCD]+[.。]?\s*', '', t)
                t = re.sub(r'\n+故答案为[:：]', '', t)
                t = re.sub(r'^\s*故选[:：][ABCD]+[.。]?\s*$', '', t, flags=re.MULTILINE)
                t = re.sub(r'[，,]?\s*故选[:：]\s*[ABCD]+[。．.]*\s*$', '', t, flags=re.MULTILINE)
                t = re.sub(r'^【?详解】?[:：]?\s*', '', t)
                if '∵' in t or '∴' in t:
                    t = t.replace('∵', '$\\because$').replace('∴', '$\\therefore$')
                if not is_math_heavy:
                    t = escape_latex_special(t, in_math_mode=False)
                t = smart_inline_math(t)
                t = fix_double_wrapped_math(t)
                t = fix_inline_math_glitches(t)
                return t
            process_text_for_latex = _legacy_wrapper  # type: ignore

        md_file, images_dir = find_markdown_and_images(args.input)

        # 处理图片目录：优先使用命令行参数，否则尝试智能推断
        if args.figures_dir:
            manual_dir = Path(args.figures_dir).expanduser().resolve()
            if manual_dir.exists():
                images_dir = manual_dir
            else:
                print(f"⚠️  指定的图片目录 {manual_dir} 不存在，将尝试自动检测结果")
        elif not images_dir:
            # 如果 find_markdown_and_images 没有找到图片目录，尝试智能推断
            inferred_dir = infer_figures_dir(str(md_file))
            if inferred_dir:
                images_dir = Path(inferred_dir)
                print(f"🔍 自动推断图片目录: {images_dir}")

        print(f"📄 Markdown: {md_file.name}")
        if images_dir:
            img_count = len(list(images_dir.glob('*')))
            print(f"🖼️  图片目录: {images_dir} ({img_count} 个文件)")
        else:
            print(f"⚠️  未找到图片目录")
        
        output_path = Path(args.output)
        if output_path.suffix == '.tex':
            output_tex = output_path
            output_dir = output_path.parent
        else:
            output_dir = output_path
            output_tex = output_dir / f"{md_file.stem.replace('_local', '_raw')}.tex"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if images_dir:
            img_count = copy_images_to_output(images_dir, output_dir)
            print(f"✅ 已复制 {img_count} 个图片到 {output_dir}/images/")
        
        title = args.title
        if title is None:
            input_path = Path(args.input)
            if input_path.is_dir():
                title = input_path.name
            else:
                title = md_file.stem.replace('_local', '')

        # 🆕 v1.6.3：提取 slug 用于问题日志
        slug = md_file.stem.replace('_local', '').replace('_preprocessed', '').replace('_raw', '')

        print(f"\n📖 正在转换...")
        print(f"📝 标题: {title}")
        print(f"🏷️  Slug: {slug}")

        md_text = md_file.read_text(encoding='utf-8')
        tex_text = convert_md_to_examx(md_text, title, slug=slug, enable_issue_detection=True)
        
        # 🆕 v1.6 P0 修复：后处理清理
        tex_text = fix_array_boundaries(tex_text)
        tex_text = clean_residual_image_attrs(tex_text)
        
        # 🆕 v1.3：验证输出
        warnings = validate_latex_output(tex_text)
        integrity_issues = validate_math_integrity(tex_text)
        # 🆕 v1.8.6：花括号平衡检查
        brace_issues = validate_brace_balance(tex_text)
        
        output_tex.write_text(tex_text, encoding='utf-8')
        
        print(f"\n✅ 转换完成！")
        print("━" * 60)
        print(f"📊 输出文件: {output_tex}")
        print(f"📏 文件大小: {len(tex_text):,} 字节")
        
        question_count = tex_text.count(r'\begin{question}')
        image_count = tex_text.count('IMAGE_TODO')
        print(f"📋 题目数量: {question_count}")
        if image_count > 0:
            print(f"🖼️  图片占位: {image_count}")
        
        # 🆕 v1.8.6：显示验证结果（包含花括号检查）
        if warnings or integrity_issues or brace_issues:
            combined = warnings + integrity_issues + brace_issues
            print(f"\n⚠️  验证发现 {len(combined)} 个潜在问题:")

            # 分类显示（只显示前几条）
            if warnings:
                print(f"  📋 结构问题: {len(warnings)} 个")
                for issue in warnings[:3]:
                    print(f"    {issue}")
                if len(warnings) > 3:
                    print(f"    ... 还有 {len(warnings) - 3} 个")

            if brace_issues:
                print(f"  🔧 花括号问题: {len(brace_issues)} 个")
                for issue in brace_issues[:3]:
                    print(f"    {issue}")
                if len(brace_issues) > 3:
                    print(f"    ... 还有 {len(brace_issues) - 3} 个")

            if integrity_issues:
                print(f"  🔢 数学定界符问题: {len(integrity_issues)} 个")
                for issue in integrity_issues[:3]:
                    print(f"    {issue}")
                if len(integrity_issues) > 3:
                    print(f"    ... 还有 {len(integrity_issues) - 3} 个")

            print("\n💡 建议：使用 AI Agent 检查并人工确认数学结构")
        else:
            print(f"\n✅ 验证通过：未发现明显问题")

        # 🆕 Prompt 1: 强制检查【分析】残留
        if slug:
            print(f"\n🔍 检查【分析】残留...")
            try:
                assert_no_analysis_meta_in_auto_tex(slug)
                print(f"✅ 未发现【分析】残留")
            except RuntimeError as e:
                print(f"❌ {e}")
                raise

        # 恢复原数学处理函数（若启用 legacy）
        if _orig_process is not None:
            process_text_for_latex = _orig_process  # type: ignore
        return 0
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


# ==================== 🆕 v1.6.3 新增：简单单元测试 ====================

def run_self_tests() -> bool:
    """🆕 v1.6.3：运行简单的自测用例

    Returns:
        True if all tests pass, False otherwise
    """
    print("🧪 运行自测用例...")
    print("=" * 60)

    all_passed = True

    # 测试 1：【分析】段被正确丢弃
    print("\n测试 1: 【分析】段被正确丢弃")
    test_md = """
# 一、单选题

1. 测试题目

A. 选项A
B. 选项B

【分析】这是分析内容，应该被丢弃
【详解】这是详解内容，应该被保留
【答案】A
"""
    result = convert_md_to_examx(test_md, "测试", slug="", enable_issue_detection=False)
    if "【分析】" in result:
        print("  ❌ FAILED: 【分析】未被丢弃")
        all_passed = False
    elif "这是分析内容" in result:
        print("  ❌ FAILED: 分析内容未被丢弃")
        all_passed = False
    elif "这是详解内容" not in result:
        print("  ❌ FAILED: 详解内容未被保留")
        all_passed = False
    else:
        print("  ✅ PASSED")

    # 测试 2：【详解】被正确保留到 \explain{}
    print("\n测试 2: 【详解】被正确保留到 \\explain{}")
    if "\\explain{" in result and "这是详解内容" in result:
        print("  ✅ PASSED")
    else:
        print("  ❌ FAILED: 详解未正确保留")
        all_passed = False

    # 测试 3：*$x$* 模式被正确修复
    print("\n测试 3: *$x$* 模式被正确修复")
    test_text = "这是一个 *$x$* 变量和 *y* 强调"
    result_text = process_text_for_latex(test_text, is_math_heavy=True)
    if "*$" in result_text or "$*" in result_text:
        print(f"  ❌ FAILED: *$x$* 模式未被修复")
        print(f"     结果: {result_text}")
        all_passed = False
    elif "\\emph{y}" not in result_text:
        print(f"  ❌ FAILED: *y* 未转换为 \\emph{{y}}")
        print(f"     结果: {result_text}")
        all_passed = False
    else:
        print("  ✅ PASSED")

    # 测试 4：全角括号被统一
    print("\n测试 4: 全角括号被统一")
    test_text = "这是（全角括号）和｛花括号｝"
    result_text = normalize_fullwidth_brackets(test_text)
    if "（" in result_text or "）" in result_text or "｛" in result_text or "｝" in result_text:
        print(f"  ❌ FAILED: 全角括号未被统一")
        print(f"     结果: {result_text}")
        all_passed = False
    else:
        print("  ✅ PASSED")

    # 测试 5：空 $$ 被清理
    print("\n测试 5: 空 $$ 被清理")
    test_text = "这是 $$ 空数学和 $x$ 正常数学"
    result_text = fix_inline_math_glitches(test_text)
    if "$$" in result_text:
        print(f"  ❌ FAILED: 空 $$ 未被清理")
        print(f"     结果: {result_text}")
        all_passed = False
    else:
        print("  ✅ PASSED")

    # 测试 6：内联图片被正确处理（旧版）
    print("\n测试 6: 内联图片被正确处理（旧版）")
    test_md = """
# 一、单选题

1. 已知集合![](image2.wmf)，则 A∩B 等于

A. 选项A
B. 选项B

【答案】A
"""
    result = convert_md_to_examx(test_md, "测试", slug="", enable_issue_detection=False)
    # 检查：不应该有残留的 ![](image2.wmf)
    if "![](image2.wmf)" in result:
        print(f"  ❌ FAILED: 内联图片标记未被转换")
        all_passed = False
    # 检查：应该有 IMAGE_TODO 注释
    elif "IMAGE_TODO" not in result or "image2.wmf" not in result:
        print(f"  ❌ FAILED: 内联图片未生成 IMAGE_TODO 占位符")
        all_passed = False
    else:
        print("  ✅ PASSED")

    # 测试 7：新格式 IMAGE_TODO_START/END 占位块
    print("\n测试 7: 新格式 IMAGE_TODO_START/END 占位块")
    test_md_new = """
# 一、单选题

1. 已知函数 f(x) 在区间 [0,1] 上单调递增，如图所示：

![](media/graph1.png)

则下列结论中正确的是

A. f(0) < f(1)
B. f(0) > f(1)

【答案】A

2. 集合 A={x|x>0}，集合 B 如图![](media/venn.wmf)所示，则 A∩B 等于

A. 选项A
B. 选项B

【答案】B
"""
    result_new = convert_md_to_examx(test_md_new, "测试新格式", slug="test2025", enable_issue_detection=False)

    # 检查1：不应该有残留的 Markdown 图片语法
    if "![](media/graph1.png)" in result_new or "![](media/venn.wmf)" in result_new:
        print(f"  ❌ FAILED: Markdown 图片语法未被转换")
        all_passed = False
    # 检查2：应该有两个 IMAGE_TODO_START 标记
    elif result_new.count("IMAGE_TODO_START") != 2:
        print(f"  ❌ FAILED: IMAGE_TODO_START 数量不正确 (期望2个，实际{result_new.count('IMAGE_TODO_START')}个)")
        all_passed = False
    # 检查3：应该有两个 IMAGE_TODO_END 标记
    elif result_new.count("IMAGE_TODO_END") != 2:
        print(f"  ❌ FAILED: IMAGE_TODO_END 数量不正确")
        all_passed = False
    # 检查4：第一个图片应该是独立图片 (inline=false)
    elif "inline=false" not in result_new:
        print(f"  ❌ FAILED: 未找到独立图片标记 (inline=false)")
        all_passed = False
    # 检查5：第二个图片应该是内联图片 (inline=true)
    elif "inline=true" not in result_new:
        print(f"  ❌ FAILED: 未找到内联图片标记 (inline=true)")
        all_passed = False
    # 检查6：应该包含 question_index 字段
    elif "question_index=" not in result_new:
        print(f"  ❌ FAILED: 未找到 question_index 字段")
        all_passed = False
    # 检查7：应该包含 AI_AGENT_REPLACE_ME 标记
    elif "AI_AGENT_REPLACE_ME" not in result_new:
        print(f"  ❌ FAILED: 未找到 AI_AGENT_REPLACE_ME 标记")
        all_passed = False
    # 检查8：应该包含 CONTEXT_BEFORE 或 CONTEXT_AFTER
    elif "CONTEXT_BEFORE" not in result_new and "CONTEXT_AFTER" not in result_new:
        print(f"  ❌ FAILED: 未找到上下文信息 (CONTEXT_BEFORE/AFTER)")
        all_passed = False
    # 检查9：ID 应该包含 slug 和题号
    elif "test2025-Q1" not in result_new or "test2025-Q2" not in result_new:
        print(f"  ❌ FAILED: 图片 ID 格式不正确 (应包含 slug-Q{n})")
        all_passed = False
    else:
        print("  ✅ PASSED")
        # 打印一个示例供检查
        print("\n  示例输出片段:")
        lines = result_new.split('\n')
        for i, line in enumerate(lines):
            if 'IMAGE_TODO_START' in line:
                # 打印该行及后续5行
                for j in range(i, min(i+6, len(lines))):
                    print(f"    {lines[j]}")
                break

    # 测试 8：反向定界符简单自动修复（v1.8.8）
    print("\n[自测] 测试 8: 反向定界符简单自动修复")
    test_md_reversed = r"""
# 一、单选题

1. 已知数列 a_n 满足，其中\) ，\(x_i 为整数。

A. 选项A
B. 选项B

【答案】A
"""
    result_reversed = convert_md_to_examx(test_md_reversed, "自测-反向", slug="selftest-reverse", enable_issue_detection=False)
    # 检查：原始的错误模式不应该出现
    if r'\) ，\(' in result_reversed:
        print("  ❌ FAILED: 反向定界符未被修复")
        all_passed = False
    else:
        print("  ✅ PASSED")

    # 测试 9：题内 meta 重复检测（v1.8.8）
    print("\n[自测] 测试 9: 题内 meta 重复检测")
    test_md_meta = """
# 一、单选题

1. 已知函数 f(x) = x^2 + 1 的性质

A. 选项A
B. 选项B

【详解】第一段详解
【详解】第二段详解

【答案】A
"""
    result_meta = convert_md_to_examx(test_md_meta, "自测-重复详解", slug="selftest-meta", enable_issue_detection=True)
    # 检查：多段详解应该被合并成 1 个 \explain
    count_explain = result_meta.count(r'\explain{')
    if count_explain != 1:
        print(f"  ❌ FAILED: \\explain 宏数量为 {count_explain}, 预期为 1")
        all_passed = False
    else:
        print("  ✅ PASSED")

    # 测试 10：array/cases 方程组补 \left\{（v1.8.9）
    print("\n[自测] 测试 10: _fix_array_left_braces 函数 - array 环境")
    # 直接测试函数，避免依赖复杂的转换流程
    test_block_array = r'\begin{array}{l} x + y = 1 \\ x - y = 3 \end{array} \right.'
    result_block_array = _fix_array_left_braces(test_block_array)
    if r'\left\{' in result_block_array and r'\begin{array}' in result_block_array:
        print("  ✅ PASSED")
    else:
        print(f"  ❌ FAILED: 未补上 \\left\\{{")
        print(f"     输入: {test_block_array[:60]}...")
        print(f"     输出: {result_block_array[:60]}...")
        all_passed = False

    # 测试 11：cases 方程组补 \left\{（v1.8.9）
    print("\n[自测] 测试 11: _fix_array_left_braces 函数 - cases 环境")
    test_block_cases = r'f(x) = \begin{cases} x^2, & x > 0 \\ -x, & x \leq 0 \end{cases} \right.'
    result_block_cases = _fix_array_left_braces(test_block_cases)
    if r'\left\{' in result_block_cases and r'\begin{cases}' in result_block_cases:
        print("  ✅ PASSED")
    else:
        print(f"  ❌ FAILED: 未补上 \\left\\{{")
        print(f"     输入: {test_block_cases[:60]}...")
        print(f"     输出: {result_block_cases[:60]}...")
        all_passed = False

    # 测试 12：_fix_array_left_braces 函数 - 已有 \left 的情况（不应重复补）
    print("\n[自测] 测试 12: _fix_array_left_braces 函数 - 已有 \\left 不应重复补")
    test_block_exist = r'\left\{\begin{array}{l} x = 1 \\ y = 2 \end{array} \right.'
    result_block_exist = _fix_array_left_braces(test_block_exist)
    # 应该只有一个 \left\{
    left_brace_count = result_block_exist.count(r'\left\{')
    if left_brace_count == 1:
        print("  ✅ PASSED")
    else:
        print(f"  ❌ FAILED: \\left\\{{ 数量为 {left_brace_count}, 预期为 1")
        print(f"     输出: {result_block_exist[:80]}...")
        all_passed = False

    # 测试 13：单行多选项展开（含 $$）
    print("\n测试 13: 单行多选项展开（含 $$）")
    inline_choices = """> A．$$\\left\\{2,3\\right\\}$$ B．$$\\left\\{1,2\\right\\}$$
> C．文字说明 D．纯文本"""
    expanded = expand_inline_choices(inline_choices)
    expanded_lines = [ln for ln in expanded.splitlines() if re.match(r'^[A-D]', ln)]
    if len(expanded_lines) == 4 and all(ln.startswith(letter) for ln, letter in zip(expanded_lines, ['A', 'B', 'C', 'D'])):
        print("  ✅ PASSED")
    else:
        print(f"  ❌ FAILED: 单行选项展开结果异常: {expanded_lines}")
        all_passed = False

    # 测试 14：图片属性/装饰图片清理
    print("\n测试 14: 图片属性清理与装饰图片移除")
    attr_sample = '![](img.png){width="120px" height="60px"}'
    cleaned_attr = clean_image_attributes(attr_sample)
    tiny_sample = '![](tiny.png){width="1.0e-2in" height="1.0e-2in"}'
    removed_tiny = remove_decorative_images(tiny_sample)
    if '{' in cleaned_attr or 'width' in cleaned_attr:
        print("  ❌ FAILED: 图片属性未被清理")
        all_passed = False
    elif removed_tiny.strip():
        print("  ❌ FAILED: 极小装饰图片未被移除")
        all_passed = False
    else:
        print("  ✅ PASSED")

    # 测试 15：clean_explain_content 空行处理
    print("\n测试 15: clean_explain_content 空行处理")
    explain_text = "第一段内容\n\n第二段\n\n\n第三段"
    cleaned_explain = clean_explain_content(explain_text)
    if "\\par" not in cleaned_explain or "\n\n" in cleaned_explain:
        print(f"  ❌ FAILED: clean_explain_content 未正确替换空行: {cleaned_explain}")
        all_passed = False
    else:
        print("  ✅ PASSED")

    # 测试 16：\\left/\\right 平衡
    print("\n测试 16: balance_left_right_delimiters 修复孤立定界符")
    lr_sample = "\\left( x + y"
    lr_fixed = balance_left_right_delimiters(lr_sample)
    if "\\left" in lr_fixed:
        print(f"  ❌ FAILED: 未降级孤立 \\left: {lr_fixed}")
        all_passed = False
    else:
        print("  ✅ PASSED")

    # 测试 17：ASCII 表格转换
    print("\n测试 17: convert_ascii_table_blocks 转换破折号表格")
    ascii_table = """
  ---------------------- ----------------------
           级数                   名称

            2                     轻风

  ---------------------- ----------------------
"""
    converted = convert_ascii_table_blocks(ascii_table)
    if "\\begin{tabular}" in converted:
        print("  ✅ PASSED")
    else:
        print("  ❌ FAILED: ASCII 表格未被转换")
        all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有测试通过！")
        return True
    else:
        print("❌ 部分测试失败")
        return False


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        success = run_self_tests()
        exit(0 if success else 1)
    else:
        exit(main())
