#!/usr/bin/env python3
"""
墨芯 v5.0 真实模型验证 - 方案A
样本：30章（前10 + 中10 + 后10）
"""

import re
import json
from pathlib import Path

# 文件路径
NOVEL_PATH = "/root/.openclaw/workspace/.kimi/downloads/19d4c1b0-afb2-8db6-8000-0000134019ce_间客_猫腻_TXT小说天堂.txt"
OUTPUT_DIR = Path("/root/.openclaw/workspace/inkcore-v5/validation_sample")

def extract_chapters():
    """提取30个样本章节"""
    print("=" * 60)
    print("《间客》样本章节提取")
    print("=" * 60)
    
    # 读取全文
    with open(NOVEL_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"\n文本总长度: {len(content):,} 字符")
    
    # 匹配章节
    # 模式：第X章 标题
    chapter_pattern = r'(第[一二三四五六七八九十百千零\d]+章\s+[^\n]+)'
    chapters = list(re.finditer(chapter_pattern, content))
    
    print(f"识别章节数: {len(chapters)}")
    
    # 选取样本
    indices = list(range(10)) + list(range(len(chapters)//2 - 5, len(chapters)//2 + 5)) + list(range(len(chapters) - 10, len(chapters)))
    
    sample_chapters = []
    for idx in indices[:30]:  # 取30个
        if idx < len(chapters):
            match = chapters[idx]
            title = match.group(1).strip()
            start_pos = match.start()
            
            # 找到下一章开始位置
            end_pos = len(content)
            if idx + 1 < len(chapters):
                end_pos = chapters[idx + 1].start()
            
            chapter_text = content[start_pos:end_pos].strip()
            
            sample_chapters.append({
                "index": idx + 1,
                "title": title,
                "text": chapter_text,
                "char_count": len(chapter_text)
            })
    
    print(f"\n选取样本: {len(sample_chapters)} 章")
    print("\n样本列表:")
    for ch in sample_chapters[:5]:
        print(f"  第{ch['index']:3d}章: {ch['title'][:30]}... ({ch['char_count']:,}字)")
    print("  ...")
    
    # 保存样本
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    for ch in sample_chapters:
        safe_title = re.sub(r'[\\/:*?"<>|]', '_', ch['title'])[:30]
        filename = f"ch_{ch['index']:03d}_{safe_title}.txt"
        filepath = OUTPUT_DIR / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(ch['text'])
    
    # 保存索引
    index_data = [{
        "index": ch["index"],
        "title": ch["title"],
        "char_count": ch["char_count"],
        "file": f"ch_{ch['index']:03d}_{re.sub(r'[\\\\/:*?\"<>|]', '_', ch['title'])[:30]}.txt"
    } for ch in sample_chapters]
    
    with open(OUTPUT_DIR / "index.json", 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 样本已保存到: {OUTPUT_DIR}")
    print(f"   共 {len(sample_chapters)} 个文件")
    
    return sample_chapters

if __name__ == "__main__":
    extract_chapters()
