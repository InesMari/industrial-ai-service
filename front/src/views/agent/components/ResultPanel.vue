<script setup lang="ts">
import { computed } from 'vue'
import { CheckCircle2, XCircle, RotateCcw, FileText } from 'lucide-vue-next'

const props = defineProps<{
  decision: string | null
  output: string | null
}>()

const emit = defineEmits<{ (e: 'restart'): void }>()

const outcome = computed(() => {
  if (props.decision === 'approved') {
    return {
      label: '评审通过',
      icon: CheckCircle2,
      badgeCls: 'bg-green-100 text-green-700',
      iconCls: 'text-green-600',
    }
  }
  if (props.decision === 'rejected') {
    return {
      label: '已驳回',
      icon: XCircle,
      badgeCls: 'bg-red-100 text-red-700',
      iconCls: 'text-red-600',
    }
  }
  return {
    label: '流程结束',
    icon: CheckCircle2,
    badgeCls: 'bg-blue-100 text-blue-700',
    iconCls: 'text-primary',
  }
})
</script>

<template>
  <div class="card-hover rounded-2xl bg-white p-8 shadow-card">
    <!-- 结果徽章 -->
    <div class="flex items-center gap-4">
      <component :is="outcome.icon" class="h-12 w-12" :class="outcome.iconCls" />
      <div>
        <h3 class="text-2xl font-semibold text-gray-800">{{ outcome.label }}</h3>
        <p class="mt-1 text-sm text-gray-400">Agent 评审流程已结束，以下为最终输出</p>
      </div>
    </div>

    <!-- 最终输出 -->
    <div class="mt-6">
      <h4 class="mb-2 flex items-center gap-1.5 text-sm font-medium text-gray-500">
        <FileText class="h-4 w-4" />
        最终评审结果
      </h4>
      <pre
        class="max-h-[420px] overflow-y-auto rounded-xl border-l-4 border-primary bg-slate-50 p-5 font-sans text-base leading-7 text-gray-800 whitespace-pre-wrap"
      >{{ output || '（无最终输出内容）' }}</pre>
    </div>

    <!-- 重新开始 -->
    <button
      class="mt-6 flex min-h-[56px] w-full cursor-pointer items-center justify-center gap-2.5 rounded-xl border-2 border-primary text-lg font-bold text-primary transition-all hover:bg-blue-50 active:scale-[0.99]"
      @click="emit('restart')"
    >
      <RotateCcw class="h-5 w-5" />
      开始新评审
    </button>
  </div>
</template>
