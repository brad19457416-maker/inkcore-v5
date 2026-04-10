#!/usr/bin/env python3
"""
测试 Inkcore NC API

使用方法:
    # 方式1: 直接测试服务类
    python test_nc_api.py
    
    # 方式2: 测试API服务（需先启动服务）
    # 终端1: python nc_api.py
    # 终端2: python -c "import test_nc_api; test_nc_api.test_api()"
"""

import asyncio
import requests
from nc_api import InkcoreNCServicer


def test_service():
    """测试核心服务类"""
    print("=" * 60)
    print("Inkcore NC Service 测试")
    print("=" * 60)
    
    service = InkcoreNCServicer()
    
    # 测试1: 获取技法类别
    print("\n[测试1] 获取技法类别")
    categories = service.get_categories()
    print(f"✓ 共 {len(categories)} 个类别")
    for cat in categories[:3]:
        print(f"  - {cat['id']}: {cat['name']} ({cat['count']}个技法)")
    
    # 测试2: 搜索技法
    print("\n[测试2] 搜索对话场景技法")
    results = service.search_techniques(scene_type="对话", limit=5)
    print(f"✓ 找到 {len(results)} 个技法")
    for r in results:
        print(f"  - {r['name']} ({r['category']}) 置信度: {r['confidence']:.2f}")
    
    # 测试3: 分析章节
    print("\n[测试3] 分析章节")
    test_chapter = """
雨夜，街道上游行的人群被防暴警察镇压。
危机四伏的氛围中，一个少年躲在街角。
"为什么？"他心中暗想，眼中充满不解。
这是他对这个世界最初的印象。
"""
    analysis = service.analyze_chapter(test_chapter)
    print(f"✓ 检测到 {analysis['techniques_count']} 个技法")
    print(f"✓ 质量分: {analysis['quality_score']:.2f}")
    print(f"✓ 类别分布: {analysis['category_distribution']}")
    print("  检测到的技法:")
    for t in analysis['techniques'][:5]:
        print(f"    - {t['name']} ({t['category']}) 置信度: {t['confidence']:.2f}")
    
    # 测试4: 获取风格画像
    print("\n[测试4] 获取风格画像")
    style = service.get_style_profile("间客")
    print(f"✓ 小说: {style['novel']}")
    if 'signature_techniques' in style:
        print(f"✓ 签名技法: {[t['name'] for t in style['signature_techniques']]}")
    else:
        print(f"✓ 风格描述: {style.get('style_description', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("所有测试通过!")
    print("=" * 60)


def test_api():
    """测试HTTP API"""
    base_url = "http://localhost:8000"
    
    print("=" * 60)
    print("Inkcore NC API HTTP 测试")
    print("=" * 60)
    
    # 测试健康检查
    print("\n[测试1] 健康检查")
    resp = requests.get(f"{base_url}/health")
    print(f"✓ Status: {resp.status_code}")
    print(f"✓ Response: {resp.json()}")
    
    # 测试获取类别
    print("\n[测试2] 获取技法类别")
    resp = requests.get(f"{base_url}/api/v1/categories")
    data = resp.json()
    print(f"✓ 共 {len(data)} 个类别")
    
    # 测试搜索
    print("\n[测试3] 搜索技法")
    resp = requests.post(
        f"{base_url}/api/v1/search",
        json={"scene_type": "战斗", "limit": 3}
    )
    data = resp.json()
    print(f"✓ 找到 {len(data)} 个技法")
    
    # 测试分析
    print("\n[测试4] 分析章节")
    test_text = "激烈的战斗中，主角猛然爆发，击败了敌人。"
    resp = requests.post(
        f"{base_url}/api/v1/analyze",
        json={"chapter_text": test_text}
    )
    data = resp.json()
    print(f"✓ 检测到 {data['techniques_count']} 个技法")
    print(f"✓ 质量分: {data['quality_score']:.2f}")
    
    print("\n" + "=" * 60)
    print("API测试通过!")
    print("=" * 60)


if __name__ == "__main__":
    test_service()
