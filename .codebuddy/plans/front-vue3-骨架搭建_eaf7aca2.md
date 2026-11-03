---
name: front-vue3-骨架搭建
overview: 在 `e:/IndustryAI/industrial-ai-service/front` 下从零创建 Vue3 + TypeScript + Vite 工程骨架，集成 Element Plus、Vue Router、Pinia、Axios，完成统一 APIResponse 处理、开发代理与中后台布局，暂不做具体业务页面。
design:
  architecture:
    framework: vue
  styleKeywords:
    - 现代中后台
    - 简洁专业
    - 深色侧边栏
    - 卡片化布局
  fontSystem:
    fontFamily: PingFang-SC
    heading:
      size: 20px
      weight: 600
    subheading:
      size: 16px
      weight: 500
    body:
      size: 14px
      weight: 400
  colorSystem:
    primary:
      - "#2563EB"
      - "#1D4ED8"
    background:
      - "#001529"
      - "#F5F7FA"
      - "#FFFFFF"
    text:
      - "#1F2937"
      - "#6B7280"
    functional:
      - "#22C55E"
      - "#EF4444"
      - "#F59E0B"
todos:
  - id: init-vite-project
    content: 在 front 目录用 npm 初始化 Vite + Vue3 + TS 工程并安装 element-plus/vue-router/pinia/axios 及按需导入插件
    status: completed
  - id: config-vite-env
    content: 配置 vite.config.ts（@ 别名、/api 与 /health 代理到 localhost:8000）与 .env 环境变量
    status: completed
    dependencies:
      - init-vite-project
  - id: build-request-module
    content: 编写 types/api.d.ts 与 api/request.ts，统一解包 APIResponse 并兼容 msg/message 错误提示
    status: completed
    dependencies:
      - config-vite-env
  - id: build-layout-router
    content: 实现 DefaultLayout 布局、路由懒加载结构、AppStore 及四个占位页面（含首页）
    status: completed
    dependencies:
      - config-vite-env
  - id: verify-skeleton
    content: 运行 npm run build 与 vue-tsc 类型检查，启动 dev server 验证代理与路由跳转
    status: completed
    dependencies:
      - build-request-module
      - build-layout-router
---

## 用户需求

在 `e:\IndustryAI\industrial-ai-service\front`（当前为空目录）从零创建 Vue3 前端工程，作为 industrial-ai-service 的前端部分。

## 明确的技术选择

- 语言：TypeScript
- UI 组件库：Element Plus
- 包管理器：npm
- 构建工具：Vite

## 本轮范围：仅工程骨架

- Vite + Vue3 + TypeScript 工程初始化
- Vue Router 路由（懒加载）+ 中后台布局（侧边栏 / 顶栏 / 主内容区）
- Pinia 状态管理
- Axios 封装：统一处理后端 `APIResponse` 响应结构、拦截器、错误提示
- 开发代理配置（转发到后端 FastAPI `localhost:8000`）
- 预留传感器 / 闭环 / Agent 业务的模块结构与占位页面，**本轮不实现具体业务页面**

## 视觉效果

中后台风格骨架：左侧深色导航菜单 + 顶部工具栏 + 内容区，首页展示欢迎与系统状态占位卡片，整体简洁可用，后续业务页面可直接挂载。

## Tech Stack

- Vue 3.5+（`<script setup>` 语法）+ TypeScript
- 构建工具：Vite 7（`npm create vite@latest`）
- UI：Element Plus（按需引入 + `unplugin-auto-import` / `unplugin-vue-components`）
- 路由：Vue Router 4（懒加载 + 嵌套布局路由）
- 状态：Pinia
- HTTP：Axios（实例 + 拦截器封装）
- 代码规范（可选轻量）：`.editorconfig` + Vue 官方 TS 配置

## Implementation Approach

- **后端对接事实（已勘察）**：FastAPI 监听 `0.0.0.0:8000`，API 统一前缀 `/api/v1`（`src/app/main.py:128`）；统一响应 `APIResponse { code: int = 0, msg: str, data: any|null }`（`src/app/schemas/common.py`）；但全局异常处理器返回 `{"code": <string>, "message": <str>, "data": null}`——前端封装必须兼容 `msg`/`message` 两种字段、`code` 的 int/string 两种类型。
- **跨域策略**：后端未启用 CORS，开发期使用 Vite `server.proxy` 将 `/api`、`/health` 转发至 `http://localhost:8000`，避免改后端代码。
- **Axios 封装策略**：响应拦截器统一解包——`code === 0` 视为成功直接返回 `data`；非 0 或 HTTP 异常时弹 `ElMessage.error` 并 reject，业务组件无需重复写错误处理。类型上定义 `ApiRes<T>` 泛型对齐后端模型。
- **路由结构**：`/` 为布局路由（DefaultLayout），子路由懒加载：首页（仪表盘占位）、传感器监控（占位）、闭环状态（占位）、Agent 评审（占位）。占位页用统一的 `Placeholder.vue`（props 传入标题），不写业务逻辑。
- **性能**：全部路由 `() => import()` 懒加载；Element Plus 按需自动导入减小首屏体积；开发代理无生产影响。

