<script setup lang="ts">
import { computed, onMounted } from 'vue'

import { useReviewStore } from '@/stores/review'

import DocumentInput from './components/DocumentInput.vue'
import ApprovalCard from './components/ApprovalCard.vue'
import ToolApprovalCard from './components/ToolApprovalCard.vue'
import ResultPanel from './components/ResultPanel.vue'
import ErrorPanel from './components/ErrorPanel.vue'

const store = useReviewStore()

// 刷新 / 重新打开页面时，尝试恢复未完成的审批
onMounted(() => {
  if (store.status === 'idle') {
    store.restoreFromStorage()
  }
})

const stepActive = computed(() => {
  switch (store.status) {
    case 'running':
    case 'pending_review':
    case 'error':
      return 1
    case 'completed':
      return 2
    default:
      return 0
  }
})
</script>

<template>
  <div class="mx-auto max-w-3xl space-y-5">
    <!-- 标题 + 会话标识 -->
    <div class="flex items-center justify-between">
      <h2 class="text-[22px] font-semibold text-gray-800">文档智能评审</h2>
      <span
        v-if="store.threadId"
        class="rounded-md bg-gray-100 px-2.5 py-1 font-mono text-xs text-gray-500"
        :title="store.threadId"
      >
        {{ store.threadId }}
      </span>
    </div>

    <!-- 状态机步骤指示 -->
    <el-steps :active="stepActive" align-center>
      <el-step title="提交文档" description="输入待评审内容" />
      <el-step title="人工审批" description="中断等待决策" />
      <el-step title="评审完结" description="输出最终结果" />
    </el-steps>

    <!-- 三态调度：组件只派发，业务逻辑全走 store action -->
    <Transition name="fade" mode="out-in">
      <DocumentInput
        v-if="store.status === 'idle' || store.status === 'running'"
        :running="store.status === 'running'"
        @submit="store.startReview"
      />

      <ApprovalCard
        v-else-if="store.status === 'pending_review' && store.interruptKind === 'review'"
        :draft="store.draftReview"
        :score="store.qualityScore"
        :submitting="store.submitting"
        @approve="store.resumeReview('approve')"
        @edit="(text: string) => store.resumeReview('edit', text)"
        @reject="store.resumeReview('reject')"
      />

      <ToolApprovalCard
        v-else-if="store.status === 'pending_review'"
        :requests="store.toolRequests"
        :submitting="store.submitting"
        @allow="store.resumeReview('tool_allow')"
        @deny="store.resumeReview('tool_deny')"
      />

      <ResultPanel
        v-else-if="store.status === 'completed'"
        :decision="store.finalDecision"
        :output="store.finalOutput"
        @restart="store.reset()"
      />

      <ErrorPanel
        v-else
        :message="store.errorMessage"
        :has-thread="store.hasThread"
        :checking="store.submitting"
        @check="store.checkStatus()"
        @restart="store.reset()"
      />
    </Transition>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
