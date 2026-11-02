"""
封装 interrupt_on 的中断检测、决策构造和恢复调用。
"""
from typing import Any

def extract_interrupt(result:dict):
    """从 graph.ainvoke 的返回值中提取中断信息。"""
    interrupts = result.get("__interrupt__")
    if not interrupts:
        return None

    # interrupts 是一个列表，每个元素是一个 Interrupt 对象
    # 取第一个（单工具调用场景）
    first = interrupts[0]
    return{
        "interrupt_id": getattr(first, "id", None),
        "payload": getattr(first, "value", {}),
    }

def build_approve_decision() -> dict:
    return {"type": "approve"}

def build_reject_decision(reason: str = "") -> dict:
    return {"type": "reject", "reason": reason}

def build_edit_decision(edited_args: dict) -> dict:
    return {"type": "edit", "args": edited_args}

def is_interrupted(result: dict) -> bool:
    return "__interrupt__" in result and bool(result["__interrupt__"])