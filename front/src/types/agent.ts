/**
 * Agent 评审工作台类型定义，与后端 src/app/api/routes/agent.py 契约一一对应。
 */

/** 工具级中断时的单个工具调用请求（HumanInTheLoopMiddleware 的 action_request） */
export interface ToolActionRequest {
  name: string
  args: Record<string, unknown>
  [key: string]: unknown
}

/** human_review 中断的 payload */
export interface ReviewInterruptPayload {
  draft_review?: string
  quality_score?: number
  question?: string
}

/** 工具级中断的 payload */
export interface ToolInterruptPayload {
  action_requests?: ToolActionRequest[]
  [key: string]: unknown
}

/** 结构化中断信息（后端 extract_all_interrupts 产出） */
export interface InterruptInfo {
  interrupt_id: string | null
  kind: 'review' | 'tool'
  payload: ReviewInterruptPayload & ToolInterruptPayload
}

/** POST /agent/review 响应 data */
export interface StartReviewResult {
  thread_id: string
  interrupted: boolean
  interrupts: InterruptInfo[] | null
  state: Record<string, unknown>
}

/** resume 动作：评审决策（前三种）与工具授权（后两种） */
export type ResumeAction = 'approve' | 'edit' | 'reject' | 'tool_allow' | 'tool_deny'

/** POST /agent/review/{thread_id}/resume 响应 data */
export interface ResumeResult {
  thread_id: string
  interrupted: boolean
  interrupts: InterruptInfo[] | null
  final_decision: string | null
  final_output: string | null
}

/** GET /agent/review/{thread_id}/status 响应 data */
export interface ReviewStatusResult {
  status: 'interrupted' | 'completed'
  next_nodes: string[]
  values: Record<string, unknown>
}
