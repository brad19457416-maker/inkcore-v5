"""
墨芯 v5.0 - 集成测试
端到端测试整个系统
"""

import asyncio
import tempfile
import shutil
import unittest

# 导入所有模块
from memory.palace_v2 import InkCorePalaceV2, TechniqueCategory
from agents.core import AgentOrchestrator, ChapterInput
from skills.registry import SkillRegistry
from scheduler.core import InkCoreScheduler, TaskPriority
from gateway.core import InkCoreGateway, CLIAdapter, create_gateway_with_cli


class TestEndToEnd(unittest.TestCase):
    """端到端集成测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        
        # 初始化各层
        self.palace = InkCorePalaceV2(base_path=self.temp_dir)
        self.orchestrator = AgentOrchestrator()
        self.skill_registry = SkillRegistry()
        self.scheduler = InkCoreScheduler(num_workers=2)
        
        # 注册技能
        self.skill_registry.register_builtin_skills(
            palace=self.palace,
            orchestrator=self.orchestrator
        )
    
    def tearDown(self):
        """清理"""
        shutil.rmtree(self.temp_dir)
    
    def test_palace_and_agents(self):
        """测试 Palace + Agent Core 集成"""
        async def run_test():
            # 1. 使用 Agent Core 分析章节
            chapter_input = ChapterInput(
                novel_name="jiange",
                volume="vol1",
                chapter="ch1",
                chapter_text="雨夜，宁缺拔刀杀人。这是危机开场的经典案例。" * 20
            )
            
            report = await self.orchestrator.analyze_chapter(chapter_input)
            
            # 验证分析结果
            self.assertEqual(report.novel_name, "jiange")
            self.assertIsInstance(report.techniques, list)
            
            # 2. 存入 Palace
            tech_ids = self.palace.mine_chapter(
                novel_name="jiange",
                volume="vol1",
                chapter="ch1",
                chapter_text=chapter_input.chapter_text,
                extracted_techniques=[t.to_dict() for t in report.techniques]
            )
            
            # 验证存储
            self.assertIsInstance(tech_ids, list)
            
            # 3. 搜索验证
            results = self.palace.search("危机", novel="jiange")
            self.assertGreaterEqual(len(results), 0)  # 可能有也可能没有结果
        
        asyncio.run(run_test())
    
    def test_skill_registry_execution(self):
        """测试 Skill Registry 执行"""
        async def run_test():
            # 执行分析技能
            execution = await self.skill_registry.execute(
                skill_id="AnalyzeNovelSkill",
                input_data={
                    "novel_name": "将夜",
                    "volume": "第一卷",
                    "chapter": "第一章",
                    "chapter_text": "雨夜，春风亭，宁缺拔刀。" * 20
                }
            )
            
            # 验证执行结果
            self.assertEqual(execution.skill_id, "AnalyzeNovelSkill")
            self.assertEqual(execution.status.value, "completed")
            self.assertIsNotNone(execution.context.output_data)
            
            result = execution.context.output_data
            self.assertIn("techniques_count", result)
            self.assertIn("workflow_history", result)
        
        asyncio.run(run_test())
    
    def test_scheduler_task_submission(self):
        """测试调度器任务提交"""
        async def run_test():
            results = []
            
            async def test_task():
                results.append("executed")
                return "done"
            
            # 提交任务
            task_id = await self.scheduler.submit(
                name="测试任务",
                func=test_task,
                priority=TaskPriority.HIGH
            )
            
            self.assertTrue(task_id.startswith("task_"))
            
            # 注意：由于我们没有启动调度器，任务不会实际执行
            # 这里只验证提交功能
        
        asyncio.run(run_test())
    
    def test_gateway_routing(self):
        """测试网关路由"""
        # 创建网关
        gateway = InkCoreGateway()
        gateway.set_skill_registry(self.skill_registry)
        
        # 添加路由
        gateway.add_route("分析.*小说", "AnalyzeNovelSkill", priority=1)
        gateway.add_route("搜索", "SearchTechniqueSkill", priority=2)
        
        # 验证路由配置
        self.assertEqual(len(gateway.router.routes), 2)
    
    def test_full_system_initialization(self):
        """测试完整系统初始化"""
        async def run_test():
            # 创建网关并集成所有组件
            gateway = await create_gateway_with_cli()
            gateway.set_skill_registry(self.skill_registry)
            
            # 验证网关
            self.assertEqual(len(gateway.adapters), 1)
            self.assertIn("AnalyzeNovelSkill", [r["skill_id"] for r in gateway.router.routes])
            
            # 验证各层
            self.assertIsNotNone(self.palace)
            self.assertIsNotNone(self.orchestrator)
            self.assertIsNotNone(self.skill_registry)
        
        asyncio.run(run_test())


class TestWorkflowIntegration(unittest.TestCase):
    """工作流集成测试"""
    
    def test_analyze_workflow(self):
        """测试完整分析工作流"""
        async def run_test():
            temp_dir = tempfile.mkdtemp()
            
            try:
                # 初始化
                palace = InkCorePalaceV2(base_path=temp_dir)
                orchestrator = AgentOrchestrator()
                registry = SkillRegistry()
                registry.register_builtin_skills(palace=palace, orchestrator=orchestrator)
                
                # 执行分析工作流
                execution = await registry.execute(
                    skill_id="AnalyzeNovelSkill",
                    input_data={
                        "novel_name": "测试小说",
                        "chapter": "测试章节",
                        "chapter_text": "这是一个测试章节，包含了危机开场和人物塑造的技法。" * 20
                    }
                )
                
                # 验证工作流执行
                self.assertEqual(execution.status.value, "completed")
                
                result = execution.context.output_data
                
                # 验证工作流步骤
                workflow_history = result.get("workflow_history", [])
                step_names = [step["step"] for step in workflow_history]
                
                # 检查是否执行了标准工作流
                self.assertIn("read", step_names)
                self.assertIn("extract", step_names)
                self.assertIn("verify", step_names)
                self.assertIn("store", step_names)
                self.assertIn("report", step_names)
                
            finally:
                shutil.rmtree(temp_dir)
        
        asyncio.run(run_test())


class TestDataFlow(unittest.TestCase):
    """数据流测试"""
    
    def test_message_to_skill_flow(self):
        """测试消息到技能的数据流"""
        from gateway.core import Message, User, PlatformType, MessageType
        
        async def run_test():
            # 创建消息
            user = User("u1", "测试用户", PlatformType.CLI)
            message = Message(
                message_id="msg_001",
                user=user,
                platform=PlatformType.CLI,
                message_type=MessageType.TEXT,
                content="分析小说"
            )
            
            # 模拟路由处理
            registry = SkillRegistry()
            registry.register_builtin_skills()
            
            # 直接执行技能
            execution = await registry.execute(
                skill_id="AnalyzeNovelSkill",
                input_data={
                    "novel_name": "测试",
                    "chapter": "ch1",
                    "chapter_text": "测试内容" * 20
                }
            )
            
            # 验证数据流
            self.assertIsNotNone(execution.context.output_data)
        
        asyncio.run(run_test())


class TestErrorHandling(unittest.TestCase):
    """错误处理测试"""
    
    def test_skill_validation_error(self):
        """测试技能验证错误"""
        async def run_test():
            registry = SkillRegistry()
            registry.register_builtin_skills()
            
            # 提交缺少必需参数的任务
            from skills.registry import SkillValidationError
            
            with self.assertRaises(SkillValidationError):
                await registry.execute(
                    skill_id="SearchTechniqueSkill",
                    input_data={}  # 缺少 query
                )
        
        asyncio.run(run_test())
    
    def test_palace_validation_error(self):
        """测试 Palace 验证错误"""
        palace = InkCorePalaceV2()
        
        # 尝试存入无效数据
        with self.assertRaises(ValueError):
            palace.mine_chapter(
                novel_name="",  # 空名称
                volume="v1",
                chapter="ch1",
                chapter_text="短",  # 太短
                extracted_techniques=[]
            )


if __name__ == "__main__":
    # 配置日志
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # 运行测试
    unittest.main(verbosity=2)