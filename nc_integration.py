#!/usr/bin/env python3
"""
Inkcore NC 深度集成模块

提供：
1. 事前推荐：场景→技法匹配
2. 事中指导：风格指南
3. 事后验证：质量分析
4. 反馈循环：改进建议

使用方法:
    from nc_integration import InkcoreNCO集成
    
    service = InkcoreNCIntegration()
    
    # 1. 事前推荐
    recommendations = service.recommend_techniques(
        scene_type="博物馆修复室",
        beat_type="场景建立",  # 或"触发事件"/"情节推进"/"高潮发现"/"收尾悬念"
        goal_words=800
    )
    
    # 2. 风格指导
    style = service.get_style_guide("间客")
    
    # 3. 事后验证
    analysis = service.analyze_chapter(chapter_text)
    
    # 4. 反馈建议
    feedback = service.get_feedback(analysis, target_techniques)
"""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from nc_api import InkcoreNCServicer


class InkcoreNCIntegration:
    """
    Inkcore NC 深度集成服务
    
    为 NC 提供完整的创作支持：策划→创作→验证→反馈
    """
    
    def __init__(self, novels_dir: Path = None):
        self.base_service = InkcoreNCServicer(novels_dir)
        
        # 场景类型到节拍类型的映射
        self.scene_to_beat = {
            # 场景类型 -> 对应的节拍类型
            "博物馆": ["场景建立", "情节推进"],
            "修复室": ["场景建立", "情节推进"],
            "实验室": ["情节推进", "高潮发现"],
            "街道": ["情节推进", "收尾悬念"],
            "夜晚": ["收尾悬念", "场景建立"],
            "室内": ["场景建立"],
            "户外": ["情节推进"],
        }
        
        # 节拍类型到技法的映射
        self.beat_to_techniques = {
            "场景建立": {
                "primary": ["环境描写", "氛围营造", "人物出场"],
                "secondary": ["慢节奏", "内心独白"],
                "weight": 0.3  # 字数权重
            },
            "触发事件": {
                "primary": ["悬念设置", "危机开场", "内心独白"],
                "secondary": ["快节奏", "环境描写"],
                "weight": 0.2
            },
            "情节推进": {
                "primary": ["对话推进", "快节奏", "人物出场"],
                "secondary": ["空间转换", "氛围营造"],
                "weight": 0.3
            },
            "高潮发现": {
                "primary": ["高潮爆发", "情绪爆发", "哲学思辨"],
                "secondary": ["快节奏", "内心独白"],
                "weight": 0.2
            },
            "收尾悬念": {
                "primary": ["悬念设置", "氛围营造"],
                "secondary": ["慢节奏", "空间转换"],
                "weight": 0.1
            }
        }
        
        # 场景关键词到技法的映射
        self.scene_keywords = {
            "博物馆": ["环境描写", "氛围营造", "空间转换"],
            "修复": ["人物出场", "对话推进"],
            "科技": ["快节奏", "对话推进", "高潮爆发"],
            "战斗": ["快节奏", "高潮爆发", "情绪爆发"],
            "对话": ["对话推进", "潜台词"],
            "抒情": ["温情描写", "慢节奏", "内心独白"],
            "回忆": ["内心独白", "慢节奏"],
            "夜晚": ["环境描写", "氛围营造", "慢节奏"],
            "危机": ["危机开场", "悬念设置", "快节奏"],
            "分析": ["对话推进", "快节奏", "内心独白"],
        }
        
        # 风格指南模板
        self.style_templates = {
            "猫腻": {
                "description": "猫腻风格：政治斗争、细腻情感、伏笔深远",
                "techniques": ["对话推进", "潜台词", "内心独白", "伏笔埋设"],
                "ratio": {"dialogue": 0.4, "inner": 0.3, "action": 0.2, "desc": 0.1},
                "pacing": "中慢节奏，注重内心变化",
                "参考作品": ["间客", "将夜", "庆余年"]
            },
            "烽火": {
                "description": "烽火戏诸侯风格：热血战斗、兄弟情义、爽点密集",
                "techniques": ["快节奏", "高潮爆发", "情绪爆发", "对话推进"],
                "ratio": {"action": 0.5, "dialogue": 0.3, "inner": 0.1, "desc": 0.1},
                "pacing": "快节奏，高潮迭起",
                "参考作品": ["雪中悍刀行", "剑来"]
            },
            "土豆": {
                "description": "土豆风格：废柴流、升级流、简洁有力",
                "techniques": ["快节奏", "悬念设置", "高潮爆发"],
                "ratio": {"action": 0.4, "dialogue": 0.3, "inner": 0.2, "desc": 0.1},
                "pacing": "快节奏，简洁不拖沓",
                "参考作品": ["斗破苍穹", "元尊"]
            },
            "默认": {
                "description": "网络小说主流风格",
                "techniques": ["悬念设置", "对话推进", "高潮爆发", "环境描写"],
                "ratio": {"action": 0.3, "dialogue": 0.3, "inner": 0.2, "desc": 0.2},
                "pacing": "中等节奏",
                "参考作品": []
            }
        }
        
        # 反模式提醒
        self.antipatterns = {
            "场景建立": [
                "避免：直接大段介绍人物背景",
                "避免：场景与情节脱节",
                "避免：节奏过慢，缺乏吸引力"
            ],
            "触发事件": [
                "避免：事件突兀，缺乏铺垫",
                "避免：过于平淡，无危机感"
            ],
            "情节推进": [
                "避免：对话过长，缺乏动作",
                "避免：节奏拖沓，水字数"
            ],
            "高潮发现": [
                "避免：情感爆发突兀",
                "避免：发现过于容易，缺乏张力"
            ],
            "收尾悬念": [
                "避免：悬念过于明显",
                "避免：戛然而止，无余韵"
            ]
        }
    
    def recommend_techniques(
        self,
        scene_type: str = None,
        beat_type: str = None,
        goal_words: int = 1000,
        novel_style: str = "默认",
        context: Dict = None
    ) -> Dict:
        """
        根据场景和节拍类型推荐适用技法
        
        Args:
            scene_type: 场景类型（如"博物馆"、"战斗"）
            beat_type: 节拍类型（场景建立/触发事件/情节推进/高潮发现/收尾悬念）
            goal_words: 目标字数
            novel_style: 小说风格（默认/猫腻/烽火/土豆）
            context: 额外上下文信息
        
        Returns:
            推荐结果字典
        """
        recommended = []
        
        # 1. 基于节拍类型的推荐
        if beat_type and beat_type in self.beat_to_techniques:
            beat_info = self.beat_to_techniques[beat_type]
            
            for technique in beat_info["primary"]:
                # 搜索匹配的技法（不使用query参数，改为返回默认列表）
                results = self.base_service.search_techniques(
                    query=None,
                    category=None,
                    min_confidence=0.6,
                    limit=20
                )
                # 筛选包含关键词的
                for r in results:
                    if technique in r.get("name", ""):
                        r["priority"] = "primary"
                        r["reason"] = f"节拍{beat_type}核心技法"
                        if r not in recommended:
                            recommended.append(r)
            
            for technique in beat_info["secondary"]:
                results = self.base_service.search_techniques(
                    query=None,
                    min_confidence=0.5,
                    limit=20
                )
                for r in results:
                    if technique in r.get("name", ""):
                        r["priority"] = "secondary"
                        r["reason"] = f"节拍{beat_type}辅助技法"
                        if r not in recommended:
                            recommended.append(r)
        
        # 2. 基于场景关键词的补充推荐
        if scene_type:
            # 先获取所有技法作为备选
            all_techniques = self.base_service.search_techniques(
                query=None, min_confidence=0.5, limit=30
            )
            
            for keyword, techniques in self.scene_keywords.items():
                if keyword in scene_type:
                    for tech_name in techniques:
                        # 查找匹配
                        for t in all_techniques:
                            if tech_name in t.get("name", ""):
                                t["priority"] = "scene_based"
                                t["reason"] = f"场景'{keyword}'适用"
                                if t not in recommended:
                                    recommended.append(t)
        
        # 3. 获取风格建议
        style_guide = self.style_templates.get(novel_style, self.style_templates["默认"])
        
        # 4. 获取反模式提醒
        antipattern_warnings = self.antipatterns.get(beat_type, [])
        
        # 5. 字数分配建议
        word_distribution = {}
        if beat_type:
            weight = self.beat_to_techniques[beat_type].get("weight", 0.2)
            word_distribution = {
                "total_goal": goal_words,
                "current_beat": int(goal_words * weight),
                "remaining": int(goal_words * (1 - weight))
            }
        
        return {
            "scene_type": scene_type,
            "beat_type": beat_type,
            "style": novel_style,
            "recommended_techniques": recommended[:10],  # 最多10个
            "style_guide": style_guide,
            "antipattern_warnings": antipattern_warnings,
            "word_distribution": word_distribution,
            "tips": self._generate_tips(scene_type, beat_type, novel_style)
        }
    
    def _generate_tips(self, scene_type: str, beat_type: str, style: str) -> List[str]:
        """生成创作提示"""
        tips = []
        
        # 基于节拍的提示
        beat_tips = {
            "场景建立": "用细节建立氛围，让读者感受到场景的真实感",
            "触发事件": "制造冲突或悬念，让主角面临选择",
            "情节推进": "通过对话和动作展现人物性格",
            "高潮发现": "情感爆发要自然累积，释放要有冲击力",
            "收尾悬念": "留有余味，让读者期待下一章"
        }
        
        if beat_type and beat_type in beat_tips:
            tips.append(beat_tips[beat_type])
        
        # 基于风格的提示
        style_tips = {
            "猫腻": "注重对话中的潜台词，让人物语言有言外之意",
            "烽火": "增加战斗场面的冲击力，注意节奏把控",
            "土豆": "简洁有力，避免冗余描写，每句话都要推动情节",
            "默认": "保持节奏，平衡叙事与对话"
        }
        
        if style in style_tips:
            tips.append(style_tips[style])
        
        # 基于场景的提示
        if scene_type:
            if "博物" in scene_type or "馆" in scene_type:
                tips.append("通过专业细节展现场景的真实感")
            if "夜" in scene_type:
                tips.append("利用光线变化营造氛围和情绪")
        
        return tips
    
    def get_style_guide(self, novel_name: str = None) -> Dict:
        """
        获取风格指南
        
        Args:
            novel_name: 小说名称
        
        Returns:
            风格指南字典
        """
        # 尝试从已分析的小说中获取
        if novel_name:
            base_style = self.base_service.get_style_profile(novel_name)
            if "statistics" in base_style:
                return base_style
        
        # 返回默认风格
        return self.style_templates["默认"]
    
    def analyze_and_feedback(
        self,
        chapter_text: str,
        target_recommendations: Dict = None
    ) -> Dict:
        """
        分析章节并提供反馈
        
        Args:
            chapter_text: 章节文本
            target_recommendations: 目标推荐（来自recommend_techniques）
        
        Returns:
            分析报告和反馈
        """
        # 1. 基础分析
        analysis = self.base_service.analyze_chapter(chapter_text)
        
        # 2. 对比目标
        feedback = {
            "quality_score": analysis["quality_score"],
            "techniques_found": analysis["techniques_count"],
            "category_balance": analysis["category_distribution"],
            "target_met": {},
            "improvements": [],
            "verdict": ""
        }
        
        # 3. 检查目标达成
        if target_recommendations:
            target_techniques = set(t["name"] for t in target_recommendations.get("recommended_techniques", []))
            found_techniques = set(t["name"] for t in analysis["techniques"])
            
            matched = target_techniques & found_techniques
            missing = target_techniques - found_techniques
            extra = found_techniques - target_techniques
            
            feedback["target_met"] = {
                "matched": list(matched),
                "missing": list(missing),
                "extra": list(extra),
                "match_rate": len(matched) / len(target_techniques) if target_techniques else 0
            }
            
            # 4. 改进建议
            if missing:
                missing_list = list(missing)[:3]
                feedback["improvements"].append(
                    f"建议增加以下技法：{', '.join(missing_list)}"
                )
            
            # 5. 判定
            match_rate = feedback["target_met"]["match_rate"]
            if match_rate >= 0.7 and analysis["quality_score"] >= 0.7:
                feedback["verdict"] = "pass"
            elif match_rate >= 0.5:
                feedback["verdict"] = "revise"
            else:
                feedback["verdict"] = "fail"
        
        # 6. 总结
        feedback["summary"] = self._generate_summary(analysis, feedback)
        
        return feedback
    
    def _generate_summary(self, analysis: Dict, feedback: Dict) -> str:
        """生成总结"""
        score = feedback.get("quality_score", 0)
        techniques = analysis.get("techniques_count", 0)
        
        if score >= 0.8 and techniques >= 10:
            return "优秀：技法丰富，质量上乘"
        elif score >= 0.6 and techniques >= 5:
            return "良好：达到基本质量标准"
        elif score >= 0.4:
            return "一般：需要适度改进"
        else:
            return "不足：建议大幅调整"
    
    def get_full_workflow(
        self,
        scene_type: str,
        beat_type: str,
        goal_words: int,
        novel_style: str,
        chapter_text: str = None
    ) -> Dict:
        """
        完整工作流：策划→验证
        
        Args:
            scene_type: 场景类型
            beat_type: 节拍类型
            goal_words: 目标字数
            novel_style: 小说风格
            chapter_text: 章节文本（可选，用于验证）
        
        Returns:
            完整工作流结果
        """
        result = {
            "phase": "planning" if not chapter_text else "verification"
        }
        
        # 阶段1：策划推荐
        result["planning"] = self.recommend_techniques(
            scene_type=scene_type,
            beat_type=beat_type,
            goal_words=goal_words,
            novel_style=novel_style
        )
        
        # 阶段2：验证（如有文本）
        if chapter_text:
            result["verification"] = self.analyze_and_feedback(
                chapter_text=chapter_text,
                target_recommendations=result["planning"]
            )
        
        return result


