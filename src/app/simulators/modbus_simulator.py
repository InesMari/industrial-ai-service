"""
可动态修改寄存器的 Modbus TCP 从站模拟器。
运行方式：uv run python -m app.simulators.modbus_simulator
"""

import asyncio
import logging
import random

from pymodbus.server import StartAsyncTcpServer, async_io
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusSlaveContext,
    ModbusServerContext,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# ===== 寄存器布局 =====
# 保持寄存器（功能码 03 读 / 06 写）
#   HR[0]  温度 * 10    （250 = 25.0°C）
#   HR[1]  压力 * 10    （1013 = 101.3 kPa）
#   HR[2]  振动 * 100   （150 = 1.50 mm/s）
#
# 线圈（功能码 01 读 / 05 写）
#   CO[0]  报警灯       （True = 亮）
#   CO[1]  冷却阀       （True = 开）

TEMP_ADDR = 100
PRESSURE_ADDR = 101
VIBRATION_ADDR = 102
ALARM_COIL = 0
COOLING_COIL = 1

class DynamicDataBlock(ModbusSequentialDataBlock):
    """带后台更新任务的保持寄存器数据块。"""

    def __init__(self):
        super().__init__(0x00, [0] * 200)
        self._running = False
        self._task = None
        # 25.0°C
        self.setValues(TEMP_ADDR,[250])
        # 101.3 kPa
        self.setValues(PRESSURE_ADDR,[1013])
        # 1.50 mm/s
        self.setValues(VIBRATION_ADDR,[150])

    def start_updater(self):
        self._running = True
        self._task = asyncio.create_task(self._update_loop())

    async def _update_loop(self):
        temp = 25.0
        while self._running:
            temp += random.uniform(-0.3, 0.8)
            temp = max(20.0, min(40.0, temp))
            pressure = 101.3 + (temp - 25.0) * 0.5 + random.uniform(-0.2, 0.2)
            vibration = 1.5 + random.uniform(-0.3, 0.8)
            vibration = max(0.5, min(4.0, vibration))

            self.setValues(TEMP_ADDR, [int(temp * 10)])
            self.setValues(PRESSURE_ADDR, [int(pressure * 10)])
            self.setValues(VIBRATION_ADDR, [int(vibration * 100)])

            logger.info(
                f"模拟更新: 温度={temp:.1f}°C 压力={pressure:.1f}kPa "
                f"振动={vibration:.2f}mm/s"
            )
            await asyncio.sleep(2)

    def stop_updater(self):
        self._running = False
        if self._task:
            self._task.cancel() 

async def main():
    hr_block = DynamicDataBlock()
    co_block = ModbusSequentialDataBlock(0x00, [0] * 100)
    store = ModbusSlaveContext(
        hr=hr_block, co=co_block, ir=hr_block, di=co_block,
        zero_mode=True,   # 客户端地址直接映射到数据块索引，不做 +1
    )
    context = ModbusServerContext(slaves={1: store}, single=False)

    hr_block.start_updater()

    logger.info("Modbus 从站启动，监听 0.0.0.0:5020，从站 ID=1")
    logger.info(f"温度: HR[{TEMP_ADDR}]，压力: HR[{PRESSURE_ADDR}]，"f"振动: HR[{VIBRATION_ADDR}]")

    try:
        await StartAsyncTcpServer(context=context, address=("0.0.0.0", 5020))
    except asyncio.CancelledError:
        hr_block.stop_updater()
        logger.info("Modbus 从站已停止")

if __name__ == "__main__":
    asyncio.run(main())