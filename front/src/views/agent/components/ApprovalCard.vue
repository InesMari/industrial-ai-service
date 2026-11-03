<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessageBox } from 'element-plus'
import { Check, Pencil, X, RotateCcw, FileCheck2 } from 'lucide-vue-next'

const props = defineProps<{
  draft: string
  score: number
  submitting: boolean
}>()

const emit = defineEmits<{
  (e: 'approve'): void
  (e: 'edit', text: string): void
  (e: 'reject'): void
}>()

const editing = ref(false)
const editedText = ref(props.draft)

// 中断数据变化（多轮审批）时同步编辑框初值
watch(
  () => props.draft,
  (v) => {
    editedText.value = v
    editing.value = false
  },
)

// 三档评分：质检员看颜色即知是否需要仔细审查
const scoreLevel = computed(() => {
  if (props.score >= 80) return { label: '合格', cls: 'bg-green-100 text-green-700' }
  if (props.score >= 60) return { cls: 'bg-amber-100 text-amber-700', label: '待改进' }
  return { label: '不合格', cls: 'bg-red-100 text-red-700' }
})

function submitEdit() {
  const trimmed = editedText.value.trim()
  if (!trimmed || props.submitting) return
  emit('edit', trimmed)
}

/** 不可逆动作：驳回必须二次确认 */
async function confirmReject() {
  const ok = await ElMessageBox.confirm(
    '确认驳回该评审意见？驳回后 Agent 将终止流程，该操作不可撤销。',
    '驳回确认',
    { confirmButtonText: '确认驳回', cancelButtonText: '取消', type: 'warning' },
  )
    .then(() => true)
    .catch(() => false)
  if (ok && !props.submitting) emit('reject')
}
</script>

<template>
  <div class="rounded-2xl border-2 border-blue-700 bg-white p-6 shadow-card">
    <!-- 头部：评分徽章 + 提示 -->
    <header class="flex flex-wrap items-center gap-4">
      <span
        class="rounded-md px-4 py-1.5 text-lg font-bold"
        :class="scoreLevel.cls"
      >
        质量评分：{{ score }} / 100 · {{ scoreLevel.label }}
      </span>
      <span class="text-sm text-gray-500">请审核下方评审意见草稿</span>
    </header>

    <!-- 草稿：pre 保留 LLM 输出的换行与编号格式 -->
    <div class="mt-5">
      <h3 class="mb-2 flex items-center gap-1.5 text-sm font-medium text-gray-500">
        <FileCheck2 class="h-4 w-4" />
        评审意见草稿
      </h3>
      <pre
        class="max-h-[400px] overflow-y-auto rounded-lg border-l-4 border-blue-700 bg-slate-50 p-4 font-sans text-base leading-7 text-gray-800 whitespace-pre-wrap"
      >{{ draft || '（Agent 未返回草稿内容）' }}</pre>
    </div>

    <!-- 修改模式 -->
    <div v-if="editing" class="mt-5">
      <h3 class="mb-2 text-sm font-medium text-gray-500">修改后提交</h3>
      <textarea
        v-model="editedText"
        rows="10"
        placeholder="在此修改评审意见..."
        class="w-full resize-y rounded-xl border-2 border-primary p-4 text-base leading-relaxed text-gray-800 focus:outline-none"
      />
    </div>

    <!-- 操作按钮：大、粗、分开（工业 UI 硬约束） -->
    <footer class="mt-6 flex gap-4">
      <template v-if="!editing">
        <button
          class="min-h-[64px] flex-1 cursor-pointer rounded-xl bg-green-600 text-xl font-bold text-white transition-all hover:bg-green-700 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="submitting"
          @click="emit('approve')"
        >
          <span class="inline-flex items-center gap-2">
            <Check class="h-6 w-6" />
            通过
          </span>
        </button>
        <button
          class="min-h-[64px] flex-1 cursor-pointer rounded-xl bg-blue-600 text-xl font-bold text-white transition-all hover:bg-blue-700 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="submitting"
          @click="editing = true"
        >
          <span class="inline-flex items-center gap-2">
            <Pencil class="h-6 w-6" />
            修改
          </span>
        </button>
        <button
          class="min-h-[64px] flex-1 cursor-pointer rounded-xl bg-red-600 text-xl font-bold text-white transition-all hover:bg-red-700 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="submitting"
          @click="confirmReject"
        >
          <span class="inline-flex items-center gap-2">
            <X class="h-6 w-6" />
            驳回
          </span>
        </button>
      </template>

      <template v-else>
        <button
          class="min-h-[64px] flex-1 cursor-pointer rounded-xl bg-gray-200 text-xl font-bold text-gray-800 transition-all hover:bg-gray-300 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="submitting"
          @click="editing = false"
        >
          <span class="inline-flex items-center gap-2">
            <RotateCcw class="h-6 w-6" />
            取消
          </span>
        </button>
        <button
          class="min-h-[64px] flex-[2] cursor-pointer rounded-xl bg-green-600 text-xl font-bold text-white transition-all hover:bg-green-700 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="submitting || !editedText.trim()"
          @click="submitEdit"
        >
          <span class="inline-flex items-center gap-2">
            <Check class="h-6 w-6" />
            提交修改
          </span>
        </button>
      </template>
    </footer>
  </div>
</template>
