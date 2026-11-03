# 工业AI前端（industrial-ai-front）

`industrial-ai-service` 的前端工程，Vue 3 + TypeScript + Vite 5 + Element Plus + Tailwind CSS。

## 快速开始

```bash
cd front
npm install        # 需 Node 18+（推荐 20/22/24，本机可用 nvm 切换）
npm run dev        # http://localhost:5173
```

开发环境下，`/api` 与 `/health` 由 Vite 代理转发至后端 `http://localhost:8000`（见 `vite.config.ts`），后端无需开启 CORS。

## 脚本

| 命令 | 说明 |
| --- | --- |
| `npm run dev` | 启动开发服务器 |
| `npm run build` | 类型检查 + 生产构建（输出 `dist/`） |
| `npm run type-check` | 仅运行 `vue-tsc` 类型检查 |
| `npm run preview` | 本地预览构建产物 |

## 目录结构

```
src/
├── api/
│   ├── request.ts     # Axios 封装：统一解包后端 APIResponse（code=0 取 data），get/post 支持透传 timeout
│   └── modules/       # sensor / closedLoop / agent 接口模块
├── layouts/           # DefaultLayout：侧边栏 + 顶栏 + 内容区
├── router/            # 路由（懒加载）
├── stores/            # Pinia（app 全局 UI 状态；review 评审五态状态机）
├── types/             # 通用类型（api.ts 通用契约；agent.ts 评审契约）
└── views/             # 页面
    └── agent/         # Agent 评审工作台：AgentView 三态调度中心 + components/
```

## Agent 评审工作台（/agent）

LangGraph interrupt「暂停-恢复」三态工作台，五态状态机：`idle → running → pending_review → completed / error`。

- **两类中断审批**：评审审批（通过/修改/驳回，human_review 中断）与工具授权（允许/拒绝，trigger_alarm 等工具级中断）
- **多轮审批**：resume 后可能再次中断（工具循环），工作台循环渲染审批卡直至完结
- **120s 长超时**：评审接口显式调大（LLM + 工具调用可能跑 30s+）
- **防双击**：store 的 submitting 锁 + 按钮 disabled
- **会话恢复**：thread_id 存 localStorage（2 小时有效），刷新页面可恢复待审批状态
- **错误态**：「检查结果」（GET /agent/review/{thread_id}/status 查询真实状态）与「重新开始」
- **工业 UI 硬约束**：审批按钮最小高度 64px、字号 20px+、高对比配色、驳回/拒绝二次确认、pre 保留 LLM 输出格式

## 后端对接约定

- 统一前缀：`VITE_API_BASE_URL`（默认 `/api/v1`，见 `.env.*`）
- 成功响应：`{ code: 0, msg: "success", data: ... }`，请求封装直接返回 `data`
- 异常响应：`{ code: "<字符串错误码>", message: "...", data: null }`，自动弹出 `ElMessage.error`
