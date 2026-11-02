"""
6.4 验证脚本：interrupt_on 保护高危工具
运行方式：uv run python verify_6_4.py
前置条件：已设置环境变量 DASHSCOPE_API_KEY
"""
import asyncio
import os
import sys


# ============================================================
# 第 0 步：检查依赖和版本
# ============================================================
def check_deps():
    try:
        import langgraph
        import langchain
    except ImportError as e:
        print(f"❌ 依赖缺失: {e}")
        print("请先运行: uv add langgraph langchain langchain-openai")
        sys.exit(1)

    # 检测 API 版本：LangChain 1.0+ 用 create_agent，旧版用 create_react_agent
    try:
        from langchain.agents import create_agent  # noqa: F401
        from langchain.agents.middleware import HumanInTheLoopMiddleware  # noqa: F401
        print("✅ 使用新版 API: create_agent + HumanInTheLoopMiddleware")
        return "new"
    except ImportError:
        try:
            from langgraph.prebuilt import create_react_agent  # noqa: F401
            print("✅ 使用旧版 API: create_react_agent + interrupt_on 参数")
            return "old"
        except ImportError:
            print("❌ 找不到 create_agent 或 create_react_agent")
            print("请升级: uv add 'langgraph>=1.0' 'langchain>=1.0'")
            sys.exit(1)


API_VERSION = check_deps()


# ============================================================
# 第 1 步：检查 API Key
# ============================================================
api_key = os.getenv("DASHSCOPE_API_KEY")
if not api_key:
    print("\n❌ 未设置 DASHSCOPE_API_KEY 环境变量")
    print("请先设置：")
    print("  macOS/Linux:  export DASHSCOPE_API_KEY=sk-你的key")
    print("  Windows:      set DASHSCOPE_API_KEY=sk-你的key")
    print("\n如果没有通义千问的 key，也可以换成本地 Ollama，")
    print("改下面 init_chat_model 那几行即可。")
    sys.exit(1)
print("✅ DASHSCOPE_API_KEY 已设置")


# ============================================================
# 第 2 步：定义工具（自包含，不依赖项目代码）
# ============================================================
from langchain_core.tools import tool


@tool
async def read_sensor_data(line_id: str) -> dict:
    """读取产线实时传感器数据（只读，安全，不需要审批）。

    Args:
        line_id: 产线编号，例如 line1
    """
    print(f"  [工具执行] read_sensor_data(line_id={line_id})")
    return {"line_id": line_id, "temperature": 36.5, "unit": "celsius"}


@tool
async def trigger_alarm(line_id: str, reason: str) -> str:
    """触发产线报警（高危操作，需人工审批。会写PLC线圈并发送MQTT告警）。

    Args:
        line_id: 产线编号
        reason: 报警原因
    """
    print(f"  [工具执行] trigger_alarm(line_id={line_id}, reason={reason})")
    return f"已触发 {line_id} 报警：{reason}"


# ============================================================
# 第 3 步：初始化 LLM
# ============================================================
from langchain.chat_models import init_chat_model

