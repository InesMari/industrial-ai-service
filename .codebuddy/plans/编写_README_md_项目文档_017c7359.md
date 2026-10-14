---
name: 编写 README.md 项目文档
overview: 基于实际代码内容编写 e:/IndustryAI/industrial-ai-service/README.md，介绍项目定位、目录结构、各文件职责、Modbus 模拟器使用方法和快速启动流程。
todos:
  - id: write-readme-structure
    content: 撰写 README.md：项目简介、技术栈、目录结构树（逐文件注释，空文件标注规划中）、核心设计说明（应用工厂/依赖注入/统一响应/日志请求ID/异常体系）
    status: completed
  - id: write-readme-usage
    content: 补充 README.md 使用部分：模拟器与写入脚本说明、快速开始步骤（含 MODBUS_PORT=5020 提示）、API 端点表、配置项说明、路线图
    status: completed
    dependencies:
      - write-readme-structure
  - id: verify-readme
    content: 核对 README.md 与实际代码一致性：端点路径、命令、文件名、默认配置值均与源码吻合
    status: completed
    dependencies:
      - write-readme-usage
---

## 用户需求

为 `e:/IndustryAI/industrial-ai-service` 项目撰写一份完整的 `README.md`，内容基于对实际代码的阅读，如实介绍项目结构、各文件作用与使用方式。用户特别说明：

- `modbus_sim.py` 是 Modbus TCP 模拟器（监听 5020 端口，从站 1，地址 100 初始值 250 即 25.0°C）
- `write_register.py` 用于向模拟器寄存器写入值（连接 localhost:5020，向地址 100 写入 250）
- 用户的描述仅作参考，以实际代码为准，不得虚构不存在的功能

## 产品概述

一份中文技术文档（README.md），帮助开发者快速理解工业 AI 数据服务的架构分层、请求处理链路（中间件 → 路由 → 服务 → Modbus 设备）、本地模拟调试方法，并能按快速开始步骤成功运行验证。

## 核心功能

- 项目简介与技术栈说明（FastAPI + Pydantic + pymodbus + uv）
- 完整目录结构树，每个文件附带一句话职责说明
- 核心架构概念说明：应用工厂、lifespan 连接管理、依赖注入、统一响应格式、JSON 日志与 X-Request-ID 中间件、异常体系
- Modbus 模拟器（modbus_sim.py）与寄存器写入脚本（write_register.py）的使用说明及命令示例
- 快速开始流程：安装依赖 → 配置 .env → 启动模拟器 → 启动服务 → curl 验证
- API 端点一览（含 /test 测试端点）与规划中模块的如实标注

## 技术方案

文档任务，仅创建/覆写 `e:/IndustryAI/industrial-ai-service/README.md` 一个 Markdown 文件，不改动任何代码。

### 内容结构（写作大纲）

1. **项目简介**：工业设备 Modbus 数据采集与 AI 服务的 FastAPI 后端，当前实现温度读取
2. **技术栈**：依据 pyproject.toml 如实列出（Python >=3.14、FastAPI、Pydantic v2、pydantic-settings、pymodbus 3.6.9、uvicorn、uv 包管理）
3. **目录结构**：完整目录树 + 逐文件注释；空文件（device.py、mqtt_service.py、tests/）标注"规划中"
4. **核心设计**：

- 应用工厂 `create_app()` + lifespan 生命周期内建立/断开 Modbus 连接
- `lru_cache` 单例的 `get_settings()` / `get_modbus_service()` 依赖注入
- 统一响应 `APIResponse{code,msg,data}` 与三类异常处理器（AppException / 校验异常 / 未预期异常）
- JSON 结构化日志 + RequestIdMiddleware（X-Request-ID 请求追踪）
- ModbusService：读保持寄存器地址 100，raw/10 换算温度，异常映射为 DeviceOfflineError(503)/MODBUS_ERROR(502)

5. **模拟器使用**：`uv run modbus_sim.py` 启动（0.0.0.0:5020，从站 1，寄存器 0-199，地址 100 = 250 即 25.0°C）；`uv run write_register.py` 修改寄存器值
6. **快速开始**：`uv sync` → `copy .env.example .env`（Windows PowerShell 命令，MODBUS_PORT 需改为 5020 对接模拟器）→ 启动模拟器 → `uv run uvicorn app.main:app --reload`（或 uvicorn src 路径方式）→ `curl "http://localhost:8000/api/v1/sensor/temperature?line_id=line1"` 验证
7. **API 端点表**：GET /health、GET /api/v1/health、GET /api/v1/sensor/temperature、GET /test/business-error、GET /test/unknown-error，附请求/响应示例
8. **配置说明**：.env 变量表（APP_*、MODBUS_*、MQTT_*）
9. **路线图**：设备控制（device.py）、MQTT 发布（mqtt_service.py）、单元测试（tests/）、Dockerfile

### 写作注意事项

- 全部内容以已核实的代码事实为准，禁止虚构端点行为或文件
- MODBUS_PORT 默认为 502（config.py），本地联调模拟器需在 .env 中改为 5020，文档必须明确指出此差异
- 命令示例使用 PowerShell 语法（用户环境为 Windows）