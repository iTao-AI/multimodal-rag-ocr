#!/usr/bin/env python3
"""
测试覆盖率报告生成脚本
"""
import os
import json
import subprocess
from datetime import datetime
from pathlib import Path

def run_coverage():
    """运行测试覆盖率"""
    backend_dir = Path(__file__).parent.parent
    
    # 运行 pytest 覆盖率
    cmd = [
        "python3", "-m", "pytest",
        "tests/",
        "--cov=.",
        "--cov-report=term-missing",
        "--cov-report=json:logs/coverage.json",
        "--cov-report=html:logs/htmlcov",
        "-v"
    ]
    
    print("🚀 运行测试覆盖率...")
    print(f"工作目录：{backend_dir}")
    print(f"命令：{' '.join(cmd)}")
    print("="*80)
    
    try:
        result = subprocess.run(
            cmd,
            cwd=backend_dir,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ 测试超时 (300s)")
        return False
    except Exception as e:
        print(f"❌ 运行失败：{e}")
        return False


def generate_summary_report():
    """生成覆盖率摘要报告"""
    backend_dir = Path(__file__).parent.parent
    coverage_json = backend_dir / "logs" / "coverage.json"
    
    if not coverage_json.exists():
        print("⚠️  覆盖率 JSON 文件不存在")
        return
    
    with open(coverage_json, 'r') as f:
        data = json.load(f)
    
    # 提取覆盖率信息
    total_covered = data.get('totals', {}).get('covered_lines', 0)
    total_lines = data.get('totals', {}).get('num_lines', 1)
    coverage_percent = (total_covered / total_lines * 100) if total_lines > 0 else 0
    
    # 生成 Markdown 报告
    report = f"""# 测试覆盖率报告

> 📊 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📈 覆盖率摘要

| 指标 | 数值 |
|------|------|
| **总行数** | {total_lines:,} |
| **已覆盖** | {total_covered:,} |
| **未覆盖** | {total_lines - total_covered:,} |
| **覆盖率** | {coverage_percent:.2f}% |

---

## 📁 文件覆盖率详情

| 文件 | 覆盖率 | 已覆盖 | 总行数 | 缺失行 |
|------|--------|--------|--------|--------|
"""
    
    # 按文件统计
    files_data = []
    for file_path, file_data in data.get('files', {}).items():
        if 'monitoring' in file_path or 'config' in file_path or 'tests' in file_path:
            continue  # 跳过监控和测试文件
        
        covered = file_data.get('covered_lines', 0)
        total = file_data.get('num_lines', 0)
        percent = (covered / total * 100) if total > 0 else 0
        missing = file_data.get('missing_lines', [])
        
        files_data.append({
            'file': os.path.basename(file_path),
            'path': file_path,
            'covered': covered,
            'total': total,
            'percent': percent,
            'missing': missing[:10]  # 只显示前 10 个缺失行
        })
    
    # 按覆盖率排序
    files_data.sort(key=lambda x: x['percent'], reverse=True)
    
    for file_info in files_data[:20]:  # 只显示前 20 个文件
        missing_str = ', '.join(map(str, file_info['missing']))
        if len(file_info['missing']) > 10:
            missing_str += '...'
        
        report += f"| {file_info['file']} | {file_info['percent']:.1f}% | {file_info['covered']} | {file_info['total']} | {missing_str} |\n"
    
    report += f"""
---

## 🎯 覆盖率目标

| 等级 | 覆盖率要求 | 当前状态 |
|------|-----------|---------|
| **优秀** | ≥ 80% | {'✅' if coverage_percent >= 80 else '❌'} |
| **良好** | ≥ 60% | {'✅' if coverage_percent >= 60 else '❌'} |
| **合格** | ≥ 40% | {'✅' if coverage_percent >= 40 else '❌'} |

---

## 📊 覆盖率趋势

_待添加：历史覆盖率对比数据_

---

## 🔧 使用说明

### 运行覆盖率测试

```bash
cd ~/projects/demo/Multimodal_RAG/backend
python tests/coverage_report.py
```

### 查看 HTML 报告

```bash
open logs/htmlcov/index.html
```

### 查看 JSON 详细数据

```bash
cat logs/coverage.json | jq
```

---

## 📝 改进建议

"""
    
    # 生成改进建议
    low_coverage_files = [f for f in files_data if f['percent'] < 50]
    if low_coverage_files:
        report += "### 低覆盖率文件 (需要增加测试)\n\n"
        for f in low_coverage_files[:5]:
            report += f"- `{f['file']}` ({f['percent']:.1f}%)\n"
        report += "\n"
    else:
        report += "✅ 所有文件覆盖率均高于 50%\n\n"
    
    report += f"""---

_报告生成：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_
"""
    
    # 保存报告
    report_file = backend_dir / "COVERAGE_REPORT.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n💾 覆盖率报告已保存：{report_file}")
    print(f"📊 HTML 报告：logs/htmlcov/index.html")
    print(f"📈 覆盖率：{coverage_percent:.2f}%")


def main():
    """主函数"""
    print("="*80)
    print("🧪 测试覆盖率报告生成")
    print("="*80)
    
    # 运行覆盖率测试
    success = run_coverage()
    
    if success:
        # 生成报告
        generate_summary_report()
        print("\n✅ 覆盖率测试完成")
    else:
        print("\n❌ 覆盖率测试失败")
        # 仍然尝试生成报告 (如果有部分结果)
        generate_summary_report()


if __name__ == "__main__":
    main()