llm = init_chat_model(
    model="qwen-plus",
    model_provider="openai",
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
print("✅ LLM 初始化完成: qwen-plus")


# ============================================================
# 第 4 步：构建 Agent（兼容新旧两版 API）
# ============================================================
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

checkpointer = InMemorySaver()
TOOLS = [read_sensor_data, trigger_alarm]
INTERRUPT_CONFIG = {
    "trigger_alarm": True,        # 高危：必须人工审批
    "read_sensor_data": False,    # 只读：放行
}

if API_VERSION == "new":
    from langchain.agents import create_agent
    from langchain.agents.middleware import HumanInTheLoopMiddleware

    agent = create_agent(
        model=llm,
        tools=TOOLS,
        middleware=[
            HumanInTheLoopMiddleware(interrupt_on=INTERRUPT_CONFIG),
        ],
        checkpointer=checkpointer,
    )
else:
    from langgraph.prebuilt import create_react_agent

    agent = create_react_agent(
        model=llm,
        tools=TOOLS,
        interrupt_on=INTERRUPT_CONFIG,
        checkpointer=checkpointer,
    )
print("✅ Agent 构建完成")


# ============================================================
# 验证2：高危工具应触发中断
# ============================================================
async def test_2_interrupt():
    print("\n" + "=" * 60)
    print("验证2：高危工具 trigger_alarm 应触发中断")
    print("=" * 60)

    config = {"configurable": {"thread_id": "verify_002"}}
    result = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "line1 温度超过 35 度了，请立即调用 trigger_alarm 触发报警，"
                               "line_id 填 line1，reason 填 温度超限",
                }
            ]
        },
        config,
    )

    if "__interrupt__" not in result:
        print("❌ 失败：未触发中断")
        print("   可能原因：")
        print("   1. interrupt_on 配置没生效")
        print("   2. LLM 没有选择调用 trigger_alarm")
        print("   返回结果:", result)
        return False

    interrupt_info = result["__interrupt__"][0]
    print("✅ 成功：中断已触发")
    print("   中断 payload:", interrupt_info.value)
    return True


# ============================================================
# 验证3：批准后恢复执行
# ============================================================
async def test_3_resume():
    print("\n" + "=" * 60)
    print("验证3：批准后应从暂停点恢复执行")
    print("=" * 60)

    config = {"configurable": {"thread_id": "verify_003"}}
    result = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "line1 温度超过 35 度了，请立即调用 trigger_alarm 触发报警，"
                               "line_id 填 line1，reason 填 温度超限",
                }
            ]
        },
        config,
    )

    if "__interrupt__" not in result:
        print("❌ 失败：第一步就没触发中断，无法测试恢复")
        return False
    print("✅ 第一步中断已触发，准备批准恢复...")

    # 批准并恢复
    resumed = await agent.ainvoke(Command(resume={"type": "approve"}), config)

    if "__interrupt__" in resumed:
        print("❌ 失败：批准后仍然处于中断状态")
        print("   返回结果:", resumed)
        return False

    print("✅ 成功：批准后恢复执行，图跑完")
    # 打印最后一条消息
    last_msg = resumed["messages"][-1]
    content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
    print("   最终回复:", content[:200])
    return True


# ============================================================
# 验证1（补充）：只读工具不应中断
# ============================================================
async def test_1_no_interrupt():
    print("\n" + "=" * 60)
    print("验证1（补充）：只读工具 read_sensor_data 不应中断")
    print("=" * 60)

    config = {"configurable": {"thread_id": "verify_001"}}
    result = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "请调用 read_sensor_data 读取 line1 的温度数据，line_id 填 line1",
                }
            ]
        },
        config,
    )

    if "__interrupt__" in result:
        print("❌ 失败：只读工具不应该触发中断")
        return False

    print("✅ 成功：只读工具正常放行，未触发中断")
    return True


# ============================================================
# main
# ============================================================
async def main():
    print("\n" + "#" * 60)
    print("# 开始 6.4 验证：interrupt_on 保护高危工具")
    print("#" * 60)

    ok1 = await test_1_no_interrupt()
    ok2 = await test_2_interrupt()
    ok3 = await test_3_resume()

    print("\n" + "=" * 60)
    print("验证总结")
    print("=" * 60)
    print(f"  验证1（只读工具放行）: {'✅ 通过' if ok1 else '❌ 失败'}")
    print(f"  验证2（高危工具中断）: {'✅ 通过' if ok2 else '❌ 失败'}")
    print(f"  验证3（批准后恢复）  : {'✅ 通过' if ok3 else '❌ 失败'}")

    if all([ok1, ok2, ok3]):
        print("\n🎉 全部通过，可以进入第 7 步 FastAPI 集成")
    else:
        print("\n⚠️ 有失败项，请先排查再进入下一步")


if __name__ == "__main__":
    asyncio.run(main())