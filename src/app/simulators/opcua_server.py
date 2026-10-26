"""
带信息模型的 OPC UA 服务器。
节点树：
  Objects
    └── ProductionLine
          ├── Temperature  (Float, °C)
          ├── Pressure     (Float, kPa)
          ├── Vibration    (Float, mm/s)
          └── Status       (String)

运行方式：uv run python -m app.simulators.opcua_server
"""

import asyncio
import logging
import random

from asyncua import ua, Server

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# 自定义命名空间 URI
NAMESPACE_URI = "http://my.factory.namespace"

# 节点路径（给客户端用）
TEMP_PATH = "ProductionLine/Temperature"
PRESSURE_PATH = "ProductionLine/Pressure"
VIBRATION_PATH = "ProductionLine/Vibration"
STATUS_PATH = "ProductionLine/Status"

async def main():
    # ===== 1. 创建服务器 =====
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
    server.set_server_name("产线模拟 OPC UA 服务器")

    # ===== 2. 注册命名空间 =====
    # 返回值是命名空间索引，通常是 2（0 是 OPC UA 标准，1 是服务器自身）
    idx = await server.register_namespace(NAMESPACE_URI)
    logger.info(f"命名空间已注册: {NAMESPACE_URI} -> ns={idx}")

    # ===== 3. 在节点树上创建对象和变量 =====
    # 在标准 Objects 节点下创建 ProductionLine 对象
    production_line = await server.nodes.objects.add_object(idx, "ProductionLine")

    # 挂载温度节点，显式指定 NodeId 为 ProductionLine/Temperature
    temp_node = await production_line.add_variable(
        ua.NodeId(TEMP_PATH, idx),
        "Temperature",
        25.0,
        datatype=ua.VariantType.Double,
    )


    pressure_node = await production_line.add_variable(
        ua.NodeId(PRESSURE_PATH, idx),
        "Pressure",
        101.3,
        datatype=ua.VariantType.Double,
    )
    
    vibration_node = await production_line.add_variable(
        ua.NodeId(VIBRATION_PATH, idx),
        "Vibration",
        1.5,
        datatype=ua.VariantType.Double,
    )

    status_node = await production_line.add_variable(
        ua.NodeId(STATUS_PATH, idx),
        "Status",
        "RUNNING",
        datatype=ua.VariantType.String,
    )

    logger.info("节点树已创建:")
    logger.info(f"  ns={idx};s={TEMP_PATH}")
    logger.info(f"  ns={idx};s={PRESSURE_PATH}")
    logger.info(f"  ns={idx};s={VIBRATION_PATH}")
    logger.info(f"  ns={idx};s={STATUS_PATH}")

    # ===== 4. 启动服务器 =====
    async with server:
        logger.info("OPC UA 服务器已启动，监听 opc.tcp://0.0.0.0:4840")

        # 后台更新节点值
        async def update_loop():
            temp = 25.0
            while True:
                temp += random.uniform(-0.3, 0.8)
                temp = max(20.0, min(40.0, temp))
                pressure = 101.3 + (temp - 25.0) * 0.5 + random.uniform(-0.2, 0.2)
                vibration = 1.5 + random.uniform(-0.3, 0.8)
                vibration = max(0.5, min(4.0, vibration))

                await temp_node.write_value(
                    ua.Variant(round(temp, 1), ua.VariantType.Double)
                )
                await pressure_node.write_value(
                    ua.Variant(round(pressure, 1), ua.VariantType.Double)
                )
                await vibration_node.write_value(
                    ua.Variant(round(vibration, 2), ua.VariantType.Double)
                )

                logger.info(
                    f"OPC UA 更新: 温度={temp:.1f}°C "
                    f"压力={pressure:.1f}kPa 振动={vibration:.2f}mm/s"
                )
                await asyncio.sleep(2)
        
        updater = asyncio.create_task(update_loop())

        try:
            # 保持服务器运行
            await asyncio.sleep(1e9)
        except asyncio.CancelledError:
            updater.cancel()
            logger.info("OPC UA 服务器已停止")



if __name__ == "__main__":
    asyncio.run(main())






