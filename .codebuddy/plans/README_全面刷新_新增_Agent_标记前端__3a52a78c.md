---
name: README 全面刷新（新增 Agent、标记前端）
overview: 全面刷新仓库根 README.md：补充 LangGraph 文档评审 Agent 模块、技术栈/目录/API/配置项/路线图；仅在目录树中用一行标记 front/ 为前端工程；按用户选择保留闭环采集器原有描述、不改动 .env.example。
todos:
  - id: update-intro-stack
    content: 更新开篇能力清单与技术栈表，补 Agent 定位及 LangChain/LangGraph、qwen-plus
    status: completed
  - id: update-tree-lifecycle
    content: 更新目录结构：front/ 一行标记、agents/ 子树、routes/agent.py；生命周期节追加 Agent 挂载
    status: completed
    dependencies:
      - update-intro-stack
  - id: add-agent-section
    content: 新增「文档评审 Agent（LangGraph）」小节：七节点流程图、ReviewState 字段表、路由规则、两类中断对照
    status: completed
    dependencies:
      - update-tree-lifecycle
  - id: update-api-config
    content: API 端点表补三个 /api/v1/agent 接口，配置项与快速开始补 DASHSCOPE_API_KEY 并修正过时提示
    status: completed
    dependencies:
      - add-agent-section
  - id: update-tests-roadmap
    content: 运行测试补 agents 用例目录与命令，更新路线图，并全文校对路径、字段与 mermaid 一致性
    status: completed
    dependencies:
      - update-api-config
---

## 用户需求

更新仓库根 `README.md`，使其反映项目当前真实状态；`front/` 前端工程不做详细说明，仅在目录结构中标记为前端项目。已确认的四项口径：全面刷新内容、前端只做目录树一行标记、闭环采集器保持原有描述、`.env.example` 不在本次修改范围。

## 产品概述

面向开发者的项目说明文档，读者打开根 README 即可了解：项目能力边界（工业数据采集 + 闭环控制 + LangGraph 文档评审 Agent）、技术栈、目录组织、核心设计、本地联调与容器化部署方式、对外 API 与配置项。

## 核心功能

- **能力简介更新**：在开篇能力清点中补充「AI 文档评审 Agent」一项，说明其检索 → 生成 → 工具调用 → 质量评估 → 人工审批的闭环。
- **技术栈补全**：技术栈表新增 LangChain / LangGraph 与 qwen-plus（阿里云百炼 DashScope OpenAI 兼容模式），开发依赖保持原样。
- **目录结构更新**：补齐 `src/app/agents/`（含 `tests/`）、`src/app/api/routes/agent.py`，并在根目录层面新增一行 `front/` 标记为前端工程（不展开技术栈与启动方式，细节指向 `front/README.md`）。
- **核心设计新增章节**：新增「文档评审 Agent（LangGraph）」说明，包含七节点流程图、`ReviewState` 关键字段、两类中断（评审审批 / 工具授权）与 resume 动作、`trigger_alarm` 高危工具需人工授权的约束、checkpointer 与 `thread_id` 会话复用要求。
- **API 与配置补全**：端点表补三个 `/api/v1/agent/*` 接口；配置说明补 `DASHSCOPE_API_KEY`（注明其由 `llm.py` 直接读环境变量，不经过 settings 类）；快速开始的 ini 示例补该变量并修正已过时的 `.env.example` 提示。
- **测试与路线图更新**：测试小节补充 `src/app/agents/tests/` 及其显式运行命令（默认 `testpaths` 不含该目录）；路线图勾选 Agent 已完成项并补充后续待办。
- **视觉与阅读效果**：保持现有中文技术文档风格，沿用表格、mermaid 流程图与 PowerShell 代码块，新增内容与既有章节排版一致，不引入新的文档结构范式。

## 技术栈选择

