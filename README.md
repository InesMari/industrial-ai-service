# industrial-ai-service

工业 AI 数据服务 —— 基于 FastAPI 的工业设备数据采集后端服务。通过 Modbus TCP 协议读取现场设备（传感器）数据，对外提供统一的 HTTP API，为上层 AI 分析与工业应用提供数据接入能力。当前已实现温度数据读取，并附带本地 Modbus 模拟器，便于脱离真实硬件进行开发调试。

## 技术栈

| 组件 | 说明 |
| --- | --- |
| Python | >= 3.14 |
| FastAPI | Web 框架（应用工厂 + lifespan 生命周期管理） |
| Pydantic v2 / pydantic-settings | 请求/响应模型校验与配置管理 |
| pymodbus 3.6.9 | Modbus TCP 异步客户端与服务端（模拟器） |
| uvicorn | ASGI 服务器 |
| uv | 包管理与项目构建 |
| Docker / Docker Compose | 容器化构建与一键编排（含 Modbus 模拟容器） |

开发依赖（dev 组）：`pytest`、`pytest-asyncio`、`pytest-cov`、`httpx`（异步 API 测试客户端）、`ruff`（代码检查）。

## 目录结构

```
industrial-ai-service/
├── src/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── sensor.py        # 传感器数据接口：GET /api/v1/sensor/temperature
│   │   │   │   ├── device.py        # 设备控制接口（规划中）
│   │   │   │   └── health.py        # 健康检查：GET /api/v1/health
│   │   │   └── router.py            # 路由汇总，将各子路由挂载到应用
│   │   ├── core/
│   │   │   ├── config.py            # 配置管理：pydantic-settings 加载 .env，lru_cache 单例
│   │   │   ├── logging.py           # 日志配置：JSON 结构化日志，附带 request_id 与异常信息
│   │   │   ├── exceptions.py        # 自定义异常：AppException 基类、DeviceOfflineError、InvalidParameterError
│   │   │   └── middleware.py         # RequestIdMiddleware：生成/透传 X-Request-ID，记录请求日志
│   │   ├── schemas/
│   │   │   ├── sensor.py            # Pydantic 请求/响应模型：SensorReading、DeviceCommand
│   │   │   └── common.py            # 通用响应模型：APIResponse{code, msg, data}
│   │   ├── services/
│   │   │   ├── modbus_service.py    # Modbus 读写逻辑：连接管理、读取保持寄存器并换算温度
│   │   │   └── mqtt_service.py      # MQTT 发布逻辑（规划中）
│   │   ├── dependencies/
│   │   │   └── providers.py         # 依赖注入提供者：get_modbus_service() 单例工厂
│   │   └── main.py                  # 应用工厂入口：create_app()、lifespan、统一异常处理器
│   └── industrial_ai_service/       # uv 构建的包入口（industrial-ai-service 命令）
├── tests/
│   ├── conftest.py                  # pytest fixtures：FakeModbusService 伪造服务 + httpx AsyncClient
│   └── test_sensor.py               # 传感器接口测试：正常读取、参数校验、设备离线等用例
├── modbus_sim.py                    # 本地 Modbus TCP 模拟器（见下文）
├── write_register.py                # 向模拟器寄存器写入值的工具脚本（见下文）
├── Dockerfile                       # 多阶段构建镜像：uv 构建依赖 + 非 root 用户运行
├── docker-compose.yml               # 编排 API 服务与 Modbus 模拟容器
├── pyproject.toml                   # 项目元数据、依赖与 pytest 配置（uv）
├── uv.lock                          # 依赖锁定文件
└── .env.example                     # 环境变量模板
```

## 核心设计

### 应用工厂与生命周期

`src/app/main.py` 使用 `create_app()` 工厂函数创建 FastAPI 实例，通过 `lifespan` 在应用启动时建立 Modbus TCP 连接、关闭时断开连接：

- 启动：`lifespan` 中调用 `get_modbus_service()` 获取单例并 `connect()`，连接失败抛出 `DeviceOfflineError`
- 关闭：`disconnect()` 释放连接

### 依赖注入

`src/app/dependencies/providers.py` 中的 `get_modbus_service()` 使用 `lru_cache` 缓存 `ModbusService` 实例，配置来源于 `get_settings()`（同样单例），路由通过 `Depends` 注入服务。

