"""
墨芯 v5.0 - Skill System 单元测试
"""

import asyncio
import unittest

from skills.registry import (
    SkillRegistry,
    AnalyzeNovelSkill,
    SearchTechniqueSkill,
    CompareWorksSkill,
    SkillMetadata,
    SkillContext,
    SkillStatus,
    WorkflowStep,
    SkillValidationError,
    SkillNotFoundError
)


class TestSkillMetadata(unittest.TestCase):
    """测试 SkillMetadata"""
    
    def test_creation(self):
        """测试创建元数据"""
        meta = SkillMetadata(
            name="test_skill",
            description="测试技能",
            version="1.0.0",
            author="test",
            category="test",
            tags=["test", "demo"]
        )
        
        self.assertEqual(meta.name, "test_skill")
        self.assertEqual(meta.version, "1.0.0")
        self.assertIn("test", meta.tags)
    
    def test_to_dict(self):
        """测试转换为字典"""
        meta = SkillMetadata(
            name="test_skill",
            description="测试技能",
            version="1.0.0",
            author="test",
            category="test"
        )
        
        data = meta.to_dict()
        
        self.assertEqual(data["name"], "test_skill")
        self.assertEqual(data["version"], "1.0.0")


class TestSkillContext(unittest.TestCase):
    """测试 SkillContext"""
    
    def test_get_set(self):
        """测试获取和设置"""
        context = SkillContext(
            skill_id="test",
            input_data={"key1": "value1"}
        )
        
        # 从 input_data 获取
        self.assertEqual(context.get("key1"), "value1")
        
        # 设置新值
        context.set("key2", "value2")
        self.assertEqual(context.get("key2"), "value2")
        
        # 默认值
        self.assertEqual(context.get("nonexistent", "default"), "default")


class TestAnalyzeNovelSkill(unittest.TestCase):
    """测试 AnalyzeNovelSkill"""
    
    def setUp(self):
        self.skill = AnalyzeNovelSkill()
    
    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.skill.skill_id, "analyze_novel")
        self.assertEqual(self.skill.metadata.name, "analyze_novel")
    
    def test_simple_extract(self):
        """测试简化提取"""
        text = "雨夜，宁缺拔刀杀人。" * 10
        
        result = asyncio.run(self._run_simple_extract(text))
        
        self.assertIn("techniques", result)
        self.assertGreaterEqual(len(result["techniques"]), 1)
    
    async def _run_simple_extract(self, text):
        return await self.skill._simple_extract(text)
    
    def test_verify_techniques(self):
        """测试验证技法"""
        raw_result = {
            "techniques": [
                {
                    "name": "有效技法",
                    "category": "plot",
                    "example": "示例",
                    "analysis": {},
                    "confidence": 0.9
                },
                {
                    "name": "",
                    "category": "plot",
                    "confidence": 0.3
                }
            ]
        }
        
        result = self.skill._verify_techniques(raw_result, "原文")
        
        self.assertEqual(len(result["techniques"]), 1)
    
    def test_async_execute(self):
        """测试异步执行"""
        async def run_test():
            context = SkillContext(
                skill_id="analyze_novel",
                input_data={
                    "novel_name": "将夜",
                    "volume": "第一卷",
                    "chapter": "第一章",
                    "chapter_text": "雨夜，宁缺拔刀杀人。" * 20
                }
            )
            
            result = await self.skill.execute(context)
            
            self.assertIn("techniques_count", result)
            self.assertIn("techniques", result)
            self.assertIn("workflow_history", result)
        
        asyncio.run(run_test())


class TestSearchTechniqueSkill(unittest.TestCase):
    """测试 SearchTechniqueSkill"""
    
    def setUp(self):
        self.skill = SearchTechniqueSkill()
    
    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.skill.metadata.name, "search_technique")
    
    def test_execute_without_palace(self):
        """测试无 Palace 时执行"""
        async def run_test():
            context = SkillContext(
                skill_id="search_technique",
                input_data={
                    "query": "危机开场",
                    "novel": "将夜"
                }
            )
            
            result = await self.skill.execute(context)
            
            self.assertEqual(result["query"], "危机开场")
            self.assertEqual(result["results_count"], 0)
        
        asyncio.run(run_test())
    
    def test_validation_error(self):
        """测试验证错误"""
        async def run_test():
            context = SkillContext(
                skill_id="search_technique",
                input_data={}  # 缺少 query
            )
            
            with self.assertRaises(SkillValidationError):
                await self.skill.execute(context)
        
        asyncio.run(run_test())


