#!/usr/bin/env python3
"""
小说章节分割工具
将TXT小说按章分割成独立文件
"""

import re
import os
from pathlib import Path

def split_novel_by_chapters(input_file: str, output_dir: str):
    """
    按章节分割小说
    
    支持的章节格式：
    - 第X章 标题
    - 第X章标题
    - 第X章　标题（全角空格）
    """
    print(f"正在读取: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 章节标题匹配模式
    # 匹配：第一章、第1章、第001章等，后面可跟标题
    chapter_pattern = r'第[一二三四五六七八九十百千零0-9]+章[\s　]*[^\n]*'
    
    # 找到所有章节标题
    chapters = []
    matches = list(re.finditer(chapter_pattern, content))
    
    print(f"找到 {len(matches)} 个章节")
    
    if len(matches) == 0:
        print("未找到章节，尝试其他模式...")
        return []
    
    # 提取每一章的内容
    for i, match in enumerate(matches):
        chapter_title = match.group().strip()
        start_pos = match.start()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        chapter_content = content[start_pos:end_pos].strip()
        
        chapters.append({
            'index': i + 1,
            'title': chapter_title,
            'content': chapter_content
        })
    
    # 保存章节文件
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    saved_files = []
    for chapter in chapters:
        # 清理文件名并限制长度
        safe_title = re.sub(r'[\\/*?:"<>|]', '_', chapter['title'])
        # 限制文件名长度，避免超出系统限制
        max_title_len = 80
        if len(safe_title) > max_title_len:
            safe_title = safe_title[:max_title_len] + "..."
        filename = f"ch_{chapter['index']:04d}_{safe_title}.txt"
        filepath = output_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(chapter['content'])
        
        saved_files.append(str(filepath))
        print(f"  ✓ 保存: {filename}")
    
    # 生成索引文件
    index_data = {
        'novel_name': Path(input_file).stem,
        'total_chapters': len(chapters),
        'chapters': [
            {'index': c['index'], 'title': c['title'], 'file': f"ch_{c['index']:04d}_{re.sub(r'[\\\\/*?:\"<>|]', '_', c['title'])}.txt"}
            for c in chapters
        ]
    }
    
    import json
    with open(output_path / 'index.json', 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 共分割 {len(chapters)} 章，保存到: {output_dir}")
    print(f"✓ 索引文件: {output_dir}/index.json")
    
    return saved_files


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("用法: python split_chapters.py <输入文件> <输出目录>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_dir = sys.argv[2]
    
    split_novel_by_chapters(input_file, output_dir)
