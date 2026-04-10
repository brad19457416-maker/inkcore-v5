#!/usr/bin/env python3
"""
墨芯 v5.0 vs v4.0 对比测试脚本
使用 v5.0 分析《间客》并与 v4.0 结果对比
"""

import asyncio
import sys
import tempfile
import shutil
from datetime import datetime

# 添加项目路径
sys.path.insert(0, '/root/.openclaw/workspace/inkcore-v5')

from memory.palace_v2 import InkCorePalaceV2, TechniqueCategory
from agents.core import AgentOrchestrator, ChapterInput
from skills.registry import SkillRegistry


# 间客第一章样本
JIANGE_CHAPTER_1 = """
《间客》第一章 钟楼街的游行

如果从太空里俯瞰东林，这是一颗美丽的星球。星球表面那些蓝色的海水和一望无尽的绿色原野，
还有那些苍白的令人心悸的矿坑，被透过高空微粒洒下的恒星光芒照拂，会透露出来一股难以言喻的
朦胧美感，就像是一张一放很多年的油画，蒙着历史的尘埃。

然而对于东林区的居民和孤儿们来说，这个星球有的只是石头，除了石头之外，什么都没有。哪怕是
那些绿色的原野，在他们坚毅渐成麻木的眼光中，也只是一些覆在财富和光荣历史上的青色草皮，
他们的目光只习惯于透过这些草皮，直视那些东林人最渴望的矿脉。

从行政规划来说，东林是二级行政大区，和首都星圈那三颗夺目的星球以及西林大区拥有完全一样的
行政等级。但是在联邦人民们的心里，遥远的东林，实际上已经是被遗忘了的角落。除了在联邦政府
成立六百年的庆典上还能看到东林的名字，很多时候，对于那些生活在富裕文明社会里的人们来说，
东林已经不存在了。

东林大区只有一颗星球，东林星，这似乎是废话，其实又不是废话，因为东林大区名字的由来，
便是因为东林星，由此可见，在极为遥远的过去，这颗孤单悬于三角星系最外方的星球，对于整个人类
社会而言，拥有怎样重要的意义。

然而自从东林大区的各种品型的矿石被采掘完毕之后，东林星便成了一个渐渐荒芜的星球，这里只有
石头，没有矿石，只有石头。

……

有能力离开东林的人们，早已经离开了这里。凭借着专业的技能和积蓄的财富，通过首都星圈或
西林大区的亲人担保，他们成功地获取得了户籍转移证明，乘坐着因为能源短缺而越来越少的航班，
离开了这个越来越没有生机的地方。

能够拿到户籍转移证明的人毕竟是少数，半废弃状态下的星球，依然要维持很多人的生活。在一个
物质文明相对发达的社会里，温饱早已经不再是人类需要担心的问题，东林星上的人们依然安稳的活着，
社会综援依旧发挥着极其重要的作用，货币依然平稳的流通，这个世界里依然有公司，有机场，
有食品加工厂，机甲维护站，电脑联结中心，甚至还有一个军备基地。

应该有的，可以有的，东林区全部都有，只是依然掩不住一股淡淡的老味儿，死味儿从每一条街道，
每一幢建筑，每一个无所事事，端着咖啡，看着电视的人们脸上渗了出来。

数千年的矿石采掘，为联邦社会提供了源源不断的支撑，就像是一条为平原输送养分的大河一样，
然而当这条大河渐渐干涸，变成了一条充满了臭气的小溪沟时，联邦社会反哺回来的支援，
却明显有些不够——因为人类从来都不仅仅是能够活着，便能感觉到幸福的。

东林的人们在数千年的历史中，培养出来了坚毅，吃苦耐劳的精神，远古时期连绵而至的矿难，
也并没有让他们有丝毫的退缩。然而眼前的这一切，却让他们感到了浓郁的悲哀和无奈。无矿可挖，
无事可做，从某一个角度讲，连矿难都没有的人生，绝对不是东林人想要的生活。

吃苦耐劳的东林人，在联邦社会里有东林石头的称号，如今的东林人，变成了愈发沉默，
愈发冷漠的石头，把自己塑成了雕像，杵在自己习惯的圈椅和家中的沙发上，似乎永远不会再动。

……

"""


