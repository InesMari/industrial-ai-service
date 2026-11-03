import logging
import uuid
from typing import Any

from fastapi import APIRouter, Request
from langgraph.types import Command
from pydantic import BaseModel

from app.agents.interrupt_handler import (
    build_tool_decisions,
    extract_all_interrupts,
)
from app.schemas.common import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent", tags=["Agent"])

# 评审决策（human_review 中断）与工具授权（工具级中断）两类 resume 动作
VALID_ACTIONS = ("approve", "edit", "reject", "tool_allow", "tool_deny")


# ===== 请求/响应模型 =====
class StartReviewRequest(BaseModel):
    document_text: str


class ResumeRequest(BaseModel):
    action: str                     # "approve" | "edit" | "reject" | "tool_allow" | "tool_deny"
    edited_text: str | None = None  # action="edit" 时必填


# ===== 端点1：启动评审 =====

@router.post("/review", response_model=APIResponse)
async def start_review(request: Request, body: StartReviewRequest):
    """启动一次评审。如果Agent在 human_review 或工具调用处中断，返回 interrupts。"""
    agent = request.app.state.agent

    thread_id = f"review_{uuid.uuid4().hex[:12]}"
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "document_text": body.document_text,
        "revision_count": 0,
        "human_decision": "pending",
        "messages": [],
    }

    result = await agent.ainvoke(initial_state, config=config)
    interrupts = extract_all_interrupts(result)
    return APIResponse(data={
        "thread_id": thread_id,
        "state": _serialize_state(result),
        "interrupted": interrupts is not None,
        "interrupts": interrupts,
    })


# ===== 端点2：恢复评审 =====
@router.post("/review/{thread_id}/resume", response_model=APIResponse)
async def resume_review(request: Request, thread_id: str, body: ResumeRequest):
    """用人工决策恢复一个已中断的评审。必须使用同一个 thread_id。

    - approve / edit / reject：恢复 human_review 中断，值成为 human_review_node
      里 interrupt() 的返回值。
    - tool_allow / tool_deny：恢复工具级中断（HumanInTheLoopMiddleware batched
      模式），resume 值为 {"decisions": [...]}，每个挂起的工具调用一条决策。
    """
    agent = request.app.state.agent

    if body.action not in VALID_ACTIONS:
        return APIResponse(code=400, msg=f"未知决策类型: {body.action}")

    # 关键：thread_id 必须与启动时完全一致，否则会加载一个空状态
    config = {"configurable": {"thread_id": thread_id}}

    resume_value: dict[str, Any]
    if body.action in ("approve", "edit", "reject"):
        resume_value = {"action": body.action}
        if body.action == "edit":
            if not body.edited_text:
                return APIResponse(code=400, msg="edit 操作必须提供 edited_text")
            resume_value["edited_text"] = body.edited_text
    else:
        # decisions 数量必须与挂起的 action_requests 数量一致，从 checkpoint 里数出来
        count = await _count_pending_tool_requests(agent, config)
        resume_value = build_tool_decisions(
            allow=body.action == "tool_allow",
            count=count,
        )

    result = await agent.ainvoke(
        Command(resume=resume_value),
        config=config,
    )

    # 恢复后可能再次中断（工具循环 / 评审循环），前端据此渲染下一张审批卡
    interrupts = extract_all_interrupts(result)
    if interrupts:
        return APIResponse(data={
            "thread_id": thread_id,
            "state": _serialize_state(result),
            "interrupted": True,
            "interrupts": interrupts,
            "final_decision": None,
            "final_output": None,
        })

    return APIResponse(data={
        "thread_id": thread_id,
        "state": _serialize_state(result),
        "interrupted": False,
        "interrupts": None,
        "final_decision": result.get("human_decision"),
        "final_output": result.get("final_output"),
    })


# ===== 端点3：查询评审状态（只读） =====
@router.get("/review/{thread_id}/status", response_model=APIResponse)
async def get_review_status(request: Request, thread_id: str):
    """用 thread_id 查询评审当前状态（前端错误态"检查结果"用）。

    - interrupted：Agent 仍在等待人工决策（snapshot.next 非空）
    - completed：流程已走完，values 里带最终结果
    """
    agent = request.app.state.agent
    config = {"configurable": {"thread_id": thread_id}}

    snapshot = await agent.aget_state(config)
    if snapshot is None or (not snapshot.values and not snapshot.next):
        return APIResponse(code=404, msg="thread 不存在或已过期")

    return APIResponse(data={
        "status": "interrupted" if snapshot.next else "completed",
        "next_nodes": list(snapshot.next),
        "values": _serialize_state(dict(snapshot.values)),
    })


async def _count_pending_tool_requests(agent: Any, config: dict[str, Any]) -> int:
    """从 checkpoint 数出当前挂起的工具级 action_requests 数量。"""
    snapshot = await agent.aget_state(config)
    count = 0
    for task in (getattr(snapshot, "tasks", None) or {}).values():
        for intr in getattr(task, "interrupts", None) or []:
            payload = getattr(intr, "value", {}) or {}
            if "action_requests" in payload:
                count = max(count, len(payload["action_requests"]))
    return count


def _serialize_state(state: dict[str, Any]) -> dict[str, Any]:
    """把 State 里不可 JSON 序列化的对象（如 LangChain Message）转成 dict。"""
    safe = {}
    for k, v in state.items():
        if k == "__interrupt__":
            continue
        if k == "messages" and isinstance(v, list):
            safe[k] = [
                {"type": getattr(m, "type", "unknown"),
                 "content": getattr(m, "content", str(m))}
                for m in v
            ]
        else:
            safe[k] = v
    return safe
