"""临时脚本：验证只读工具不触发中断（需要 Modbus 模拟器已启动）"""
import asyncio

from app.agents.graph import build_graph
from app.dependencies.providers import get_modbus_service


async def main():
    # 关键：先手动连接 Modbus，模拟 FastAPI lifespan 的 startup
    modbus = get_modbus_service()
    await modbus.connect()
    print(f"Modbus 已连接 {modbus.host}:{modbus.port}")

    try:
        graph = build_graph()
        config = {"configurable": {"thread_id": "test_read_001"}}
        result = await graph.ainvoke(
            {"document_text": "请读取line1温度并生成报告", "revision_count": 0},
            config,
        )

        if "__interrupt__" in result:
            print("⚠️ 意外触发中断:", result["__interrupt__"])
        else:
            print("✅ 只读工具正常放行，无中断")

        print("最终草稿:", result.get("draft_review", "")[:200])
    finally:
        # 模拟 lifespan 的 shutdown
        await modbus.disconnect()
        print("Modbus 已断开")


if __name__ == "__main__":
    asyncio.run(main())