async def run_v5_analysis():
    """运行 v5.0 分析"""
    print("=" * 60)
    print("墨芯 v5.0 技法提取测试")
    print("=" * 60)
    print()
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 初始化组件
        print("[1/4] 初始化 PalaceV2...")
        palace = InkCorePalaceV2(base_path=temp_dir)
        
        print("[2/4] 初始化 Agent Orchestrator...")
        orchestrator = AgentOrchestrator()
        
        print("[3/4] 初始化 Skill Registry...")
        registry = SkillRegistry()
        registry.register_builtin_skills(palace=palace, orchestrator=orchestrator)
        
        print("[4/4] 开始分析...")
        print()
        
        # 执行分析技能
        start_time = datetime.now()
        
        execution = await registry.execute(
            skill_id="AnalyzeNovelSkill",
            input_data={
                "novel_name": "间客",
                "volume": "第一卷",
                "chapter": "第一章 钟楼街的游行",
                "chapter_text": JIANGE_CHAPTER_1
            }
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("-" * 60)
        print(f"分析完成！耗时: {duration:.2f}秒")
        print("-" * 60)
        print()
        
        # 提取结果
        result = execution.context.output_data
        
        print("【v5.0 分析结果】")
        print()
        print(f"技能ID: {execution.skill_id}")
        print(f"状态: {execution.status.value}")
        print(f"技法数量: {result.get('techniques_count', 0)}")
        print()
        
        # 工作流历史
        print("【工作流执行记录】")
        for step in result.get('workflow_history', []):
            data_info = f" ({step['data']})" if step.get('data') else ""
            print(f"  - {step['step']}{data_info}")
        print()
        
        # 详细技法
        techniques = result.get('techniques', [])
        if techniques:
            print(f"【识别的技法】({len(techniques)}项)")
            print()
            for i, tech in enumerate(techniques[:5], 1):  # 只显示前5个
                print(f"  {i}. {tech.get('technique', '未知')}")
                print(f"     类别: {tech.get('category', '未知')}")
                print(f"     描述: {tech.get('description', '无')[:50]}...")
                print()
            
            if len(techniques) > 5:
                print(f"     ... 还有 {len(techniques) - 5} 项")
        
        #  Palace 存储结果
        print("【Palace 存储结果】")
        tech_ids = palace.mine_chapter(
            novel_name="间客",
            volume="第一卷",
            chapter="第一章",
            chapter_text=JIANGE_CHAPTER_1,
            extracted_techniques=techniques
        )
        print(f"  存入 Palace 的技法ID: {len(tech_ids)} 个")
        print()
        
        # 搜索测试
        print("【搜索测试】")
        search_results = palace.search("危机", novel="间客")
        print(f"  搜索'危机': {len(search_results)} 个结果")
        
        search_results = palace.search("人物", novel="间客")
        print(f"  搜索'人物': {len(search_results)} 个结果")
        print()
        
        return {
            "v5_result": result,
            "techniques_count": len(techniques),
            "duration": duration,
            "status": execution.status.value
        }
        
    finally:
        shutil.rmtree(temp_dir)


def compare_with_v4(v5_result):
    """与 v4.0 对比"""
    print("=" * 60)
    print("v5.0 vs v4.0 对比分析")
    print("=" * 60)
    print()
    
    # v4.0 数据（从报告中提取）
    v4_data = {
        "total_cases": 500,
        "chapters_analyzed": 914,
        "categories": {
            "人物塑造": 150,
            "爽点设计": 150,
            "情节设计": 100,
            "开篇技法": 50,
            "节奏把控": 50
        },
        "techniques": [
            "反差人设法", "人物弧光法", "配角衬托法",
            "期待感兑现", "装逼打脸", "金手指设计",
            "危机开局法", "张弛交替", "伏笔回收", "反转设计"
        ]
    }
    
    print("【v4.0 数据（完整分析 914 章）】")
    print(f"  总案例数: {v4_data['total_cases']}")
    print(f"  分析章节: {v4_data['chapters_analyzed']}")
    print()
    
    print("【v5.0 数据（单章测试）】")
    print(f"  识别技法: {v5_result['techniques_count']} 项")
    print(f"  分析耗时: {v5_result['duration']:.2f}秒")
    print(f"  执行状态: {v5_result['status']}")
    print()
    
    print("【架构对比】")
    print()
    print("  v4.0 架构:")
    print("    - 单进程顺序处理")
    print("    - 简单正则匹配")
    print("    - 无智能体协作")
    print()
    print("  v5.0 架构:")
    print("    - Agent Core: 1 ReadAgent + 4 ExtractAgent 并行")
    print("    - PalaceV2: L0/L1/L2 分层存储")
    print("    - Skill System: 强制工作流 (read→extract→verify→store→report)")
    print("    - 结构化输出 + 图遍历检索")
    print()
    
    print("【改进点】")
    print("  ✅ 并行分析: 4维度同时提取 (Character/Plot/Pacing/Catharsis)")
    print("  ✅ 分层存储: 原始→结构化→语义索引")
    print("  ✅ 强制工作流: 标准化处理流程")
    print("  ✅ 可扩展性: 插件化技能系统")
    print()
    
    print("【局限】")
    print("  ⚠️  本次仅测试单章，未做全量对比")
    print("  ⚠️  v5.0 Agent 使用模拟实现（非真实 LLM）")
    print("  ⚠️  需要真实小说文本才能做全面对比")
    print()


async def main():
    """主函数"""
    # 运行 v5.0 分析
    v5_result = await run_v5_analysis()
    
    # 对比分析
    compare_with_v4(v5_result)
    
    print("=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
