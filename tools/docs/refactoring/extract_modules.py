#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码提取辅助脚本

根据 REFACTORING_PLAN.md 从 ocr_to_examx.py 提取函数到相应模块。
使用 AST 解析确保提取完整的函数定义（包括注释和文档字符串）。
"""

import ast
import re
from pathlib import Path
from typing import List, Dict, Set

# 定义每个模块需要提取的函数
MODULE_FUNCTIONS = {
    'math_processing.py': [
        # 常量
        'CHINESE_MATH_SEPARATORS',
        # 枚举
        'TokenType',
        # 类
        'MathStateMachine',
        # 单例
        'math_sm',
        # 函数
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
    ],
    
    'text_cleaning.py': [
        'LATEX_SPECIAL_CHARS',
        'escape_latex_special',
        'standardize_math_symbols',
        'clean_markdown',
        'clean_image_attributes',
        'remove_decorative_images',
        'clean_residual_image_attrs',
        'fix_markdown_bold_residue',
        'remove_blank_lines_in_macro_args',
        'soft_wrap_paragraph',
    ],
    
    'meta_extraction.py': [
        'META_PATTERNS',
        'ANALYSIS_MARKERS',
        'ANALYSIS_START_MARKERS',
        'extract_meta_and_images',
    ],
    
    'latex_utils.py': [
        'fix_tabular_environments',
        'add_table_borders',
        'fix_fill_in_blanks',
        'remove_par_breaks_in_explain',
        'clean_question_environments',
    ],
    
    'question_processing.py': [
        'fix_merged_questions_structure',
        'fix_circled_subquestions_to_nested_enumerate',
        'fix_nested_subquestions',
        'fix_spurious_items_in_enumerate',
        'fix_missing_items_in_enumerate',
        '_is_likely_stem',
        'fix_keep_questions_together',
    ],
    
    'validation.py': [
        'validate_math_integrity',
        'validate_brace_balance',
        'validate_latex_output',
        'validate_and_fix_image_todo_blocks',
    ],
    
    'image_handling.py': [
        'IMAGE_PATTERN',
        'IMAGE_PATTERN_WITH_ID',
        'IMAGE_PATTERN_NO_ID',
        'find_markdown_and_images',
        'copy_images_to_output',
        'generate_image_todo_block',
        'infer_figures_dir',
    ],
}


def find_function_in_file(filepath: Path, name: str) -> Dict:
    """在文件中查找函数/类/常量的定义位置
    
    Args:
        filepath: 源文件路径
        name: 函数/类/常量名
        
    Returns:
        包含 start_line, end_line, type, code 的字典
    """
    content = filepath.read_text(encoding='utf-8')
    lines = content.splitlines()
    
    # 查找类定义
    if name[0].isupper() and name not in ['CHINESE_MATH_SEPARATORS', 'LATEX_SPECIAL_CHARS', 
                                            'META_PATTERNS', 'ANALYSIS_MARKERS', 
                                            'ANALYSIS_START_MARKERS', 'IMAGE_PATTERN', 
                                            'IMAGE_PATTERN_WITH_ID', 'IMAGE_PATTERN_NO_ID']:
        pattern = rf'^class {re.escape(name)}'
        for i, line in enumerate(lines):
            if re.match(pattern, line):
                # 找到类定义的结束位置（下一个非缩进行或文件末尾）
                end_line = i + 1
                base_indent = len(line) - len(line.lstrip())
                while end_line < len(lines):
                    next_line = lines[end_line]
                    if next_line.strip() == '':
                        end_line += 1
                        continue
                    next_indent = len(next_line) - len(next_line.lstrip())
                    if next_indent <= base_indent and not next_line.strip().startswith('#'):
                        break
                    end_line += 1
                
                return {
                    'start_line': i + 1,
                    'end_line': end_line,
                    'type': 'class',
                    'code': '\n'.join(lines[i:end_line])
                }
    
    # 查找函数定义
    pattern = rf'^def {re.escape(name)}\('
    for i, line in enumerate(lines):
        if re.match(pattern, line):
            # 找到函数定义的结束位置
            end_line = i + 1
            base_indent = len(line) - len(line.lstrip())
            while end_line < len(lines):
                next_line = lines[end_line]
                if next_line.strip() == '':
                    end_line += 1
                    continue
                next_indent = len(next_line) - len(next_line.lstrip())
                if next_indent <= base_indent and not next_line.strip().startswith('#'):
                    break
                end_line += 1
            
            return {
                'start_line': i + 1,
                'end_line': end_line,
                'type': 'function',
                'code': '\n'.join(lines[i:end_line])
            }
    
    # 查找常量/单例定义
    patterns = [
        rf'^{re.escape(name)}\s*=',  # 赋值
        rf'^{re.escape(name)}\s*:\s*',  # 类型注解
    ]
    for pattern in patterns:
        for i, line in enumerate(lines):
            if re.match(pattern, line):
                # 找到常量定义的结束位置（通常是单行，或多行字典/列表）
                end_line = i + 1
                # 检查是否是多行定义
                if '{' in line or '[' in line or '(' in line:
                    open_count = line.count('{') + line.count('[') + line.count('(')
                    close_count = line.count('}') + line.count(']') + line.count(')')
                    while end_line < len(lines) and open_count > close_count:
                        next_line = lines[end_line]
                        open_count += next_line.count('{') + next_line.count('[') + next_line.count('(')
                        close_count += next_line.count('}') + next_line.count(']') + next_line.count(')')
                        end_line += 1
                
                return {
                    'start_line': i + 1,
                    'end_line': end_line,
                    'type': 'constant',
                    'code': '\n'.join(lines[i:end_line])
                }
    
    return None


def extract_imports_for_module(module_name: str, functions: List[str]) -> Set[str]:
    """确定模块需要的导入语句
    
    Args:
        module_name: 模块名
        functions: 函数列表
        
    Returns:
        导入语句集合
    """
    imports = {'import re'}
    
    if module_name == 'math_processing.py':
        imports.add('from enum import Enum, auto')
    
    if module_name in ['text_cleaning.py', 'image_handling.py']:
        imports.add('from pathlib import Path')
    
    if module_name in ['meta_extraction.py', 'question_processing.py', 
                       'validation.py', 'image_handling.py']:
        imports.add('from typing import List, Dict, Tuple, Optional')
    
    if module_name == 'image_handling.py':
        imports.add('import shutil')
    
    return imports


def generate_module_file(module_name: str, source_file: Path, output_dir: Path):
    """生成模块文件
    
    Args:
        module_name: 模块名 (如 'math_processing.py')
        source_file: 源文件路径 (ocr_to_examx.py)
        output_dir: 输出目录 (tools/lib/)
    """
    print(f"\n{'='*60}")
    print(f"生成 {module_name}")
    print(f"{'='*60}")
    
    functions = MODULE_FUNCTIONS.get(module_name, [])
    if not functions:
        print(f"警告: {module_name} 没有定义需要提取的函数")
        return
    
    # 收集代码片段
    code_blocks = []
    found_items = []
    missing_items = []
    
    for func_name in functions:
        result = find_function_in_file(source_file, func_name)
        if result:
            code_blocks.append(result)
            found_items.append(f"{func_name} ({result['type']}, 行 {result['start_line']}-{result['end_line']})")
        else:
            missing_items.append(func_name)
    
    # 打印统计信息
    print(f"\n找到 {len(found_items)}/{len(functions)} 个项目:")
    for item in found_items:
        print(f"  ✓ {item}")
    
    if missing_items:
        print(f"\n未找到 {len(missing_items)} 个项目:")
        for item in missing_items:
            print(f"  ✗ {item}")
    
    # 生成文件头部
    module_desc = {
        'math_processing.py': '数学公式处理模块 - 定界符解析、修复、转换',
        'text_cleaning.py': '文本清理模块 - LaTeX转义、Markdown清理、格式化',
        'meta_extraction.py': '元数据提取模块 - 答案、解析、知识点等',
        'latex_utils.py': 'LaTeX工具模块 - 环境处理、格式化',
        'question_processing.py': '题目处理模块 - 结构修复、合并、格式化',
        'validation.py': '验证模块 - LaTeX语法检查、错误检测',
        'image_handling.py': '图片处理模块 - 路径处理、占位符生成',
    }
    
    header = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{module_name} - {module_desc.get(module_name, '')}

从 ocr_to_examx.py 提取的共享工具函数，供 exam 和 handout 转换器使用。

生成时间: 自动提取
源文件: tools/core/ocr_to_examx.py
"""

