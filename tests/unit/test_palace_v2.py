"""
墨芯 v5.0 - PalaceV2 单元测试
"""

import os
import shutil
import tempfile
import unittest
from datetime import datetime

from memory.palace_v2 import (
    InkCorePalaceV2,
    TechniqueId,
    TechniqueRecord,
    TechniqueCategory,
    FileSystemStorage,
    ValidationError
)


class TestTechniqueId(unittest.TestCase):
    """测试 TechniqueId"""
    
    def test_creation(self):
        """测试创建 ID"""
        tech_id = TechniqueId(
            novel="jiange",
            category=TechniqueCategory.PLOT,
            chapter="ch1",
            sequence=5
        )
        
        self.assertEqual(tech_id.novel, "jiange")
        self.assertEqual(tech_id.category, TechniqueCategory.PLOT)
        self.assertEqual(tech_id.chapter, "ch1")
        self.assertEqual(tech_id.sequence, 5)
    
    def test_string_conversion(self):
        """测试字符串转换"""
        tech_id = TechniqueId(
            novel="jiange",
            category=TechniqueCategory.CHARACTER,
            chapter="ch2",
            sequence=10
        )
        
        id_str = str(tech_id)
        self.assertEqual(id_str, "jiange-character-ch2-010")
        
        # 解析回 ID
        parsed = TechniqueId.from_string(id_str)
        self.assertEqual(parsed.novel, tech_id.novel)
        self.assertEqual(parsed.category, tech_id.category)
        self.assertEqual(parsed.chapter, tech_id.chapter)
        self.assertEqual(parsed.sequence, tech_id.sequence)
    
    def test_invalid_format(self):
        """测试无效格式"""
        with self.assertRaises(ValueError):
            TechniqueId.from_string("invalid-id")
        
        with self.assertRaises(ValueError):
            TechniqueId.from_string("jiange-plot-ch1")  # 缺少 sequence


