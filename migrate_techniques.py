#!/usr/bin/env python3
"""
墨芯 v5.0 - 技法存储重构与数据迁移脚本
将逐章存储的技法数据迁移到三维聚合存储结构
"""

import os
import json
from pathlib import Path
from collections import defaultdict

NOVEL_NAME = "间客"
BASE_DIR = Path("/root/.openclaw/workspace/inkcore-v5/novels") / NOVEL_NAME
SOURCE_DIR = BASE_DIR / "techniques"  # 源数据目录
TARGET_DIR = BASE_DIR / "techniques"  # 目标目录

def load_chapter_files():
    """加载所有章节技法文件"""
    chapter_files = []
    for f in SOURCE_DIR.glob("ch_*_techniques.json"):
        if f.is_file() and f.parent.name == "techniques":  # 只处理根目录下的文件
            chapter_files.append(f)
    return sorted(chapter_files)

def load_definitions():
    """加载技法定义库"""
    def_file = TARGET_DIR / "library" / "technique_definitions.json"
    with open(def_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def migrate_to_new_structure():
    """执行数据迁移"""
    print("=" * 70)
    print(f"墨芯 v5.0 - 《{NOVEL_NAME}》技法存储重构")
    print("=" * 70)
    
    # 1. 加载所有章节数据
    print("\n📂 加载章节数据...")
    chapter_files = load_chapter_files()
    print(f"   发现 {len(chapter_files)} 个章节文件")
    
    # 2. 聚合数据
    print("\n🔀 聚合数据中...")
    
    # 按类别聚合
    by_category = defaultdict(lambda: defaultdict(list))
    # 按批次聚合
    by_batch = defaultdict(list)
    # 技法-章节映射
    technique_chapter_map = defaultdict(list)
    chapter_technique_map = {}
    # 精选示例库
    examples_bank = defaultdict(lambda: defaultdict(list))
    
    # 统计
    total_techniques = 0
    technique_counts = defaultdict(int)
    
    for cf in chapter_files:
        with open(cf, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        chapter_num = data.get("chapter_number", 0)
        chapter_title = data.get("chapter_title", "")
        
        # 确定批次
        batch_start = ((chapter_num - 1) // 100) * 100 + 1
        batch_end = batch_start + 99
        batch_key = f"batch_{batch_start:04d}_{batch_end:04d}"
        
        # 按批次聚合
        chapter_data = {
            "chapter_number": chapter_num,
            "chapter_title": chapter_title,
            "filename": data.get("filename", ""),
            "char_count": data.get("char_count", 0),
            "techniques_count": data.get("techniques_count", 0),
            "techniques": data.get("techniques", [])
        }
        by_batch[batch_key].append(chapter_data)
        
        # 章节-技法映射
        chapter_technique_map[chapter_num] = [t.get("name") for t in data.get("techniques", [])]
        
        # 处理每个技法
        for t in data.get("techniques", []):
            tech_name = t.get("name", "")
            category = t.get("category", "")
            
            total_techniques += 1
            technique_counts[tech_name] += 1
            
            # 技法-章节映射
            if chapter_num not in technique_chapter_map[tech_name]:
                technique_chapter_map[tech_name].append(chapter_num)
            
            # 按类别聚合
            tech_example = {
                "chapter": chapter_num,
                "chapter_title": chapter_title,
                "context": t.get("example", ""),
                "analysis": t.get("analysis", {}).get("definition", ""),
                "confidence": t.get("confidence", 0)
            }
            by_category[category][tech_name].append(tech_example)
            
            # 精选示例（置信度 >= 0.9）
            if t.get("confidence", 0) >= 0.9:
                examples_bank[category][tech_name].append(tech_example)
    
    # 3. 保存按类别聚合的数据
    print("\n💾 保存类别聚合数据...")
    category_names = {
        "plot": "plot",
        "character": "character", 
        "scene": "scene",
        "emotion": "emotion",
        "pacing": "pacing",
        "dialogue": "dialogue",
        "theme": "theme"
    }
    
    for category, techniques in by_category.items():
        cat_file = TARGET_DIR / "by_category" / f"{category_names.get(category, category)}.json"
        cat_data = {
            "category": category,
            "category_name": {
                "plot": "情节",
                "character": "人物",
                "scene": "场景",
                "emotion": "情感",
                "pacing": "节奏",
                "dialogue": "对话",
                "theme": "主题"
            }.get(category, category),
            "total_occurrences": sum(len(examples) for examples in techniques.values()),
            "unique_techniques": len(techniques),
            "techniques": {
                tech_name: {
                    "name": tech_name,
                    "occurrences": len(examples),
                    "examples": examples
                }
                for tech_name, examples in techniques.items()
            }
        }
        with open(cat_file, 'w', encoding='utf-8') as f:
            json.dump(cat_data, f, ensure_ascii=False, indent=2)
        print(f"   ✓ {cat_file.name}: {len(techniques)} 个技法")
    
    # 4. 保存按批次聚合的数据
    print("\n💾 保存批次聚合数据...")
    for batch_key, chapters in sorted(by_batch.items()):
        batch_file = TARGET_DIR / "by_chapter" / f"{batch_key}.json"
        batch_data = {
            "batch": batch_key,
            "chapter_range": {
                "start": min(c["chapter_number"] for c in chapters),
                "end": max(c["chapter_number"] for c in chapters)
            },
            "total_chapters": len(chapters),
            "chapters": chapters
        }
        with open(batch_file, 'w', encoding='utf-8') as f:
            json.dump(batch_data, f, ensure_ascii=False, indent=2)
        print(f"   ✓ {batch_file.name}: {len(chapters)} 章")
    
    # 5. 保存索引数据
    print("\n💾 保存索引数据...")
    
    # 技法-章节映射
    index_file = TARGET_DIR / "index" / "technique_chapter_map.json"
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump({
            "description": "技法 -> 章节列表映射",
            "techniques": {
                tech: {
                    "name": tech,
                    "chapters": sorted(chapters),
                    "count": len(chapters)
                }
                for tech, chapters in technique_chapter_map.items()
            }
        }, f, ensure_ascii=False, indent=2)
    print(f"   ✓ technique_chapter_map.json: {len(technique_chapter_map)} 个技法")
    
    # 章节-技法映射
    chapter_map_file = TARGET_DIR / "index" / "chapter_technique_map.json"
    with open(chapter_map_file, 'w', encoding='utf-8') as f:
        json.dump({
            "description": "章节 -> 技法列表映射",
            "chapters": {
                str(ch): {
                    "chapter": ch,
                    "techniques": techs
                }
                for ch, techs in chapter_technique_map.items()
            }
        }, f, ensure_ascii=False, indent=2)
    print(f"   ✓ chapter_technique_map.json: {len(chapter_technique_map)} 章")
    
    # 精选示例库
    examples_file = TARGET_DIR / "index" / "examples_bank.json"
    with open(examples_file, 'w', encoding='utf-8') as f:
        json.dump({
            "description": "高质量技法示例库（置信度 >= 0.9）",
            "categories": {
                cat: {
                    "techniques": {
                        tech: examples[:5]  # 每个技法最多5个示例
                        for tech, examples in techs.items()
                    }
                }
                for cat, techs in examples_bank.items()
            }
        }, f, ensure_ascii=False, indent=2)
    
    total_examples = sum(
        sum(len(examples) for examples in techs.values())
        for techs in examples_bank.values()
    )
    print(f"   ✓ examples_bank.json: {total_examples} 个精选示例")
    
    # 6. 更新技法定义库统计
    print("\n💾 更新技法定义库统计...")
    definitions = load_definitions()
    for tech_name, count in technique_counts.items():
        if tech_name in definitions["techniques"]:
            definitions["techniques"][tech_name]["examples_count"] = count
            definitions["techniques"][tech_name]["coverage"] = f"{count/len(chapter_files)*100:.1f}%"
    
    def_file = TARGET_DIR / "library" / "technique_definitions.json"
    with open(def_file, 'w', encoding='utf-8') as f:
        json.dump(definitions, f, ensure_ascii=False, indent=2)
    
    # 7. 生成迁移报告
    print("\n📊 生成迁移报告...")
    report = {
        "migration_report": {
            "novel": NOVEL_NAME,
            "source_files": len(chapter_files),
            "total_techniques": total_techniques,
            "avg_per_chapter": total_techniques / len(chapter_files) if chapter_files else 0,
            "category_distribution": {
                cat: sum(len(techs) for techs in techniques.values())
                for cat, techniques in by_category.items()
            },
            "top_techniques": sorted(
                technique_counts.items(),
                key=lambda x: -x[1]
            )[:10],
            "structure": {
                "library": "技法定义库",
                "by_category": f"{len(by_category)} 个类别文件",
                "by_chapter": f"{len(by_batch)} 个批次文件",
                "index": "3 个索引文件"
            }
        }
    }
    
    report_file = TARGET_DIR / "migration_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # 8. 打印总结
    print("\n" + "=" * 70)
    print("✓ 数据迁移完成")
    print("=" * 70)
    print(f"\n📈 统计摘要:")
    print(f"   处理章节: {len(chapter_files)}")
    print(f"   技法总数: {total_techniques}")
    print(f"   平均每章: {total_techniques/len(chapter_files):.1f} 个技法")
    print(f"\n📁 新存储结构:")
    print(f"   library/technique_definitions.json - 技法定义库")
    for cat in by_category.keys():
        print(f"   by_category/{cat}.json - {cat}类技法")
    for batch in sorted(by_batch.keys()):
        print(f"   by_chapter/{batch}.json - 批次数据")
    print(f"   index/*.json - 索引文件")
    print(f"\n📄 报告: {report_file}")

def create_creators_guide():
    """生成创作者手册"""
    print("\n📖 生成创作者手册...")
    
    definitions = load_definitions()
    
    guide = f"""# 《{NOVEL_NAME}》技法创作者手册

**墨芯 v5.0** | 生成时间: 2026-04-10

---

## 快速导航

### 按创作需求查找

| 你想解决的问题 | 查看文件 |
|---------------|---------|
| 如何写开头吸引人 | `by_category/plot.json` → 危机开场 |
| 如何让读者猜不到结局 | `by_category/plot.json` → 悬念设置 |
| 如何写群像戏 | `by_category/character.json` → 群像描写/群像刻画 |
| 如何渲染氛围 | `by_category/scene.json` → 氛围营造 |
| 如何写情感爆发 | `by_category/emotion.json` → 情绪爆发 |
| 如何控制节奏 | `by_category/pacing.json` → 快节奏/慢节奏 |
| 如何写对话 | `by_category/dialogue.json` → 对话推进/潜台词 |

---

## 技法速查表

"""
    
    # 按类别添加技法
    for cat_id, cat_info in definitions.get("categories", {}).items():
        guide += f"\n### {cat_info['name']}类技法\n\n"
        guide += f"_{cat_info['description']}_\n\n"
        
        for tech_name in cat_info.get("techniques", []):
            tech = definitions["techniques"].get(tech_name, {})
            guide += f"**{tech_name}**\n"
            guide += f"- 定义: {tech.get('definition', '')}\n"
            guide += f"- 适用: {tech.get('usage_scenario', '')}\n"
            guide += f"- 效果: {tech.get('effect', '')}\n"
            guide += f"- 本书出现: {tech.get('examples_count', 0)} 次 ({tech.get('coverage', '0%')})\n\n"
    
    # 添加使用示例
    guide += """
---

## 使用示例

### 示例1: 学习"悬念设置"

```python
# 查看所有悬念设置的示例
import json

with open('by_category/plot.json', 'r') as f:
    data = json.load(f)

suspense = data['techniques']['悬念设置']
print(f"共 {suspense['occurrences']} 个示例")

for ex in suspense['examples'][:3]:
    print(f"第{ex['chapter']}章: {ex['context'][:100]}...")
```

### 示例2: 查看某章节用了什么技法

```python
with open('index/chapter_technique_map.json', 'r') as f:
    data = json.load(f)

ch50 = data['chapters']['50']
print(f"第50章使用了: {', '.join(ch50['techniques'])}")
```

### 示例3: 查找使用"危机开场"的所有章节

```python
with open('index/technique_chapter_map.json', 'r') as f:
    data = json.load(f)

crisis = data['techniques']['危机开场']
print(f"危机开场出现在: 第{crisis['chapters']}章")
```

---

## 进阶技巧

1. **组合使用**: 大多数章节同时使用2-5种技法，观察它们的搭配方式
2. **跨类别融合**: 情节+情感、场景+对话的组合往往效果更好
3. **节奏控制**: 快慢交替，张弛有度

---

*本手册由墨芯 v5.0 自动生成*
"""
    
    guide_file = BASE_DIR / "reports" / "creators_guide.md"
    with open(guide_file, 'w', encoding='utf-8') as f:
        f.write(guide)
    
    print(f"   ✓ {guide_file}")

if __name__ == "__main__":
    migrate_to_new_structure()
    create_creators_guide()
    
    print("\n" + "=" * 70)
    print("🎉 重构完成！")
    print("=" * 70)
    print("\n创作者可以查看:")
    print("  - techniques/library/technique_definitions.json (技法定义)")
    print("  - techniques/by_category/*.json (按类别查看)")
    print("  - techniques/index/examples_bank.json (精选示例)")
    print("  - reports/creators_guide.md (创作者手册)")
