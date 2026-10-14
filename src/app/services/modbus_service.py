import logging
from app.core.exceptions import AppException,DeviceOfflineError
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException, ConnectionException

logger = logging.getLogger(__name__)

class ModbusService:
    def __init__(self, host: str, port: int, slave_id: int, timeout: float = 3.0):
        self.host = host
        self.port = port
        self.slave_id = slave_id
        self.timeout = timeout
        self.client: AsyncModbusTcpClient | None = None

    async def connect(self):
        """建立 Modbus TCP 连接"""
        logger.info(f"正在连接 Modbus {self.host}:{self.port}")
        self.client = AsyncModbusTcpClient(
            host=self.host,
            port=self.port,
            timeout=self.timeout,
        )
        await self.client.connect()
        if not self.client.connected:
            raise DeviceOfflineError(f"modbus@{self.host}:{self.port}")
        logger.info(f"Modbus 已连接 {self.host}:{self.port}")

    async def disconnect(self):
        """断开连接"""
        if self.client and self.client.connected:
            self.client.close()
            logger.info("Modbus 连接已关闭")

    async def read_temperature(self, line_id: str) -> dict :
        """读取温度，真实调用 Modbus 寄存器"""
        if not self.client or not self.client.connected:
            raise DeviceOfflineError(f"modbus@{self.host}:{self.port}")

        try:
            # 读取保持寄存器地址 100，读取 1 个寄存器
            rr = await self.client.read_holding_registers(
                address=100,
                count=1,
                slave=self.slave_id,
            )
        except ConnectionException as e:
            logger.error(f"Modbus 连接异常: {e}")
            raise DeviceOfflineError(f"modbus@{self.host}:{self.port}")
        except ModbusException as e:
            logger.error(f"Modbus 协议异常: {e}")
            raise AppException("MODBUS_ERROR", f"Modbus 通信错误: {e}", 502)

        if rr.isError():
            logger.error(f"Modbus 返回错误: {rr}")
            raise AppException("MODBUS_READ_ERROR", "读取寄存器失败", 502)

        # 模拟器默认寄存器值为 0，我们临时把值当作温度
        # 真实场景需要根据现场约定做量程换算
        raw_value = rr.registers[0]
        temperature = raw_value / 10.0  # 假设 250 表示 25.0°C

        return {
            "line_id": line_id,
            "temperature": temperature,
            "unit": "celsius",
            "raw_value": raw_value,
        }
