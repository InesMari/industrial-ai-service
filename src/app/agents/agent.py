from fastapi import APIRouter, Request
from langgraph.types import Command
from app.schemas.common import APIResponse
from app.agents.interrupt_handler import (
    extract_interrupt, is_interrupted,
    build_approve_decision, build_reject_decision,
)

router = APIRouter(prefix="/agent", tags=["Agent"])

@router.post("/review")
async def start_review(request: Request, document_text: str):
    agent = request.app.state.agent
    thread_id = f"review_{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": thread_id}}

    result = await agent.ainvoke(
        {"document_text": document_text, "revision_count": 0},
        config,
    )

    if is_interrupted(result):
        interrupt_info  = extract_interrupt(result)
        return APIResponse(data = {
            "thread_id": thread_id,
            "status": "interrupted",
            "interrupt": interrupt_info,
        })
    return APIResponse(data={"thread_id": thread_id, "status": "completed", "state": result})

@router.post("/review/{thread_id}/resume")
async def resume_review(
    request: Request,
    thread_id: str,
    decision_type: str,
    reason: str = "",
    edited_args: dict | None = None,
):
    agent = request.app.state.agent
    config = {"configurable": {"thread_id": thread_id}}

    if decision_type == "approve":
        decision = build_approve_decision()
    elif decision_type == "reject":
        decision = build_reject_decision(reason)
    elif decision_type == "edit":
        decision = build_edit_decision(edited_args or {})
    else:
        return APIResponse(code=400, message="未知决策类型")

    # resume 的值会成为 interrupt() 的返回值
    result = await agent.ainvoke(Command(resume=decision), config)

    if is_interrupted(result):
        return APIResponse(data = {
                "thread_id": thread_id,
                "status": "interrupted",
                "interrupt": extract_interrupt(result),
        })