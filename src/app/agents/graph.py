from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware

from app.agents.state import ReviewState
from app.agents.nodes import (
    retrieve_node, generate_node, evaluate_node,
    revise_node, human_review_node,
)
from app.agents.routing import route_after_evaluate
from app.agents.tools import INDUSTRIAL_TOOLS
from app.agents.llm import llm


def build_industrial_agent(checkpointer):
    """用 create_agent 构建带 interrupt_on 的工业工具 Agent。

    注意：checkpointer 必须传入，否则 HumanInTheLoopMiddleware
    的中断状态无法持久化，Command(resume=...) 会找不到暂停点。
    """
    return create_agent(
        model=llm,
        tools=INDUSTRIAL_TOOLS,
        middleware=[
            HumanInTheLoopMiddleware(
                interrupt_on={
                    "trigger_alarm": True,
                    "read_sensor_data": False,
                    "query_equipment_manual": False,
                },
                description_prefix="【工业工具审批】",
            )
        ],
        checkpointer=checkpointer,   # ← 关键修复
    )


async def extract_draft_node(state: ReviewState) -> dict:
    """从 messages 中提取 LLM 最终回答，写入 draft_review。

    create_agent 的输出是 messages，不直接更新 draft_review，
    所以需要这个节点做一次字段搬运。
    """
    messages = state.get("messages", [])
    # 从后往前找第一条 assistant 消息
    for msg in reversed(messages):
        role = getattr(msg, "type", None) or getattr(msg, "role", None)
        if role in ("ai", "assistant"):
            content = getattr(msg, "content", "")
            if content:
                return {"draft_review": content}
    return {"draft_review": ""}


def build_graph(checkpointer):
    builder = StateGraph(ReviewState)
    if not checkpointer:
        checkpointer = InMemorySaver()

    # 节点注册
    builder.add_node("retrieve", retrieve_node)
    builder.add_node("generate", generate_node)
    builder.add_node("industrial_agent", build_industrial_agent(checkpointer))
    builder.add_node("extract_draft", extract_draft_node)   # 新增
    builder.add_node("evaluate", evaluate_node)
    builder.add_node("revise", revise_node)
    builder.add_node("human_review", human_review_node)

    # 入口与顺序边
    builder.set_entry_point("retrieve")
    builder.add_edge("retrieve", "generate")
    builder.add_edge("generate", "industrial_agent")

    # industrial_agent 内部跑完工具循环后，提取草稿
    builder.add_edge("industrial_agent", "extract_draft")
    builder.add_edge("extract_draft", "evaluate")

    # 评估后的条件分支
    builder.add_conditional_edges(
        "evaluate",
        route_after_evaluate,
        {
            "human_review": "human_review",
            "revise": "revise",
        },
    )
    builder.add_edge("revise", "evaluate")
    builder.add_edge("human_review", END)

    return builder.compile(checkpointer=checkpointer)