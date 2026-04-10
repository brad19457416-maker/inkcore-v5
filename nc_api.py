#!/usr/bin/env python3
"""
Inkcore NC 集成 API 服务

为 Nova Agent (NC) 提供技法查询和章节分析服务

使用方法:
    python nc_api.py
    # 默认端口 8000

API端点:
    GET  /health              - 健康检查
    GET  /api/v1/techniques  - 列出可用技法类别
    POST /api/v1/search      - 搜索技法
    POST /api/v1/analyze     - 分析章节
    GET  /api/v1/style/{novel} - 获取风格画像
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 小说数据目录
NOVELS_DIR = Path(os.environ.get('INKCORE_NOVELS_DIR', '/root/.openclaw/workspace/inkcore-v5/novels'))

# 技法类别
TECHNIQUE_CATEGORIES = {
    'plot': '情节类（悬念设置、危机开场、高潮爆发等）',
    'character': '人物类（人物出场、内心独白、群像描写等）',
    'scene': '场景类（环境描写、空间转换、氛围营造等）',
    'dialogue': '对话类（对话推进、潜台词等）',
    'emotion': '情感类（情感铺垫、情绪爆发、温情描写等）',
    'pacing': '节奏类（快节奏、慢节奏、场景切换等）',
    'theme': '主题类（哲学思辨、社会隐喻等）'
}


class InkcoreNCServicer:
    """Inkcore NC 集成服务"""
    
    def __init__(self, novels_dir: Path = None):
        self.novels_dir = novels_dir or NOVELS_DIR
        self._load_technique_rules()
    
    def _load_technique_rules(self):
        """加载技法规则"""
        # 简化的技法规则（完整版见 extract_techniques.py）
        self.rules = [
            # 情节类
            {"name": "危机开场", "category": "plot", 
             "keywords": ["危机", "冲突", "危险", "紧急", "逃亡", "追杀", "对峙", "战斗"], 
             "confidence": 0.85},
            {"name": "悬念设置", "category": "plot", 
             "keywords": ["秘密", "真相", "谜团", "疑问", "为什么", "究竟", "难道"], 
             "confidence": 0.80},
            {"name": "伏笔埋设", "category": "plot", 
             "keywords": ["日后", "将来", "以后", "某年", "伏笔", "暗示"], 
             "confidence": 0.75},
            {"name": "高潮爆发", "category": "plot", 
             "keywords": ["爆发", "决战", "最终", "巅峰", "最强", "全力", "拼命"], 
             "confidence": 0.85},
            
            # 人物类
            {"name": "人物出场", "category": "character", 
             "keywords": ["初见", "初遇", "第一次", "陌生", "新来", "登场", "出现"], 
             "confidence": 0.80},
            {"name": "内心独白", "category": "character", 
             "keywords": ["心想", "暗想", "思酌", "念头", "思绪", "感慨", "自嘲"], 
             "confidence": 0.80},
            {"name": "性格刻画", "category": "character", 
             "keywords": ["性格", "脾气", "性子", "为人", "素来", "一向", "从来"], 
             "confidence": 0.75},
            {"name": "群像描写", "category": "character", 
             "keywords": ["众人", "人群", "人们", "大家", "无数", "纷纷", "一片"], 
             "confidence": 0.75},
            
            # 场景类
            {"name": "环境描写", "category": "scene", 
             "keywords": ["天空", "大地", "风", "雨", "雪", "山", "水", "街道", "房间"], 
             "confidence": 0.75},
            {"name": "空间转换", "category": "scene", 
             "keywords": ["来到", "离去", "进入", "走出", "离开", "前往", "抵达"], 
             "confidence": 0.75},
            {"name": "氛围营造", "category": "scene", 
             "keywords": ["寂静", "喧嚣", "压抑", "紧张", "轻松", "愉快", "沉重", "凝重"], 
             "confidence": 0.80},
            
            # 对话类
            {"name": "对话推进", "category": "dialogue", 
             "keywords": ["说道", "问道", "回答", "笑道", "冷道", "轻声", "大声"], 
             "confidence": 0.75},
            {"name": "潜台词", "category": "dialogue", 
             "keywords": ["意味深长", "话中有话", "言外之意", "暗示", "弦外之音"], 
             "confidence": 0.80},
            
            # 情感类
            {"name": "情感铺垫", "category": "emotion", 
             "keywords": ["思念", "牵挂", "担心", "忧虑", "期待", "盼望", "渴望"], 
             "confidence": 0.80},
            {"name": "情绪爆发", "category": "emotion", 
             "keywords": ["愤怒", "狂怒", "悲痛", "狂喜", "激动", "颤抖", "落泪"], 
             "confidence": 0.85},
            {"name": "温情描写", "category": "emotion", 
             "keywords": ["温暖", "温柔", "柔和", "温馨", "幸福", "甜蜜", "满足"], 
             "confidence": 0.75},
            
            # 节奏类
            {"name": "快节奏", "category": "pacing", 
             "keywords": ["瞬间", "刹那", "转眼", "猛然", "骤然", "突然", "立刻", "马上"], 
             "confidence": 0.80},
            {"name": "慢节奏", "category": "pacing", 
             "keywords": ["缓缓", "慢慢", "徐徐", "悠然", "闲适", "安静", "宁静"], 
             "confidence": 0.75},
            {"name": "场景切换", "category": "pacing", 
             "keywords": ["与此同时", "另一边", "同时", "那一边"], 
             "confidence": 0.80},
            
            # 主题类
            {"name": "哲学思辨", "category": "theme", 
             "keywords": ["意义", "价值", "存在", "本质", "真理", "道理", "人生"], 
             "confidence": 0.85},
            {"name": "社会隐喻", "category": "theme", 
             "keywords": ["社会", "时代", "命运", "阶级", "制度", "权力", "压迫"], 
             "confidence": 0.80},
        ]
    
    def search_techniques(
        self, 
        query: str = None,
        category: str = None,
        scene_type: str = None,
        min_confidence: float = 0.6,
        limit: int = 10
    ) -> List[Dict]:
        """
        搜索技法
        
        Args:
            query: 搜索关键词
            category: 技法类别
            scene_type: 场景类型（如"战斗"、"对话"、"抒情"）
            min_confidence: 最小置信度
            limit: 返回数量限制
        
        Returns:
            技法列表
        """
        results = []
        
        # 场景类型到类别的映射
        scene_to_category = {
            '战斗': ['plot', 'pacing'],
            '冲突': ['plot'],
            '对话': ['dialogue', 'character'],
            '抒情': ['emotion'],
            '描写': ['scene'],
            '回忆': ['character'],
            '开端': ['plot'],
            '高潮': ['plot', 'pacing'],
            '结尾': ['plot', 'theme'],
        }
        
        for rule in self.rules:
            # 类别过滤
            if category and rule['category'] != category:
                continue
            
            # 场景类型过滤
            if scene_type:
                allowed_cats = scene_to_category.get(scene_type, [scene_type])
                if rule['category'] not in allowed_cats:
                    continue
            
            # 关键词匹配
            matches = []
            text_to_search = query or ""
            for keyword in rule['keywords']:
                if keyword in text_to_search:
                    matches.append(keyword)
            
            # 查询匹配模式
            if query:
                if matches:
                    # 有匹配，增加置信度
                    confidence = min(0.95, rule['confidence'] + len(matches) * 0.03)
                    results.append({
                        "name": rule['name'],
                        "category": rule['category'],
                        "confidence": confidence,
                        "matched_keywords": matches,
                        "definition": f"在文本中使用{rule['name']}技法",
                        "scenario": f"适用于{rule['category']}类场景"
                    })
            else:
                # 无查询，返回推荐
                if rule['confidence'] >= min_confidence:
                    results.append({
                        "name": rule['name'],
                        "category": rule['category'],
                        "confidence": rule['confidence'],
                        "definition": f"在文本中使用{rule['name']}技法"
                    })
        
        # 按置信度排序
        results.sort(key=lambda x: x['confidence'], reverse=True)
        return results[:limit]
    
    def analyze_chapter(self, chapter_text: str) -> Dict:
        """
        分析章节，提取技法
        
        Args:
            chapter_text: 章节文本
        
        Returns:
            分析结果
        """
        techniques = []
        
        for rule in self.rules:
            matches = []
            for keyword in rule['keywords']:
                if keyword in chapter_text:
                    idx = chapter_text.find(keyword)
                    start = max(0, idx - 50)
                    end = min(len(chapter_text), idx + 100)
                    context = chapter_text[start:end].replace('\n', ' ')
                    matches.append({
                        "keyword": keyword,
                        "context": context
                    })
            
            if matches:
                confidence = min(0.95, rule['confidence'] + (len(matches) - 1) * 0.02)
                techniques.append({
                    "name": rule['name'],
                    "category": rule['category'],
                    "confidence": confidence,
                    "match_count": len(matches),
                    "examples": [m['context'] for m in matches[:3]],
                    "definition": f"在文本中使用{rule['name']}技法",
                    "effect": f"增强{rule['category']}表现"
                })
        
        # 统计各类别
        category_stats = {}
        for t in techniques:
            cat = t['category']
            category_stats[cat] = category_stats.get(cat, 0) + 1
        
        # 计算质量分
        quality_score = min(1.0, len(techniques) / 10)
        
        return {
            "techniques_count": len(techniques),
            "techniques": techniques[:20],  # 最多返回20个
            "category_distribution": category_stats,
            "quality_score": quality_score,
            "char_count": len(chapter_text)
        }
    
    def get_style_profile(self, novel_name: str = None) -> Dict:
        """
        获取风格画像
        
        Args:
            novel_name: 小说名称
        
        Returns:
            风格画像
        """
        # 如果有已分析的小说数据，使用它
        # 否则返回默认风格
        if novel_name:
            novel_dir = self.novels_dir / novel_name
            if novel_dir.exists():
                # 尝试读取统计
                report_file = novel_dir / 'reports' / 'progress_report.json'
                if report_file.exists():
                    with open(report_file) as f:
                        data = json.load(f)
                        return {
                            "novel": novel_name,
                            "statistics": data.get('statistics', {}),
                            "style_description": f"{novel_name}的写作风格"
                        }
        
        # 默认返回
        return {
            "novel": novel_name or "default",
            "signature_techniques": [
                {"name": "危机开场", "category": "plot"},
                {"name": "对话推进", "category": "dialogue"},
                {"name": "内心独白", "category": "character"}
            ],
            "category_weights": {
                "plot": 0.25,
                "character": 0.20,
                "dialogue": 0.20,
                "scene": 0.15,
                "emotion": 0.10,
                "pacing": 0.05,
                "theme": 0.05
            },
            "style_description": "网络小说主流风格"
        }
    
    def get_categories(self) -> List[Dict]:
        """获取所有技法类别"""
        return [
            {"id": cat, "name": TECHNIQUE_CATEGORIES[cat], "count": len([r for r in self.rules if r['category'] == cat])}
            for cat in TECHNIQUE_CATEGORIES
        ]


# FastAPI 应用
try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    from typing import Optional
    
    app = FastAPI(
        title="Inkcore NC API",
        description="为Nova Agent提供技法查询和章节分析服务",
        version="1.0.0-nc"
    )
    
    service = InkcoreNCServicer()
    
    class SearchRequest(BaseModel):
        query: Optional[str] = None
        category: Optional[str] = None
        scene_type: Optional[str] = None
        min_confidence: Optional[float] = 0.6
        limit: Optional[int] = 10
    
    class AnalyzeRequest(BaseModel):
        chapter_text: str
    
    @app.get("/health")
    async def health():
        return {"status": "healthy", "service": "inkcore-nc", "version": "1.0.0"}
    
    @app.get("/api/v1/categories")
    async def list_categories():
        return service.get_categories()
    
    @app.post("/api/v1/search")
    async def search(request: SearchRequest):
        return service.search_techniques(
            query=request.query,
            category=request.category,
            scene_type=request.scene_type,
            min_confidence=request.min_confidence or 0.6,
            limit=request.limit or 10
        )
    
    @app.post("/api/v1/analyze")
    async def analyze(request: AnalyzeRequest):
        return service.analyze_chapter(request.chapter_text)
    
    @app.get("/api/v1/style/{novel_name}")
    async def get_style(novel_name: str = None):
        return service.get_style_profile(novel_name)
    
    HAS_FASTAPI = True

except ImportError:
    HAS_FASTAPI = False
    logger.warning("FastAPI not installed. Running in basic mode.")


def main():
    """主入口"""
    port = int(os.environ.get('INKCORE_PORT', 8000))
    
    if HAS_FASTAPI:
        import uvicorn
        logger.info(f"Starting Inkcore NC API on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port)
    else:
        # 简单测试模式
        service = InkcoreNCServicer()
        
        # 测试搜索
        print("\n=== 测试：搜索战斗场景技法 ===")
        results = service.search_techniques(scene_type="战斗", limit=5)
        for r in results:
            print(f"  - {r['name']} ({r['category']}) 置信度: {r['confidence']:.2f}")
        
        # 测试分析
        print("\n=== 测试：分析章节 ===")
        test_text = """
        雨夜，电闪雷鸣。
        街道上，一个身影迅速穿过。他是国安局的特工，正在追捕一名危险的罪犯。
        "站住！"他大声喊道。
        罪犯回过头，露出意味深长的笑容："你以为你能抓到我？"
        """
        analysis = service.analyze_chapter(test_text)
        print(f" 检测到 {analysis['techniques_count']} 个技法")
        print(f" 类别分布: {analysis['category_distribution']}")
        print(f" 质量分: {analysis['quality_score']:.2f}")
        
        # 测试风格
        print("\n=== 测试：获取风格画像 ===")
        style = service.get_style_profile("间客")
        print(f" 小说: {style['novel']}")
        print(f" 签名技法: {[t['name'] for t in style['signature_techniques']]}")


if __name__ == "__main__":
    main()
