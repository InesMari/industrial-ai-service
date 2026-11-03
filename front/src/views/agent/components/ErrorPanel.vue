<script setup lang="ts">
import { AlertTriangle, SearchCheck, RotateCcw, Loader2 } from 'lucide-vue-next'

defineProps<{
  message: string
  hasThread: boolean
  checking: boolean
}>()

const emit = defineEmits<{
  (e: 'check'): void
  (e: 'restart'): void
}>()
</script>

<template>
  <div class="rounded-2xl border-2 border-red-300 bg-white shadow-card">
    <!-- 错误警示条 -->
    <header class="flex items-start gap-3 rounded-t-xl border-b border-red-200 bg-red-50 px-6 py-5">
      <AlertTriangle class="mt-0.5 h-6 w-6 shrink-0 text-red-600" />
      <div>
        <h3 class="text-lg font-semibold text-red-700">评审流程出现异常</h3>
        <p class="mt-1 text-sm leading-6 break-all text-red-600">{{ message || '未知错误' }}</p>
      </div>
    </header>

    <!-- 提示：resume 超时时 Agent 可能已在后台执行完 -->
    <div class="px-6 pt-5 text-xs leading-5 text-gray-400">
      网络超时时 Agent 可能仍在后台执行并已写入检查点，建议先「检查结果」确认真实状态，再决定是否重新开始。
    </div>

    <!-- 操作按钮 -->
    <footer class="flex gap-4 p-6">
      <button
        class="min-h-[64px] flex-[2] cursor-pointer rounded-xl bg-primary text-xl font-bold text-white transition-all hover:bg-primary-dark active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
        :disabled="!hasThread || checking"
        @click="emit('check')"
      >
        <span class="inline-flex items-center gap-2">
          <Loader2 v-if="checking" class="h-6 w-6 animate-spin" />
          <SearchCheck v-else class="h-6 w-6" />
          {{ checking ? '正在查询...' : '检查结果' }}
        </span>
      </button>
      <button
        class="min-h-[64px] flex-1 cursor-pointer rounded-xl bg-gray-200 text-xl font-bold text-gray-800 transition-all hover:bg-gray-300 active:scale-[0.98]"
        @click="emit('restart')"
      >
        <span class="inline-flex items-center gap-2">
          <RotateCcw class="h-6 w-6" />
          重新开始
        </span>
      </button>
    </footer>
  </div>
</template>
