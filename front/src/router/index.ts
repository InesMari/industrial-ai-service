import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: () => import('@/layouts/DefaultLayout.vue'),
      redirect: '/home',
      children: [
        {
          path: 'home',
          name: 'home',
          component: () => import('@/views/HomeView.vue'),
          meta: { title: '首页' },
        },
        {
          path: 'sensor',
          name: 'sensor',
          component: () => import('@/views/sensor/SensorView.vue'),
          meta: { title: '传感器监控' },
        },
        {
          path: 'closed-loop',
          name: 'closedLoop',
          component: () => import('@/views/closed-loop/ClosedLoopView.vue'),
          meta: { title: '闭环状态' },
        },
        {
          path: 'agent',
          name: 'agent',
          component: () => import('@/views/agent/AgentView.vue'),
          meta: { title: 'Agent 评审' },
        },
      ],
    },
  ],
})

router.afterEach((to) => {
  const title = (to.meta.title as string) ?? ''
  document.title = title ? `${title} · 工业AI前端` : '工业AI前端'
})

export default router
