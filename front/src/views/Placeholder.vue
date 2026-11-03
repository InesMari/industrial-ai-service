<script setup lang="ts">
defineProps<{
  title: string
  description?: string
}>()
</script>

<template>
  <div class="flex min-h-[calc(100vh-9rem)] items-center justify-center">
    <div class="card-hover w-full max-w-xl rounded-2xl bg-white p-10 shadow-card">
      <h2 class="text-xl font-semibold text-gray-800">{{ title }}</h2>
      <p class="mt-2 text-sm leading-6 text-gray-500">
        {{ description ?? '该页面正在建设中，敬请期待。' }}
      </p>
      <el-empty description="页面建设中" :image-size="120" />
    </div>
  </div>
</template>
