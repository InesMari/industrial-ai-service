# 临时验证脚本

import asyncio
from langgraph.types import Command
from app.agents.graph import build_graph

async def main():
    graph = build_graph()
    config = {"configurable": {"thread_id": "review_test_001"}}

    # 第一次调用：故意让草稿很短，触发低分 -> revise 循环
    print("=== 第一次调用（预期触发 revise 循环）===")
    result = await graph.ainvoke(
        {"document_text": "测试合同...", "revision_count": 0, "draft_review": ""},
        config,
    )
    print("中断信息:", result.get("__interrupt__"))
    print("当前 revision_count:", result.get("revision_count"))

    # 第二次调用：用同一个 thread_id 恢复
    # 由于 revise 循环后仍低分，最终会达到 revision_count >= 3 而进入 human_review
    print("\n=== 恢复执行（预期最终停在 human_review）===")
    result = await graph.ainvoke(Command(resume={"action": "approve"}), config)
    print("最终决策:", result.get("human_decision"))
    print("最终输出:", result.get("final_output")[:100], "...")

asyncio.run(main())