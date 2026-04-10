"""
墨芯 v5.0 - Gateway 接入层
"""

from .core import (
    InkCoreGateway,
    MessageRouter,
    PlatformAdapter,
    CLIAdapter,
    WebSocketAdapter,
    FeishuAdapter,
    Message,
    Response,
    User,
    PlatformType,
    MessageType,
    GatewayError,
    AdapterError,
    create_gateway_with_cli
)

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