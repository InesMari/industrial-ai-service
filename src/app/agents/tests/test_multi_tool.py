import asyncio
import logging
from app.agents.graph import build_graph
from app.dependencies.providers import get_modbus_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


async def main():
    modbus = get_modbus_service()
    await modbus.connect()
    print("Modbus 已连接")

    try:
        graph = build_graph()
        config = {"configurable": {"thread_id": "test_multi_001"}}

        result = await graph.ainvoke(
            {
                "document_text": "某焊接件出现气孔缺陷，请评审工艺参数是否合规。",
                "revision_count": 0,
                "draft_review": "",
                "messages": [],
            },
            config,
        )

        print("\n===== 最终状态 =====")
        print("messages 条数:", len(result.get("messages", [])))
        print("draft_review:", (result.get("draft_review") or "")[:200])
        print("quality_score:", result.get("quality_score"))
        print("revision_count:", result.get("revision_count"))
        print("human_decision:", result.get("human_decision"))
        print("interrupt:", result.get("__interrupt__"))
    finally:
        await modbus.disconnect()
        print("Modbus 已断开")


if __name__ == "__main__":
    asyncio.run(main())