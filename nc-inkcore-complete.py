#!/usr/bin/env python3
"""
NC + Inkcore + AI 完整协作系统

流程：
1. NC完整策划（节拍、人物、伏笔、世界观）
2. Inkcore技法推荐（基于NC策划）
3. AI创作（基于NC约束 + Inkcore技法）
4. Inkcore验证（反馈）

使用方法:
    # 完整流程
    python nc-inkcore-complete.py workflow --chapter 1
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/inkcore-v5')
from nc_integration import InkcoreNCIntegration


class NCPlanner:
    """NC 小说创作策划系统"""
    
    def __init__(self):
        self.project = {
            "name": "星隐回响",
            "volume": "第一卷：星启",
            "core_mystery": "青铜神树的秘密"
        }
        self.characters = {
            "沈仲梵": {
                "role": "主角",
                "profession": "文物修复师",
                "language": "简洁专业",
                "traits": ["沉稳", "专注", "有秘密"],
                "signature": ["转修复刀", "嗯", "从专业角度看"]
            },
            "林深": {
                "role": "配角",
                "profession": "研究员",
                "language": "话痨数据派",
                "traits": ["热情", "好奇", "话多"],
                "signature": ["从数据上看", "理论上讲", "但是等等"]
            },
            "白夜": {
                "role": "配角",
                "profession": "安保",
                "language": "简洁神秘",
                "traits": ["直觉准", "话少"],
                "signature": ["直觉告诉我", "你小心点"]
            }
        }
        self.world_elements = {
            "博物馆": ("地点", "文物修复室所在地"),
            "青铜器": ("文物", "蕴含未知元素"),
            "鸣沙": ("古遗址", "曾经是绿洲")
        }
    
    def plan_chapter(self, chapter_num: int, chapter_title: str, scene: str, 
                     characters: list, goals: list, total_words: int = 5000) -> dict:
        """生成章节策划"""
        
        # 节拍设计
        beats = [
            {"name": "场景建立", "target_words": int(total_words * 0.20), 
             "goals": ["建立场景", "展示人物", "铺陈氛围"]},
            {"name": "触发事件", "target_words": int(total_words * 0.12), 
             "goals": ["引入冲突", "发现神秘符号"]},
            {"name": "情节推进", "target_words": int(total_words * 0.32), 
             "goals": ["展开剧情", "技术分析", "展示人物"]},
            {"name": "高潮发现", "target_words": int(total_words * 0.20), 
             "goals": ["核心发现", "未知元素", "师父秘密"]},
            {"name": "收尾悬念", "target_words": int(total_words * 0.16), 
             "goals": ["收束情节", "埋设钩子", "黑影出现"]}
        ]
        
        # 伏笔
        foreshadowings = [
            {"name": "青铜神树", "hint": "青铜器的秘密", "chapter": 45},
            {"name": "鸣沙", "hint": "沙漠古文明", "chapter": 30}
        ]
        
        # 人物详细
        char_details = {name: self.characters.get(name, {}) for name in characters if name in self.characters}
        
        return {
            "chapter": {"num": chapter_num, "title": chapter_title, "scene": scene, "total_words": total_words},
            "project": self.project,
            "characters": {"in_scene": characters, "details": char_details},
            "goals": goals,
            "beats": beats,
            "foreshadowings": foreshadowings
        }
    
    def format_plan(self, plan: dict) -> str:
        """格式化输出策划"""
        lines = []
        proj = plan["project"]
        
        lines.append("=" * 70)
        lines.append(f"🎬 {proj['volume']} - 第{plan['chapter']['num']}章")
        lines.append(f"📖 标题：{plan['chapter']['title']}")
        lines.append("=" * 70)
        
        lines.append(f"\n📍 场景：{plan['chapter']['scene']}")
        lines.append(f"📏 目标字数：{plan['chapter']['total_words']}字")
        lines.append(f"🔐 核心谜题：{proj['core_mystery']}")
        
        lines.append(f"\n👤 出场人物：")
        for char, info in plan["characters"]["details"].items():
            lines.append(f"   • {char}（{info.get('role', '')}）")
            lines.append(f"     性格：{', '.join(info.get('traits', []))}")
            lines.append(f"     语言：{info.get('language', '')}")
            lines.append(f"     口头禅：{', '.join(info.get('signature', []))}")
        
        lines.append(f"\n🎯 本章目标：")
        for goal in plan["goals"]:
            lines.append(f"   • {goal}")
        
        lines.append(f"\n📊 节拍设计：")
        for i, beat in enumerate(plan["beats"], 1):
            lines.append(f"\n   【节拍{i}：{beat['name']}】{beat['target_words']}字")
            for goal in beat["goals"]:
                lines.append(f"      • {goal}")
        
        lines.append(f"\n🔮 伏笔埋设：")
        for fs in plan["foreshadowings"]:
            lines.append(f"   • {fs['name']}: {fs['hint']}（第{fs['chapter']}章回收）")
        
        lines.append("=" * 70)
        return "\n".join(lines)


class CompleteWorkflow:
    """完整工作流"""
    
    def __init__(self):
        self.nc = NCPlanner()
        self.inkcore = InkcoreNCIntegration()
    
    def run(self, chapter_num: int = 1):
        """运行完整流程"""
        
        # ========== 阶段1：NC完整策划 ==========
        print("=" * 70)
        print("🎬 阶段1：NC 完整策划")
        print("=" * 70)
        
        plan = self.nc.plan_chapter(
            chapter_num=chapter_num,
            chapter_title="青铜之光",
            scene="博物馆修复室",
            characters=["沈仲梵", "林深", "白夜"],
            goals=["建立主角身份", "引出青铜器谜团", "埋设伏笔"],
            total_words=5000
        )
        
        print(self.nc.format_plan(plan))
        
        # ========== 阶段2：Inkcore技法推荐 ==========
        print("\n" + "=" * 70)
        print("🎨 阶段2：Inkcore 技法推荐")
        print("=" * 70)
        
        for beat in plan["beats"]:
            print(f"\n【{beat['name']}】")
            rec = self.inkcore.recommend_techniques(
                scene_type=plan["chapter"]["scene"],
                beat_type=beat["name"],
                goal_words=beat["target_words"],
                novel_style="默认"
            )
            
            print(f"   🔴 主要技法：")
            for t in rec["recommended_techniques"]:
                if t.get("priority") == "primary":
                    print(f"      • {t['name']}")
            
            print(f"   🟡 辅助技法：")
            for t in rec["recommended_techniques"]:
                if t.get("priority") == "secondary":
                    print(f"      • {t['name']}")
            
            if rec["antipattern_warnings"]:
                print(f"   ⚠️ 注意：")
                for w in rec["antipattern_warnings"][:2]:
                    print(f"      • {w}")
        
        # ========== 阶段3：AI创作指南 ==========
        print("\n" + "=" * 70)
        print("📝 阶段3：AI 创作指南")
        print("=" * 70)
        
        print("""