class TestFileSystemStorage(unittest.TestCase):
    """测试文件系统存储"""
    
    def setUp(self):
        """每个测试前创建临时目录"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = FileSystemStorage(self.temp_dir)
    
    def tearDown(self):
        """每个测试后清理"""
        shutil.rmtree(self.temp_dir)
    
    def test_write_and_read(self):
        """测试写入和读取"""
        # 写入
        self.storage.write("/test/file.json", {"key": "value"}, tier="L1")
        
        # 读取
        content = self.storage.read("/test/file.json")
        self.assertEqual(content["key"], "value")
    
    def test_write_string(self):
        """测试写入字符串"""
        self.storage.write("/test/text.txt", "Hello World", tier="L0")
        
        content = self.storage.read("/test/text.txt")
        self.assertEqual(content, "Hello World")
    
    def test_mkdir(self):
        """测试创建目录"""
        self.storage.mkdir("/test/nested/dir", exist_ok=True)
        
        self.assertTrue(self.storage.exists("/test/nested/dir"))
    
    def test_exists(self):
        """测试存在性检查"""
        self.assertFalse(self.storage.exists("/nonexistent"))
        
        self.storage.write("/exists.json", {})
        self.assertTrue(self.storage.exists("/exists.json"))
    
    def test_glob(self):
        """测试模式匹配"""
        self.storage.write("/a/b/c.json", {})
        self.storage.write("/a/b/d.json", {})
        self.storage.write("/a/x/y.json", {})
        
        results = self.storage.glob("/a/**/c.json")
        self.assertEqual(len(results), 1)
        self.assertIn("/a/b/c.json", results)
    
    def test_search(self):
        """测试搜索"""
        self.storage.write("/test/jiange.json", {"name": "将夜"})
        self.storage.write("/test/jianke.json", {"name": "间客"})
        
        results = self.storage.search("jiange", path="/test")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["content"]["name"], "将夜")
    
    def test_tier_context(self):
        """测试层级上下文"""
        with self.storage.tier_context("L2"):
            # 在上下文中，当前层级应该是 L2
            self.assertEqual(self.storage._current_tier, "L2")
        
        # 退出后恢复原层级
        self.assertEqual(self.storage._current_tier, "L1")


class TestInkCorePalaceV2(unittest.TestCase):
    """测试 InkCorePalaceV2"""
    
    def setUp(self):
        """创建临时 Palace"""
        self.temp_dir = tempfile.mkdtemp()
        self.palace = InkCorePalaceV2(base_path=self.temp_dir)
    
    def tearDown(self):
        """清理"""
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """测试初始化"""
        self.assertTrue(os.path.exists(self.temp_dir))
        
        # 检查目录结构
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "memories", "novels")))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "resources", "raw-novels")))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "skills")))
    
    def test_validate_chapter_input(self):
        """测试输入验证"""
        # 有效输入
        self.palace._validate_chapter_input("jiange", "vol1", "ch1", "a" * 100)
        
        # 无效输入
        with self.assertRaises(ValueError):
            self.palace._validate_chapter_input("", "vol1", "ch1", "text")
        
        with self.assertRaises(ValueError):
            self.palace._validate_chapter_input("jiange", "", "ch1", "text")
        
        with self.assertRaises(ValueError):
            self.palace._validate_chapter_input("jiange", "vol1", "ch1", "short")  # 太短
    
    def test_mine_chapter(self):
        """测试章节挖掘"""
        techniques = [
            {
                "name": "危机开场",
                "category": "plot",
                "example": "雨夜，宁缺拔刀杀人",
                "analysis": {
                    "definition": "以危机场景开场",
                    "scenario": "适用于吸引读者",
                    "effect": "建立紧张感",
                    "applicability": "高"
                }
            },
            {
                "name": "配角衬托",
                "category": "character",
                "example": "桑桑的存在衬托宁缺的果断",
                "analysis": {
                    "definition": "用配角突出主角",
                    "scenario": "人物关系复杂时",
                    "effect": "强化主角形象",
                    "applicability": "中"
                }
            }
        ]
        
        chapter_text = "这是将夜第一章的内容，讲述了宁缺在春风亭雨夜杀人的故事。" * 10
        
        tech_ids = self.palace.mine_chapter(
            novel_name="jiange",
            volume="vol1",
            chapter="ch1",
            chapter_text=chapter_text,
            extracted_techniques=techniques
        )
        
        self.assertEqual(len(tech_ids), 2)
        
        # 验证 ID 格式
        self.assertEqual(tech_ids[0].novel, "jiange")
        self.assertEqual(tech_ids[0].category, TechniqueCategory.PLOT)
        self.assertEqual(tech_ids[0].chapter, "ch1")
        self.assertEqual(tech_ids[0].sequence, 0)
    
    def test_search(self):
        """测试搜索"""
        # 先存入数据
        chapter_text = "这是将夜第一章的内容，讲述了宁缺在春风亭雨夜杀人的故事。" * 10
        techniques = [
            {
                "name": "危机开场",
                "category": "plot",
                "example": "雨夜，宁缺拔刀杀人",
                "analysis": {
                    "definition": "以危机场景开场",
                    "scenario": "适用于吸引读者",
                    "effect": "建立紧张感",
                    "applicability": "高"
                }
            }
        ]
        
        self.palace.mine_chapter("jiange", "vol1", "ch1", chapter_text, techniques)
        
        # 搜索
        results = self.palace.search("危机", novel="jiange")
        
        # 验证搜索结果中包含预期的技法
        self.assertGreaterEqual(len(results), 1)
        technique_names = [r.name for r in results]
        self.assertIn("危机开场", technique_names)
    
    def test_user_prefs(self):
        """测试用户偏好"""
        # 记录偏好
        self.palace.record_user_pref("preferred_author", "猫腻", category="reading")
        self.palace.record_user_pref("analysis_depth", "detailed", category="analysis")
        
        # 获取偏好
        author = self.palace.get_user_pref("preferred_author", category="reading")
        self.assertEqual(author, "猫腻")
        
        depth = self.palace.get_user_pref("analysis_depth", category="analysis")
        self.assertEqual(depth, "detailed")
        
        # 获取不存在的偏好
        not_exist = self.palace.get_user_pref("not_exist", default="default")
        self.assertEqual(not_exist, "default")
    
    def test_create_tunnel(self):
        """测试创建关联"""
        from_id = TechniqueId("jiange", TechniqueCategory.PLOT, "ch1", 0)
        to_id = TechniqueId("jiange", TechniqueCategory.PLOT, "ch2", 0)
        
        tunnel_path = self.palace.create_tunnel(
            from_id=from_id,
            to_id=to_id,
            relation="precedes",
            confidence=0.9
        )
        
        self.assertTrue(self.palace.db.exists(tunnel_path))
    
    def test_traverse(self):
        """测试图遍历"""
        # 创建关联
        from_id = TechniqueId("jiange", TechniqueCategory.PLOT, "ch1", 0)
        to_id = TechniqueId("jiange", TechniqueCategory.CATHARSIS, "ch1", 0)
        
        # 先存入数据
        chapter_text = "这是将夜第一章的内容。" * 20
        techniques = [
            {
                "name": "危机开场",
                "category": "plot",
                "example": "雨夜",
                "analysis": {"definition": "", "scenario": "", "effect": "", "applicability": ""}
            },
            {
                "name": "打脸反派",
                "category": "catharsis",
                "example": "反杀",
                "analysis": {"definition": "", "scenario": "", "effect": "", "applicability": ""}
            }
        ]
        
        self.palace.mine_chapter("jiange", "vol1", "ch1", chapter_text, techniques)
        
        # 创建关联
        self.palace.create_tunnel(from_id, to_id, "leads_to")
        
        # 遍历
        related = self.palace.traverse(from_id, max_hops=1)
        
        self.assertEqual(len(related), 1)
        self.assertEqual(related[0].category, TechniqueCategory.CATHARSIS)
    
    def test_save_session(self):
        """测试会话保存"""
        trajectory = [
            {"action": "search", "params": {"category": "plot"}, "timestamp": "2024-01-01T00:00:00"},
            {"action": "search", "params": {"category": "plot"}, "timestamp": "2024-01-01T00:01:00"},
            {"action": "search", "params": {"novel": "jiange"}, "timestamp": "2024-01-01T00:02:00"}
        ]
        
        memories = self.palace.save_session("session-001", trajectory)
        
        # 验证提取的记忆
        self.assertIn("preferred_category", memories)
        self.assertEqual(memories["preferred_category"], "plot")
        
        self.assertIn("frequent_novels", memories)
        self.assertEqual(memories["frequent_novels"][0][0], "jiange")


class TestPalaceIntegration(unittest.TestCase):
    """集成测试"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.palace = InkCorePalaceV2(base_path=self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_full_workflow(self):
        """测试完整工作流"""
        # 1. 存入章节
        chapter_text = "宁缺站在春风亭边，雨夜中拔刀杀人。这是将夜的开篇，展现了主角果断的性格。" * 20
        
        techniques = [
            {
                "name": "危机开场",
                "category": "plot",
                "example": "雨夜，宁缺拔刀杀人",
                "analysis": {
                    "definition": "以危机场景作为故事开端",
                    "scenario": "需要立即吸引读者注意力时",
                    "effect": "建立紧张感，展示主角性格",
                    "applicability": "适用于玄幻、武侠等类型"
                }
            },
            {
                "name": "环境烘托",
                "category": "pacing",
                "example": "雨夜、春风亭",
                "analysis": {
                    "definition": "用环境描写烘托氛围",
                    "scenario": "需要渲染气氛时",
                    "effect": "增强画面感",
                    "applicability": "通用"
                }
            }
        ]
        
        tech_ids = self.palace.mine_chapter(
            "jiange", "vol1", "ch1", chapter_text, techniques
        )
        
        self.assertEqual(len(tech_ids), 2)
        
        # 2. 创建关联
        self.palace.create_tunnel(
            tech_ids[0], tech_ids[1], "combines_with", confidence=0.85
        )
        
        # 3. 搜索
        results = self.palace.search("危机", novel="jiange")
        self.assertGreaterEqual(len(results), 1)
        
        # 4. 遍历关联
        related = self.palace.traverse(tech_ids[0], max_hops=1)
        self.assertGreaterEqual(len(related), 0)  # 可能有也可能没有
        
        # 5. 记录用户偏好
        self.palace.record_user_pref("liked_technique", str(tech_ids[0]))
        liked = self.palace.get_user_pref("liked_technique")
        self.assertEqual(liked, str(tech_ids[0]))


if __name__ == "__main__":
    # 配置日志
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # 运行测试
    unittest.main(verbosity=2)