# 测试
if __name__ == "__main__":
    service = InkcoreNCIntegration()
    
    print("=" * 60)
    print("Inkcore NC 深度集成测试")
    print("=" * 60)
    
    # 测试1：推荐
    print("\n[测试1] 场景建立节拍的技法推荐")
    rec = service.recommend_techniques(
        scene_type="博物馆修复室",
        beat_type="场景建立",
        goal_words=800,
        novel_style="默认"
    )
    print(f"✓ 推荐技法数: {len(rec['recommended_techniques'])}")
    print(f"✓ 风格指南: {rec['style_guide']['description']}")
    print(f"✓ 反模式提醒: {len(rec['antipattern_warnings'])} 条")
    print(f"✓ 创作提示: {rec['tips']}")
    
    # 测试2：完整工作流
    print("\n[测试2] 完整工作流（带验证）")
    workflow = service.get_full_workflow(
        scene_type="博物馆修复室",
        beat_type="场景建立",
        goal_words=800,
        novel_style="默认",
        chapter_text="下午的阳光透过博物馆修复室的落地窗..."
    )
    print(f"✓ 流程阶段: {workflow['phase']}")
    if "verification" in workflow:
        v = workflow["verification"]
        print(f"✓ 质量分: {v['quality_score']:.2f}")
        print(f"✓ 判定: {v['verdict']}")
        print(f"✓ 总结: {v['summary']}")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)
