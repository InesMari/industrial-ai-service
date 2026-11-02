from app.agents.state import ReviewState

def route_after_evaluate(state: ReviewState):
    """评估之后的路由决策"""
    score = state.get("quality_score", 0)
    revision_count = state.get("revision_count", 0)
    print(f"quality_score: {score}, revision_count: {revision_count}")
    # 条件1：质量达标，进入人工审核
    if score >=80:
        return "human_review"
    # 条件2：迭代次数达到上限（3次），强制进入人工审核
    # 这是防止无限循环的“断路器”，必须有[reference:5][reference:6]
    if revision_count >= 3:
        return "human_review"
        
    # 条件3：质量不达标且还有迭代机会，回去修改
    return "revise"

def route_after_agent(state: ReviewState) -> str:
    """agent节点之后：如果LLM生成了tool_calls，就去执行工具；否则去评估"""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "evaluate"