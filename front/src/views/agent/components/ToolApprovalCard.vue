<script setup lang="ts">
import { ElMessageBox } from 'element-plus'
import { Siren, ShieldCheck, ShieldX, Wrench } from 'lucide-vue-next'

import type { ToolActionRequest } from '@/types/agent'

const props = defineProps<{
  requests: ToolActionRequest[]
  submitting: boolean
}>()

const emit = defineEmits<{
  (e: 'allow'): void
  (e: 'deny'): void
}>()

function formatArgs(args: Record<string, unknown>): string {
  return JSON.stringify(args ?? {}, null, 2)
}

/** 拒绝工具调用（如触发告警）属于不可逆动作，二次确认 */
async function confirmDeny() {
  const ok = await ElMessageBox.confirm(
    '确认拒绝该工具调用？Agent 可能据此调整后续评审流程，该操作不可撤销。',
    '拒绝确认',
    { confirmButtonText: '确认拒绝', cancelButtonText: '取消', type: 'warning' },
  )
    .then(() => true)
    .catch(() => false)
  if (ok && !props.submitting) emit('deny')
}
</script>

<template>
  <div class="rounded-2xl border-2 border-orange-300 bg-white shadow-card">
    <!-- 警示头部 -->
    <header
      class="flex items-center gap-3 rounded-t-xl border-b border-orange-200 bg-orange-50 px-6 py-4"
    >
      <span class="flex h-10 w-10 items-center justify-center rounded-xl bg-orange-100 text-orange-600">
        <Siren class="h-5 w-5 animate-pulse" />
      </span>
      <div>
        <h3 class="text-lg font-semibold text-orange-800">工具调用请求人工授权</h3>
        <p class="mt-0.5 text-xs text-orange-600">
          Agent 在评审过程中请求执行以下高危工具，请确认是否允许
        </p>
      </div>
    </header>

    <!-- 工具请求列表 -->
    <div class="space-y-4 p-6">
      <div
        v-for="(req, i) in requests"
        :key="i"
        class="rounded-xl border border-orange-100 bg-orange-50/40 p-4"
      >
        <div class="mb-3 flex items-center gap-2.5">
          <Wrench class="h-4 w-4 text-orange-600" />
          <span class="rounded-md bg-orange-600 px-3 py-1 font-mono text-sm font-bold text-white">
            {{ req.name }}
          </span>
        </div>
        <pre class="overflow-x-auto rounded-lg bg-slate-50 p-3 font-mono text-sm leading-6 text-gray-700">{{ formatArgs(req.args) }}</pre>
      </div>
      <p v-if="!requests.length" class="text-sm text-gray-400">（未收到工具调用详情）</p>
    </div>

    <!-- 操作按钮 -->
    <footer class="flex gap-4 px-6 pb-6">
      <button
        class="min-h-[64px] flex-1 cursor-pointer rounded-xl bg-green-600 text-xl font-bold text-white transition-all hover:bg-green-700 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
        :disabled="submitting"
        @click="emit('allow')"
      >
        <span class="inline-flex items-center gap-2">
          <ShieldCheck class="h-6 w-6" />
          允许执行
        </span>
      </button>
      <button
        class="min-h-[64px] flex-1 cursor-pointer rounded-xl bg-red-600 text-xl font-bold text-white transition-all hover:bg-red-700 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
        :disabled="submitting"
        @click="confirmDeny"
      >
        <span class="inline-flex items-center gap-2">
          <ShieldX class="h-6 w-6" />
          拒绝执行
        </span>
      </button>
    </footer>
  </div>
</template>
