#!/usr/bin/env python3
"""
墨芯 v5.0 - 最终报告生成器
汇总所有技法提取结果，生成完整的分析报告
"""

import os
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

NOVELS_DIR = Path("/root/.openclaw/workspace/inkcore-v5/novels")

def generate_novel_report(novel_name: str):
    """为单本小说生成完整报告"""
    print(f"=" * 70)
    print(f"墨芯 v5.0 - 《{novel_name}》技法分析报告")
    print(f"=" * 70)
    
    # 读取所有技法文件
    techniques_dir = NOVELS_DIR / novel_name / "techniques"
    technique_files = list(techniques_dir.glob("ch_*_techniques.json"))
    
    print(f"\n📚 数据汇总")
    print(f"   章节数: {len(technique_files)}")
    
    # 统计
    all_techniques = []
    categories = defaultdict(int)
    technique_names = defaultdict(int)
    chapter_techniques = defaultdict(list)
    
    for tf in technique_files:
        with open(tf, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        chapter_num = data.get("chapter_number", 0)
        
        for t in data.get("techniques", []):
            technique_info = {
                "chapter": chapter_num,
                "chapter_title": data.get("chapter_title", ""),
                "name": t.get("name", ""),
                "category": t.get("category", ""),
                "confidence": t.get("confidence", 0),
                "example": t.get("example", "")[:200]
            }
            all_techniques.append(technique_info)
            categories[t.get("category", "unknown")] += 1
            technique_names[t.get("name", "unknown")] += 1
            chapter_techniques[chapter_num].append(technique_info)
    
    print(f"   技法数: {len(all_techniques)}")
    print(f"   平均每章: {len(all_techniques)/len(technique_files):.1f} 个技法")
    
    # 类别统计
    print(f"\n📊 技法类别分布")
    total_cat = sum(categories.values())
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        pct = count / total_cat * 100
        bar = "█" * int(pct / 2)
        cat_name = {
            "plot": "情节",
            "character": "人物",
            "scene": "场景",
            "dialogue": "对话",
            "emotion": "情感",
            "pacing": "节奏",
            "theme": "主题"
        }.get(cat, cat)
        print(f"   {cat_name:6s}: {bar:20s} {count:3d} ({pct:5.1f}%)")
    
    # 高频技法
    print(f"\n🔥 TOP 15 高频技法")
    for i, (name, count) in enumerate(sorted(technique_names.items(), key=lambda x: -x[1])[:15], 1):
        pct = count / len(technique_files) * 100
        print(f"   {i:2d}. {name:12s} 出现 {count:3d} 次  覆盖率 {pct:5.1f}%")
    
    # 生成Markdown报告
    report_md = f"""# 《{novel_name}》技法分析报告

**墨芯 v5.0** | 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## 数据概览

| 指标 | 数值 |
|------|------|
| 总章节数 | {len(technique_files)} |
| 技法总数 | {len(all_techniques)} |
| 平均每章技法 | {len(all_techniques)/len(technique_files):.1f} |
| 技法类别数 | {len(categories)} |

---

## 技法类别分布

"""
    
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        pct = count / total_cat * 100
        cat_name = {
            "plot": "情节",
            "character": "人物",
            "scene": "场景",
            "dialogue": "对话",
            "emotion": "情感",
            "pacing": "节奏",
            "theme": "主题"
        }.get(cat, cat)
        report_md += f"- **{cat_name}**: {count} 个 ({pct:.1f}%)\n"
    
    report_md += f"""

---

## 高频技法排行

| 排名 | 技法名称 | 出现次数 | 覆盖率 |
|------|----------|----------|--------|
"""
    
    for i, (name, count) in enumerate(sorted(technique_names.items(), key=lambda x: -x[1])[:20], 1):
        pct = count / len(technique_files) * 100
        report_md += f"| {i} | {name} | {count} | {pct:.1f}% |\n"
    
    report_md += f"""

---

## 技法详细列表

"""
    
    # 按类别分组展示技法
    by_category = defaultdict(list)
    for t in all_techniques:
        by_category[t["category"]].append(t)
    
    for cat in sorted(by_category.keys()):
        cat_name = {
            "plot": "情节",
            "character": "人物",
            "scene": "场景",
            "dialogue": "对话",
            "emotion": "情感",
            "pacing": "节奏",
            "theme": "主题"
        }.get(cat, cat)
        
        report_md += f"### {cat_name}类技法\n\n"
        
        # 获取该类别下的前10个技法示例
        cat_techniques = by_category[cat][:10]
        for t in cat_techniques:
            report_md += f"""
#### {t['name']} (第{t['chapter']}章)

> 置信度: {t['confidence']:.2f}

**示例片段**:
```
{t['example'][:150]}...
```

"""
    
    # 保存报告
    reports_dir = NOVELS_DIR / novel_name / "reports"
    md_file = reports_dir / "final_report.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(report_md)
    
    # 保存JSON数据
    json_file = reports_dir / "final_report.json"
    report_data = {
        "novel": novel_name,
        "timestamp": datetime.now().isoformat(),
        "statistics": {
            "total_chapters": len(technique_files),
            "total_techniques": len(all_techniques),
            "avg_per_chapter": len(all_techniques) / len(technique_files),
            "category_count": len(categories)
        },
        "category_distribution": dict(categories),
        "technique_frequency": dict(technique_names),
        "top_techniques": [
            {"name": name, "count": count}
            for name, count in sorted(technique_names.items(), key=lambda x: -x[1])[:30]
        ]
    }
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 报告已生成")
    print(f"   Markdown: {md_file}")
    print(f"   JSON: {json_file}")
    
    return report_data

def generate_comparison_report(novels: list):
    """生成多本小说对比报告"""
    print(f"\n" + "=" * 70)
    print(f"墨芯 v5.0 - 多作品技法对比分析")
    print(f"=" * 70)
    
    all_data = {}
    for novel in novels:
        json_file = NOVELS_DIR / novel / "reports" / "final_report.json"
        if json_file.exists():
            with open(json_file, 'r', encoding='utf-8') as f:
                all_data[novel] = json.load(f)
    
    if len(all_data) < 2:
        print("✗ 需要至少2本小说的数据才能生成对比报告")
        return
    
    # 对比分析
    print(f"\n📚 参与对比的作品:")
    for novel, data in all_data.items():
        print(f"   - 《{novel}》: {data['statistics']['total_chapters']}章, {data['statistics']['total_techniques']}个技法")
    
    # 生成对比报告
    report_md = f"""# 多作品技法对比分析报告

**墨芯 v5.0** | 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## 作品概览

| 作品 | 章节数 | 技法数 | 平均技法/章 |
|------|--------|--------|-------------|
"""
    
    for novel, data in all_data.items():
        s = data['statistics']
        report_md += f"| 《{novel}》 | {s['total_chapters']} | {s['total_techniques']} | {s['avg_per_chapter']:.1f} |\n"
    
    report_md += """

---

## 类别偏好对比

"""
    
    # 找出所有类别
    all_categories = set()
    for data in all_data.values():
        all_categories.update(data['category_distribution'].keys())
    
    report_md += "| 类别 | " + " | ".join([f"《{n}》" for n in all_data.keys()]) + " |\n"
    report_md += "|------|" + "|".join(["------"] * len(all_data)) + "|\n"
    
    for cat in sorted(all_categories):
        cat_name = {
            "plot": "情节",
            "character": "人物",
            "scene": "场景",
            "dialogue": "对话",
            "emotion": "情感",
            "pacing": "节奏",
            "theme": "主题"
        }.get(cat, cat)
        
        row = f"| {cat_name} |"
        for novel, data in all_data.items():
            count = data['category_distribution'].get(cat, 0)
            total = data['statistics']['total_techniques']
            pct = count / total * 100 if total > 0 else 0
            row += f" {count} ({pct:.1f}%) |"
        report_md += row + "\n"
    
    # 保存报告
    report_file = NOVELS_DIR / "comparison_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_md)
    
    print(f"\n✓ 对比报告已生成: {report_file}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        novels = sys.argv[1:]
    else:
        # 默认处理所有小说
        novels = [d.name for d in NOVELS_DIR.iterdir() if d.is_dir()]
    
    print("=" * 70)
    print("墨芯 v5.0 - 技法分析报告生成器")
    print("=" * 70)
    
    for novel in novels:
        try:
            generate_novel_report(novel)
        except Exception as e:
            print(f"✗ 《{novel}》报告生成失败: {e}")
    
    # 如果有多个小说，生成对比报告
    if len(novels) >= 2:
        generate_comparison_report(novels)
    
    print("\n" + "=" * 70)
    print("✓ 所有报告生成完成！")
    print("=" * 70)