## Directory Structure

```
front/                          # 全部为 [NEW]
├── index.html                  # 入口 HTML，中文 lang、标题"工业AI前端"
├── package.json                # 依赖与脚本（dev/build/preview/type-check）
├── vite.config.ts              # 插件(vue/auto-import/components)、@ 别名、/api 与 /health 代理到 localhost:8000
├── tsconfig.json / tsconfig.app.json / tsconfig.node.json   # Vite 官方 TS 模板 + @ 路径映射
├── .env.development            # VITE_API_BASE_URL=/api/v1
├── .env.production             # 生产 API 地址占位
├── .gitignore                  # node_modules / dist 等
└── src/
    ├── main.ts                 # createApp + pinia + router + element 样式
    ├── App.vue                 # 根组件（仅 <RouterView/>）
    ├── router/index.ts         # 布局路由 + 4 个懒加载子路由
    ├── stores/app.ts           # AppStore 示例（侧边栏折叠状态），演示 Pinia 用法
    ├── api/
    │   ├── request.ts          # axios 实例：baseURL 取 env、响应拦截解包 APIResponse、兼容 msg/message、ElMessage 错误提示、统一 reject
    │   └── modules/            # [占位] sensor.ts / closedLoop.ts / agent.ts 空模块，预留后端三组接口的调用入口
    ├── types/api.d.ts          # ApiRes<T>（code: number|string; msg: string; data: T|null）等通用类型
    ├── layouts/
    │   └── DefaultLayout.vue   # el-container 布局：el-aside 深色 el-menu 导航、el-header 面包屑+折叠按钮、el-main 路由出口
    ├── views/
    │   ├── HomeView.vue        # 首页：欢迎横幅 + 3 张状态占位卡片
    │   └── Placeholder.vue     # 通用占位页（props: title/description）
    └── assets/main.css         # 全局基础样式（重置、CSS 变量）
```

## Key Code Structures

```typescript
// src/types/api.d.ts —— 对齐后端 APIResponse，并兼容异常处理器的 message 字段
export interface ApiRes<T = unknown> {
  code: number | string
  msg?: string
  message?: string
  data: T | null
}

// src/api/request.ts —— 核心签名
const request = axios.create({ baseURL: env.VITE_API_BASE_URL, timeout: 15000 })
// 响应拦截：code === 0 -> resolve(data)；否则 ElMessage.error(msg ?? message ?? '请求失败') 并 reject
export async function get<T>(url: string, params?: object): Promise<T>
export async function post<T>(url: string, body?: unknown): Promise<T>
```

## Implementation Notes

- 用 `npm create vite@latest . -- --template vue-ts` 在 `front` 内初始化（目录已存在，注意命令在 front 目录内执行），再 `npm i element-plus axios vue-router pinia` 及两个 unplugin 开发依赖。
- Element Plus 采用自动按需导入，**不要**在 main.ts 全量 `app.use(ElementPlus)`，避免体积膨胀。
- 后端接口已确认无需鉴权头，请求拦截器暂不写 token 逻辑，仅留 TODO 注释。
- 构建验证：`npm run build` + `npm run type-check`（即 `vue-tsc --noEmit`）通过即达标。

## 设计说明（工程骨架 UI）

中后台管理风格骨架，Element Plus 深色侧边栏 + 浅色内容区经典布局：

- **DefaultLayout**：左侧固定 220px 深色导航（el-menu），含 Logo 区与 4 个菜单项（首页/传感器监控/闭环状态/Agent 评审），支持折叠；顶部 64px 白色工具栏（折叠按钮、面包屑、右侧用户头像占位）；主内容区浅灰底、卡片化留白。
- **HomeView**：顶部欢迎横幅（渐变底、项目名与简述），下方 3 张状态占位卡片（服务健康/传感器/Agent），预留数据接入位。
- **Placeholder**：居中卡片，标题 + 描述 + "页面建设中"空状态插画（el-empty），后续业务页逐个替换。
- **交互**：菜单高亮跟随路由、侧边栏折叠动画、卡片 hover 微上浮阴影，整体克制专业，为业务页面打好一致的视觉基底。