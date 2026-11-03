import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { agentApi } from '@/api/modules/agent'
import type { InterruptInfo, ResumeAction, ToolActionRequest } from '@/types/agent'

/** 工作台五态：空闲 | 评审中 | 待审批 | 已完结 | 错误 */
export type ReviewStatus = 'idle' | 'running' | 'pending_review' | 'completed' | 'error'

const STORAGE_KEY = 'pending_review'
const STORAGE_TTL = 2 * 3600 * 1000 // 超过 2 小时视为过期（车间电脑非专人专用）

/** localStorage 里保存的待恢复数据 */
interface SavedReview {
  threadId: string
  documentText: string
  kind: 'review' | 'tool'
  draftReview: string
  qualityScore: number
  toolRequests: ToolActionRequest[]
  timestamp: number
}

export const useReviewStore = defineStore('review', () => {
  // ===== state =====
  const status = ref<ReviewStatus>('idle')
  const threadId = ref<string | null>(null)
  const documentText = ref('')
  const interruptKind = ref<'review' | 'tool' | null>(null)
  const draftReview = ref('')
  const qualityScore = ref(0)
  const toolRequests = ref<ToolActionRequest[]>([])
  const finalDecision = ref<string | null>(null)
  const finalOutput = ref<string | null>(null)
  const errorMessage = ref('')
  /** 提交锁：防止双击触发重复 resume */
  const submitting = ref(false)

  const hasThread = computed(() => threadId.value !== null)

  // ===== 内部工具 =====
  function saveStorage() {
    if (status.value !== 'pending_review' || !threadId.value) return
    const saved: SavedReview = {
      threadId: threadId.value,
      documentText: documentText.value,
      kind: interruptKind.value ?? 'review',
      draftReview: draftReview.value,
      qualityScore: qualityScore.value,
      toolRequests: toolRequests.value,
      timestamp: Date.now(),
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(saved))
  }

  function clearStorage() {
    localStorage.removeItem(STORAGE_KEY)
  }

  /** 应用一次中断：按 kind 分流填充，进入待审批态 */
  function applyInterrupt(thread: string, info: InterruptInfo) {
    threadId.value = thread
    interruptKind.value = info.kind
    if (info.kind === 'tool') {
      toolRequests.value = info.payload.action_requests ?? []
    } else {
      draftReview.value = info.payload.draft_review ?? ''
      qualityScore.value = info.payload.quality_score ?? 0
    }
    status.value = 'pending_review'
    saveStorage()
  }

  function setError(message: string) {
    status.value = 'error'
    errorMessage.value = message
  }

  /** 提交锁包装：并发调用直接忽略 */
  async function withSubmitting(fn: () => Promise<void>) {
    if (submitting.value) return
    submitting.value = true
    try {
      await fn()
    } finally {
      submitting.value = false
    }
  }

  // ===== actions =====
  function reset() {
    status.value = 'idle'
    threadId.value = null
    documentText.value = ''
    interruptKind.value = null
    draftReview.value = ''
    qualityScore.value = 0
    toolRequests.value = []
    finalDecision.value = null
    finalOutput.value = null
    errorMessage.value = ''
    submitting.value = false
    clearStorage()
  }

  /** 启动评审 */
  async function startReview(text: string) {
    await withSubmitting(async () => {
      reset()
      status.value = 'running'
      documentText.value = text
      const res = await agentApi.startReview(text)
      if (res.interrupted && res.interrupts?.length) {
        applyInterrupt(res.thread_id, res.interrupts[0])
      } else {
        // Agent 未走人工审核直接完结（理论上少见）
        threadId.value = res.thread_id
        finalDecision.value = (res.state.human_decision as string) ?? null
        finalOutput.value = (res.state.final_output as string) ?? ''
        status.value = 'completed'
      }
    }).catch((e: unknown) => {
      console.error('[review] 启动评审失败:', e)
      setError(e instanceof Error ? e.message : '评审启动失败，请稍后重试')
    })
  }

  /**
   * 恢复评审（审批提交）。恢复后可能再次中断（工具循环 / 评审循环），
   * 此时回到 pending_review 渲染下一张审批卡，直至完结。
   */
  async function resumeReview(action: ResumeAction, editedText?: string) {
    if (!threadId.value) return
    const current = threadId.value
    await withSubmitting(async () => {
      status.value = 'running'
      const res = await agentApi.resumeReview(current, action, editedText)
      if (res.interrupted && res.interrupts?.length) {
        applyInterrupt(res.thread_id, res.interrupts[0])
      } else {
        finalDecision.value = res.final_decision
        finalOutput.value = res.final_output ?? ''
        status.value = 'completed'
        clearStorage()
      }
    }).catch((e: unknown) => {
      console.error('[review] 恢复评审失败:', e)
      // 注意：不清 threadId——resume 超时时 Agent 可能已在后台执行完，仍可"检查结果"
      setError(e instanceof Error ? e.message : '审批提交失败，请稍后重试')
    })
  }

  /** 错误态"检查结果"：向后端查询该 thread 的真实状态 */
  async function checkStatus() {
    if (!threadId.value) return
    const current = threadId.value
    await withSubmitting(async () => {
      const res = await agentApi.getReviewStatus(current)
      if (res.status === 'interrupted') {
        // 仍在等待人工决策，用 checkpoint 里的最新草稿/评分回填
        const values = res.values
        if (typeof values.draft_review === 'string') draftReview.value = values.draft_review
        if (typeof values.quality_score === 'number') qualityScore.value = values.quality_score
        interruptKind.value = 'review'
        status.value = 'pending_review'
        saveStorage()
      } else {
        finalDecision.value = (res.values.human_decision as string) ?? null
        finalOutput.value = (res.values.final_output as string) ?? ''
        status.value = 'completed'
        clearStorage()
      }
    }).catch((e: unknown) => {
      console.error('[review] 查询状态失败:', e)
      setError(e instanceof Error ? e.message : '状态查询失败，请稍后重试')
    })
  }

  /** 从 localStorage 恢复未完成的审批（页面刷新 / 重新打开） */
  function restoreFromStorage() {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return

    let parsed: unknown
    try {
      parsed = JSON.parse(raw)
    } catch (e) {
      console.error('[review] 本地缓存数据损坏，已清除:', e)
      clearStorage()
      return
    }

    if (typeof parsed !== 'object' || parsed === null) {
      clearStorage()
      return
    }
    const saved = parsed as SavedReview
    if (Date.now() - saved.timestamp >= STORAGE_TTL) {
      clearStorage()
      return
    }
    threadId.value = saved.threadId
    documentText.value = saved.documentText ?? ''
    interruptKind.value = saved.kind ?? 'review'
    draftReview.value = saved.draftReview ?? ''
    qualityScore.value = saved.qualityScore ?? 0
    toolRequests.value = saved.toolRequests ?? []
    status.value = 'pending_review'
  }

  return {
    status,
    threadId,
    documentText,
    interruptKind,
    draftReview,
    qualityScore,
    toolRequests,
    finalDecision,
    finalOutput,
    errorMessage,
    submitting,
    hasThread,
    reset,
    startReview,
    resumeReview,
    checkStatus,
    restoreFromStorage,
  }
})
