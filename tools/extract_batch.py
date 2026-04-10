#!/usr/bin/env python3
"""
墨芯5.0 技法提取脚本 - 批次处理
每批50章，全量提取
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

# 配置
NOVEL_NAME = "间客"
CHAPTERS_DIR = "/root/.openclaw/workspace/inkcore-v5/novels/间客/chapters"
TECHNIQUES_DIR = "/root/.openclaw/workspace/inkcore-v5/novels/间客/techniques"
BATCH_SIZE = 50

# 技法分类定义
CATEGORIES = {
    "plot": "情节",
    "character": "人物", 
    "scene": "场景",
    "dialogue": "对话",
    "emotion": "情感",
    "pacing": "节奏",
    "theme": "主题"
}

def get_chapter_files():
    """获取所有章节文件，按序号排序"""
    chapters = []
    for f in os.listdir(CHAPTERS_DIR):
        if f.startswith("ch_") and f.endswith(".txt"):
            # 解析序号
            try:
                seq = int(f.split("_")[1])
                chapters.append((seq, f))
            except:
                continue
    chapters.sort(key=lambda x: x[0])
    return chapters

def read_chapter(filepath):
    """读取章节内容"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"  读取失败: {e}")
        return None

def extract_techniques_mock(chapter_content, chapter_title):
    """
    模拟技法提取 - 实际应调用墨芯5.0 Agent
    这里先创建一个空的提取框架
    """
    # 这里只是一个框架，实际提取需要调用墨芯5.0
    # 返回空列表表示待提取
    return []

def process_batch(batch_num, chapter_files):
    """处理一批章节"""
    print(f"\n{'='*60}")
    print(f"处理批次 {batch_num}: 第{chapter_files[0][0]}章 ~ 第{chapter_files[-1][0]}章")
    print(f"{'='*60}")
    
    batch_results = []
    
    for seq, filename in chapter_files:
        filepath = os.path.join(CHAPTERS_DIR, filename)
        
        # 解析章节标题
        title = filename.replace("ch_", "").replace(".txt", "")
        
        print(f"  [{seq}] {title[:40]}...", end=" ")
        
        # 读取内容
        content = read_chapter(filepath)
        if not content:
            print("✗ 读取失败")
            continue
        
        # 提取技法（实际应调用墨芯5.0）
        techniques = extract_techniques_mock(content, title)
        
        result = {
            "chapter": title,
            "file": filename,
            "seq": seq,
            "status": "pending",  # 待实际提取
            "techniques_count": len(techniques),
            "techniques": techniques,
            "timestamp": datetime.now().isoformat()
        }
        
        batch_results.append(result)
        print(f"✓ 已加载 ({len(content)} 字符)")
    
    # 保存批次结果
    batch_file = os.path.join(
        TECHNIQUES_DIR, 
        "by_chapter", 
        f"batch_{batch_num:04d}_{batch_num+BATCH_SIZE-1:04d}.json"
    )
    
    os.makedirs(os.path.dirname(batch_file), exist_ok=True)
    
    with open(batch_file, 'w', encoding='utf-8') as f:
        json.dump(batch_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n  批次结果已保存: {batch_file}")
    return len(batch_results)

def main():
    """主函数"""
    print("墨芯5.0 技法提取 - 批次处理")
    print(f"小说: {NOVEL_NAME}")
    print(f"批次大小: {BATCH_SIZE}章")
    print("="*60)
    
    # 获取所有章节
    chapters = get_chapter_files()
    total = len(chapters)
    
    print(f"发现章节: {total}章")
    
    # 分批处理
    batch_count = (total + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"预计批次: {batch_count}批")
    
    # 处理第一批（第1-50章）
    first_batch = chapters[:BATCH_SIZE]
    if first_batch:
        processed = process_batch(1, first_batch)
        print(f"\n✓ 第一批处理完成: {processed}章")
    
    print("\n" + "="*60)
    print("说明: 这是提取框架，实际技法提取需要调用墨芯5.0 Agent")
    print("="*60)

if __name__ == "__main__":
    main()
