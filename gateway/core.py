"""
墨芯 v5.0 - Gateway 接入层
多平台统一接入：Feishu/WeChat/CLI/WebSocket
"""

from __future__ import annotations

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union

# 配置日志
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# 枚举与常量
# ═══════════════════════════════════════════════════════════════════════════

class PlatformType(Enum):
    """平台类型"""
    FEISHU = "feishu"
    WECHAT = "wechat"
    CLI = "cli"
    WEBSOCKET = "websocket"
    WEB = "web"


class MessageType(Enum):
    """消息类型"""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    COMMAND = "command"
    EVENT = "event"


# ═══════════════════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class User:
    """用户信息"""
    user_id: str
    username: str
    platform: PlatformType
    metadata: Dict = field(default_factory=dict)


@dataclass
class Message:
    """消息"""
    message_id: str
    user: User
    platform: PlatformType
    message_type: MessageType
    content: str
    raw_data: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "message_id": self.message_id,
            "user_id": self.user.user_id,
            "username": self.user.username,
            "platform": self.platform.value,
            "message_type": self.message_type.value,
            "content": self.content,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class Response:
    """响应"""
    response_id: str
    message_id: str
    content: str
    response_type: str = "text"
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


# ═══════════════════════════════════════════════════════════════════════════
# 平台适配器基类
# ═══════════════════════════════════════════════════════════════════════════

class PlatformAdapter(ABC):
    """平台适配器基类"""
    
    def __init__(self, platform: PlatformType, config: Dict = None):
        self.platform = platform
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{platform.value}")
        self.message_handler: Optional[Callable[[Message], None]] = None
    
    @abstractmethod
    async def start(self) -> None:
        """启动适配器"""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """停止适配器"""
        pass
    
    @abstractmethod
    async def send_response(self, response: Response, user: User) -> bool:
        """发送响应"""
        pass
    
    def on_message(self, handler: Callable[[Message], None]) -> None:
        """注册消息处理器"""
        self.message_handler = handler
    
    async def handle_incoming_message(self, message: Message) -> None:
        """处理收到的消息"""
        if self.message_handler:
            await self.message_handler(message)
        else:
            self.logger.warning(f"No message handler registered for {self.platform.value}")


# ═══════════════════════════════════════════════════════════════════════════
# CLI 适配器
# ═══════════════════════════════════════════════════════════════════════════

class CLIAdapter(PlatformAdapter):
    """
    命令行适配器
    
    用于本地开发和调试
    """
    
    def __init__(self, config: Dict = None):
        super().__init__(PlatformType.CLI, config)
        self.running = False
        self.prompt = config.get("prompt", "墨芯> ") if config else "墨芯> "
    
    async def start(self) -> None:
        """启动 CLI"""
        self.running = True
        self.logger.info("CLI adapter started")
        
        # 在后台运行输入循环
        asyncio.create_task(self._input_loop())
    
    async def stop(self) -> None:
        """停止 CLI"""
        self.running = False
        self.logger.info("CLI adapter stopped")
    
    async def _input_loop(self) -> None:
        """输入循环"""
        while self.running:
            try:
                # 使用线程池处理同步输入
                loop = asyncio.get_event_loop()
                user_input = await loop.run_in_executor(
                    None, lambda: input(self.prompt)
                )
                
                if user_input.strip():
                    await self._process_input(user_input)
                    
            except EOFError:
                break
            except Exception as e:
                self.logger.error(f"CLI input error: {e}")
    
    async def _process_input(self, user_input: str) -> None:
        """处理用户输入"""
        message = Message(
            message_id=f"cli_{datetime.now().timestamp()}",
            user=User(
                user_id="cli_user",
                username="CLI User",
                platform=PlatformType.CLI
            ),
            platform=PlatformType.CLI,
            message_type=MessageType.COMMAND if user_input.startswith("/") else MessageType.TEXT,
            content=user_input
        )
        
        await self.handle_incoming_message(message)
    
    async def send_response(self, response: Response, user: User) -> bool:
        """发送响应到控制台"""
        print(f"\n[{response.response_type}] {response.content}\n")
        return True


