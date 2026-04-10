#!/usr/bin/env python3
"""
墨芯 v5.0 - 小说技法提取脚本
逐章分析并提取写作技法
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime

# 配置
NOVELS_DIR = Path("/root/.openclaw/workspace/inkcore-v5/novels")

def ensure_directories(novel_name: str):
    """确保目录结构存在"""
    (NOVELS_DIR / novel_name / "chapters").mkdir(parents=True, exist_ok=True)
    (NOVELS_DIR / novel_name / "techniques").mkdir(parents=True, exist_ok=True)
    (NOVELS_DIR / novel_name / "reports").mkdir(parents=True, exist_ok=True)

def get_chapter_files(novel_name: str) -> list:
    """获取所有章节文件，按序号排序"""
    chapters_dir = NOVELS_DIR / novel_name / "chapters"
    files = [f for f in chapters_dir.glob("ch_*.txt") if f.is_file()]
    # 按序号排序
    def get_chapter_number(f):
        match = re.match(r'ch_(\d+)_', f.name)
        return int(match.group(1)) if match else 0
    return sorted(files, key=get_chapter_number)

def get_processed_chapters(novel_name: str) -> set:
    """获取已处理的章节号"""
    techniques_dir = NOVELS_DIR / novel_name / "techniques"
    processed = set()
    for f in techniques_dir.glob("ch_*_techniques.json"):
        match = re.match(r'ch_(\d+)_', f.name)
        if match:
            processed.add(int(match.group(1)))
    return processed

def extract_chapter_info(chapter_file: Path) -> dict:
    """提取章节信息"""
    # 从文件名提取章节号
    match = re.match(r'ch_(\d+)_(.+?)\.txt$', chapter_file.name)
    if match:
        chapter_num = int(match.group(1))
        chapter_title = match.group(2)
    else:
        chapter_num = 0
        chapter_title = chapter_file.stem
    
    # 读取内容
    with open(chapter_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return {
        "number": chapter_num,
        "title": chapter_title,
        "filename": chapter_file.name,
        "content": content,
        "char_count": len(content)
    }

def analyze_chapter_techniques(chapter_info: dict) -> list:
    """
    分析章节技法
    基于内容特征进行规则匹配，返回技法列表
    """
    techniques = []
    content = chapter_info["content"]
    title = chapter_info["title"]
    
    # 技法规则库
    rules = [
        # 情节类技法
        {
            "name": "危机开场",
            "category": "plot",
            "keywords": ["危机", "冲突", "危险", "紧急", "逃亡", "追杀", "对峙", "战斗", "暴起"],
            "confidence": 0.85
        },
        {
            "name": "悬念设置",
            "category": "plot",
            "keywords": ["秘密", "真相", "谜团", "疑问", "为什么", "究竟", "难道", "果然"],
            "confidence": 0.80
        },
        {
            "name": "伏笔埋设",
            "category": "plot",
            "keywords": ["日后", "将来", "以后", "某年", "将来", "伏笔", "暗示"],
            "confidence": 0.75
        },
        {
            "name": "高潮爆发",
            "category": "plot",
            "keywords": ["爆发", "决战", "最终", "巅峰", "最强", "全力", "拼命"],
            "confidence": 0.85
        },
        # 人物类技法
        {
            "name": "人物出场",
            "category": "character",
            "keywords": ["初见", "初遇", "第一次", "陌生", "新来", "登场", "出现"],
            "confidence": 0.80
        },
        {
            "name": "内心独白",
            "category": "character",
            "keywords": ["心想", "心想", "暗想", "思忖", "念头", "思绪", "感慨", "自嘲"],
            "confidence": 0.80
        },
        {
            "name": "性格刻画",
            "category": "character",
            "keywords": ["性格", "脾气", "性子", "为人", "素来", "一向", "从来"],
            "confidence": 0.75
        },
        {
            "name": "群像描写",
            "category": "character",
            "keywords": ["众人", "人群", "人们", "大家", "无数", "纷纷", "一片"],
            "confidence": 0.75
        },
        # 场景类技法
        {
            "name": "环境描写",
            "category": "scene",
            "keywords": ["天空", "大地", "风", "雨", "雪", "山", "水", "街道", "房间"],
            "confidence": 0.75
        },
        {
            "name": "空间转换",
            "category": "scene",
            "keywords": ["来到", "离去", "进入", "走出", "离开", "前往", "抵达"],
            "confidence": 0.75
        },
        {
            "name": "氛围营造",
            "category": "scene",
            "keywords": ["寂静", "喧嚣", "压抑", "紧张", "轻松", "愉快", "沉重", "凝重"],
            "confidence": 0.80
        },
        # 节奏类技法
        {
            "name": "快节奏",
            "category": "pacing",
            "keywords": ["瞬间", "刹那", "转眼", "猛然", "骤然", "突然", "立刻", "马上"],
            "confidence": 0.80
        },
        {
            "name": "慢节奏",
            "category": "pacing",
            "keywords": ["缓缓", "慢慢", "徐徐", "悠然", "闲适", "安静", "宁静"],
            "confidence": 0.75
        },
        {
            "name": "场景切换",
            "category": "pacing",
            "keywords": [" meanwhile", "同时", "另一边", "与此同时", "那一边"],
            "confidence": 0.80
        },
        # 情感类技法
        {
            "name": "情感铺垫",
            "category": "emotion",
            "keywords": ["思念", "牵挂", "担心", "忧虑", "期待", "盼望", "渴望"],
            "confidence": 0.80
        },
        {
            "name": "情绪爆发",
            "category": "emotion",
            "keywords": ["愤怒", "狂怒", "悲痛", "狂喜", "激动", "颤抖", "落泪"],
            "confidence": 0.85
        },
        {
            "name": "温情描写",
            "category": "emotion",
            "keywords": ["温暖", "温柔", "柔和", "温馨", "幸福", "甜蜜", "满足"],
            "confidence": 0.75
        },
        # 对话类技法
        {
            "name": "对话推进",
            "category": "dialogue",
            "keywords": ["说道", "问道", "回答", "笑道", "冷道", "轻声", "大声"],
            "confidence": 0.75
        },
        {
            "name": "潜台词",
            "category": "dialogue",
            "keywords": ["意味深长", "话中有话", "言外之意", "暗示", "弦外之音"],
            "confidence": 0.80
        },
        # 主题类技法
        {
            "name": "哲学思辨",
            "category": "theme",
            "keywords": ["意义", "价值", "存在", "本质", "真理", "道理", "人生"],
            "confidence": 0.85
        },
        {
            "name": "社会隐喻",
            "category": "theme",
            "keywords": ["社会", "时代", "命运", "阶级", "制度", "权力", "压迫"],
            "confidence": 0.80
        },
    ]
    
    # 应用规则
    for rule in rules:
        matches = []
        for keyword in rule["keywords"]:
            if keyword in content:
                # 找到关键词周围的上下文
                idx = content.find(keyword)
                if idx >= 0:
                    start = max(0, idx - 50)
                    end = min(len(content), idx + 100)
                    context = content[start:end].strip()
                    matches.append(context)
        
        if matches:
            # 计算置信度（根据匹配次数调整）
            match_count = len(matches)
            adjusted_confidence = min(0.95, rule["confidence"] + (match_count - 1) * 0.05)
            
            techniques.append({
                "name": rule["name"],
                "category": rule["category"],
                "example": matches[0][:150] if matches else "",
                "analysis": {
                    "definition": f"在文本中使用{rule['name']}技法",
                    "scenario": f"适用于{rule['category']}类场景",
                    "effect": f"增强{rule['category']}表现",
                    "applicability": "网络小说"
                },
                "confidence": adjusted_confidence,
                "match_count": match_count
            })
    
    # 根据置信度排序，返回所有匹配的技法（不设上限）
    techniques.sort(key=lambda x: x["confidence"], reverse=True)
    return techniques

def save_technique_result(novel_name: str, chapter_info: dict, techniques: list):
    """保存技法提取结果"""
    techniques_dir = NOVELS_DIR / novel_name / "techniques"
    
    # 构建文件名
    chapter_num = chapter_info["number"]
    safe_title = re.sub(r'[\\/*?:"<>|]', '_', chapter_info["title"])[:50]
    filename = f"ch_{chapter_num:04d}_{safe_title}_techniques.json"
    
    result = {
        "novel": novel_name,
        "chapter_number": chapter_num,
        "chapter_title": chapter_info["title"],
        "filename": chapter_info["filename"],
        "char_count": chapter_info["char_count"],
        "timestamp": datetime.now().isoformat(),
        "techniques_count": len(techniques),
        "techniques": techniques
    }
    
    with open(techniques_dir / filename, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    return filename

def update_progress_report(novel_name: str, results: list):
    """更新进度报告"""
    reports_dir = NOVELS_DIR / novel_name / "reports"
    report_file = reports_dir / "progress_report.json"
    
    # 统计
    total = len(results)
    success = sum(1 for r in results if r.get("status") == "success")
    failed = sum(1 for r in results if r.get("status") == "failed")
    
    # 计算技法统计
    all_categories = {}
    all_techniques = {}
    for r in results:
        if "techniques" in r:
            for t in r["techniques"]:
                cat = t.get("category", "unknown")
                all_categories[cat] = all_categories.get(cat, 0) + 1
                name = t.get("name", "unknown")
                all_techniques[name] = all_techniques.get(name, 0) + 1
    
    report = {
        "novel": novel_name,
        "timestamp": datetime.now().isoformat(),
        "progress": {
            "total": total,
            "processed": success,
            "failed": failed
        },
        "statistics": {
            "categories": all_categories,
            "top_techniques": sorted(all_techniques.items(), key=lambda x: -x[1])[:20]
        },
        "recent_results": results[-10:]  # 最近10条
    }
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

def process_novel(novel_name: str, start_from: int = None, limit: int = None):
    """
    处理小说技法提取
    
    Args:
        novel_name: 小说名称（如"间客"）
        start_from: 从第几章开始（None则从上次中断处继续）
        limit: 最多处理多少章（None则全部处理）
    """
    print(f"=" * 60)
    print(f"墨芯 v5.0 - 《{novel_name}》技法提取")
    print(f"=" * 60)
    
    # 确保目录存在
    ensure_directories(novel_name)
    
    # 获取章节列表
    chapter_files = get_chapter_files(novel_name)
    print(f"\n总章节数: {len(chapter_files)}")
    
    # 获取已处理章节
    processed = get_processed_chapters(novel_name)
    print(f"已处理: {len(processed)} 章")
    
    # 确定起始点
    if start_from is None:
        # 从上次中断处继续
        if processed:
            start_from = max(processed) + 1
        else:
            start_from = 1
    
    print(f"从第 {start_from} 章开始处理")
    
    # 筛选待处理章节
    to_process = []
    for f in chapter_files:
        match = re.match(r'ch_(\d+)_', f.name)
        if match:
            ch_num = int(match.group(1))
            if ch_num >= start_from and ch_num not in processed:
                to_process.append(f)
    
    if limit:
        to_process = to_process[:limit]
    
    print(f"待处理: {len(to_process)} 章")
    print("-" * 60)
    
    # 处理章节
    results = []
    for i, chapter_file in enumerate(to_process, 1):
        chapter_info = extract_chapter_info(chapter_file)
        print(f"[{i:4d}/{len(to_process):4d}] 第{chapter_info['number']:04d}章: {chapter_info['title'][:30]}...", end=" ")
        
        try:
            # 分析技法
            techniques = analyze_chapter_techniques(chapter_info)
            
            # 保存结果
            saved_file = save_technique_result(novel_name, chapter_info, techniques)
            
            results.append({
                "chapter": f"第{chapter_info['number']}章 {chapter_info['title']}",
                "file": chapter_file.name,
                "status": "success",
                "techniques_count": len(techniques),
                "techniques": techniques[:2],  # 只保存前2个在报告中
                "timestamp": datetime.now().isoformat()
            })
            
            print(f"✓ {len(techniques)} 个技法")
            
        except Exception as e:
            results.append({
                "chapter": f"第{chapter_info['number']}章 {chapter_info['title']}",
                "file": chapter_file.name,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            print(f"✗ 失败: {e}")
        
        # 每10章更新一次进度报告
        if i % 10 == 0:
            update_progress_report(novel_name, results)
    
    # 最终更新报告
    update_progress_report(novel_name, results)
    
    print("\n" + "=" * 60)
    print("处理完成")
    print("=" * 60)
    print(f"\n成功: {sum(1 for r in results if r['status'] == 'success')}")
    print(f"失败: {sum(1 for r in results if r['status'] == 'failed')}")
    print(f"\n报告位置: {NOVELS_DIR / novel_name / 'reports' / 'progress_report.json'}")

if __name__ == "__main__":
    import sys
    
    # 解析命令行参数
    novel = "间客"  # 默认处理间客
    start = None
    limit = 100  # 默认每次处理100章
    
    if len(sys.argv) > 1:
        novel = sys.argv[1]
    if len(sys.argv) > 2:
        start = int(sys.argv[2])
    if len(sys.argv) > 3:
        limit = int(sys.argv[3])
    
    process_novel(novel, start, limit)
