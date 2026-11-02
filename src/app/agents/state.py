"""
文档智能评审 Agent 的共享状态。

设计原则：
1. 每个字段都显式声明，不藏在 messages 里，保证可审计、可回放。
2. 每个字段都能回答"它影响流程的哪个分支"，否则不该出现在 State 里。
3. 循环类字段（revision_count）必须有硬上限，防止 LLM 自我修正无限循环。
"""
from typing import TypedDict, Literal, Annotated
from langgraph.graph.message import add_messages


class ReviewState(TypedDict):
    # 对话历史（含tool_calls）
    # 写入：API 入口（/agent/review）、tool_calls_node（tool_calls 写入）
    # 读取：API 返回、前端展示
    messages: Annotated[list, add_messages]

    # ── 输入 ──────────────────────────────────────────────────────────────
    # 原始待评审文档文本。
    # 写入：API 入口（/agent/review）
    # 读取：retrieve_node（作为检索 query）、generate_node（作为生成上下文）
    document_text: str

    # ── 检索产物 ──────────────────────────────────────────────────────────
    # RAG 检索召回的依据块，每块建议带 source / chunk_id / content。
    # 写入：retrieve_node
    # 读取：generate_node（拼 prompt）、evaluate_node（判断是否有依据）
    # 影响分支：evaluate 后若 retrieved_chunks 为空，可直接降级到 human_review
    retrieved_chunks: list[dict]

    # ── 生成产物 ──────────────────────────────────────────────────────────
    # LLM 生成的评审意见草稿。
    # 写入：generate_node（首次）、revise_node（修订后覆盖）
    # 读取：evaluate_node（打分）、human_review_node（展示给审批人）
    draft_review: str

    # ── 质量评估 ──────────────────────────────────────────────────────────
    # 评审意见质量分（0-100），由规则或 LLM 打分。
    # 写入：evaluate_node
    # 读取：route_after_evaluate（决定走 human_review 还是 revise）
    # 影响分支：>= 80 直接进人工；< 80 且 revision_count < 3 走修订
    quality_score: int

    # 评审意见缺失的信息点，用于指导 revise_node 补充。
    # 写入：evaluate_node
    # 读取：revise_node（作为修订指令）
    missing_info: list[str]

    # ── 循环控制 ──────────────────────────────────────────────────────────
    # 已修订次数，防止 LLM 自我修正无限循环。
    # 写入：revise_node（每次 +1）
    # 读取：route_after_evaluate（>= 3 强制转人工）
    # 设计要点：这是"硬刹车"，工业场景不能依赖 LLM 自己判断"改好了"
    revision_count: int

    # ── 人机协同 ──────────────────────────────────────────────────────────
    # 人工审批决策状态。
    # 写入：human_review_node（interrupt 恢复后写入）
    # 读取：human_review_node 内部、下游节点、前端展示
    # 初值：pending（表示等待审批）；批准后 approved；拒绝后 rejected
    # 设计要点：这个字段的存在，意味着系统从设计之初就允许"暂停"
    human_decision: Literal["pending", "approved", "rejected"]

    # ── 最终输出 ──────────────────────────────────────────────────────────
    # 最终评审意见（可能被人工编辑过）。
    # 写入：human_review_node（批准时取 draft_review 或人工编辑内容；拒绝时置空）
    # 读取：API 返回、前端展示、下游系统（如写入 MES）
    final_output: str