"""临时脚本：验证 trigger_alarm 是否触发工具级中断。
注意：需要 Modbus 模拟器已启动，且脚本手动 connect。
"""
import asyncio

from app.agents.graph import build_graph
from app.dependencies.providers import get_modbus_service


async def main():
    # 关键：手动 connect，模拟 FastAPI lifespan 的 startup
    modbus = get_modbus_service()
    await modbus.connect()
    print(f"Modbus 已连接 {modbus.host}:{modbus.port}")

    try:
        graph = build_graph()
        config = {"configurable": {"thread_id": "test_alarm_001"}}
        result = await graph.ainvoke(
            {"document_text": "line1温度超过35°C，请立即触发报警", "revision_count": 0},
            config,
        )

        if "__interrupt__" not in result:
            print("❌ 没有触发中断")
            print("Result keys:", list(result.keys()))
            return

        # 遍历所有中断，区分"工具级中断"和"human_review 中断"
        print(f"\n共 {len(result['__interrupt__'])} 个中断:")
        for i, intr in enumerate(result["__interrupt__"]):
            payload = intr.value
            print(f"\n--- 中断 {i+1} ---")
            print(f"payload keys: {list(payload.keys())}")
            print(f"payload: {payload}")

            # 判断中断类型
            if "action_requests" in payload:
                print("✅ 这是工具级中断（interrupt_on 触发）")
                for req in payload["action_requests"]:
                    print(f"  工具名: {req.get('name')}")
                    print(f"  参数: {req.get('args')}")
                    print(f"  描述: {req.get('description', '')[:100]}")
            elif "question" in payload:
                print("ℹ️ 这是 human_review 节点的手写中断（流程正常）")

    finally:
        await modbus.disconnect()
        print("\nModbus 已断开")


if __name__ == "__main__":
    asyncio.run(main())