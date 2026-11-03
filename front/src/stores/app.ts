import { ref } from 'vue'
import { defineStore } from 'pinia'

/** 全局 UI 状态 */
export const useAppStore = defineStore('app', () => {
  /** 侧边栏是否折叠 */
  const collapsed = ref(false)

  function toggleSidebar() {
    collapsed.value = !collapsed.value
  }

  return { collapsed, toggleSidebar }
})
