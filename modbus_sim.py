from pymodbus.server import StartTcpServer
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusSlaveContext,
    ModbusServerContext,
)

# 地址 0-199 可读写，地址 100 初始值 250（25.0°C）
hr_values = [0] * 200
hr_values[100] = 250

block = ModbusSequentialDataBlock(0, hr_values)
store = ModbusSlaveContext(hr=block)
context = ModbusServerContext(slaves={1: store}, single=False)

print("Modbus TCP 模拟器已启动，监听 0.0.0.0:5020")
StartTcpServer(context=context, address=("0.0.0.0", 5020))