# ═══════════════════════════════════════════════════════════════════════════
# WebSocket 适配器
# ═══════════════════════════════════════════════════════════════════════════

class WebSocketAdapter(PlatformAdapter):
    """
    WebSocket 适配器
    
    支持 Web 客户端实时通信
    """
    
    def __init__(self, config: Dict = None):
        super().__init__(PlatformType.WEBSOCKET, config)
        self.host = config.get("host", "0.0.0.0") if config else "0.0.0.0"
        self.port = config.get("port", 8765) if config else 8765
        self.connections: Dict[str, Any] = {}
        self.server = None
    
    async def start(self) -> None:
        """启动 WebSocket 服务器"""
        try:
            import websockets
            
            self.server = await websockets.serve(
                self._handle_connection,
                self.host,
                self.port
            )
            
            self.logger.info(f"WebSocket server started on {self.host}:{self.port}")
            
        except ImportError:
            self.logger.error("websockets library not installed")
        except Exception as e:
            self.logger.error(f"Failed to start WebSocket server: {e}")
    
    async def stop(self) -> None:
        """停止 WebSocket 服务器"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.logger.info("WebSocket server stopped")
    
    async def _handle_connection(self, websocket, path):
        """处理 WebSocket 连接"""
        connection_id = f"ws_{id(websocket)}"
        self.connections[connection_id] = websocket
        
        self.logger.info(f"WebSocket client connected: {connection_id}")
        
        try:
            async for message in websocket:
                await self._process_message(connection_id, message)
        except Exception as e:
            self.logger.error(f"WebSocket error: {e}")
        finally:
            del self.connections[connection_id]
            self.logger.info(f"WebSocket client disconnected: {connection_id}")
    
    async def _process_message(self, connection_id: str, raw_message: str) -> None:
        """处理收到的消息"""
        try:
            data = json.loads(raw_message)
            
            message = Message(
                message_id=data.get("message_id", f"ws_{datetime.now().timestamp()}"),
                user=User(
                    user_id=data.get("user_id", connection_id),
                    username=data.get("username", "Web User"),
                    platform=PlatformType.WEBSOCKET
                ),
                platform=PlatformType.WEBSOCKET,
                message_type=MessageType(data.get("type", "text")),
                content=data.get("content", ""),
                raw_data={"connection_id": connection_id}
            )
            
            await self.handle_incoming_message(message)
            
        except json.JSONDecodeError:
            self.logger.warning(f"Invalid JSON received: {raw_message[:100]}")
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
    
    async def send_response(self, response: Response, user: User) -> bool:
        """发送响应到 WebSocket 客户端"""
        try:
            # 从 user.metadata 获取 connection_id
            connection_id = user.metadata.get("connection_id")
            
            if connection_id and connection_id in self.connections:
                websocket = self.connections[connection_id]
                
                data = {
                    "response_id": response.response_id,
                    "message_id": response.message_id,
                    "content": response.content,
                    "type": response.response_type,
                    "timestamp": datetime.now().isoformat()
                }
                
                await websocket.send(json.dumps(data, ensure_ascii=False))
                return True
            else:
                self.logger.warning(f"Connection not found for user {user.user_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send WebSocket response: {e}")
            return False


# ═══════════════════════════════════════════════════════════════════════════
# Feishu 适配器 (占位)
# ═══════════════════════════════════════════════════════════════════════════

class FeishuAdapter(PlatformAdapter):
    """
    飞书适配器
    
    对接飞书开放平台
    """
    
    def __init__(self, config: Dict = None):
        super().__init__(PlatformType.FEISHU, config)
        self.app_id = config.get("app_id", "") if config else ""
        self.app_secret = config.get("app_secret", "") if config else ""
        self.webhook_url = config.get("webhook_url", "") if config else ""
    
    async def start(self) -> None:
        """启动飞书适配器"""
        self.logger.info("Feishu adapter started (placeholder)")
        # TODO: 实现飞书 webhook 服务器
    
    async def stop(self) -> None:
        """停止飞书适配器"""
        self.logger.info("Feishu adapter stopped")
    
    async def send_response(self, response: Response, user: User) -> bool:
        """发送响应到飞书"""
        self.logger.info(f"[Feishu] To {user.username}: {response.content[:50]}...")
        # TODO: 实现飞书消息发送 API
        return True


# ═══════════════════════════════════════════════════════════════════════════
# 消息路由
# ═══════════════════════════════════════════════════════════════════════════

class MessageRouter:
    """
    消息路由器
    
    将消息路由到对应的处理器（Skill）
    """
    
    def __init__(self, skill_registry=None):
        self.skill_registry = skill_registry
        self.routes: List[Dict] = []
        self.default_handler: Optional[Callable[[Message], Response]] = None
        self.logger = logging.getLogger(__name__)
    
    def add_route(self, pattern: str, skill_id: str, priority: int = 0) -> None:
        """
        添加路由规则
        
        Args:
            pattern: 匹配模式（关键词或正则）
            skill_id: 目标技能ID
            priority: 优先级（数字小的优先）
        """
        import re
        
        self.routes.append({
            "pattern": pattern,
            "regex": re.compile(pattern) if pattern.startswith("^") else None,
            "skill_id": skill_id,
            "priority": priority
        })
        
        # 按优先级排序
        self.routes.sort(key=lambda r: r["priority"])
        
        self.logger.info(f"Added route: {pattern} -> {skill_id}")
    
    def set_default_handler(self, handler: Callable[[Message], Response]) -> None:
        """设置默认处理器"""
        self.default_handler = handler
    
    async def route(self, message: Message) -> Optional[Response]:
        """
        路由消息
        
        Args:
            message: 输入消息
            
        Returns:
            响应或 None
        """
        content = message.content
        
        # 尝试匹配路由
        for route in self.routes:
            matched = False
            
            if route["regex"]:
                # 正则匹配
                matched = route["regex"].search(content) is not None
            else:
                # 关键词匹配
                matched = route["pattern"] in content
            
            if matched:
                self.logger.info(f"Message matched route: {route['pattern']} -> {route['skill_id']}")
                
                if self.skill_registry:
                    # 执行对应技能
                    try:
                        execution = await self.skill_registry.execute(
                            skill_id=route["skill_id"],
                            input_data={
                                "message": message.to_dict(),
                                "content": content,
                                "user_id": message.user.user_id
                            }
                        )
                        
                        if execution.status.value == "completed":
                            result = execution.context.output_data
                            
                            return Response(
                                response_id=f"resp_{datetime.now().timestamp()}",
                                message_id=message.message_id,
                                content=self._format_result(result),
                                response_type="text"
                            )
                            
                    except Exception as e:
                        self.logger.error(f"Skill execution failed: {e}")
                        return Response(
                            response_id=f"resp_{datetime.now().timestamp()}",
                            message_id=message.message_id,
                            content=f"处理失败: {str(e)}",
                            response_type="error"
                        )
                else:
                    self.logger.warning("No skill registry configured")
        
        # 使用默认处理器
        if self.default_handler:
            return await self.default_handler(message)
        
        return None
    
    def _format_result(self, result: Dict) -> str:
        """格式化结果为文本"""
        if isinstance(result, dict):
            # 尝试提取报告或摘要
            if "report" in result:
                return result["report"]
            elif "summary" in result:
                return result["summary"]
            elif "techniques_count" in result:
                return f"分析完成，识别到 {result['techniques_count']} 项技法"
            else:
                return json.dumps(result, ensure_ascii=False, indent=2)
        
        return str(result)


# ═══════════════════════════════════════════════════════════════════════════
# Gateway 主类
# ═══════════════════════════════════════════════════════════════════════════

class InkCoreGateway:
    """
    墨芯网关
    
    统一接入层，管理多平台适配器
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 适配器
        self.adapters: Dict[PlatformType, PlatformAdapter] = {}
        
        # 路由
        self.router = MessageRouter()
        
        # 技能注册表
        self.skill_registry = None
        
        # 消息历史
        self.message_history: List[Message] = []
        self.max_history = self.config.get("max_history", 1000)
    
    def set_skill_registry(self, skill_registry) -> None:
        """设置技能注册表"""
        self.skill_registry = skill_registry
        self.router.skill_registry = skill_registry
    
    def register_adapter(self, adapter: PlatformAdapter) -> None:
        """注册平台适配器"""
        self.adapters[adapter.platform] = adapter
        
        # 设置消息处理器
        adapter.on_message(self._handle_message)
        
        self.logger.info(f"Registered adapter: {adapter.platform.value}")
    
    async def start(self) -> None:
        """启动网关"""
        self.logger.info("Starting InkCore Gateway...")
        
        # 启动所有适配器
        for platform, adapter in self.adapters.items():
            try:
                await adapter.start()
                self.logger.info(f"Adapter {platform.value} started")
            except Exception as e:
                self.logger.error(f"Failed to start adapter {platform.value}: {e}")
        
        self.logger.info("InkCore Gateway started")
    
    async def stop(self) -> None:
        """停止网关"""
        self.logger.info("Stopping InkCore Gateway...")
        
        # 停止所有适配器
        for platform, adapter in self.adapters.items():
            try:
                await adapter.stop()
                self.logger.info(f"Adapter {platform.value} stopped")
            except Exception as e:
                self.logger.error(f"Error stopping adapter {platform.value}: {e}")
        
        self.logger.info("InkCore Gateway stopped")
    
    async def _handle_message(self, message: Message) -> None:
        """处理收到的消息"""
        self.logger.info(f"Received message from {message.user.username}: {message.content[:50]}...")
        
        # 记录消息
        self.message_history.append(message)
        if len(self.message_history) > self.max_history:
            self.message_history.pop(0)
        
        # 路由消息
        response = await self.router.route(message)
        
        if response:
            # 发送响应
            await self.send_response(response, message.user)
        else:
            self.logger.warning(f"No response generated for message {message.message_id}")
    
    async def send_response(self, response: Response, user: User) -> bool:
        """发送响应给用户"""
        adapter = self.adapters.get(user.platform)
        
        if adapter:
            return await adapter.send_response(response, user)
        else:
            self.logger.error(f"No adapter found for platform {user.platform.value}")
            return False
    
    def add_route(self, pattern: str, skill_id: str, priority: int = 0) -> None:
        """添加路由规则"""
        self.router.add_route(pattern, skill_id, priority)
    
    def get_stats(self) -> Dict:
        """获取网关统计"""
        return {
            "adapters": len(self.adapters),
            "adapter_types": [p.value for p in self.adapters.keys()],
            "routes": len(self.router.routes),
            "message_history": len(self.message_history)
        }


