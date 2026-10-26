"""
OPC UA 订阅验证脚本（使用 OpcUaService 封装）。
运行前确认 OPC UA 服务器已在 0.0.0.0:4840 启动。

运行方式：
    uv run python verify_opcua_subscribe.py
"""
import asyncio
import logging

from app.services.opcua_service import OpcUaService

# 关键：配置日志级别，让 INFO 能输出
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


async def main():
    svc = OpcUaService("opc.tcp://localhost:4840/freeopcua/server/")

    # 1. 连接
    await svc.connect()

    # 2. 先直接读一次，确认节点路径和命名空间索引没问题
    try:
        val = await svc.read_value("ProductionLine/Temperature")
        print(f"[直读] ProductionLine/Temperature = {val}")
    except Exception as e:
        print(f"[直读失败] {e}")
        await svc.disconnect()
        return

    # 3. 显式传一个回调，直接 print 到 stdout，不依赖日志
    def on_change(name, val):
        print(f">>> 收到变化: {name} = {val}")

    await svc.subscribe(
        ["ProductionLine/Temperature", "ProductionLine/Vibration"],
        on_change=on_change,
    )
    print("订阅已建立，等待 15 秒...")

    # 4. 等待接收变化
    await asyncio.sleep(15)

    # 5. 断开
    await svc.disconnect()
    print("验证结束")


if __name__ == "__main__":
    asyncio.run(main())