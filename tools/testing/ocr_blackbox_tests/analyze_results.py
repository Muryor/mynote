#!/usr/bin/env python3
"""
汇总黑箱测试结果，生成 SUMMARY.md 和 ISSUES.md
"""

import json
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

def load_all_reports(reports_dir: Path):
    """加载所有 JSON 测试报告"""
    reports = []
    for report_file in reports_dir.glob('*_test_report.json'):
        try:
            data = json.loads(report_file.read_text(encoding='utf-8'))
            reports.append(data)
        except Exception as e:
            print(f"⚠️ 无法加载 {report_file}: {e}")
    return reports

def analyze_reports(reports):
    """分析所有测试报告"""
    total_exams = len(reports)
    
    # 统计每个测试用例的通过率
    test_stats = defaultdict(lambda: {'passed': 0, 'failed': 0, 'failures': []})
    
    # 统计问题类型
    issue_types = Counter()
    
    for report in reports:
        exam_name = Path(report['exam_file']).stem
        for result in report['results']:
            test_id = result['test_id']
            if result['passed']:
                test_stats[test_id]['passed'] += 1
            else:
                test_stats[test_id]['failed'] += 1
                test_stats[test_id]['failures'].append({
                    'exam': exam_name,
                    'message': result['message'],
                    'details': result['details']
                })
                issue_types[result['name']] += 1
    
    return {
        'total_exams': total_exams,
        'test_stats': dict(test_stats),
        'issue_types': issue_types
    }

def generate_summary(analysis, output_path: Path):
    """生成 SUMMARY.md"""
    total_exams = analysis['total_exams']
    test_stats = analysis['test_stats']
    issue_types = analysis['issue_types']
    
    content = f"""# OCR 黑箱测试总结报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**测试试卷数量**: {total_exams}  
**测试用例数量**: {len(test_stats)}

## 整体统计

| 指标 | 数值 |
|------|------|
| 测试试卷总数 | {total_exams} |
| 测试用例总数 | {len(test_stats)} |
| 总测试次数 | {total_exams * len(test_stats)} |
| 总通过次数 | {sum(s['passed'] for s in test_stats.values())} |
| 总失败次数 | {sum(s['failed'] for s in test_stats.values())} |
| 整体通过率 | {sum(s['passed'] for s in test_stats.values()) / (total_exams * len(test_stats)) * 100:.1f}% |

## 测试用例通过率详情

| 测试ID | 测试名称 | 通过 | 失败 | 通过率 | 状态 |
|--------|---------|------|------|--------|------|
"""
    
    # 按失败次数排序
    sorted_tests = sorted(test_stats.items(), key=lambda x: x[1]['failed'], reverse=True)
    
    for test_id, stats in sorted_tests:
        passed = stats['passed']
        failed = stats['failed']
        total = passed + failed
        pass_rate = passed / total * 100 if total > 0 else 0
        
        # 获取测试名称
        test_name = "未知"
        if failed > 0 and stats['failures']:
            # 从第一个失败中获取名称（需要从原始报告反查）
            pass
        
        status = "✅" if failed == 0 else "❌" if failed > total * 0.5 else "⚠️"
        
        content += f"| {test_id} | | {passed} | {failed} | {pass_rate:.1f}% | {status} |\n"
    
    content += f"""
## 主要问题类型（按出现频率）

| 问题类型 | 出现次数 | 严重程度 |
|---------|---------|----------|
"""
    
    for issue_type, count in issue_types.most_common():
        severity = "P0" if issue_type in ["定界符平衡", "question 环境闭合"] else \
                   "P1" if issue_type in ["【答案】提取", "【分析】过滤"] else "P2"
        content += f"| {issue_type} | {count} | {severity} |\n"
    
    content += """
## 问题严重程度分级说明

- **P0**: 导致编译失败（定界符不平衡、环境不闭合）
- **P1**: 导致内容错误（【答案】丢失、【分析】未过滤）
- **P2**: 导致格式问题（空行、图片属性残留、中文标点）

## 关键发现

"""
    
    # 添加关键发现
    critical_issues = []
    for test_id, stats in sorted_tests:
        if stats['failed'] > 0:
            if test_id == "T008":
                critical_issues.append(f"⚠️ **定界符不平衡**: {stats['failed']}/{total_exams} 份试卷存在 `\\(` 和 `\\)` 不匹配问题")
            elif test_id == "T017":
                critical_issues.append(f"⚠️ **数学模式内中文标点**: {stats['failed']}/{total_exams} 份试卷存在中文标点未转换问题")
            elif test_id == "T016":
                critical_issues.append(f"⚠️ **LaTeX 字符未转义**: {stats['failed']}/{total_exams} 份试卷存在 `&`, `%`, `#` 等字符未转义")
    
    for issue in critical_issues[:5]:
        content += issue + "\n\n"
    
    content += """
## 测试覆盖范围

### 测试的试卷文件
"""
    
    # 列出所有测试的文件（从报告目录获取）
    content += "\n查看 `tools/testing/ocr_blackbox_tests/reports/` 目录下的详细报告。\n"
    
    content += """
## 后续行动建议

1. **优先修复 P0 问题**: 定界符不平衡会导致 LaTeX 编译失败
2. **处理 P1 问题**: 确保元信息提取的准确性
3. **优化 P2 问题**: 提升生成文档的专业性

## 详细问题清单

参见 `ISSUES.md` 获取每个问题的详细分析和修复建议。
"""
    
    output_path.write_text(content, encoding='utf-8')
    print(f"✅ 生成测试总结: {output_path}")

