<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  Home,
  Activity,
  RefreshCw,
  Bot,
  PanelLeftClose,
  PanelLeftOpen,
  Cpu,
} from 'lucide-vue-next'

import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
const route = useRoute()

const activeMenu = computed(() => route.path)
const currentTitle = computed(() => (route.meta.title as string) ?? '')

const menus = [
  { path: '/home', title: '首页', icon: Home },
  { path: '/sensor', title: '传感器监控', icon: Activity },
  { path: '/closed-loop', title: '闭环状态', icon: RefreshCw },
  { path: '/agent', title: 'Agent 评审', icon: Bot },
]
</script>

<template>
  <el-container class="h-screen w-screen overflow-hidden bg-page-bg">
    <!-- 侧边栏 -->
    <el-aside
      :width="appStore.collapsed ? '64px' : '220px'"
      class="flex shrink-0 flex-col bg-sidebar transition-all duration-300"
    >
      <div class="flex h-16 shrink-0 items-center gap-2.5 overflow-hidden px-4">
        <span
          class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-blue-700 text-white shadow-lg shadow-blue-500/30"
        >
          <Cpu class="h-5 w-5" />
        </span>
        <span v-show="!appStore.collapsed" class="truncate text-base font-semibold text-white">
          工业AI平台
        </span>
      </div>
      <el-scrollbar class="flex-1">
        <el-menu
          :default-active="activeMenu"
          :collapse="appStore.collapsed"
          :collapse-transition="false"
          router
          background-color="#001529"
          text-color="rgba(255,255,255,0.65)"
          active-text-color="#ffffff"
          class="!border-r-0"
        >
          <el-menu-item v-for="m in menus" :key="m.path" :index="m.path">
            <component :is="m.icon" class="h-[18px] w-[18px]" />
            <template #title>{{ m.title }}</template>
          </el-menu-item>
        </el-menu>
      </el-scrollbar>
    </el-aside>

    <el-container class="flex min-w-0 flex-col overflow-hidden">
      <!-- 顶栏 -->
      <el-header
        class="flex h-16 shrink-0 items-center justify-between border-b border-gray-200 bg-white px-4"
      >
        <div class="flex items-center gap-3">
          <button
            class="flex h-9 w-9 cursor-pointer items-center justify-center rounded-md text-gray-500 transition-colors hover:bg-gray-100 hover:text-primary"
            :title="appStore.collapsed ? '展开侧边栏' : '折叠侧边栏'"
            @click="appStore.toggleSidebar()"
          >
            <PanelLeftClose v-if="!appStore.collapsed" class="h-5 w-5" />
            <PanelLeftOpen v-else class="h-5 w-5" />
          </button>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/home' }">工业AI平台</el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentTitle">{{ currentTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="flex items-center gap-3">
          <span class="hidden text-xs text-gray-400 md:inline">v0.0.1</span>
          <el-avatar :size="32" class="bg-primary font-semibold text-white">AI</el-avatar>
        </div>
      </el-header>

      <!-- 主内容区 -->
      <el-main class="flex-1 overflow-auto p-5">
        <RouterView />
      </el-main>
    </el-container>
  </el-container>
</template>
