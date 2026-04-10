#!/usr/bin/env python3
"""
NC + Inkcore + AI 协作 CLI 工具

一键执行三方协作工作流：
    python nc-inkcore-cli.py generate \
        --scene "博物馆修复室" \
        --beat "场景建立" \
        --words 800 \
        --style "默认"

完整流程：
    1. NC策划 → 2. Inkcore技法推荐 → 3. AI创作 → 4. Inkcore验证

使用方法:
    # 生成章节（完整流程）
    python nc-inkcore-cli.py generate --scene "博物馆" --beat "场景建立"
    
    # 只获取策划推荐
    python nc-inkcore-cli.py plan --scene "博物馆" --beat "场景建立"
    
    # 验证已写内容
    python nc-inkcore-cli.py verify --file chapter.txt --scene "博物馆" --beat "场景建立"
"""

import os
import sys
import argparse
import json
from pathlib import Path

# 添加 inkcore 路径
sys.path.insert(0, '/root/.openclaw/workspace/inkcore-v5')
from nc_integration import InkcoreNCIntegration


class NCInkcoreCLI:
    """NC-Inkcore-AI 协作 CLI"""
    
    def __init__(self):
        self.inkcore = InkcoreNCIntegration()
        
        # 模拟 NC 的策划输出（实际应从 NC 模块获取）
        self.nc_plan_template = {
            "chapter": "第1章",
            "title": "青铜之光",
            "volume": "第一卷：星启",
            "characters": ["沈仲梵", "林深"],
            "core_mystery": "青铜神树的秘密",
            "foreshadowing": ["鸣沙地名", "未知元素"]
        }
    
    def cmd_plan(self, args):
        """策划命令：输出 NC + Inkcore 的策划建议"""
        print("=" * 70)
        print("🎬 阶段1：策划（NC + Inkcore）")
        print("=" * 70)
        
        # NC 策划输出
        print("\n📚 NC 策划输出：")
        print(f"   章节：{self.nc_plan_template['chapter']} - {self.nc_plan_template['title']}")
        print(f"   卷：{self.nc_plan_template['volume']}")
        print(f"   出场人物：{', '.join(self.nc_plan_template['characters'])}")
        print(f"   核心谜题：{self.nc_plan_template['core_mystery']}")
        print(f"   伏笔埋设：{', '.join(self.nc_plan_template['foreshadowing'])}")
        
        # Inkcore 技法推荐
        print(f"\n🎨 Inkcore 技法推荐：")
        rec = self.inkcore.recommend_techniques(
            scene_type=args.scene,
            beat_type=args.beat,
            goal_words=args.words,
            novel_style=args.style
        )
        
        print(f"\n   主要技法（必须）：")
        for t in rec['recommended_techniques']:
            if t.get('priority') == 'primary':
                print(f"      🔴 {t['name']} - {t.get('reason', '')}")
        
        print(f"\n   辅助技法（建议）：")
        for t in rec['recommended_techniques']:
            if t.get('priority') == 'secondary':
                print(f"      🟡 {t['name']} - {t.get('reason', '')}")
        
        # 风格指南
        print(f"\n📖 风格指南：")
        sg = rec['style_guide']
        print(f"   风格：{sg['description']}")
        print(f"   核心技法：{', '.join(sg['techniques'][:4])}")
        print(f"   节奏：{sg['pacing']}")
        
        # 反模式
        print(f"\n⚠️ 反模式提醒：")
        for warning in rec['antipattern_warnings']:
            print(f"   • {warning}")
        
        # 创作提示
        print(f"\n💡 创作提示：")
        for tip in rec['tips']:
            print(f"   • {tip}")
        
        # 字数分配
        wd = rec['word_distribution']
        print(f"\n📝 字数分配：")
        print(f"   本节拍：{wd.get('current_beat', '?')}字")
        print(f"   剩余分配：{wd.get('remaining', '?')}字")
        
        print("\n" + "=" * 70)
        print("✅ 策划完成！请根据以上建议进行创作")
        print("=" * 70)
        
        # 保存策划结果供后续使用
        plan_file = f".plan_{args.beat}.json"
        with open(plan_file, 'w', encoding='utf-8') as f:
            json.dump({
                'scene': args.scene,
                'beat': args.beat,
                'words': args.words,
                'style': args.style,
                'recommendations': rec
            }, f, ensure_ascii=False, indent=2)
        print(f"\n💾 策划结果已保存到：{plan_file}")
    
    def cmd_generate(self, args):
        """生成命令：完整流程（策划→创作→验证）"""
        # 步骤1：策划
        self.cmd_plan(args)
        
        print("\n" + "=" * 70)
        print("📝 阶段2：AI 创作")
        print("=" * 70)
        print("\n⚠️ 注意：实际创作由 AI 执行")
        print("   此处演示如何读取策划结果并准备创作...")
        
        # 读取策划结果
        plan_file = f".plan_{args.beat}.json"
        if os.path.exists(plan_file):
            with open(plan_file, 'r', encoding='utf-8') as f:
                plan = json.load(f)
            print(f"\n✅ 已加载策划：{plan['beat']}")
            print(f"   目标字数：{plan['words']}字")
            print(f"   推荐技法：{len(plan['recommendations']['recommended_techniques'])}个")
        
        print("\n🤖 AI 应在此根据策划进行创作...")
        print("   （实际创作由 AI 完成）")
        
        # 步骤3：验证（如果有输出文件）
        if args.output and os.path.exists(args.output):
            print("\n" + "=" * 70)
            print("🔍 阶段3：Inkcore 验证")
            print("=" * 70)
            self._verify_file(args.output, args)
        else:
            print("\n💡 提示：使用 --output 文件路径可以在创作后自动验证")
    
    def cmd_verify(self, args):
        """验证命令：对已有内容进行质量验证"""
        if not args.file:
            print("❌ 错误：请提供要验证的文件路径")
            print("   用法：python nc-inkcore-cli.py verify --file chapter.txt")
            return
        
        if not os.path.exists(args.file):
            print(f"❌ 错误：文件不存在：{args.file}")
            return
        
        self._verify_file(args.file, args)
    
    def _verify_file(self, filepath, args):
        """验证文件内容"""
        print("=" * 70)
        print("🔍 Inkcore 质量验证")
        print("=" * 70)
        
        # 读取内容
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 获取策划推荐（如果存在）
        plan_file = f".plan_{args.beat}.json" if args.beat else ".plan.json"
        target_rec = None
        if os.path.exists(plan_file):
            with open(plan_file, 'r', encoding='utf-8') as f:
                plan = json.load(f)
                target_rec = plan.get('recommendations')
        
        # 执行验证
        workflow = self.inkcore.get_full_workflow(
            scene_type=args.scene or "默认场景",
            beat_type=args.beat or "场景建立",
            goal_words=args.words or 1000,
            novel_style=args.style or "默认",
            chapter_text=content
        )
        
        v = workflow['verification']
        
        print(f"\n📊 验证结果：")
        print(f"   文件：{filepath}")
        print(f"   字数：{len(content)} 字")
        print(f"   检测技法：{v['techniques_found']} 个")
        print(f"   质量分：{v['quality_score']:.2f}")
        
        if v['target_met']:
            match_rate = v['target_met'].get('match_rate', 0)
            print(f"   目标达成率：{match_rate*100:.1f}%")
        
        # 判定
        verdict = v['verdict']
        verdict_icons = {
            'pass': '✅ PASS',
            'revise': '⚠️ REVISE',
            'fail': '❌ FAIL'
        }
        print(f"   判定：{verdict_icons.get(verdict, verdict)}")
        
        # 成功技法
        if v['target_met'] and v['target_met'].get('matched'):
            print(f"\n✅ 成功应用的技法：")
            for t in list(v['target_met']['matched'])[:5]:
                print(f"   • {t}")
        
        # 缺失技法
        if v['target_met'] and v['target_met'].get('missing'):
            print(f"\n❌ 缺失技法（建议增加）：")
            for t in list(v['target_met']['missing'])[:3]:
                print(f"   • {t}")
        
        # 改进建议
        if v['improvements']:
            print(f"\n🔧 改进建议：")
            for imp in v['improvements']:
                print(f"   • {imp}")
        
        print(f"\n📝 总结：{v['summary']}")
        print("\n" + "=" * 70)
    
    def cmd_full(self, args):
        """完整章节生成：生成全部5个节拍"""
        beats = [
            ("场景建立", 800),
            ("触发事件", 600),
            ("情节推进", 1600),
            ("高潮发现", 1200),
            ("收尾悬念", 600)
        ]
        
        print("=" * 70)
        print("🎬 完整章节生成流程")
        print("=" * 70)
        print(f"\n章节：第1章 - 青铜之光")
        print(f"场景：{args.scene}")
        print(f"风格：{args.style}")
        print(f"预计总字数：4800字")
        print(f"\n将生成以下{len(beats)}个节拍：")
        for i, (beat, words) in enumerate(beats, 1):
            print(f"   {i}. {beat}（{words}字）")
        
        print("\n" + "=" * 70)
        
        for i, (beat, words) in enumerate(beats, 1):
            print(f"\n{'='*70}")
            print(f"🎬 节拍{i}：{beat}（{words}字）")
            print("=" * 70)
            
            # 更新参数
            args.beat = beat
            args.words = words
            
            # 执行该节拍的完整流程
            self.cmd_generate(args)
        
        print("\n" + "=" * 70)
        print("✅ 完整章节生成流程结束！")
        print("=" * 70)


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description='NC + Inkcore + AI 协作 CLI 工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 获取策划建议
  python nc-inkcore-cli.py plan --scene "博物馆" --beat "场景建立"
  
  # 完整生成流程
  python nc-inkcore-cli.py generate --scene "博物馆" --beat "场景建立"
  
  # 验证已有内容
  python nc-inkcore-cli.py verify --file chapter.txt --scene "博物馆"
  
  # 生成完整章节（5个节拍）
  python nc-inkcore-cli.py full --scene "博物馆修复室"
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # plan 命令
    plan_parser = subparsers.add_parser('plan', help='获取策划建议')
    plan_parser.add_argument('--scene', '-s', required=True, help='场景类型')
    plan_parser.add_argument('--beat', '-b', required=True, 
                            choices=['场景建立', '触发事件', '情节推进', '高潮发现', '收尾悬念'],
                            help='节拍类型')
    plan_parser.add_argument('--words', '-w', type=int, default=1000, help='目标字数')
    plan_parser.add_argument('--style', default='默认', 
                            choices=['默认', '猫腻', '烽火', '土豆'],
                            help='小说风格')
    
    # generate 命令
    gen_parser = subparsers.add_parser('generate', help='完整生成流程')
    gen_parser.add_argument('--scene', '-s', required=True, help='场景类型')
    gen_parser.add_argument('--beat', '-b', required=True,
                           choices=['场景建立', '触发事件', '情节推进', '高潮发现', '收尾悬念'],
                           help='节拍类型')
    gen_parser.add_argument('--words', '-w', type=int, default=1000, help='目标字数')
    gen_parser.add_argument('--style', default='默认',
                           choices=['默认', '猫腻', '烽火', '土豆'],
                           help='小说风格')
    gen_parser.add_argument('--output', '-o', help='输出文件路径（用于后续验证）')
    
    # verify 命令
    verify_parser = subparsers.add_parser('verify', help='验证已有内容')
    verify_parser.add_argument('--file', '-f', required=True, help='要验证的文件')
    verify_parser.add_argument('--scene', '-s', default='默认场景', help='场景类型')
    verify_parser.add_argument('--beat', '-b', default='场景建立',
                              choices=['场景建立', '触发事件', '情节推进', '高潮发现', '收尾悬念'],
                              help='节拍类型')
    verify_parser.add_argument('--words', '-w', type=int, default=1000, help='目标字数')
    verify_parser.add_argument('--style', default='默认', help='小说风格')
    
    # full 命令
    full_parser = subparsers.add_parser('full', help='生成完整章节（5个节拍）')
    full_parser.add_argument('--scene', '-s', required=True, help='场景类型')
    full_parser.add_argument('--style', default='默认',
                            choices=['默认', '猫腻', '烽火', '土豆'],
                            help='小说风格')
    full_parser.add_argument('--output', '-o', help='输出目录')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = NCInkcoreCLI()
    
    if args.command == 'plan':
        cli.cmd_plan(args)
    elif args.command == 'generate':
        cli.cmd_generate(args)
    elif args.command == 'verify':
        cli.cmd_verify(args)
    elif args.command == 'full':
        cli.cmd_full(args)


if __name__ == '__main__':
    main()
