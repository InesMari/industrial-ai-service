<script setup lang="ts">
import { ref } from 'vue'
import { FileText, Send, Loader2, Lightbulb } from 'lucide-vue-next'

const props = defineProps<{ running: boolean }>()
const emit = defineEmits<{ (e: 'submit', text: string): void }>()

const text = ref('')

function submit() {
  const trimmed = text.value.trim()
  if (!trimmed || props.running) return
  emit('submit', trimmed)
}
</script>

<template>
  <div class="card-hover rounded-2xl bg-white p-6 shadow-card">
    <div class="mb-4 flex items-center gap-3">
      <span
        class="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 text-primary"
      >
        <FileText class="h-5 w-5" />
      </span>
      <div>
        <h3 class="text-lg font-medium text-gray-800">提交待评审文档</h3>
        <p class="mt-0.5 text-xs text-gray-400">
          Agent 将自动检索设备手册并生成评审意见，过程中可能需要人工审批
        </p>
      </div>
    </div>

    <textarea
      v-model="text"
      :disabled="running"
      rows="8"
      placeholder="请粘贴设备故障描述、巡检记录或需要评审的技术文档..."
      class="min-h-[200px] w-full resize-y rounded-xl border-2 border-gray-200 p-4 text-base leading-relaxed text-gray-800 transition-colors placeholder:text-gray-300 focus:border-primary focus:outline-none disabled:cursor-not-allowed disabled:bg-gray-50"
    />

    <div class="mt-3 flex items-start gap-2 rounded-lg bg-amber-50 p-3 text-xs leading-5 text-amber-700">
      <Lightbulb class="mt-0.5 h-4 w-4 shrink-0" />
      <span>
        示例：3号产线压缩机 C-203 于今日 10:42 出现振动值持续升高（最高 8.2mm/s，报警阈值
        7.1mm/s），伴随出口温度上升 4℃。请基于历史维修记录与设备手册给出检修建议。
      </span>
    </div>

    <button
      class="mt-5 flex min-h-[56px] w-full cursor-pointer items-center justify-center gap-2.5 rounded-xl bg-primary text-lg font-bold text-white shadow-lg shadow-blue-600/25 transition-all hover:bg-primary-dark active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-60"
      :disabled="running || !text.trim()"
      @click="submit"
    >
      <Loader2 v-if="running" class="h-5 w-5 animate-spin" />
      <Send v-else class="h-5 w-5" />
      {{ running ? 'Agent 评审中，可能需要 5~30 秒...' : '开始评审' }}
    </button>
  </div>
</template>
