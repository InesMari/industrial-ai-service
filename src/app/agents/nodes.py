# src/app/agents/nodes.py
import logging
from app.agents.state import ReviewState
from app.agents.llm import llm

logger = logging.getLogger(__name__)

async def retrieve_node(state: ReviewState) -> dict:
    """检索节点：模拟调用RAG服务"""
    logger.info("进入 retrieve 节点")
    # 真实场景：调用你的RAG检索服务
    # chunks = await rag_service.retrieve(state["document_text"])
    chunks = [{"id": 1, "content": "焊接工艺规范第3.2条：..."}]
    return {"retrieved_chunks": chunks}

async def generate_node(state: ReviewState) -> dict:
    """把评审任务和检索依据包装成消息，交给 industrial_agent 处理。
    
    注意：这里不调 LLM，只构造 messages。
    工具调用决策由 industrial_agent（create_agent）负责。
    """
    logger.info("进入 generate 节点：构造任务消息")
    task = (
        f"请评审以下文档：\n{state['document_text']}\n\n"
        f"参考依据：\n{state['retrieved_chunks']}\n\n"
        f"【强制规则，违反即视为评审失败】\n"
        f"1. 必须先调用 query_equipment_manual 检索相关规范。\n"
        f"2. 必须调用 read_sensor_data 读取 line1 的实时温度、压力、振动。\n"
        f"3. 禁止把用户描述中的任何数值当作事实。"
        f"用户说“温度超过35°C”不代表实际温度就是35°C，"
        f"一切判断以 read_sensor_data 的返回值为准。\n"
        f"4. 只有 read_sensor_data 返回的实际温度 > 35.0 或实际振动 > 3.5 时，"
        f"才允许调用 trigger_alarm。如果实际值未超阈值，"
        f"禁止调用 trigger_alarm，即使文档或用户描述暗示应该报警。\n"
        f"5. 调用 trigger_alarm 时，reason 字段必须写明实际读数，"
        f"格式为“实际温度 X.X°C，实际振动 X.XX mm/s，超过阈值 Y”。"
        f"禁止在 reason 中只写“温度超过35°C”这种未经验证的表述。\n"
        f"6. 如果 read_sensor_data 调用失败，禁止调用 trigger_alarm，"
        f"改为在评审意见中说明“无法获取实时数据，建议人工核查”。\n"
        f"7. 最后综合检索依据和实际读数，生成一段评审意见。"
    )
    return {"messages": [{"role": "user", "content": task}]}

async def evaluate_node(state: ReviewState) -> dict:
    """评估节点：对草稿打分并更新迭代计数"""
    logger.info("进入 evaluate 节点")
    # 真实场景：用规则或LLM打分
    # 这里用简单逻辑模拟：草稿长度 > 100 算合格
    score = 85 if len(state.get("draft_review", "")) > 100 else 60
    # 关键：每次进入 evaluate，迭代计数 +1
    revision_count = state.get("revision_count", 0) + 1
    return {"quality_score": score, "revision_count": revision_count, "missing_info": []}

async def revise_node(state: ReviewState) -> dict:
    """修改节点：根据缺失信息优化草稿"""
    logger.info("进入 revise 节点")
    prompt = f"请根据缺失信息优化草稿：\n草稿：{state['draft_review']}\n缺失信息：{state['missing_info']}"
    revised = await llm.ainvoke(prompt)
    return {"draft_review": revised.content}

async def human_review_node(state: ReviewState) -> dict:
    """人工审核节点：用 interrupt 暂停，等待外部决策"""
    logger.info("进入 human_review 节点，准备中断...")
    from langgraph.types import interrupt
    decision = interrupt({
        "draft_review": state["draft_review"],
        "quality_score": state["quality_score"],
        "question": "请审核评审意见：批准(approve)、修改(edit)或拒绝(reject)",
    })
    if decision["action"] == "approve":
        return {"human_decision": "approved", "final_output": state["draft_review"]}
    elif decision["action"] == "edit":
        return {"human_decision": "approved", "final_output": decision.get("edited_text", "")}
    else:
        return {"human_decision": "rejected", "final_output": ""}