"""OPC UA 客户端服务，支持订阅节点变化。"""
import asyncio
import logging
from typing import Callable, Optional

from asyncua import Client, Node

logger = logging.getLogger(__name__)


class OpcUaSubHandler:
    """asyncua 订阅回调处理器。"""

    def __init__(self, on_change: Optional[Callable] = None):
        self.on_change = on_change
        self.latest: dict = {}

    def datachange_notification(self, node: Node, val, data):
        """节点值变化时被调用。"""
        # 从 NodeId 里提取可读名字
        name = str(node.nodeid.Identifier)   # 直接取 Identifier
        self.latest[name] = val
        logger.info(f"OPC UA 变化: {name} = {val}")
        if self.on_change:
            self.on_change(name, val)


class OpcUaService:
    def __init__(self, url: str, ns_uri: str = "http://my.factory.namespace"):
        self.url = url
        self.ns_uri = ns_uri
        self.client: Optional[Client] = None
        self.handler: Optional[OpcUaSubHandler] = None
        self.subscription = None
        self._ns_index: Optional[int] = None

    async def connect(self):
        self.client = Client(url=self.url)
        await self.client.connect()
        # 动态解析命名空间索引，避免写死
        namespaces = await self.client.get_namespace_array()
        self._ns_index = namespaces.index(self.ns_uri)
        logger.info(f"OPC UA 已连接: {self.url}, ns={self._ns_index}")

    async def disconnect(self):
        if self.subscription:
            await self.subscription.delete()
        if self.client:
            await self.client.disconnect()
            logger.info("OPC UA 已断开")

    async def subscribe(self, node_paths: list[str], on_change=None):
        """订阅一组节点。node_paths 例：['ProductionLine/Temperature']"""
        if not self.client or self._ns_index is None:
            raise RuntimeError("请先调用 connect()")

        self.handler = OpcUaSubHandler(on_change=on_change)
        self.subscription = await self.client.create_subscription(
            500, self.handler  # 500ms 发布间隔
        )

        for path in node_paths:
            node_id = f"ns={self._ns_index};s={path}"
            node = self.client.get_node(node_id)
            await self.subscription.subscribe_data_change(node)
            logger.info(f"已订阅: {node_id}")

    async def read_value(self, path: str):
        if not self.client or self._ns_index is None:
            raise RuntimeError("请先调用 connect()")
        node = self.client.get_node(f"ns={self._ns_index};s={path}")
        return await node.read_value()