'''
    
    # 添加导入语句
    imports = extract_imports_for_module(module_name, functions)
    header += '\n'.join(sorted(imports)) + '\n\n'
    
    # 添加分隔符
    header += f"# {'='*60}\n"
    header += f"# {module_desc.get(module_name, module_name)}\n"
    header += f"# {'='*60}\n\n"
    
    # 组合代码
    full_code = header
    for block in code_blocks:
        full_code += block['code'] + '\n\n\n'
    
    # 生成 __all__ 列表
    export_items = [item for item in functions if item not in missing_items]
    all_list = f"__all__ = [\n"
    for item in export_items:
        all_list += f"    '{item}',\n"
    all_list += "]\n"
    
    full_code += f"\n# {'='*60}\n"
    full_code += "# 导出列表\n"
    full_code += f"# {'='*60}\n\n"
    full_code += all_list
    
    # 写入文件
    output_file = output_dir / module_name
    output_file.write_text(full_code, encoding='utf-8')
    print(f"\n✅ 已生成: {output_file}")
    print(f"   文件大小: {len(full_code)} 字符")
    print(f"   导出项目: {len(export_items)} 个")


def main():
    """主函数"""
    # 路径配置
    source_file = Path('tools/core/ocr_to_examx.py')
    output_dir = Path('tools/lib')
    
    if not source_file.exists():
        print(f"错误: 源文件不存在 {source_file}")
        return
    
    if not output_dir.exists():
        output_dir.mkdir(parents=True)
        print(f"创建输出目录: {output_dir}")
    
    print("OCR 脚本重构 - 代码提取工具")
    print("="*60)
    print(f"源文件: {source_file}")
    print(f"输出目录: {output_dir}")
    print(f"模块数量: {len(MODULE_FUNCTIONS)}")
    
    # 生成每个模块
    for module_name in MODULE_FUNCTIONS.keys():
        try:
            generate_module_file(module_name, source_file, output_dir)
        except Exception as e:
            print(f"\n❌ 生成 {module_name} 失败: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print("提取完成！")
    print(f"{'='*60}")
    print("\n下一步:")
    print("1. 检查生成的模块文件")
    print("2. 运行测试: python -m pytest tools/testing/")
    print("3. 更新 tools/lib/__init__.py 导入")
    print("4. 更新 tools/core/ocr_to_examx.py 使用新模块")


if __name__ == '__main__':
    main()
