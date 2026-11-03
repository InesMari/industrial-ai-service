<script setup lang="ts">
import { useRouter } from 'vue-router'
import { Server, Thermometer, Bot, ArrowRight } from 'lucide-vue-next'

const router = useRouter()

const statusCards = [
  {
    title: '服务健康',
    desc: 'FastAPI 服务运行状态与版本信息',
    icon: Server,
    gradient: 'from-emerald-500 to-emerald-600',
    shadow: 'shadow-emerald-500/30',
    badge: '待接入',
    badgeType: 'success',
    path: '',
  },
  {
    title: '传感器数据',
    desc: '各产线温度实时读取（Modbus 采集）',
    icon: Thermometer,
    gradient: 'from-blue-500 to-blue-600',
    shadow: 'shadow-blue-500/30',
    badge: '待接入',
    badgeType: 'primary',
    path: '/sensor',
  },
  {
    title: 'Agent 评审',
    desc: '文档评审流程与人工中断决策恢复',
    icon: Bot,
    gradient: 'from-violet-500 to-violet-600',
    shadow: 'shadow-violet-500/30',
    badge: '待接入',
    badgeType: 'warning',
    path: '/agent',
  },
]

const quickLinks = [
  { path: '/sensor', title: '前往传感器监控', desc: '产线温度查询' },
  { path: '/closed-loop', title: '前往闭环状态', desc: '最新判定与历史记录' },
  { path: '/agent', title: '前往 Agent 评审', desc: '启动评审 / 恢复中断' },
]

function go(path: string) {
  if (path) router.push(path)
}
</script>

<template>
  <div class="mx-auto max-w-6xl space-y-5">
    <!-- 欢迎横幅 -->
    <section
      class="relative overflow-hidden rounded-2xl bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-800 px-8 py-10 text-white shadow-lg shadow-blue-600/20"
    >
      <div class="absolute -right-10 -top-16 h-48 w-48 rounded-full bg-white/10 blur-2xl" />
      <div class="absolute -bottom-20 right-24 h-40 w-40 rounded-full bg-indigo-400/20 blur-2xl" />
      <h1 class="relative text-2xl font-semibold">欢迎使用工业AI数据平台</h1>
      <p class="relative mt-2 max-w-xl text-sm leading-6 text-blue-100">
        整合传感器采集、闭环判定与 Agent 评审能力，为工业现场提供实时数据服务与智能化决策支持。
      </p>
    </section>

    <!-- 状态卡片 -->
    <section class="grid grid-cols-1 gap-5 md:grid-cols-3">
      <div
        v-for="card in statusCards"
        :key="card.title"
        class="card-hover cursor-pointer rounded-2xl bg-white p-6 shadow-card"
        @click="go(card.path)"
      >
        <div class="flex items-start justify-between">
          <span
            class="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br text-white shadow-lg"
            :class="[card.gradient, card.shadow]"
          >
            <component :is="card.icon" class="h-5 w-5" />
          </span>
          <span
            class="rounded-full px-2.5 py-0.5 text-xs"
            :class="{
              'bg-emerald-50 text-emerald-600': card.badgeType === 'success',
              'bg-blue-50 text-blue-600': card.badgeType === 'primary',
              'bg-amber-50 text-amber-600': card.badgeType === 'warning',
            }"
          >
            {{ card.badge }}
          </span>
        </div>
        <h3 class="mt-4 text-base font-medium text-gray-800">{{ card.title }}</h3>
        <p class="mt-1.5 text-xs leading-5 text-gray-500">{{ card.desc }}</p>
      </div>
    </section>

    <!-- 快捷入口 -->
    <section class="rounded-2xl bg-white p-6 shadow-card">
      <h3 class="mb-4 text-base font-medium text-gray-800">快捷入口</h3>
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <button
          v-for="link in quickLinks"
          :key="link.path"
          class="group flex cursor-pointer items-center justify-between rounded-xl border border-gray-100 bg-gray-50/60 px-4 py-3.5 text-left transition-all hover:border-blue-200 hover:bg-blue-50/50"
          @click="go(link.path)"
        >
          <span>
            <span class="block text-sm font-medium text-gray-700 group-hover:text-primary">
              {{ link.title }}
            </span>
            <span class="mt-0.5 block text-xs text-gray-400">{{ link.desc }}</span>
          </span>
          <ArrowRight
            class="h-4 w-4 shrink-0 text-gray-300 transition-all group-hover:translate-x-0.5 group-hover:text-primary"
          />
        </button>
      </div>
    </section>
  </div>
</template>
