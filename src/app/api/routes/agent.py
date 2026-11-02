import logging
import uuid 
from typing import Annotated
from venv import logger

from fastapi import APIRouter, Request
from pydantic import BaseModel
from langgraph.types import Command

from app.schemas.common import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent", tags=["Agent"])

# ===== 请求/响应模型 =====
class StartReviewRequest(BaseModel):
    document_text: str

class ResumeRequest(BaseModel):
    action: str                     # "approve" | "edit" | "reject"
    edited_text: str | None = None  # action="edit" 时必填

# ===== 端点1：启动评审 =====

@router.post("/review", response_model=APIResponse)
async def start_review(request: Request, body: StartReviewRequest):
    """启动一次评审。如果Agent在 human_review 节点中断，返回 __interrupt__。"""
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
    return APIResponse(data={
        "thread_id": thread_id,
        "state": _serialize_state(result),
        "interrupted": "__interrupt__" in result,
        "interrupt_payload": result.get("__interrupt__"),
    })


# ===== 端点2：恢复评审 =====
@router.post("/review/{thread_id}/resume", response_model=APIResponse)
async def resume_review(request: Request, thread_id: str, body: ResumeRequest):
    """用人工决策恢复一个已中断的评审。必须使用同一个 thread_id。"""
    agent = request.app.state.agent

    # 关键：thread_id 必须与启动时完全一致，否则会加载一个空状态
    config = {"configurable": {"thread_id": thread_id}}

    # 构造 resume payload，这个值会成为 human_review_node 里 interrupt() 的返回值
    resume_value = {"action": body.action}
    if body.action == "edit":
        if not body.edited_text:
            return APIResponse(code=400, message="edit 操作必须提供 edited_text")
        resume_value["edited_text"] = body.edited_text
    
    result = await agent.ainvoke(
        Command(resume=resume_value),
        config=config,
    )

    return APIResponse(data={
        "thread_id": thread_id,
        "state": _serialize_state(result),
        "final_decision": result.get("human_decision"),
        "final_output": result.get("final_output"),
    })

def _serialize_state(state: dict) -> dict:
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