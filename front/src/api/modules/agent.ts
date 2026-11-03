import { get, post } from '@/api/request'

import type {
  ResumeAction,
  ResumeResult,
  ReviewStatusResult,
  StartReviewResult,
} from '@/types/agent'

/**
 * Agent 评审接口（对应后端 /api/v1/agent）。
 * 评审涉及 LLM + 工具调用，可能跑 30s 以上，超时显式设为 120s。
 * 若后续确实超出 120s，再升级为"异步任务 + 轮询"模式。
 */
const REVIEW_TIMEOUT = 120_000

export const agentApi = {
  /** 启动一次评审；若在 human_review 或工具调用处中断，返回 interrupts */
  startReview: (documentText: string) =>
    post<StartReviewResult>(
      '/agent/review',
      { document_text: documentText },
      { timeout: REVIEW_TIMEOUT },
    ),

  /** 用人工决策恢复一个已中断的评审（需携带相同 thread_id） */
  resumeReview: (threadId: string, action: ResumeAction, editedText?: string) =>
    post<ResumeResult>(
      `/agent/review/${threadId}/resume`,
      { action, edited_text: editedText ?? null },
      { timeout: REVIEW_TIMEOUT },
    ),

  /** 只读查询评审当前状态（错误态"检查结果"用） */
  getReviewStatus: (threadId: string) =>
    get<ReviewStatusResult>(`/agent/review/${threadId}/status`),
}
