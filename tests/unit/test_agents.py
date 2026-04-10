"""
墨芯 v5.0 - Agent Core 单元测试
"""

import asyncio
import unittest

from agents.core import (
    AgentOrchestrator,
    ReadAgent,
    CharacterAgent,
    PlotAgent,
    PacingAgent,
    CatharsisAgent,
    VerifyAgent,
    ReportAgent,
    AgentTask,
    ChapterInput,
    AgentStatus,
    ExtractionDomain
)


class TestReadAgent(unittest.TestCase):
    """测试 ReadAgent"""
    
    def setUp(self):
        self.agent = ReadAgent()
    
    def test_tokenize(self):
        """测试分词"""
        text = "宁缺拔刀。桑桑看着。"
        tokens = self.agent._tokenize(text)
        self.assertGreater(len(tokens), 0)
    
    def test_segment_paragraphs(self):
        """测试分段"""
        text = "第一段\n\n第二段\n\n第三段"
        paragraphs = self.agent._segment_paragraphs(text)
        self.assertEqual(len(paragraphs), 3)
    
    def test_extract_character_mentions(self):
        """测试角色提及提取"""
        text = "宁缺和桑桑在春风亭。"
        mentions = self.agent._extract_character_mentions(text)
        self.assertIn("宁缺", mentions)
        self.assertIn("桑桑", mentions)
    
    def test_async_execute(self):
        """测试异步执行"""
        async def run_test():
            task = AgentTask(
                task_id="test_read",
                agent_type="read_agent",
                input_data={
                    "chapter_text": "宁缺站在春风亭边，雨夜中拔刀杀人。桑桑在旁边看着。" * 10
                }
            )
            
            result = await self.agent.execute(task)
            
            self.assertIn("word_count", result)
            self.assertIn("paragraph_count", result)
            self.assertIn("characters_mentioned", result)
            self.assertIn("宁缺", result["characters_mentioned"])
        
        asyncio.run(run_test())


class TestExtractAgents(unittest.TestCase):
    """测试提取 Agents"""
    
    def test_character_agent(self):
        """测试 CharacterAgent"""
        async def run_test():
            agent = CharacterAgent()
            task = AgentTask(
                task_id="test_character",
                agent_type="character_agent",
                input_data={
                    "chapter_text": "据说那个叫宁缺的人很强。他冷笑一声，拔刀而出。" * 5,
                    "scenes": []
                }
            )
            
            result = await agent.execute(task)
            
            self.assertEqual(result["domain"], "character")
            self.assertIn("techniques", result)
            self.assertGreaterEqual(result["count"], 0)
        
        asyncio.run(run_test())
    
    def test_plot_agent(self):
        """测试 PlotAgent"""
        async def run_test():
            agent = PlotAgent()
            task = AgentTask(
                task_id="test_plot",
                agent_type="plot_agent",
                input_data={
                    "chapter_text": "雨夜，追杀，生死危机！为什么他会在这里？" * 5
                }
            )
            
            result = await agent.execute(task)
            
            self.assertEqual(result["domain"], "plot")
            self.assertIn("techniques", result)
        
        asyncio.run(run_test())
    
    def test_pacing_agent(self):
        """测试 PacingAgent"""
        async def run_test():
            agent = PacingAgent()
            task = AgentTask(
                task_id="test_pacing",
                agent_type="pacing_agent",
                input_data={
                    "chapter_text": "刀光剑影！闪！躲！杀！然后坐下来喝茶，慢慢思考。" * 5
                }
            )
            
            result = await agent.execute(task)
            
            self.assertEqual(result["domain"], "pacing")
            self.assertIn("techniques", result)
        
        asyncio.run(run_test())
    
    def test_catharsis_agent(self):
        """测试 CatharsisAgent"""
        async def run_test():
            agent = CatharsisAgent()
            task = AgentTask(
                task_id="test_catharsis",
                agent_type="catharsis_agent",
                input_data={
                    "chapter_text": "你这种蝼蚁也敢挑战我？他冷笑。然后被一招击败，震惊！" * 5
                }
            )
            
            result = await agent.execute(task)
            
            self.assertEqual(result["domain"], "catharsis")
            self.assertIn("techniques", result)
        
        asyncio.run(run_test())


class TestVerifyAgent(unittest.TestCase):
    """测试 VerifyAgent"""
    
    def setUp(self):
        self.agent = VerifyAgent()
    
    def test_verify_single_valid(self):
        """测试验证有效技法"""
        technique = {
            "name": "测试技法",
            "category": "plot",
            "example": "宁缺拔刀",
            "analysis": {
                "definition": "定义",
                "scenario": "场景",
                "effect": "效果",
                "applicability": "适用"
            },
            "confidence": 0.9
        }
        
        original_text = "宁缺拔刀杀人。"
        result = self.agent._verify_single(technique, original_text)
        
        self.assertTrue(result["valid"])
    
    def test_verify_single_invalid(self):
        """测试验证无效技法"""
        technique = {
            "name": "",
            "category": "plot",
            "example": "",
            "analysis": {},
            "confidence": 0.3
        }
        
        original_text = "原文内容"
        result = self.agent._verify_single(technique, original_text)
        
        self.assertFalse(result["valid"])
    
    def test_deduplicate(self):
        """测试去重"""
        techniques = [
            {"name": "技法A"},
            {"name": "技法B"},
            {"name": "技法A"},  # 重复
        ]
        
        result = self.agent._deduplicate(techniques)
        
        self.assertEqual(len(result), 2)
    
    def test_async_execute(self):
        """测试异步执行验证"""
        async def run_test():
            task = AgentTask(
                task_id="test_verify",
                agent_type="verify_agent",
                input_data={
                    "raw_techniques": [
                        {
                            "name": "有效技法",
                            "category": "plot",
                            "example": "宁缺拔刀",
                            "analysis": {
                                "definition": "定义",
                                "scenario": "场景",
                                "effect": "效果",
                                "applicability": "适用"
                            },
                            "confidence": 0.9
                        },
                        {
                            "name": "",
                            "category": "plot",
                            "example": "",
                            "analysis": {},
                            "confidence": 0.3
                        }
                    ],
                    "chapter_text": "宁缺拔刀杀人。"
                }
            )
            
            result = await self.agent.execute(task)
            
            self.assertIn("verified_count", result)
            self.assertIn("rejected_count", result)
            self.assertIn("quality_score", result)
        
        asyncio.run(run_test())