### 统一响应与异常处理

- 成功响应：`APIResponse{code: 0, msg: "success", data: ...}`
- `AppException` 及其子类：返回对应的 `status_code` 与 `{code, message, data}` 结构
- 参数校验失败（`RequestValidationError`）：返回 `422 VALIDATION_ERROR`
- 未预期异常：返回 `500 INTERNAL_ERROR`

内置异常类型（`src/app/core/exceptions.py`）：

| 异常 | code | HTTP 状态码 |
| --- | --- | --- |
| `DeviceOfflineError` | `DEVICE_OFFLINE` | 503 |
| `InvalidParameterError` | `INVALID_PARAMETER` | 400 |
| `ModbusService` 通信异常 | `MODBUS_ERROR` / `MODBUS_READ_ERROR` | 502 |

### 结构化日志与请求追踪

- `src/app/core/logging.py`：JSON 格式日志（时间戳、级别、logger、消息、模块、行号），异常时附带堆栈
- `src/app/core/middleware.py`：每个请求生成 `X-Request-ID`（优先复用请求头中的值），写入 `request.state`、响应头，并注入每条日志，便于全链路问题定位

### Modbus 服务

`src/app/services/modbus_service.py` 基于 `AsyncModbusTcpClient`：

1. 读取保持寄存器地址 `100`（1 个寄存器，从站 ID 由配置 `MODBUS_SLAVE_ID` 决定，默认 1）
2. 原始值除以 10 换算为温度（如寄存器值 `250` → `25.0°C`）
3. 连接异常映射为 `DeviceOfflineError(503)`，协议异常映射为 `MODBUS_ERROR(502)`

## 本地 Modbus 模拟器

在没有真实 PLC/传感器的环境下，使用项目自带的模拟器进行联调。

### modbus_sim.py —— Modbus TCP 模拟器

启动一个 Modbus TCP 服务端：

- 监听 `0.0.0.0:5020`
- 从站 ID：`1`
- 保持寄存器（HR）地址 `0-199` 可读写
- 地址 `100` 初始值为 `250`（按 /10 换算即 25.0°C），供温度接口读取

```powershell
uv run modbus_sim.py
# 输出: Modbus TCP 模拟器已启动，监听 0.0.0.0:5020
```

### write_register.py —— 写入模拟器寄存器

作为 Modbus 客户端连接 `localhost:5020`，向从站 1 的保持寄存器地址 `100` 写入 `250`（25.0°C）。可修改脚本中的 `address` / `value` 参数来模拟不同的传感器读数：

```powershell
uv run write_register.py
# 输出: 写入成功: 地址 100 = 250
```

## 快速开始

### 1. 安装依赖

```powershell
uv sync
```

### 2. 配置环境变量

```powershell
Copy-Item .env.example .env
```

**注意**：`.env.example` 中 `MODBUS_PORT=502` 为真实设备常见端口；本地联调模拟器时需改为 **5020**：

```ini
MODBUS_HOST=localhost
MODBUS_PORT=5020
MODBUS_SLAVE_ID=1
```

### 3. 启动模拟器

```powershell
uv run modbus_sim.py
```

### 4. 启动服务

另开一个终端（在 `src` 目录下，使 `app` 包可被导入）：

```powershell
cd src
uv run uvicorn app.main:app --reload
```

服务默认监听 `http://localhost:8000`，交互式 API 文档位于 `http://localhost:8000/docs`。

### 5. 验证

```powershell
curl "http://localhost:8000/api/v1/sensor/temperature?line_id=line1"
```