📋 创作要求：

1. 人物语言约束：
   沈仲梵：简洁专业，口头禅"嗯"、"从专业角度看"，紧张时转修复刀
   林深：话痨数据派，口头禅"从数据上看"、"理论上讲"，语速快
   白夜：简洁神秘，口头禅"直觉告诉我"

2. 技法应用（按节拍）：
   - 场景建立：环境描写、人物出场、氛围营造
   - 触发事件：悬念设置、内心独白
   - 情节推进：对话推进、快节奏
   - 高潮发现：高潮爆发、情绪爆发、哲学思辨
   - 收尾悬念：悬念设置、氛围营造

3. 伏笔处理：
   - 青铜神树：本章埋设（第45章回收）
   - 鸣沙：本章提及（第30章回收）

4. 一致性检查：
   - 沈仲梵性格：沉稳专注，不急躁
   - 世界观：博物馆、青铜器、鸣沙

5. 总字数：5000字（按节拍分配）
""")
        
        # ========== 阶段4：验证说明 ==========
        print("=" * 70)
        print("🔍 阶段4：Inkcore 验证")
        print("=" * 70)
        print("""
创作完成后，使用以下命令验证：

    python nc-inkcore-complete.py verify --file chapter.txt

验证将检查：
- 技法覆盖率（目标：≥70%）
- 质量评分（目标：≥0.7）
- 反模式检测
- 改进建议

✅ PASS → 章节完成
⚠️ REVISE → 需要修改
❌ FAIL → 大幅重写
""")

    def verify(self, filepath: str):
        """验证章节"""
        with open(filepath, 'r') as f:
            content = f.read()
        
        print("=" * 70)
        print("🔍 Inkcore 质量验证")
        print("=" * 70)
        print(f"文件：{filepath}")
        print(f"字数：{len(content)} 字\n")
        
        workflow = self.inkcore.get_full_workflow(
            scene_type="博物馆修复室",
            beat_type="场景建立",
            goal_words=5000,
            novel_style="默认",
            chapter_text=content
        )
        
        v = workflow["verification"]
        print(f"检测技法：{v['techniques_found']} 个")
        print(f"质量分：{v['quality_score']:.2f}")
        
        if v['target_met']:
            print(f"目标达成率：{v['target_met'].get('match_rate', 0)*100:.1f}%")
        
        verdict_map = {"pass": "✅ PASS", "revise": "⚠️ REVISE", "fail": "❌ FAIL"}
        print(f"判定：{verdict_map.get(v['verdict'], v['verdict'])}")
        print(f"总结：{v['summary']}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='NC + Inkcore + AI 完整协作')
    parser.add_argument('--chapter', '-c', type=int, default=1, help='章节号')
    parser.add_argument('--file', '-f', help='验证文件')
    
    args = parser.parse_args()
    
    workflow = CompleteWorkflow()
    
    if args.file:
        workflow.verify(args.file)
    else:
        workflow.run(args.chapter)
