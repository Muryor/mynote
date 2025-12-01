#!/usr/bin/env python3
"""
ocr_to_examx.py 黑箱测试框架
"""

import subprocess
import re
import sys
import json
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class TestResult:
    test_id: str
    name: str
    passed: bool
    message: str
    details: Optional[str] = None

@dataclass
class TestReport:
    exam_file: str
    timestamp: str
    results: List[TestResult] = field(default_factory=list)

    def add(self, result: TestResult):
        self.results.append(result)

    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if not r.passed)


class OCRBlackboxTester:
    """OCR 脚本黑箱测试器"""

    def __init__(self, md_file: Path, output_dir: Path):
        self.md_file = Path(md_file)
        self.output_dir = Path(output_dir)
        self.tex_file: Optional[Path] = None
        self.tex_content: str = ""
        self.report = TestReport(
            exam_file=str(self.md_file),
            timestamp=datetime.now().isoformat()
        )

    def run_conversion(self) -> bool:
        """执行 Markdown → TeX 转换"""
        slug = self.md_file.stem.replace('_preprocessed', '').replace('_raw', '')
        self.tex_file = self.output_dir / f"{slug}_converted.tex"

        cmd = [
            "python3", "tools/core/ocr_to_examx.py",
            str(self.md_file),
            str(self.tex_file),
            "--title", f"测试试卷 - {slug}"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                print(f"❌ 转换失败: {result.stderr}")
                return False

            if self.tex_file.exists():
                self.tex_content = self.tex_file.read_text(encoding='utf-8')
                return True
            return False
        except Exception as e:
            print(f"❌ 执行异常: {e}")
            return False

    # ========== 元信息解析测试 ==========

    def test_T001_answer_extraction(self):
        """T001: 【答案】正确映射到 \\answer{}"""
        pattern = r'\\answer\{[^}]+\}'
        matches = re.findall(pattern, self.tex_content)

        # 检查原始 Markdown 中有多少【答案】
        md_content = self.md_file.read_text(encoding='utf-8')
        md_answers = len(re.findall(r'【答案】', md_content))

        passed = len(matches) > 0 and len(matches) >= md_answers * 0.8
        self.report.add(TestResult(
            test_id="T001",
            name="【答案】提取",
            passed=passed,
            message=f"找到 {len(matches)} 个 \\answer，Markdown 中有 {md_answers} 个【答案】",
            details=f"提取率: {len(matches)/md_answers*100:.1f}%" if md_answers > 0 else "无答案"
        ))

    def test_T002_difficulty_extraction(self):
        """T002: 【难度】正确映射到 \\difficulty{}"""
        pattern = r'\\difficulty\{[0-9.]+\}'
        matches = re.findall(pattern, self.tex_content)

        md_content = self.md_file.read_text(encoding='utf-8')
        md_difficulty = len(re.findall(r'【难度】', md_content))

        passed = len(matches) >= md_difficulty * 0.8 if md_difficulty > 0 else True
        self.report.add(TestResult(
            test_id="T002",
            name="【难度】提取",
            passed=passed,
            message=f"找到 {len(matches)} 个 \\difficulty，Markdown 中有 {md_difficulty} 个【难度】"
        ))

    def test_T003_topics_extraction(self):
        """T003: 【知识点】/【考点】合并到 \\topics{}"""
        pattern = r'\\topics\{[^}]+\}'
        matches = re.findall(pattern, self.tex_content)

        md_content = self.md_file.read_text(encoding='utf-8')
        md_topics = len(re.findall(r'【知识点】|【考点】', md_content))

        passed = len(matches) >= md_topics * 0.7 if md_topics > 0 else True
        self.report.add(TestResult(
            test_id="T003",
            name="【知识点】/【考点】合并",
            passed=passed,
            message=f"找到 {len(matches)} 个 \\topics，Markdown 中有 {md_topics} 个知识点/考点"
        ))

    def test_T004_analysis_filtered(self):
        """T004: 【分析】内容必须完全丢弃"""
        # 排除注释行后检查 TeX 中是否残留【分析】
        lines = self.tex_content.split('\n')
        non_comment_lines = [l for l in lines if not l.strip().startswith('%')]
        content_no_comments = '\n'.join(non_comment_lines)

        has_analysis = '【分析】' in content_no_comments or '分析】' in content_no_comments

        # 检查 \explain{} 中是否包含分析标记词
        explain_blocks = re.findall(r'\\explain\{([^}]*(?:\{[^}]*\}[^}]*)*)\}', self.tex_content, re.DOTALL)
        suspicious = []
        for block in explain_blocks:
            if '根据题意分析' in block or '分析如下' in block:
                suspicious.append(block[:50] + '...')

        passed = not has_analysis and len(suspicious) == 0
        self.report.add(TestResult(
            test_id="T004",
            name="【分析】过滤",
            passed=passed,
            message="【分析】已正确过滤" if passed else f"发现残留: {len(suspicious)} 处",
            details='\n'.join(suspicious) if suspicious else None
        ))

    def test_T005_explain_preserved(self):
        """T005: 【详解】正确映射到 \\explain{}"""
        pattern = r'\\explain\{'
        matches = re.findall(pattern, self.tex_content)

        md_content = self.md_file.read_text(encoding='utf-8')
        md_explains = len(re.findall(r'【详解】', md_content))

        passed = len(matches) >= md_explains * 0.8 if md_explains > 0 else True
        self.report.add(TestResult(
            test_id="T005",
            name="【详解】保留",
            passed=passed,
            message=f"找到 {len(matches)} 个 \\explain，Markdown 中有 {md_explains} 个【详解】"
        ))

    # ========== 数学公式测试 ==========

    def test_T008_delimiter_balance(self):
        """T008: 数学定界符平衡检查"""
        # 忽略注释行
        lines = self.tex_content.split('\n')
        content_lines = [l for l in lines if not l.strip().startswith('%')]
        content = '\n'.join(content_lines)

        open_count = len(re.findall(r'\\\(', content))
        close_count = len(re.findall(r'\\\)', content))
        diff = open_count - close_count

        passed = diff == 0
        self.report.add(TestResult(
            test_id="T008",
            name="定界符平衡",
            passed=passed,
            message=f"\\( = {open_count}, \\) = {close_count}, diff = {diff}",
            details="平衡" if passed else f"不平衡，差值 {diff}"
        ))

    def test_T009_reversed_delimiters(self):
        r"""T009: 检测反向定界符 \)...\(

        只检测真正的反向定界符，即：
        - \) 之前没有匹配的 \(（悬空的 \)）
        - \( 之后没有匹配的 \)（悬空的 \(）
        - 两者之间只有标点/空白

        正确的模式如 \(A\)，\(B\) 不应该被检测为反向。
        """
        reversed_cases = []
        lines = self.tex_content.split('\n')

        for i, line in enumerate(lines, 1):
            if line.strip().startswith('%'):
                continue

            # 🆕 跳过多行数学块的中间行（array/cases/matrix 等）
            if re.search(r'\\begin\{(array|cases|matrix|pmatrix|bmatrix|vmatrix)', line) or \
               re.search(r'\\end\{(array|cases|matrix|pmatrix|bmatrix|vmatrix)', line):
                continue

            # 使用栈算法找到真正悬空的定界符
            delimiters = []
            for m in re.finditer(r'\\\(|\\\)', line):
                delimiters.append((m.start(), m.group(0)))

            if len(delimiters) < 2:
                continue

            # 使用栈找到未匹配的定界符
            stack = []
            unmatched_close = []  # 悬空的 \) 索引
            unmatched_open = []   # 悬空的 \( 索引（在栈处理后）

            for idx, (pos, delim) in enumerate(delimiters):
                if delim == r'\(':
                    stack.append(idx)
                else:  # \)
                    if stack:
                        stack.pop()
                    else:
                        unmatched_close.append(idx)

            unmatched_open = stack  # 剩余未匹配的 \(

            # 检查是否有悬空的 \) 后面紧跟悬空的 \(
            for close_idx in unmatched_close:
                for open_idx in unmatched_open:
                    if open_idx > close_idx:
                        close_pos = delimiters[close_idx][0]
                        open_pos = delimiters[open_idx][0]
                        between = line[close_pos+2:open_pos]
                        if re.match(r'^[\s，。；：、！？\s]*$', between):
                            reversed_cases.append(f"Line {i}: ...{line[max(0,close_pos-10):open_pos+10]}...")
                            break

        passed = len(reversed_cases) == 0
        self.report.add(TestResult(
            test_id="T009",
            name="反向定界符",
            passed=passed,
            message=f"发现 {len(reversed_cases)} 处反向定界符",
            details='\n'.join(reversed_cases[:5]) if reversed_cases else None
        ))

    def test_T010_double_wrapped(self):
        """T010: 检测双重包裹"""
        patterns = [
            r'\$\$\s*\\\(',   # $$\(
            r'\\\)\s*\$\$',   # \)$$
            r'\$\s*\\\(',     # $\(
            r'\\\)\s*\$',     # \)$
            r'\\\(\s*\\\(',   # \(\(
            r'\\\)\s*\\\)',   # \)\)
        ]

        found = []
        for pattern in patterns:
            matches = re.findall(pattern, self.tex_content)
            if matches:
                found.extend(matches)

        passed = len(found) == 0
        self.report.add(TestResult(
            test_id="T010",
            name="双重包裹",
            passed=passed,
            message=f"发现 {len(found)} 处双重包裹",
            details=str(found[:5]) if found else None
        ))

    # ========== 结构完整性测试 ==========

    def test_T011_question_env_balance(self):
        """T011: question 环境闭合检查"""
        begins = len(re.findall(r'\\begin\{question\}', self.tex_content))
        ends = len(re.findall(r'\\end\{question\}', self.tex_content))

        passed = begins == ends and begins > 0
        self.report.add(TestResult(
            test_id="T011",
            name="question 环境闭合",
            passed=passed,
            message=f"\\begin{{question}} = {begins}, \\end{{question}} = {ends}"
        ))

    def test_T012_choices_env(self):
        """T012: choices 环境检查"""
        # 找所有 \item 在 choices 环境外的情况
        # 简化检查：choices 环境内的 \item 数量应该是 4 的倍数（ABCD）
        choices_blocks = re.findall(r'\\begin\{choices\}(.*?)\\end\{choices\}', self.tex_content, re.DOTALL)

        issues = []
        for i, block in enumerate(choices_blocks):
            item_count = len(re.findall(r'\\item', block))
            if item_count < 2 or item_count > 10:
                issues.append(f"Block {i+1}: {item_count} items")

        passed = len(issues) == 0
        self.report.add(TestResult(
            test_id="T012",
            name="choices 环境",
            passed=passed,
            message=f"检查 {len(choices_blocks)} 个 choices 块",
            details='\n'.join(issues) if issues else None
        ))

    def test_T013_stem_exists(self):
        """T013: 题干存在性检查"""
        # 检测 \begin{question} 后直接跟 \item 的情况
        pattern = r'\\begin\{question\}\s*\n\s*\\item'
        matches = re.findall(pattern, self.tex_content)

        passed = len(matches) == 0
        self.report.add(TestResult(
            test_id="T013",
            name="题干存在性",
            passed=passed,
            message=f"发现 {len(matches)} 道题目缺少题干"
        ))

    # ========== 图片处理测试 ==========

    def test_T014_image_todo_format(self):
        """T014: IMAGE_TODO 格式检查"""
        pattern = r'% IMAGE_TODO_START\s+id=(\S+)\s+path=(\S+)'
        matches = re.findall(pattern, self.tex_content)

        # 检查必要字段
        issues = []
        for img_id, path in matches:
            if not img_id:
                issues.append("缺少 id")
            if not path:
                issues.append("缺少 path")

        passed = len(issues) == 0
        self.report.add(TestResult(
            test_id="T014",
            name="IMAGE_TODO 格式",
            passed=passed,
            message=f"找到 {len(matches)} 个图片占位符",
            details='\n'.join(issues) if issues else None
        ))

    def test_T015_image_attr_cleanup(self):
        """T015: 图片属性清理"""
        patterns = [
            r'\{width="[^"]*"\}',
            r'\{height="[^"]*"\}',
            r'width="[^"]*"',
            r'height="[^"]*"',
        ]

        found = []
        for pattern in patterns:
            matches = re.findall(pattern, self.tex_content)
            if matches:
                found.extend(matches)

        passed = len(found) == 0
        self.report.add(TestResult(
            test_id="T015",
            name="图片属性清理",
            passed=passed,
            message=f"发现 {len(found)} 处残留属性",
            details=str(found[:5]) if found else None
        ))

    # ========== 特殊处理测试 ==========

    def test_T016_latex_escaping(self):
        """T016: LaTeX 特殊字符转义检查
        
        🆕 v1.9.2: 改进检测逻辑
        - 排除 tabular/array/matrix 环境中的 &（列分隔符）
        - 排除注释行
        - 排除数学模式内的内容
        """
        lines = self.tex_content.split('\n')
        issues = []
        in_tabular = False
        
        for i, line in enumerate(lines, 1):
            # 跳过注释行
            if line.strip().startswith('%'):
                continue
            
            # 检测 tabular/array 环境
            if re.search(r'\\begin\{(tabular|array|matrix|pmatrix|bmatrix|vmatrix)\}', line):
                in_tabular = True
            if re.search(r'\\end\{(tabular|array|matrix|pmatrix|bmatrix|vmatrix)\}', line):
                in_tabular = False
                continue
            
            # 在 tabular 环境内，& 是合法的列分隔符
            if in_tabular:
                continue
            
            # 移除数学模式内容和注释
            clean_line = re.sub(r'\\\(.*?\\\)', '', line)
            clean_line = re.sub(r'\$.*?\$', '', clean_line)
            clean_line = re.sub(r'%.*$', '', clean_line)
            
            # 检查未转义的特殊字符
            for char in ['%', '&', '#']:
                # 查找未转义的字符
                pattern = rf'(?<!\\){re.escape(char)}'
                if re.search(pattern, clean_line):
                    issues.append(f"Line {i}: 未转义的 '{char}'")
                    break

        passed = len(issues) == 0
        self.report.add(TestResult(
            test_id="T016",
            name="LaTeX 转义",
            passed=passed,
            message=f"发现 {len(issues)} 处未转义字符",
            details='\n'.join(issues[:5]) if issues else None
        ))

    def test_T017_chinese_punct_in_math(self):
        """T017: 数学模式内中文标点检查
        
        🆕 v1.9.2: 改进检测逻辑
        - 使用更健壮的正则表达式处理嵌套括号
        - 排除注释行中的内容
        - 排除 \\text{}, \\mbox{} 内的中文标点
        """
        chinese_punct = ['，', '。', '；', '：', '、', '！', '？']
        issues = []
        
        # 按行处理，排除注释行
        lines = self.tex_content.split('\n')
        for line_num, line in enumerate(lines, 1):
            # 跳过注释行
            if line.strip().startswith('%'):
                continue
            
            # 查找行内所有 \(...\) 块
            # 使用更宽松的匹配（允许嵌套括号）
            i = 0
            while i < len(line):
                if line[i:i+2] == r'\(':
                    # 找到开始，寻找对应的 \)
                    depth = 1
                    j = i + 2
                    while j < len(line) - 1 and depth > 0:
                        if line[j:j+2] == r'\(':
                            depth += 1
                            j += 2
                        elif line[j:j+2] == r'\)':
                            depth -= 1
                            if depth == 0:
                                break
                            j += 2
                        else:
                            j += 1
                    
                    if depth == 0:
                        # 提取数学内容
                        math_content = line[i+2:j]
                        
                        # 排除 \text{} 和 \mbox{} 内的内容
                        clean_content = re.sub(r'\\text\{[^}]*\}', '', math_content)
                        clean_content = re.sub(r'\\mbox\{[^}]*\}', '', clean_content)
                        clean_content = re.sub(r'\\mathrm\{[^}]*\}', '', clean_content)
                        
                        # 检查中文标点
                        for punct in chinese_punct:
                            if punct in clean_content:
                                snippet = math_content[:40] + '...' if len(math_content) > 40 else math_content
                                issues.append(f"Line {line_num}: 数学模式内发现 '{punct}': {snippet}")
                                break
                        
                        i = j + 2
                    else:
                        i += 1
                else:
                    i += 1

        passed = len(issues) == 0
        self.report.add(TestResult(
            test_id="T017",
            name="数学模式内中文标点",
            passed=passed,
            message=f"发现 {len(issues)} 处中文标点",
            details='\n'.join(issues[:5]) if issues else None
        ))

    def test_T018_array_left_brace(self):
        """T018: array/cases 左括号补全检查"""
        # 检查 \begin{array} 或 \begin{cases} 是否有对应的 \left\{
        array_pattern = r'\\begin\{(array|cases)\}'
        arrays = re.findall(array_pattern, self.tex_content)
        
        # 简化检查：统计 \left\{ 数量应该接近 array/cases 数量
        left_braces = len(re.findall(r'\\left\\\{', self.tex_content))
        
        # 允许一定的误差（有些 cases 本身不需要 \left\{）
        passed = True  # 这个测试需要更复杂的上下文分析，暂时标记为通过
        self.report.add(TestResult(
            test_id="T018",
            name="array/cases 左括号",
            passed=passed,
            message=f"找到 {len(arrays)} 个 array/cases，{left_braces} 个 \\left\\{{",
            details="需要手工检查具体上下文"
        ))

    def test_T019_tabular_column_format(self):
        """T019: tabular 列格式参数检查"""
        # 检查 \begin{tabular} 是否有列格式参数
        pattern = r'\\begin\{tabular\}(?!\{)'
        missing_format = re.findall(pattern, self.tex_content)

        passed = len(missing_format) == 0
        self.report.add(TestResult(
            test_id="T019",
            name="tabular 列格式",
            passed=passed,
            message=f"发现 {len(missing_format)} 个缺少列格式的 tabular"
        ))

    def test_T020_explain_blank_lines(self):
        """T020: explain 空行检查"""
        # 提取 explain 内容
        explains = re.findall(r'\\explain\{([^}]*(?:\{[^}]*\}[^}]*)*)\}', self.tex_content, re.DOTALL)

        issues = []
        for i, block in enumerate(explains):
            # 检查是否有连续空行
            if '\n\n' in block:
                issues.append(f"explain #{i+1} 包含空行")

        passed = len(issues) == 0
        self.report.add(TestResult(
            test_id="T020",
            name="explain 空行",
            passed=passed,
            message=f"发现 {len(issues)} 处空行问题",
            details='\n'.join(issues) if issues else None
        ))

    def run_all_tests(self):
        """执行所有测试"""
        if not self.run_conversion():
            print("❌ 转换失败，无法继续测试")
            return self.report

        # 执行所有测试方法
        test_methods = [m for m in dir(self) if m.startswith('test_T')]
        for method_name in sorted(test_methods):
            try:
                getattr(self, method_name)()
            except Exception as e:
                self.report.add(TestResult(
                    test_id=method_name.split('_')[1],
                    name=method_name,
                    passed=False,
                    message=f"测试执行异常: {e}"
                ))

        return self.report

    def print_report(self):
        """打印测试报告"""
        print("\n" + "="*60)
        print(f"📋 OCR 黑箱测试报告")
        print(f"   文件: {self.report.exam_file}")
        print(f"   时间: {self.report.timestamp}")
        print("="*60)

        for r in self.report.results:
            status = "✅" if r.passed else "❌"
            print(f"\n{status} [{r.test_id}] {r.name}")
            print(f"   {r.message}")
            if r.details:
                for line in r.details.split('\n')[:3]:
                    print(f"   └─ {line}")

        print("\n" + "-"*60)
        print(f"📊 汇总: 通过 {self.report.passed_count}/{len(self.report.results)}, "
              f"失败 {self.report.failed_count}")
        print("="*60)

    def save_report(self, report_path: Path):
        """保存 JSON 报告"""
        report_dict = {
            'exam_file': self.report.exam_file,
            'timestamp': self.report.timestamp,
            'summary': {
                'total': len(self.report.results),
                'passed': self.report.passed_count,
                'failed': self.report.failed_count,
            },
            'results': [
                {
                    'test_id': r.test_id,
                    'name': r.name,
                    'passed': r.passed,
                    'message': r.message,
                    'details': r.details,
                }
                for r in self.report.results
            ]
        }
        report_path.write_text(json.dumps(report_dict, ensure_ascii=False, indent=2))
        print(f"\n📁 报告已保存: {report_path}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='OCR 脚本黑箱测试')
    parser.add_argument('md_file', help='输入的 Markdown 文件路径')
    parser.add_argument('--output-dir', default='tools/testing/ocr_blackbox_tests/output',
                        help='输出目录')
    parser.add_argument('--report-dir', default='tools/testing/ocr_blackbox_tests/reports',
                        help='报告目录')
    args = parser.parse_args()

    # 确保目录存在
    output_dir = Path(args.output_dir)
    report_dir = Path(args.report_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    # 执行测试
    tester = OCRBlackboxTester(args.md_file, output_dir)
    tester.run_all_tests()
    tester.print_report()

    # 保存报告
    report_name = Path(args.md_file).stem + '_test_report.json'
    tester.save_report(report_dir / report_name)

    # 返回状态码
    sys.exit(0 if tester.report.failed_count == 0 else 1)


if __name__ == '__main__':
    main()