class TestCompareWorksSkill(unittest.TestCase):
    """测试 CompareWorksSkill"""
    
    def setUp(self):
        self.skill = CompareWorksSkill()
    
    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.skill.metadata.name, "compare_works")
    
    def test_validation_error(self):
        """测试验证错误（少于2部作品）"""
        async def run_test():
            context = SkillContext(
                skill_id="compare_works",
                input_data={
                    "novels": ["将夜"]  # 只有1部
                }
            )
            
            with self.assertRaises(SkillValidationError):
                await self.skill.execute(context)
        
        asyncio.run(run_test())


class TestSkillRegistry(unittest.TestCase):
    """测试 SkillRegistry"""
    
    def setUp(self):
        self.registry = SkillRegistry()
    
    def test_register_builtin(self):
        """测试注册内置技能"""
        self.registry.register_builtin_skills()
        
        skills = self.registry.list_skills()
        
        self.assertIn("AnalyzeNovelSkill", skills)
        self.assertIn("SearchTechniqueSkill", skills)
        self.assertIn("CompareWorksSkill", skills)
    
    def test_get_skill(self):
        """测试获取技能"""
        self.registry.register_builtin_skills()
        
        skill = self.registry.get("AnalyzeNovelSkill")
        
        self.assertIsNotNone(skill)
        self.assertIsInstance(skill, AnalyzeNovelSkill)
    
    def test_get_nonexistent_skill(self):
        """测试获取不存在的技能"""
        skill = self.registry.get("NonexistentSkill")
        
        self.assertIsNone(skill)
    
    def test_list_by_category(self):
        """测试按类别列出技能"""
        self.registry.register_builtin_skills()
        
        analysis_skills = self.registry.list_skills(category="analysis")
        query_skills = self.registry.list_skills(category="query")
        
        self.assertIn("AnalyzeNovelSkill", analysis_skills)
        self.assertIn("CompareWorksSkill", analysis_skills)
        self.assertIn("SearchTechniqueSkill", query_skills)
    
    def test_list_by_tag(self):
        """测试按标签列出技能"""
        self.registry.register_builtin_skills()
        
        skills = self.registry.list_skills(tag="analysis")
        
        self.assertIn("AnalyzeNovelSkill", skills)
    
    def test_execute_skill(self):
        """测试执行技能"""
        async def run_test():
            self.registry.register_builtin_skills()
            
            execution = await self.registry.execute(
                skill_id="AnalyzeNovelSkill",
                input_data={
                    "novel_name": "将夜",
                    "chapter": "第一章",
                    "chapter_text": "雨夜，宁缺拔刀。" * 20
                }
            )
            
            self.assertEqual(execution.skill_id, "AnalyzeNovelSkill")
            self.assertEqual(execution.status, SkillStatus.COMPLETED)
            self.assertIsNotNone(execution.context.output_data)
        
        asyncio.run(run_test())
    
    def test_execute_nonexistent_skill(self):
        """测试执行不存在的技能"""
        async def run_test():
            with self.assertRaises(SkillNotFoundError):
                await self.registry.execute(
                    skill_id="NonexistentSkill",
                    input_data={}
                )
        
        asyncio.run(run_test())
    
    def test_get_execution_history(self):
        """测试获取执行历史"""
        async def run_test():
            self.registry.register_builtin_skills()
            
            # 执行一个技能
            await self.registry.execute(
                skill_id="SearchTechniqueSkill",
                input_data={"query": "测试"}
            )
            
            # 获取历史
            history = self.registry.get_execution_history()
            
            self.assertEqual(len(history), 1)
        
        asyncio.run(run_test())


class TestWorkflowStep(unittest.TestCase):
    """测试 WorkflowStep"""
    
    def test_steps(self):
        """测试工作流步骤"""
        self.assertEqual(WorkflowStep.READ.value, "read")
        self.assertEqual(WorkflowStep.EXTRACT.value, "extract")
        self.assertEqual(WorkflowStep.VERIFY.value, "verify")
        self.assertEqual(WorkflowStep.STORE.value, "store")
        self.assertEqual(WorkflowStep.REPORT.value, "report")


if __name__ == "__main__":
    # 配置日志
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # 运行测试
    unittest.main(verbosity=2)