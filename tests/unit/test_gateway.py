"""
墨芯 v5.0 - Gateway 单元测试
"""

import asyncio
import unittest
from datetime import datetime

from gateway.core import (
    InkCoreGateway,
    MessageRouter,
    CLIAdapter,
    WebSocketAdapter,
    FeishuAdapter,
    Message,
    Response,
    User,
    PlatformType,
    MessageType,
    create_gateway_with_cli
)


class TestUser(unittest.TestCase):
    """测试 User"""
    
    def test_creation(self):
        """测试创建用户"""
        user = User(
            user_id="user_001",
            username="测试用户",
            platform=PlatformType.CLI
        )
        
        self.assertEqual(user.user_id, "user_001")
        self.assertEqual(user.username, "测试用户")
        self.assertEqual(user.platform, PlatformType.CLI)


class TestMessage(unittest.TestCase):
    """测试 Message"""
    
    def test_creation(self):
        """测试创建消息"""
        user = User("u1", "用户", PlatformType.CLI)
        
        message = Message(
            message_id="msg_001",
            user=user,
            platform=PlatformType.CLI,
            message_type=MessageType.TEXT,
            content="分析将夜第一章"
        )
        
        self.assertEqual(message.message_id, "msg_001")
        self.assertEqual(message.content, "分析将夜第一章")
        self.assertEqual(message.message_type, MessageType.TEXT)
    
    def test_to_dict(self):
        """测试转换为字典"""
        user = User("u1", "用户", PlatformType.CLI)
        message = Message("msg_001", user, PlatformType.CLI, MessageType.TEXT, "内容")
        
        data = message.to_dict()
        
        self.assertEqual(data["message_id"], "msg_001")
        self.assertEqual(data["content"], "内容")
        self.assertEqual(data["platform"], "cli")


class TestCLIAdapter(unittest.TestCase):
    """测试 CLIAdapter"""
    
    def setUp(self):
        self.adapter = CLIAdapter()
    
    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.adapter.platform, PlatformType.CLI)
        self.assertEqual(self.adapter.prompt, "墨芯> ")
    
    def test_on_message(self):
        """测试注册消息处理器"""
        handler_called = [False]
        
        async def handler(message):
            handler_called[0] = True
        
        self.adapter.on_message(handler)
        
        self.assertIsNotNone(self.adapter.message_handler)


class TestMessageRouter(unittest.TestCase):
    """测试 MessageRouter"""
    
    def setUp(self):
        self.router = MessageRouter()
    
    def test_add_route(self):
        """测试添加路由"""
        self.router.add_route("分析.*小说", "AnalyzeNovelSkill", priority=1)
        
        self.assertEqual(len(self.router.routes), 1)
        self.assertEqual(self.router.routes[0]["pattern"], "分析.*小说")
        self.assertEqual(self.router.routes[0]["skill_id"], "AnalyzeNovelSkill")
    
    def test_route_priority(self):
        """测试路由优先级"""
        self.router.add_route("分析", "SkillB", priority=2)
        self.router.add_route("分析.*小说", "SkillA", priority=1)
        
        # 优先级1的应该排在前面
        self.assertEqual(self.router.routes[0]["skill_id"], "SkillA")
        self.assertEqual(self.router.routes[1]["skill_id"], "SkillB")
    
    def test_format_result(self):
        """测试结果格式化"""
        result = {
            "techniques_count": 5,
            "summary": "分析完成"
        }
        
        formatted = self.router._format_result(result)
        
        self.assertEqual(formatted, "分析完成")


class TestInkCoreGateway(unittest.TestCase):
    """测试 InkCoreGateway"""
    
    def setUp(self):
        self.gateway = InkCoreGateway()
    
    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(len(self.gateway.adapters), 0)
        self.assertIsNotNone(self.gateway.router)
    
    def test_register_adapter(self):
        """测试注册适配器"""
        adapter = CLIAdapter()
        
        self.gateway.register_adapter(adapter)
        
        self.assertEqual(len(self.gateway.adapters), 1)
        self.assertIn(PlatformType.CLI, self.gateway.adapters)
    
    def test_add_route(self):
        """测试添加路由"""
        self.gateway.add_route("分析", "AnalyzeNovelSkill")
        
        self.assertEqual(len(self.gateway.router.routes), 1)
    
    def test_get_stats(self):
        """测试获取统计"""
        adapter = CLIAdapter()
        self.gateway.register_adapter(adapter)
        self.gateway.add_route("分析", "AnalyzeNovelSkill")
        
        stats = self.gateway.get_stats()
        
        self.assertEqual(stats["adapters"], 1)
        self.assertEqual(stats["routes"], 1)
        self.assertIn("cli", stats["adapter_types"])
    
    def test_message_history(self):
        """测试消息历史"""
        user = User("u1", "用户", PlatformType.CLI)
        message = Message("msg_001", user, PlatformType.CLI, MessageType.TEXT, "内容")
        
        self.gateway.message_history.append(message)
        
        self.assertEqual(len(self.gateway.message_history), 1)


class TestCreateGateway(unittest.TestCase):
    """测试快捷创建函数"""
    
    def test_create_gateway_with_cli(self):
        """测试创建带 CLI 的网关"""
        async def run_test():
            gateway = await create_gateway_with_cli()
            
            self.assertEqual(len(gateway.adapters), 1)
            self.assertIn(PlatformType.CLI, gateway.adapters)
            self.assertGreaterEqual(len(gateway.router.routes), 1)
        
        asyncio.run(run_test())


class TestPlatformType(unittest.TestCase):
    """测试 PlatformType"""
    
    def test_platforms(self):
        """测试平台类型"""
        self.assertEqual(PlatformType.FEISHU.value, "feishu")
        self.assertEqual(PlatformType.WECHAT.value, "wechat")
        self.assertEqual(PlatformType.CLI.value, "cli")
        self.assertEqual(PlatformType.WEBSOCKET.value, "websocket")


class TestMessageType(unittest.TestCase):
    """测试 MessageType"""
    
    def test_types(self):
        """测试消息类型"""
        self.assertEqual(MessageType.TEXT.value, "text")
        self.assertEqual(MessageType.IMAGE.value, "image")
        self.assertEqual(MessageType.COMMAND.value, "command")


if __name__ == "__main__":
    # 配置日志
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # 运行测试
    unittest.main(verbosity=2)