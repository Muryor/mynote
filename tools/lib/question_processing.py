#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
question_processing.py - 题目处理模块 - 结构修复、合并、格式化

从 ocr_to_examx.py 提取的共享工具函数，供 exam 和 handout 转换器使用。

生成时间: 自动提取
源文件: tools/core/ocr_to_examx.py
"""

from typing import List, Dict, Tuple, Optional
import re

# ============================================================
# 题目处理模块 - 结构修复、合并、格式化
# ============================================================

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
                # 检查是否已经包含 enumerate 或 choices（避免重复处理）
                has_enumerate = any(r'\begin{enumerate}' in qline for qline in question_lines)
                has_choices = any(r'\begin{choices}' in qline for qline in question_lines)

                if not has_enumerate and not has_choices:
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




def fix_circled_subquestions_to_nested_enumerate(text: str) -> str:
    r"""🆕 v1.9.13：将 enumerate 中的 ①②③ 子题转换为嵌套 enumerate
    
    问题模式：
    在 enumerate 环境的某个 \item 下，出现了 ①②③ 形式的子题，但没有被
    包裹在嵌套的 enumerate 中，导致 LaTeX 编译时出现 "Non-\item content 
    inside enumerate environment" 警告。
    
    输入示例：
        \begin{enumerate}[label=(\arabic*)]
          \item 当\(a = 1\)时，求切线方程；
          \item 若\(f(x)\)有两个极值点\(x_{1},x_{2}\)．
        
        ①求\(a\)的取值范围；
        
        ②证明：存在\(0 < x_{0} < \frac{2}{a}\)...
        \end{enumerate}
    
    输出示例：
        \begin{enumerate}[label=(\arabic*)]
          \item 当\(a = 1\)时，求切线方程；
          \item 若\(f(x)\)有两个极值点\(x_{1},x_{2}\)．
            \begin{enumerate}[label=\textcircled{\arabic*}]
              \item 求\(a\)的取值范围；
              \item 证明：存在\(0 < x_{0} < \frac{2}{a}\)...
            \end{enumerate}
        \end{enumerate}
    
    策略：
    1. 检测 enumerate 环境内的 ①②③ 开头的行
    2. 将连续的 ①②③ 行包裹在嵌套的 enumerate 中
    3. 将 ①②③ 替换为 \item
    """
    import re
    
    lines = text.split('\n')
    result = []
    i = 0
    n = len(lines)
    
    # 圆圈数字到普通数字的映射
    circled_to_num = {'①': '1', '②': '2', '③': '3', '④': '4', '⑤': '5',
                      '⑥': '6', '⑦': '7', '⑧': '8', '⑨': '9', '⑩': '10'}
    circled_pattern = re.compile(r'^(\s*)([①②③④⑤⑥⑦⑧⑨⑩])(.*)$')
    
    in_enumerate = False
    enumerate_depth = 0
    
    while i < n:
        line = lines[i]
        stripped = line.strip()
        
        # 跟踪 enumerate 环境
        if r'\begin{enumerate}' in stripped:
            enumerate_depth += 1
            in_enumerate = True
            result.append(line)
            i += 1
            continue
        
        if r'\end{enumerate}' in stripped:
            enumerate_depth -= 1
            if enumerate_depth == 0:
                in_enumerate = False
            result.append(line)
            i += 1
            continue
        
        # 在 enumerate 内部检测 ① 开头的行
        if in_enumerate and enumerate_depth == 1:
            m = circled_pattern.match(line)
            if m:
                indent = m.group(1)
                # 收集连续的 ①②③ 行
                subq_lines = []
                while i < n:
                    current_line = lines[i]
                    current_stripped = current_line.strip()
                    
                    # 检查是否是 ① 开头
                    cm = circled_pattern.match(current_line)
                    if cm:
                        # 转换为 \item
                        content = cm.group(3)
                        subq_lines.append(f'{indent}    \\item {content.strip()}')
                        i += 1
                    elif current_stripped == '':
                        # 空行可能在子题之间
                        # 检查下一行是否还是 ①②③
                        if i + 1 < n and circled_pattern.match(lines[i + 1]):
                            i += 1  # 跳过空行
                            continue
                        else:
                            break
                    elif current_stripped.startswith(r'\end{enumerate}'):
                        break
                    elif r'\item' in current_stripped or current_stripped.startswith(r'\begin'):
                        break
                    else:
                        # 可能是上一个子题的续行
                        if subq_lines:
                            subq_lines[-1] += ' ' + current_stripped
                        i += 1
                
                # 如果收集到了子题，包裹在嵌套 enumerate 中
                if subq_lines:
                    result.append(f'{indent}  \\begin{{enumerate}}[label=(\\arabic*)]')
                    result.extend(subq_lines)
                    result.append(f'{indent}  \\end{{enumerate}}')
                continue
        
        result.append(line)
        i += 1
    
    return '\n'.join(result)




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
    - 🆕 v1.9.12：对使用 label=(\arabic*) 的 enumerate 不处理（已正确格式化）
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
    # 🆕 v1.9.12：跟踪是否在 label=(\arabic*) 风格的 enumerate 中
    in_labeled_enumerate = False
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
            # 🆕 v1.9.12：检测是否是 label= 风格的 enumerate
            if 'label=' in line:
                in_labeled_enumerate = True
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
                in_labeled_enumerate = False
            i += 1
            continue
        
        # 如果不在 enumerate 中，直接输出
        if not in_enumerate:
            result.append(line)
            i += 1
            continue
        
        # 🆕 v1.9.12：如果在 label= 风格的 enumerate 中，不做合并处理
        if in_labeled_enumerate:
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




def fix_keep_questions_together(text: str) -> str:
    r"""🆕 v1.9.7：尽量不分页（保守）

    ⚠️ 已禁用：samepage 环境不能在 question 环境内部使用，会导致嵌套错误。
    需要在 examx.sty 中通过其他方式实现（如 needspace 或 samepage 在 question 环境定义中）。
    
    原设计：在每个 `question` 环境的主体前后添加 `samepage` 环境包装
    问题：question 环境有特殊结构，内部插入 samepage 会导致 LaTeX 嵌套错误
    """
    # 暂时禁用，直接返回原文本
    return text


# ============================================================
# 选项处理模块 - 选项识别、展开、解析
# ============================================================

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

        # 只在遇到【详解】时进入解析模式，遇到【分析】时跳过
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

    使用保护-分割-恢复策略，避免数学公式干扰选项分割
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
    
    先展开可能的单行选项再解析
    """
    # 先展开可能的单行选项
    content = expand_inline_choices(content)
    
    structure = parse_question_structure(content)
    
    stem = '\n'.join(structure['stem_lines']).strip()
    stem = re.sub(r"^\s*\d+[\.．、]\s*", "", stem)
    
    # 提取的解析内容
    analysis = '\n'.join(structure['analysis_lines']).strip()
    
    return stem, structure['choices'], analysis


# ============================================================
# 导出列表
# ============================================================

__all__ = [
    'fix_merged_questions_structure',
    'fix_circled_subquestions_to_nested_enumerate',
    'fix_nested_subquestions',
    'fix_spurious_items_in_enumerate',
    'fix_missing_items_in_enumerate',
    '_is_likely_stem',
    'fix_keep_questions_together',
    'parse_question_structure',
    'split_inline_choice_line',
    'expand_inline_choices',
    'convert_choices',
]
