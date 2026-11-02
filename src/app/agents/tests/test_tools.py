import asyncio
from app.agents.tools import read_sensor_data
from app.dependencies.providers import get_modbus_service


async def main():
    # 关键：先建立 Modbus 连接，再调用工具
    modbus = get_modbus_service()
    await modbus.connect()
    print("Modbus 已连接")

    try:
        # 调用工具（走的是同一个单例，连接已经建立）
        result = await read_sensor_data.ainvoke({"line_id": "line1"})
        print("工具返回:", result)

        # 打印工具的 JSON Schema，确认 docstring 和参数约束被正确解析
        schema = read_sensor_data.args_schema.model_json_schema()
        print("工具 Schema:", schema)
    finally:
        # 测试结束，断开连接
        await modbus.disconnect()
        print("Modbus 已断开")


if __name__ == "__main__":
    asyncio.run(main())