class TestReportAgent(unittest.TestCase):
    """测试 ReportAgent"""
    
    def setUp(self):
        self.agent = ReportAgent()
    
    def test_categorize(self):
        """测试分类"""
        techniques = [
            {"name": "技法1", "category": "plot"},
            {"name": "技法2", "category": "plot"},
            {"name": "技法3", "category": "character"}
        ]
        
        result = self.agent._categorize(techniques)
        
        self.assertEqual(len(result["plot"]), 2)
        self.assertEqual(len(result["character"]), 1)
    
    def test_generate_markdown(self):
        """测试生成 Markdown"""
        techniques = [
            {
                "name": "危机开场",
                "category": "plot",
                "example": "雨夜杀人",
                "analysis": {
                    "definition": "定义",
                    "scenario": "场景",
                    "effect": "效果",
                    "applicability": "适用"
                }
            }
        ]
        
        report = self.agent._generate_markdown(
            "将夜", "第一卷", "第一章",
            techniques, {"plot": techniques}
        )
        
        self.assertIn("将夜", report)
        self.assertIn("危机开场", report)
        self.assertIn("#", report)  # Markdown 标题
    
    def test_async_execute(self):
        """测试异步执行报告生成"""
        async def run_test():
            task = AgentTask(
                task_id="test_report",
                agent_type="report_agent",
                input_data={
                    "novel_name": "将夜",
                    "volume": "第一卷",
                    "chapter": "第一章",
                    "techniques": [
                        {
                            "name": "技法1",
                            "category": "plot",
                            "example": "示例",
                            "analysis": {"definition": "定义"}
                        }
                    ]
                }
            )
            
            result = await self.agent.execute(task)
            
            self.assertEqual(result["format"], "markdown")
            self.assertIn("summary", result)
            self.assertIn("report", result)
            self.assertIn("stats", result)
        
        asyncio.run(run_test())


class TestAgentOrchestrator(unittest.TestCase):
    """测试 AgentOrchestrator"""
    
    def setUp(self):
        self.orchestrator = AgentOrchestrator()
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.orchestrator.read_agent)
        self.assertIsNotNone(self.orchestrator.character_agent)
        self.assertIsNotNone(self.orchestrator.plot_agent)
        self.assertIsNotNone(self.orchestrator.pacing_agent)
        self.assertIsNotNone(self.orchestrator.catharsis_agent)
        self.assertIsNotNone(self.orchestrator.verify_agent)
        self.assertIsNotNone(self.orchestrator.report_agent)
    
    def test_analyze_chapter(self):
        """测试完整分析流程"""
        async def run_test():
            chapter_input = ChapterInput(
                novel_name="将夜",
                volume="第一卷",
                chapter="第一章",
                chapter_text="""
                雨夜，春风亭。
                
                宁缺站在亭边，手中的刀在雨中闪着寒光。
                追杀他的人已经包围了这里，但他并不慌张。
                
                "你这种蝼蚁，也配用刀？" 敌人冷笑。
                
                宁缺没有回答，只是拔刀。
                刀光一闪，血溅五步。
                
                敌人震惊地看着自己的伤口，不敢置信。
                为什么？为什么这个无名小卒这么强？
                
                桑桑在旁边安静地站着，仿佛什么都没发生。
                """ * 5
            )
            
            report = await self.orchestrator.analyze_chapter(chapter_input)
            
            self.assertEqual(report.novel_name, "将夜")
            self.assertEqual(report.chapter, "第一章")
            self.assertIsInstance(report.techniques, list)
            self.assertIn("quality_score", report.metadata)
        
        asyncio.run(run_test())
    
    def test_get_stats(self):
        """测试获取统计"""
        stats = self.orchestrator.get_stats()
        
        self.assertIn("total_tasks", stats)
        self.assertIn("status_distribution", stats)


class TestAgentTask(unittest.TestCase):
    """测试 AgentTask"""
    
    def test_creation(self):
        """测试创建任务"""
        task = AgentTask(
            task_id="test_task",
            agent_type="read_agent",
            input_data={"key": "value"}
        )
        
        self.assertEqual(task.task_id, "test_task")
        self.assertEqual(task.agent_type, "read_agent")
        self.assertEqual(task.status, AgentStatus.PENDING)
    
    def test_to_dict(self):
        """测试转换为字典"""
        task = AgentTask(
            task_id="test_task",
            agent_type="read_agent",
            input_data={},
            status=AgentStatus.COMPLETED,
            result={"key": "value"}
        )
        
        data = task.to_dict()
        
        self.assertEqual(data["task_id"], "test_task")
        self.assertEqual(data["status"], "completed")
        self.assertEqual(data["result"], {"key": "value"})


if __name__ == "__main__":
    # 配置日志
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # 运行测试
    unittest.main(verbosity=2)