- 交付物为单一 Markdown 文档：`e:/IndustryAI/industrial-ai-service/README.md`（当前 448 行）。
- 不做任何代码、配置或前端改动；不触碰 `front/` 下文件、`.env.example`、`pyproject.toml`。
- 文档内嵌 mermaid 流程图（沿用文件既有 ```mermaid 写法）与 PowerShell / ini 代码块。

## 实施方式

采用「定向增量编辑」而非整篇重写：以现有章节为骨架逐处替换/插入，尽量保留既有表述、表格列结构与措辞风格，降低读者认知成本与改动爆炸半径。所有新增内容必须来自已核实的源码事实（函数名、路由前缀、字段名、默认值），不写推测性描述。

具体落点：

1. **开篇能力清单**（第 5-8 行附近）：在「采集 / 闭环 / 对外 / 联调」四条后新增一条「评审」，说明 LangGraph 文档评审 Agent 的定位（RAG 检索 + 实时传感数据 + 高危工具人工授权 + 人工审批）。
2. **技术栈表**：新增 `LangChain / LangGraph` 行（Agent 图编排、`HumanInTheLoopMiddleware` 中断与 checkpoint 恢复）与 `qwen-plus（DashScope）` 行（OpenAI 兼容模式）；保留原有 LangChain 相关无重复表述。
3. **目录结构块**：

- 新增 `front/` 一行，注释为「前端工程（Vue 3 + Vite + Element Plus，详见 front/README.md）」，仅此一处提及前端；
- 在 `api/routes/` 下新增 `agent.py`（`/agent` 路由：评审启动 / 恢复 / 状态查询）；
- 新增 `agents/` 子树：`state.py`（`ReviewState`）、`graph.py`（`build_graph` / `build_industrial_agent`）、`nodes.py`（retrieve/generate/evaluate/revise/human_review）、`routing.py`（`route_after_evaluate` 分支与迭代硬上限）、`tools.py`（`INDUSTRIAL_TOOLS` 三工具）、`llm.py`（qwen-plus 初始化）、`interrupt_handler.py`（中断提取与 resume 决策构造）、`tests/`（8 个 Agent 用例）；
- 标注 `agents/agent.py` 为未接入的遗留草稿（不被 `router.py` 引用），避免读者误当有效接口。

4. **「应用工厂与生命周期」节**：按既定口径保持闭环/OPC UA 相关描述原样，仅在启动步骤末尾追加一条：`build_graph(InMemorySaver())` 挂载到 `app.state.agent`（开发态内存 checkpoint，进程重启即丢失）。
5. **新增「文档评审 Agent（LangGraph）」小节**（置于「闭环采集器」之后）：包含七节点流程图（retrieve → generate → industrial_agent → extract_draft → evaluate → 分支 revise / human_review → END）、`ReviewState` 字段表（document_text / retrieved_chunks / draft_review / quality_score / missing_info / revision_count / human_decision / final_output）、评估路由规则（score ≥ 80 或 revision_count ≥ 3 转人工，否则修订回环）、两类中断与五类 resume 动作对照表、`decisions` 数量必须等于挂起 `action_requests` 数量的约束、`thread_id` 必须复用否则加载空状态。
6. **API 端点表**：补 `POST /api/v1/agent/review`、`POST /api/v1/agent/review/{thread_id}/resume`、`GET /api/v1/agent/review/{thread_id}/status` 三行及简短说明。
7. **快速开始 + 配置项说明**：ini 示例补 `DASHSCOPE_API_KEY=sk-xxxxxxxx`；配置项表新增该变量并注明「由 `src/app/agents/llm.py` 通过 `os.getenv` 读取，不在 settings 类中，必填否则 LLM 调用失败」；同时修正原「`.env.example` 是早期模板、`MODBUS_PORT=502`、未含 OPCUA_*」的过时提示，改为据实描述（现已是 5020 且含 `DASHSCOPE_API_KEY` 占位说明）。
8. **运行测试**：补充 `src/app/agents/tests/` 说明与 `uv run pytest src/app/agents/tests` 命令，并注明 `pyproject.toml` 的 `testpaths = ["tests"]` 导致默认执行不会覆盖该目录。
9. **路线图**：勾选 Agent 相关已完成项，新增待办：Postgres checkpointer 持久化（`AsyncPostgresSaver` + `CHECKPOINT_DB_URI`）、RAG 检索接入真实知识库、`agents/agent.py` 遗留路由清理。

## 实现注意事项

- **准确性优先**：新增的每个路径、函数名、字段名、端点、默认值都必须与源码一致（如 `interrupt_on` 中仅 `trigger_alarm: True`、coils 0/1 分别对应报警灯与冷却阀、`100` 条历史上限保持不变）；不确定的内容宁可不写。
- **范围控制**：不因发现 `closed_loop.py` 在采集器未启动时会访问未赋值的 `app.state.collector`、以及 `agents/agent.py` 存在未导入符号等问题而去"顺手修代码"；最多在文档中以「遗留 / 未启用」一句话标注，不作为本次改动目标。
- **安全**：文档中一律使用 `sk-xxxxxxxx` 占位符，绝不把仓库内疑似真实的 `DASHSCOPE_API_KEY` 抄进 README；`.env.example` 保持原样。
- **一致性**：改完后通读一遍，确保章节编号、表格列数、代码块语言标记、mermaid 语法可渲染，且与 `docker-compose.yml` / `Dockerfile` 的既有描述不冲突。

## 目录结构

```
industrial-ai-service/
└── README.md   # [MODIFY] 唯一改动文件。更新开篇能力清单；技术栈表补 LangChain/LangGraph 与 qwen-plus；
                # 目录结构补 front/ 一行标记、src/app/agents/（含 tests/）、api/routes/agent.py，并标注 agents/agent.py 为遗留；
                # 「应用工厂与生命周期」追加 Agent 挂载说明；新增「文档评审 Agent（LangGraph）」小节（流程图 + 状态字段表 + 路由规则 + 两类中断对照表 + thread_id/checkpointer 约束）；
                # API 端点表补三个 /api/v1/agent/* 接口；快速开始 ini 示例补 DASHSCOPE_API_KEY 并修正过时的 .env.example 提示；
                # 配置项表补 DASHSCOPE_API_KEY；运行测试补 agents 用例目录与显式命令；路线图勾选 Agent 完成项并补 Postgres checkpointer / 真实 RAG / 遗留路由清理待办。
```