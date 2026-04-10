#!/usr/bin/env python3
"""
墨芯 5.0 - 小说章节批量技法提取工具
用于对《间客》和《将夜》逐章进行技法提取
"""

import asyncio
import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# 添加 inkcore-v5 到路径
sys.path.insert(0, '/root/.openclaw/workspace/inkcore-v5')

from skills.registry import SkillRegistry, SkillContext
from memory.palace_v2 import InkCorePalaceV2


def extract_volume(chapter_title: str) -> str:
    """从章节标题中提取卷号"""
    # 匹配：第一卷、第1卷、卷一等
    volume_patterns = [
        r'(第[一二三四五六七八九十百千零0-9]+卷)',
        r'(卷[一二三四五六七八九十百千零0-9]+)',
        r'(Volume\s*\d+)',
        r'(Vol\.?\s*\d+)',
    ]
    for pattern in volume_patterns:
        match = re.search(pattern, chapter_title)
        if match:
            return match.group(1)
    # 默认使用卷一
    return "第一卷"


class BatchTechniqueExtractor:
    """批量技法提取器"""
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.palace = InkCorePalaceV2(str(self.base_dir / "palace"))
        self.registry = SkillRegistry()
        self.registry.register_builtin_skills(palace=self.palace, orchestrator=None)
        
        # 统计信息
        self.stats = {
            "total_chapters": 0,
            "processed": 0,
            "failed": 0,
            "techniques_found": 0
        }
    
    async def extract_chapter(self, novel_name: str, chapter_file: Path, 
                              output_dir: Path) -> Dict[str, Any]:
        """提取单个章节的技法"""
        
        # 读取章节内容
        with open(chapter_file, 'r', encoding='utf-8') as f:
            chapter_text = f.read()
        
        # 解析章节标题和卷号
        chapter_title = chapter_file.stem
        volume = extract_volume(chapter_title)
        
        # 准备输入
        input_data = {
            "novel_name": novel_name,
            "volume": volume,
            "chapter": chapter_title,
            "chapter_text": chapter_text
        }
        
        try:
            # 执行分析
            execution = await self.registry.execute("analyze_novel", input_data)
            
            result = {
                "chapter": chapter_title,
                "file": str(chapter_file.name),
                "status": "success",
                "techniques_count": 0,
                "techniques": [],
                "timestamp": datetime.now().isoformat()
            }
            
            if execution.context.output_data:
                output = execution.context.output_data
                result["techniques_count"] = output.get("techniques_count", 0)
                result["techniques"] = output.get("techniques", [])
                result["storage"] = output.get("storage", {})
            
            self.stats["processed"] += 1
            self.stats["techniques_found"] += result["techniques_count"]
            
            return result
            
        except Exception as e:
            self.stats["failed"] += 1
            return {
                "chapter": chapter_title,
                "file": str(chapter_file.name),
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def process_novel(self, novel_name: str, start_chapter: int = 1, 
                           end_chapter: int = None, batch_size: int = 10):
        """处理整部小说"""
        
        novel_dir = self.base_dir / "novels" / novel_name
        chapters_dir = novel_dir / "chapters"
        techniques_dir = novel_dir / "techniques"
        reports_dir = novel_dir / "reports"
        
        # 确保输出目录存在
        techniques_dir.mkdir(parents=True, exist_ok=True)
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # 获取章节文件列表
        chapter_files = sorted(chapters_dir.glob("ch_*.txt"))
        
        if end_chapter:
            chapter_files = chapter_files[start_chapter-1:end_chapter]
        else:
            chapter_files = chapter_files[start_chapter-1:]
        
        self.stats["total_chapters"] = len(chapter_files)
        
        print(f"开始处理《{novel_name}》")
        print(f"章节范围: {start_chapter} - {start_chapter + len(chapter_files) - 1}")
        print(f"总计章节: {len(chapter_files)}")
        print("-" * 60)
        
        # 批量处理
        results = []
        for i, chapter_file in enumerate(chapter_files, 1):
            print(f"[{i}/{len(chapter_files)}] 处理: {chapter_file.name}", end=" ")
            
            result = await self.extract_chapter(novel_name, chapter_file, techniques_dir)
            results.append(result)
            
            # 保存单个章节的技法结果
            output_file = techniques_dir / f"{chapter_file.stem}_techniques.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            status_icon = "✓" if result["status"] == "success" else "✗"
            tech_count = result.get("techniques_count", 0)
            print(f"{status_icon} 技法: {tech_count}")
            
            # 每 batch_size 章保存一次汇总
            if i % batch_size == 0:
                self._save_progress_report(novel_name, results, reports_dir)
        
        # 最终汇总报告
        self._save_final_report(novel_name, results, reports_dir)
        
        return results
    
    def _save_progress_report(self, novel_name: str, results: List[Dict], 
                              reports_dir: Path):
        """保存进度报告"""
        report = {
            "novel": novel_name,
            "timestamp": datetime.now().isoformat(),
            "progress": {
                "total": self.stats["total_chapters"],
                "processed": self.stats["processed"],
                "failed": self.stats["failed"]
            },
            "recent_results": results[-10:]  # 最近10章
        }
        
        report_file = reports_dir / "progress_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    
    def _save_final_report(self, novel_name: str, results: List[Dict], 
                           reports_dir: Path):
        """保存最终报告"""
        
        # 统计技法类型
        category_stats = {}
        all_techniques = []
        
        for result in results:
            if result["status"] == "success":
                for tech in result.get("techniques", []):
                    category = tech.get("category", "unknown")
                    category_stats[category] = category_stats.get(category, 0) + 1
                    all_techniques.append({
                        "chapter": result["chapter"],
                        "technique": tech
                    })
        
        # 按技法名称统计
        technique_stats = {}
        for item in all_techniques:
            name = item["technique"].get("name", "unknown")
            technique_stats[name] = technique_stats.get(name, 0) + 1
        
        final_report = {
            "novel": novel_name,
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_chapters": self.stats["total_chapters"],
                "processed": self.stats["processed"],
                "failed": self.stats["failed"],
                "total_techniques": self.stats["techniques_found"]
            },
            "category_distribution": category_stats,
            "technique_frequency": dict(sorted(
                technique_stats.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:20]),  # Top 20
            "chapter_results": results
        }
        
        report_file = reports_dir / "final_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, ensure_ascii=False, indent=2)
        
        # 同时生成 Markdown 报告
        md_report = self._generate_markdown_report(final_report)
        md_file = reports_dir / "final_report.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_report)
        
        print("\n" + "=" * 60)
        print("提取完成!")
        print(f"处理章节: {self.stats['processed']}/{self.stats['total_chapters']}")
        print(f"失败: {self.stats['failed']}")
        print(f"发现技法: {self.stats['techniques_found']}")
        print(f"\n报告保存至:")
        print(f"  - JSON: {report_file}")
        print(f"  - Markdown: {md_file}")
        print("=" * 60)
    
    def _generate_markdown_report(self, report: Dict) -> str:
        """生成 Markdown 格式报告"""
        lines = [
            f"# 《{report['novel']}》技法提取报告",
            "",
            f"生成时间: {report['generated_at']}",
            "",
            "## 统计概览",
            "",
            f"- 总章节数: {report['summary']['total_chapters']}",
            f"- 成功处理: {report['summary']['processed']}",
            f"- 失败: {report['summary']['failed']}",
            f"- 发现技法: {report['summary']['total_techniques']}",
            "",
            "## 技法类别分布",
            ""
        ]
        
        for category, count in report['category_distribution'].items():
            lines.append(f"- {category}: {count}")
        
        lines.extend([
            "",
            "## 技法频率 (Top 20)",
            ""
        ])
        
        for name, count in report['technique_frequency'].items():
            lines.append(f"- {name}: {count}")
        
        lines.extend([
            "",
            "## 详细章节结果",
            ""
        ])
        
        for result in report['chapter_results']:
            status = "✓" if result['status'] == 'success' else "✗"
            lines.append(f"### {status} {result['chapter']}")
            lines.append(f"- 状态: {result['status']}")
            lines.append(f"- 技法数: {result.get('techniques_count', 0)}")
            if 'error' in result:
                lines.append(f"- 错误: {result['error']}")
            lines.append("")
        
        return '\n'.join(lines)


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='墨芯5.0 - 批量技法提取')
    parser.add_argument('novel', help='小说名称 (如: 间客, 将夜)')
    parser.add_argument('--start', type=int, default=1, help='起始章节 (默认: 1)')
    parser.add_argument('--end', type=int, help='结束章节 (默认: 全部)')
    parser.add_argument('--batch', type=int, default=10, help='批次大小 (默认: 10)')
    parser.add_argument('--base-dir', default='/root/.openclaw/workspace/inkcore-v5',
                       help='基础目录')
    
    args = parser.parse_args()
    
    extractor = BatchTechniqueExtractor(args.base_dir)
    await extractor.process_novel(
        novel_name=args.novel,
        start_chapter=args.start,
        end_chapter=args.end,
        batch_size=args.batch
    )


if __name__ == '__main__':
    asyncio.run(main())
