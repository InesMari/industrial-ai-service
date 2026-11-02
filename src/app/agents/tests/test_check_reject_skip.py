"""验证4：trigger_alarm 中断后拒绝，工具不执行，流程继续走完。
前提：Modbus 模拟器已启动。
"""
import asyncio
from langgraph.types import Command

from app.agents.graph import build_graph
from app.dependencies.providers import get_modbus_service


async def main():
    modbus = get_modbus_service()
    await modbus.connect()
    print(f"Modbus 已连接 {modbus.host}:{modbus.port}")

    try:
        # 清理初始状态
        await modbus.write_coil(0, False)
        await modbus.write_coil(1, False)
        alarm_before = await modbus.read_coil(0)
        print(f"报警灯初始状态: {alarm_before}")

        graph = build_graph()
        config = {"configurable": {"thread_id": "test_reject_001"}}

        result = await graph.ainvoke(
            {
                "document_text": (
                    "line1 已确认温度 38.5°C，超过 35°C 安全阈值。"
                    "请立即调用 trigger_alarm 触发报警，不需要再次读取传感器。"
                ),
                "revision_count": 0,
            },
            config,
        )

        step = 0
        tool_interrupt_seen = False
        rejected = False
        while "__interrupt__" in result and step < 10:
            step += 1
            payload = result["__interrupt__"][0].value

            if "action_requests" in payload:
                names = [r.get("name") for r in payload["action_requests"]]
                print(f"[第{step}次中断] 工具级中断: {names}")
                if "trigger_alarm" in names:
                    tool_interrupt_seen = True
                    print("→ 拒绝 trigger_alarm")
                    rejected = True
                    result = await graph.ainvoke(
                        Command(resume={"type": "reject", "reason": "测试拒绝"}),
                        config,
                    )
                else:
                    # 其他工具调用，批准
                    result = await graph.ainvoke(
                        Command(resume={"type": "approve"}), config
                    )
            elif "question" in payload:
                print(f"[第{step}次中断] human_review: {payload['question'][:40]}...")
                result = await graph.ainvoke(
                    Command(resume={"action": "approve"}), config
                )
            else:
                print(f"[第{step}次中断] 未知结构: {list(payload.keys())}")
                break

        alarm_after = await modbus.read_coil(0)
        cooling_after = await modbus.read_coil(1)
        print(f"\n报警灯: {alarm_before} -> {alarm_after}")
        print(f"冷却阀: {cooling_after}")
        print(f"human_decision: {result.get('human_decision')}")

        # ===== 断言 =====
        if not tool_interrupt_seen:
            print("❌ 没有观察到 trigger_alarm 工具级中断——检查 graph.py 是否用了 create_agent")
        elif not rejected:
            print("⚠️ 没有执行拒绝操作")
        elif alarm_before is False and alarm_after is False and cooling_after is False:
            print("✅ 验证4通过：拒绝后 trigger_alarm 未执行，线圈状态未变，流程继续走完")
        else:
            print(f"❌ 拒绝后线圈被变更: 报警灯={alarm_after}, 冷却阀={cooling_after}")

    finally:
        try:
            await modbus.write_coil(0, False)
            await modbus.write_coil(1, False)
        except Exception:
            pass
        await modbus.disconnect()
        print("Modbus 已断开")


if __name__ == "__main__":
    asyncio.run(main())