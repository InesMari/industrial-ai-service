"""
封装 interrupt_on 的中断检测、决策构造和恢复调用。
"""
from typing import Any


def extract_all_interrupts(result: dict[str, Any]) -> list[dict[str, Any]] | None:
    """提取全部中断，并按 payload 内容标注 kind。

    - payload 含 action_requests：工具级中断（trigger_alarm 等工具调用需人工授权）
    - payload 含 draft_review：human_review 评审中断
    """
    interrupts = result.get("__interrupt__")
    if not interrupts:
        return None

    items: list[dict[str, Any]] = []
    for intr in interrupts:
        payload = getattr(intr, "value", {}) or {}
        if "action_requests" in payload:
            kind = "tool"
        elif "draft_review" in payload:
            kind = "review"
        else:
            kind = "review"
        items.append(
            {
                "interrupt_id": getattr(intr, "id", None),
                "kind": kind,
                "payload": payload,
            }
        )
    return items


def extract_interrupt(result: dict[str, Any]) -> dict[str, Any] | None:
    """从 graph.ainvoke 的返回值中提取中断信息（取第一个，单中断场景）。"""
    items = extract_all_interrupts(result)
    if not items:
        return None
    return items[0]


def build_approve_decision() -> dict[str, Any]:
    return {"type": "approve"}


def build_reject_decision(reason: str = "") -> dict[str, Any]:
    return {"type": "reject", "reason": reason}


def build_edit_decision(edited_args: dict[str, Any]) -> dict[str, Any]:
    return {"type": "edit", "args": edited_args}


def build_tool_decisions(
    allow: bool,
    count: int = 1,
    reason: str = "人工拒绝执行该工具调用",
) -> dict[str, Any]:
    """构造工具级中断（HumanInTheLoopMiddleware batched 模式）的 resume 值。

    中断处理代码读取 interrupt(hitl_request)["decisions"]，因此 resume 值必须是
    {"decisions": [...]}，且 decisions 数量与挂起的 action_requests 数量一致。
    """
    decision = {"type": "approve"} if allow else {"type": "reject", "message": reason}
    return {"decisions": [decision for _ in range(max(1, count))]}


def is_interrupted(result: dict[str, Any]) -> bool:
    return "__interrupt__" in result and bool(result["__interrupt__"])