def generate_issues(analysis, output_path: Path):
    """生成 ISSUES.md"""
    test_stats = analysis['test_stats']
    
    content = f"""# OCR 黑箱测试问题清单

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

本文档记录了在黑箱测试中发现的所有问题，按严重程度排序。

---

"""
    
    # 按严重程度和失败次数组织问题
    p0_issues = []
    p1_issues = []
    p2_issues = []
    
    for test_id, stats in test_stats.items():
        if stats['failed'] == 0:
            continue
        
        # 确定严重程度
        if test_id in ["T008", "T011"]:
            severity = "P0"
            issue_list = p0_issues
        elif test_id in ["T001", "T002", "T004", "T005"]:
            severity = "P1"
            issue_list = p1_issues
        else:
            severity = "P2"
            issue_list = p2_issues
        
        # 构建问题条目
        issue = {
            'test_id': test_id,
            'severity': severity,
            'failed_count': stats['failed'],
            'failures': stats['failures']
        }
        issue_list.append(issue)
    
    # 生成问题详情
    issue_num = 1
    
    if p0_issues:
        content += "## P0 级别问题（导致编译失败）\n\n"
        for issue in sorted(p0_issues, key=lambda x: x['failed_count'], reverse=True):
            content += generate_issue_detail(issue_num, issue)
            issue_num += 1
    
    if p1_issues:
        content += "\n## P1 级别问题（导致内容错误）\n\n"
        for issue in sorted(p1_issues, key=lambda x: x['failed_count'], reverse=True):
            content += generate_issue_detail(issue_num, issue)
            issue_num += 1
    
    if p2_issues:
        content += "\n## P2 级别问题（导致格式问题）\n\n"
        for issue in sorted(p2_issues, key=lambda x: x['failed_count'], reverse=True):
            content += generate_issue_detail(issue_num, issue)
            issue_num += 1
    
    output_path.write_text(content, encoding='utf-8')
    print(f"✅ 生成问题清单: {output_path}")

def generate_issue_detail(issue_num, issue):
    """生成单个问题的详细信息"""
    test_id = issue['test_id']
    severity = issue['severity']
    failed_count = issue['failed_count']
    failures = issue['failures']
    
    # 问题标题映射
    title_map = {
        'T008': '数学定界符不平衡',
        'T016': 'LaTeX 特殊字符未转义',
        'T017': '数学模式内存在中文标点',
        'T001': '【答案】提取不完整',
        'T004': '【分析】内容未过滤',
        # 可以继续添加...
    }
    
    title = title_map.get(test_id, f"测试 {test_id} 失败")
    
    content = f"""### 问题 {issue_num}: {title}

**测试用例**: {test_id}  
**严重程度**: {severity}  
**影响范围**: {failed_count} 份试卷

**现象**：
"""
    
    if failures:
        first_failure = failures[0]
        content += f"{first_failure['message']}\n\n"
        
        if first_failure['details']:
            content += f"**示例**：\n```\n{first_failure['details'][:200]}\n```\n\n"
    
    # 添加原因分析和修复建议
    if test_id == "T008":
        content += """**原因分析**：
- 数学公式转换过程中，`\\(` 和 `\\)` 的配对逻辑存在问题
- 可能在处理嵌套公式或特殊格式时丢失定界符

**修复建议**：
1. 在 `ocr_to_examx.py` 中增强数学定界符平衡检查
2. 添加后处理步骤，自动修复不平衡的定界符
3. 考虑使用栈结构跟踪定界符配对

"""
    
    elif test_id == "T017":
        content += """**原因分析**：
- 数学模式内的中文标点（全角）未转换为半角
- 影响 LaTeX 公式的正确渲染

**修复建议**：
1. 在数学模式处理阶段，自动转换全角标点为半角
2. 添加 `，` → `,`、`。` → `.` 等映射规则
3. 保留 `\\text{}` 和 `\\mbox{}` 内的中文标点

"""
    
    elif test_id == "T016":
        content += """**原因分析**：
- LaTeX 特殊字符（`%`, `&`, `#` 等）在非数学模式下未正确转义
- 通常出现在表格或特殊格式中

**修复建议**：
1. 在文本处理阶段，自动转义特殊字符为 `\\%`, `\\&`, `\\#`
2. 排除已经在数学模式或注释中的字符
3. 优先处理表格环境中的 `&` 字符

"""
    
    content += "**受影响的试卷**：\n"
    for failure in failures[:5]:
        content += f"- {failure['exam']}\n"
    
    if len(failures) > 5:
        content += f"- ... 以及其他 {len(failures) - 5} 份试卷\n"
    
    content += "\n---\n\n"
    
    return content

def main():
    reports_dir = Path('tools/testing/ocr_blackbox_tests/reports')
    
    if not reports_dir.exists():
        print("❌ 报告目录不存在")
        return
    
    print("📊 加载测试报告...")
    reports = load_all_reports(reports_dir)
    
    if not reports:
        print("❌ 未找到测试报告")
        return
    
    print(f"✅ 加载了 {len(reports)} 份测试报告")
    
    print("🔍 分析测试结果...")
    analysis = analyze_reports(reports)
    
    print("📝 生成测试总结...")
    summary_path = Path('tools/testing/ocr_blackbox_tests/SUMMARY.md')
    generate_summary(analysis, summary_path)
    
    print("📝 生成问题清单...")
    issues_path = Path('tools/testing/ocr_blackbox_tests/ISSUES.md')
    generate_issues(analysis, issues_path)
    
    print("\n✅ 测试报告生成完成！")
    print(f"   - 总结报告: {summary_path}")
    print(f"   - 问题清单: {issues_path}")

if __name__ == '__main__':
    main()