响应示例：

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "line_id": "line1",
    "temperature": 25.0,
    "unit": "celsius",
    "raw_value": 250
  }
}
```

## 运行测试

测试使用 `pytest` + `httpx` 的 `ASGITransport` 直接调用 ASGI 应用，并通过依赖注入覆盖替换真实的 Modbus 服务，因此**无需启动模拟器或真实设备**。

- `tests/conftest.py`：`FakeModbusService` 伪造实现（可调温度值、可强制失败），`app` fixture 中通过 `app.dependency_overrides[get_modbus_service]` 替换，`client` fixture 提供 `AsyncClient`
- `tests/test_sensor.py`：覆盖成功读取、非法 `line_id`、缺少参数（均返回 422 `VALIDATION_ERROR`）、设备离线（503 `DEVICE_OFFLINE`）

`pyproject.toml` 中已配置 `asyncio_mode = "auto"` 与 `pythonpath = ["src"]`，直接运行即可：

```powershell
uv run pytest              # 运行全部测试
uv run pytest -v           # 显示详细用例
uv run pytest --cov=app    # 带覆盖率报告（pytest-cov）
```

## Docker 部署

### 单独构建镜像

`Dockerfile` 采用多阶段构建：

1. `builder` 阶段：基于 `uv` 官方镜像，按 `uv.lock` 冻结安装依赖（`--no-dev`）
2. 运行阶段：`python:3.12-slim`，仅拷贝 `.venv` 与 `src/`
3. 创建非 root 用户 `appuser`（uid 10001）运行，配置 `HEALTHCHECK` 探测 `/api/v1/health`，`EXPOSE 8000`

```powershell
docker build -t industrial-ai-service .
docker run -p 8000:8000 -e MODBUS_HOST=host.docker.internal -e MODBUS_PORT=5020 industrial-ai-service
```

### docker-compose 一键启动

`docker-compose.yml` 编排两个服务：

| 服务 | 说明 |
| --- | --- |
| `api` | 由当前目录 `Dockerfile` 构建，映射 `8000:8000`，环境变量 `APP_ENV=production`、`MODBUS_HOST=modbus-sim`、`MODBUS_PORT=502`，依赖 `modbus-sim` |
| `modbus-sim` | 使用 `oitc/modbus-server` 镜像作为 Modbus 服务端，映射 `502:502` |

```powershell
docker compose up --build
curl "http://localhost:8000/api/v1/sensor/temperature?line_id=line1"
```

> 注意：容器内 `MODBUS_HOST=modbus-sim` 走 compose 网络、端口 502（与本地 `modbus_sim.py` 的 5020 不同）；在 Windows 上通过本地模拟器连接容器时，可用 `host.docker.internal` 并指定 5020。

> 已知不一致：`pyproject.toml` 声明 `requires-python = ">=3.14"`，而 `Dockerfile` 使用 `python:3.12-slim`。实际构建前需统一 Python 版本（调整镜像标签或放宽 `requires-python`）。

## API 端点

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/health` | 根健康检查，返回 Hello World |
| GET | `/api/v1/health` | 健康检查，附带 Modbus 连接状态 |
| GET | `/api/v1/sensor/temperature?line_id=line[1-9]` | 读取产线温度（line_id 需匹配 `line1`~`line9`） |
| GET | `/test/business-error` | 测试端点：触发业务异常（`DEVICE_OFFLINE`，503） |
| GET | `/test/unknown-error` | 测试端点：触发未预期异常（`INTERNAL_ERROR`，500） |

## 配置项说明

配置通过 `.env` 文件加载（参见 `.env.example`），大小写敏感：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `APP_NAME` | `industrial-ai-service` | 应用名称 |
| `APP_ENV` | `development` | 运行环境 |
| `APP_LOG_LEVEL` | `INFO` | 日志级别 |
| `APP_HOST` | `0.0.0.0` | 服务监听地址 |
| `APP_PORT` | `8000` | 服务监听端口 |
| `MODBUS_HOST` | `localhost` | Modbus TCP 设备地址 |
| `MODBUS_PORT` | `502` | Modbus TCP 端口（本地模拟器为 5020） |
| `MODBUS_SLAVE_ID` | `1` | Modbus 从站 ID |
| `MODBUS_TIMEOUT` | `3.0` | Modbus 通信超时（秒） |
| `MQTT_BROKER` | `localhost` | MQTT Broker 地址（规划中） |
| `MQTT_PORT` | `1883` | MQTT 端口（规划中） |
| `MQTT_TOPIC_PREFIX` | `factory` | MQTT 主题前缀（规划中） |

## 路线图

- [ ] 设备控制接口（`src/app/api/routes/device.py`）
- [ ] MQTT 数据发布（`src/app/services/mqtt_service.py`）
- [x] 单元测试（`tests/`，含 FakeModbusService 与依赖注入覆盖）
- [x] Docker 容器化（`Dockerfile` 多阶段构建 + `docker-compose.yml` 编排）