# ═══════════════════════════════════════════════════════════════════════════
# 快捷启动函数
# ═══════════════════════════════════════════════════════════════════════════

async def create_gateway_with_cli(skill_registry=None) -> InkCoreGateway:
    """
    创建带 CLI 的网关
    
    用于本地开发和测试
    """
    gateway = InkCoreGateway()
    
    if skill_registry:
        gateway.set_skill_registry(skill_registry)
    
    # 添加 CLI 适配器
    cli_adapter = CLIAdapter()
    gateway.register_adapter(cli_adapter)
    
    # 添加默认路由
    gateway.add_route("分析.*小说", "AnalyzeNovelSkill", priority=1)
    gateway.add_route("提取.*技法", "AnalyzeNovelSkill", priority=1)
    gateway.add_route("搜索.*技法", "SearchTechniqueSkill", priority=2)
    gateway.add_route("对比.*作品", "CompareWorksSkill", priority=2)
    
    return gateway


# ═══════════════════════════════════════════════════════════════════════════
# 异常定义
# ═══════════════════════════════════════════════════════════════════════════

class GatewayError(Exception):
    """网关基础异常"""
    pass


class AdapterError(GatewayError):
    """适配器异常"""
    pass


class RoutingError(GatewayError):
    """路由异常"""
    pass


# ═══════════════════════════════════════════════════════════════════════════
# 模块入口
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    "InkCoreGateway",
    "MessageRouter",
    "PlatformAdapter",
    "CLIAdapter",
    "WebSocketAdapter",
    "FeishuAdapter",
    "Message",
    "Response",
    "User",
    "PlatformType",
    "MessageType",
    "GatewayError",
    "AdapterError",
    "create_gateway_with_cli"
]